"""
BLE Security System — Kivy GUI
Authors: manasvi-0523, Mithun Gowda B (@mithun50)
"""

import asyncio
import math
import os
import sys
import threading
import time as _time
from datetime import datetime

# Path setup
sys.path.insert(0, os.path.dirname(__file__))

os.environ['KIVY_LOG_LEVEL'] = 'error'
os.environ['KCFG_KIVY_LOG_LEVEL'] = 'error'
os.environ.setdefault('KIVY_GL_BACKEND', 'angle_sdl2')

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (StringProperty, NumericProperty,
                              ListProperty, BooleanProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from kivy.graphics import (Color, Rectangle, RoundedRectangle,
                            Line, Ellipse)
from kivy.metrics import dp

from scanner.ble_scanner import scan, detect_duplicate_macs
from scanner.distance import (estimate_distance, get_proximity_zone,
                              format_distance_value, get_zone_color)
from db.registry import (init_db, get_db, upsert_device, build_training_matrix,
                         check_spoofing, update_anomaly_result, get_registry_stats)
from ai_model.anomaly_detector import (train, train_ocsvm, predict_ensemble,
                                       normalize_risk, risk_label, label)
from blockchain.blockchain import Blockchain
from blockchain.eth_registry import (
    eth_is_trusted_batch, eth_log_anomaly, eth_enabled,
)
from alerts.alert_system import (
    trigger, alert_unknown_device, alert_duplicate_mac, alert_cleared,
)

SCAN_DURATION = 15

# ══════════════════════════════════════════════════════════════
#  KV DESIGN
# ══════════════════════════════════════════════════════════════
KV = """
#:import dp kivy.metrics.dp
#:import Animation kivy.animation.Animation

<MetricCard>:
    orientation: 'vertical'
    padding: dp(16), dp(12)
    spacing: dp(4)
    size_hint_y: None
    height: dp(110)
    canvas.before:
        Color:
            rgba: root.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
        Color:
            rgba: root.accent[0], root.accent[1], root.accent[2], 0.8
        RoundedRectangle:
            pos: self.x, self.top - dp(3)
            size: self.width, dp(3)
            radius: [dp(12), dp(12), 0, 0]
    Widget:
        size_hint_y: 0.05
    Label:
        text: root.metric_value
        font_size: dp(36)
        bold: True
        color: root.accent
        size_hint_y: 0.45
        halign: 'center'
    Label:
        text: root.metric_title
        font_size: dp(11)
        color: 0.5, 0.5, 0.58, 1
        size_hint_y: 0.25
        halign: 'center'
        text_size: self.width, None
    Label:
        text: root.metric_sub
        font_size: dp(9)
        color: 0.38, 0.38, 0.44, 1
        size_hint_y: 0.2
        halign: 'center'
        text_size: self.width, None

<DeviceEntry>:
    size_hint_y: None
    height: dp(48)
    padding: dp(16), dp(6)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: root.row_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    BoxLayout:
        size_hint_x: 0.04
        Label:
            text: root.dot
            font_size: dp(10)
            color: root.dot_color
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.28
        Label:
            text: root.name
            font_size: dp(13)
            bold: True
            color: 0.88, 0.88, 0.92, 1
            halign: 'left'
            text_size: self.width, None
            shorten: True
            shorten_from: 'right'
        Label:
            text: root.mac
            font_size: dp(10)
            color: 0.45, 0.45, 0.52, 1
            halign: 'left'
            text_size: self.width, None
    BoxLayout:
        size_hint_x: 0.10
        Label:
            text: root.scan_type
            font_size: dp(10)
            bold: True
            color: (0.2, 0.78, 0.85, 1) if root.scan_type == 'BLE' else (0.82, 0.7, 0.15, 1)
            halign: 'center'
    BoxLayout:
        size_hint_x: 0.14
        Label:
            text: root.score_text
            font_size: dp(12)
            color: root.dot_color
            halign: 'center'
    BoxLayout:
        size_hint_x: 0.12
        padding: dp(4), dp(8)
        canvas.before:
            Color:
                rgba: root.badge_bg
            RoundedRectangle:
                pos: self.pos[0] + dp(8), self.pos[1] + dp(10)
                size: self.width - dp(16), self.height - dp(20)
                radius: [dp(4)]
        Label:
            text: root.action
            font_size: dp(10)
            bold: True
            color: root.badge_text
            halign: 'center'
    BoxLayout:
        size_hint_x: 0.10
        padding: dp(4), dp(8)
        canvas.before:
            Color:
                rgba: root.risk_bg
            RoundedRectangle:
                pos: self.pos[0] + dp(4), self.pos[1] + dp(10)
                size: self.width - dp(8), self.height - dp(20)
                radius: [dp(4)]
        Label:
            text: root.risk_text
            font_size: dp(9)
            bold: True
            color: root.risk_color
            halign: 'center'
    BoxLayout:
        size_hint_x: 0.08
        Label:
            text: root.rssi_text
            font_size: dp(10)
            color: 0.5, 0.5, 0.58, 1
            halign: 'center'
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.12
        Label:
            text: root.distance_text
            font_size: dp(11)
            bold: True
            color: root.zone_color
            halign: 'center'
        Label:
            text: root.zone_text
            font_size: dp(8)
            color: root.zone_color
            halign: 'center'
"""


# ══════════════════════════════════════════════════════════════
#  CUSTOM WIDGETS
# ══════════════════════════════════════════════════════════════

class MetricCard(BoxLayout):
    metric_title = StringProperty("METRIC")
    metric_value = StringProperty("—")
    metric_sub = StringProperty("")
    accent = ListProperty([0, 0.88, 0.88, 1])
    bg = ListProperty([0.1, 0.1, 0.14, 1])


class DeviceEntry(BoxLayout):
    name = StringProperty("")
    mac = StringProperty("")
    scan_type = StringProperty("BLE")
    score_text = StringProperty("—")
    action = StringProperty("—")
    dot = StringProperty("●")
    dot_color = ListProperty([0, 0.85, 0.42, 1])
    row_color = ListProperty([0.08, 0.08, 0.11, 1])
    badge_bg = ListProperty([0.06, 0.15, 0.08, 1])
    badge_text = ListProperty([0, 0.85, 0.42, 1])
    risk_text = StringProperty("LOW")
    risk_color = ListProperty([0, 0.85, 0.42, 1])
    risk_bg = ListProperty([0.04, 0.14, 0.06, 1])
    rssi_text = StringProperty("—")
    distance_text = StringProperty("—")
    zone_text = StringProperty("")
    zone_color = ListProperty([0.45, 0.45, 0.52, 1])


# ──────────────────────────────────────────────────────────────
#  CHART WIDGETS  (pure Kivy canvas — no external deps)
# ──────────────────────────────────────────────────────────────

class DonutChart(Widget):
    """Draws a donut / pie chart from a list of (value, color) segments."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self._segments = []
        self._center_text = ""
        self._center_sub = ""
        self.bind(pos=self._redraw, size=self._redraw)

    def set_data(self, segments, center_text="", center_sub=""):
        self._segments = segments
        self._center_text = center_text
        self._center_sub = center_sub
        self._redraw()

    def _redraw(self, *_):
        self.canvas.after.clear()
        self.clear_widgets()
        if not self._segments:
            return
        total = sum(s[0] for s in self._segments)
        if total == 0:
            return

        cx, cy = self.center_x, self.center_y
        radius = min(self.width, self.height) * 0.40
        inner = radius * 0.55
        angle = 0.0

        with self.canvas.after:
            for val, col in self._segments:
                sweep = (val / total) * 360
                Color(*col)
                Ellipse(pos=(cx - radius, cy - radius),
                        size=(radius * 2, radius * 2),
                        angle_start=angle, angle_end=angle + sweep)
                angle += sweep
            # Inner hole
            Color(0.07, 0.07, 0.1, 1)
            Ellipse(pos=(cx - inner, cy - inner),
                    size=(inner * 2, inner * 2))

        lbl = Label(text=self._center_text, font_size=dp(22), bold=True,
                    color=(0.9, 0.9, 0.95, 1), halign='center',
                    pos=(cx - dp(60), cy - dp(8)),
                    size=(dp(120), dp(28)))
        self.add_widget(lbl)
        if self._center_sub:
            sub = Label(text=self._center_sub, font_size=dp(9),
                        color=(0.45, 0.45, 0.52, 1), halign='center',
                        pos=(cx - dp(60), cy - dp(26)),
                        size=(dp(120), dp(20)))
            self.add_widget(sub)


class HBarChart(Widget):
    """Horizontal bar chart drawn on canvas."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self._bars = []
        self._title = ""
        self.bind(pos=self._redraw, size=self._redraw)

    def set_data(self, bars, title=""):
        self._bars = bars
        self._title = title
        self._redraw()

    def _redraw(self, *_):
        self.canvas.after.clear()
        self.clear_widgets()
        if not self._bars:
            return

        max_val = max((abs(b[1]) for b in self._bars), default=1) or 1
        n = len(self._bars)
        bar_h = min(dp(22), (self.height - dp(30)) / max(n, 1))
        gap = dp(4)
        x0 = self.x + dp(100)
        bar_w_max = self.width - dp(160)
        y = self.top - dp(28)

        if self._title:
            t = Label(text=f"[b]{self._title}[/b]", markup=True,
                      font_size=dp(11), color=(0.55, 0.55, 0.62, 1),
                      pos=(self.x + dp(8), y - dp(2)),
                      size=(dp(200), dp(18)), halign='left')
            t.bind(size=t.setter('text_size'))
            self.add_widget(t)
            y -= dp(24)

        with self.canvas.after:
            for lbl_text, val, _, col in self._bars:
                frac = abs(val) / max_val if max_val else 0
                bw = max(bar_w_max * frac, dp(4))
                # Track
                Color(0.12, 0.12, 0.16, 1)
                RoundedRectangle(pos=(x0, y - bar_h + gap / 2),
                                 size=(bar_w_max, bar_h - gap),
                                 radius=[dp(4)])
                # Fill
                Color(*col)
                RoundedRectangle(pos=(x0, y - bar_h + gap / 2),
                                 size=(bw, bar_h - gap),
                                 radius=[dp(4)])
                y -= bar_h

        y2 = self.top - dp(28)
        if self._title:
            y2 -= dp(24)
        for lbl_text, val, _, col in self._bars:
            ll = Label(text=lbl_text, font_size=dp(9),
                       color=(0.6, 0.6, 0.68, 1), halign='right',
                       pos=(self.x, y2 - bar_h + gap / 2),
                       size=(dp(92), bar_h - gap))
            ll.bind(size=ll.setter('text_size'))
            self.add_widget(ll)
            vl = Label(
                text=str(val) if isinstance(val, int) else f"{val:.2f}",
                font_size=dp(9), bold=True, color=col, halign='left',
                pos=(x0 + bar_w_max + dp(6), y2 - bar_h + gap / 2),
                size=(dp(50), bar_h - gap))
            vl.bind(size=vl.setter('text_size'))
            self.add_widget(vl)
            y2 -= bar_h


class FlowDiagram(Widget):
    """Pipeline flow: connected nodes showing scan phases."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self._phases = []
        self.bind(pos=self._redraw, size=self._redraw)

    def set_phases(self, phases):
        self._phases = phases
        self._redraw()

    def _redraw(self, *_):
        self.canvas.after.clear()
        self.clear_widgets()
        if not self._phases:
            return

        n = len(self._phases)
        node_r = dp(18)
        total_w = self.width - dp(40)
        step = total_w / max(n - 1, 1) if n > 1 else 0
        cy = self.center_y + dp(6)
        x_start = self.x + dp(20)

        with self.canvas.after:
            for i, (name, status, col) in enumerate(self._phases):
                cx = x_start + i * step
                # Connection line
                if i < n - 1:
                    next_x = x_start + (i + 1) * step
                    Color(0.2, 0.2, 0.28, 1)
                    Line(points=[cx + node_r, cy,
                                 next_x - node_r, cy],
                         width=dp(1.5))
                    ax = next_x - node_r - dp(2)
                    Color(*col[:3], 0.4)
                    Line(points=[ax - dp(6), cy + dp(4),
                                 ax, cy,
                                 ax - dp(6), cy - dp(4)],
                         width=dp(1))
                # Glow ring
                Color(*col[:3], 0.15)
                Ellipse(pos=(cx - node_r - dp(3), cy - node_r - dp(3)),
                        size=(node_r * 2 + dp(6), node_r * 2 + dp(6)))
                # Node
                Color(*col)
                Ellipse(pos=(cx - node_r, cy - node_r),
                        size=(node_r * 2, node_r * 2))
                # Checkmark if done
                if status == 'done':
                    Color(0.05, 0.05, 0.07, 1)
                    Ellipse(pos=(cx - dp(5), cy - dp(5)),
                            size=(dp(10), dp(10)))
                    Color(*col)
                    Line(points=[cx - dp(3), cy,
                                 cx - dp(1), cy - dp(3),
                                 cx + dp(4), cy + dp(3)],
                         width=dp(1.2))

        for i, (name, status, col) in enumerate(self._phases):
            cx = x_start + i * step
            num = Label(text=str(i + 1), font_size=dp(12), bold=True,
                        color=((0.05, 0.05, 0.07, 1) if status == 'done'
                               else (1, 1, 1, 0.9)),
                        halign='center', valign='center',
                        pos=(cx - dp(14), cy - dp(10)),
                        size=(dp(28), dp(20)))
            self.add_widget(num)
            nl = Label(text=name, font_size=dp(9),
                       color=(0.55, 0.55, 0.62, 1),
                       halign='center', valign='top',
                       pos=(cx - dp(46), cy - node_r - dp(28)),
                       size=(dp(92), dp(22)))
            nl.bind(size=nl.setter('text_size'))
            self.add_widget(nl)
            st = Label(text=status.upper(), font_size=dp(7), bold=True,
                       color=col, halign='center', valign='top',
                       pos=(cx - dp(30), cy - node_r - dp(40)),
                       size=(dp(60), dp(14)))
            st.bind(size=st.setter('text_size'))
            self.add_widget(st)


# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════

class BLESecurityApp(App):
    title = "BLE Security System"

    def build(self):
        Builder.load_string(KV)
        Window.clearcolor = (0.05, 0.05, 0.07, 1)
        Window.size = (1080, 740)
        icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.ico')
        if os.path.exists(icon_path):
            Window.icon = icon_path
        Window.minimum_width = 900
        Window.minimum_height = 620

        self._scanning = False
        self._scan_data = {}

        root = BoxLayout(orientation='vertical', padding=dp(20),
                         spacing=dp(14))

        # ── TOP BAR ───────────────────────────────────────────
        top = BoxLayout(size_hint_y=None, height=dp(44))
        title_box = BoxLayout(orientation='vertical', size_hint_x=0.45)
        t1 = Label(text="[b]BLE Security System[/b]", markup=True,
                    font_size=dp(18), color=(0.92, 0.92, 0.95, 1),
                    halign='left', valign='bottom', size_hint_y=0.6)
        t1.bind(size=t1.setter('text_size'))
        t2 = Label(text="AI + Blockchain  ·  manasvi-0523 & mithun50",
                    font_size=dp(9), color=(0.4, 0.4, 0.48, 1),
                    halign='left', valign='top', size_hint_y=0.4)
        t2.bind(size=t2.setter('text_size'))
        title_box.add_widget(t1)
        title_box.add_widget(t2)
        top.add_widget(title_box)

        self.status_box = BoxLayout(size_hint_x=0.2)
        self.status_label = Label(
            text="  READY  ", font_size=dp(10), bold=True,
            color=(0, 0.85, 0.42, 1), halign='center', valign='center')
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.status_box.add_widget(self.status_label)
        top.add_widget(self.status_box)

        self.time_label = Label(
            text="", font_size=dp(10), color=(0.38, 0.38, 0.44, 1),
            halign='right', valign='center', size_hint_x=0.35)
        self.time_label.bind(size=self.time_label.setter('text_size'))
        Clock.schedule_interval(self._tick_time, 1)
        top.add_widget(self.time_label)
        root.add_widget(top)

        # ── METRICS ROW ──────────────────────────────────────
        cards = BoxLayout(size_hint_y=None, height=dp(110), spacing=dp(12))
        self.m_total = MetricCard(metric_title="TOTAL DEVICES",
                                  accent=[0.18, 0.72, 0.92, 1])
        self.m_ble = MetricCard(metric_title="BLE",
                                accent=[0, 0.85, 0.42, 1])
        self.m_classic = MetricCard(metric_title="CLASSIC BT",
                                    accent=[0.85, 0.72, 0.12, 1])
        self.m_anomalies = MetricCard(metric_title="THREATS",
                                      accent=[0.92, 0.22, 0.22, 1])
        self.m_chain = MetricCard(metric_title="CHAIN BLOCKS",
                                  accent=[0.6, 0.42, 0.92, 1])
        for c in [self.m_total, self.m_ble, self.m_classic,
                  self.m_anomalies, self.m_chain]:
            cards.add_widget(c)
        root.add_widget(cards)

        # ── PROGRESS BAR ─────────────────────────────────────
        prog_row = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(8))
        self.phase_label = Label(
            text="", font_size=dp(10), color=(0.5, 0.5, 0.58, 1),
            halign='left', size_hint_x=0.4)
        self.phase_label.bind(size=self.phase_label.setter('text_size'))
        prog_row.add_widget(self.phase_label)
        self.prog_bar_container = BoxLayout(size_hint_x=0.6,
                                            padding=(0, dp(8)))
        self.prog_bar = ProgressBar(max=100, value=0)
        self.prog_bar.height = dp(4)
        self.prog_bar_container.add_widget(self.prog_bar)
        prog_row.add_widget(self.prog_bar_container)
        root.add_widget(prog_row)

        # ── TAB BUTTONS ───────────────────────────────────────
        tab_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))

        self.tab_devices_btn = Button(
            text="DEVICES", font_size=dp(11), bold=True,
            size_hint_x=0.14, background_normal='',
            background_color=(0.12, 0.52, 0.52, 1), color=(1, 1, 1, 1))
        with self.tab_devices_btn.canvas.before:
            Color(0.12, 0.52, 0.52, 1)
            self._tdb_bg = RoundedRectangle(
                pos=self.tab_devices_btn.pos,
                size=self.tab_devices_btn.size, radius=[dp(6)])
        self.tab_devices_btn.bind(
            pos=lambda w, p: setattr(self._tdb_bg, 'pos', p),
            size=lambda w, s: setattr(self._tdb_bg, 'size', s))
        self.tab_devices_btn.bind(
            on_press=lambda *_: self._switch_tab('devices'))

        self.tab_analytics_btn = Button(
            text="ANALYTICS", font_size=dp(11), bold=True,
            size_hint_x=0.14, background_normal='',
            background_color=(0.1, 0.1, 0.14, 1),
            color=(0.5, 0.5, 0.58, 1))
        with self.tab_analytics_btn.canvas.before:
            Color(0.1, 0.1, 0.14, 1)
            self._tab_bg = RoundedRectangle(
                pos=self.tab_analytics_btn.pos,
                size=self.tab_analytics_btn.size, radius=[dp(6)])
        self.tab_analytics_btn.bind(
            pos=lambda w, p: setattr(self._tab_bg, 'pos', p),
            size=lambda w, s: setattr(self._tab_bg, 'size', s))
        self.tab_analytics_btn.bind(
            on_press=lambda *_: self._switch_tab('analytics'))

        self.tab_admin_btn = Button(
            text="ADMIN", font_size=dp(11), bold=True,
            size_hint_x=0.14, background_normal='',
            background_color=(0.1, 0.1, 0.14, 1),
            color=(0.5, 0.5, 0.58, 1))
        with self.tab_admin_btn.canvas.before:
            Color(0.1, 0.1, 0.14, 1)
            self._tad_bg = RoundedRectangle(
                pos=self.tab_admin_btn.pos,
                size=self.tab_admin_btn.size, radius=[dp(6)])
        self.tab_admin_btn.bind(
            pos=lambda w, p: setattr(self._tad_bg, 'pos', p),
            size=lambda w, s: setattr(self._tad_bg, 'size', s))
        self.tab_admin_btn.bind(
            on_press=lambda *_: self._switch_tab('admin'))

        tab_row.add_widget(self.tab_devices_btn)
        tab_row.add_widget(self.tab_analytics_btn)
        tab_row.add_widget(self.tab_admin_btn)
        tab_row.add_widget(Widget())
        root.add_widget(tab_row)

        # ── CONTENT AREA ──────────────────────────────────────
        self.content_area = BoxLayout()

        # --- Devices view ---
        self.devices_view = BoxLayout(orientation='vertical', spacing=dp(4))
        col_hdr = BoxLayout(size_hint_y=None, height=dp(28),
                            padding=(dp(16), 0), spacing=dp(6))
        hdrs = [("", 0.04), ("DEVICE", 0.28), ("TYPE", 0.10),
                ("SCORE", 0.14), ("STATUS", 0.12), ("RISK", 0.10),
                ("RSSI", 0.08), ("DISTANCE", 0.12)]
        for txt, w in hdrs:
            h = Label(text=txt, font_size=dp(9), bold=True,
                      color=(0.35, 0.35, 0.42, 1),
                      halign='left' if txt == 'DEVICE' else 'center',
                      size_hint_x=w)
            h.bind(size=h.setter('text_size'))
            col_hdr.add_widget(h)
        self.devices_view.add_widget(col_hdr)

        table_wrap = BoxLayout()
        with table_wrap.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._tw_bg = RoundedRectangle(
                pos=table_wrap.pos, size=table_wrap.size, radius=[dp(12)])
        table_wrap.bind(
            pos=lambda w, p: setattr(self._tw_bg, 'pos', p),
            size=lambda w, s: setattr(self._tw_bg, 'size', s))

        self.table_scroll = ScrollView(
            do_scroll_x=False, bar_width=dp(4),
            bar_color=(0.3, 0.3, 0.38, 0.5))
        self.table_grid = GridLayout(
            cols=1, spacing=dp(4), size_hint_y=None, padding=dp(6))
        self.table_grid.bind(
            minimum_height=self.table_grid.setter('height'))

        self.empty_label = Label(
            text="No devices scanned yet.\nPress START SCAN to begin.",
            font_size=dp(13), color=(0.35, 0.35, 0.42, 1),
            halign='center', valign='center')
        self.empty_label.bind(size=self.empty_label.setter('text_size'))
        self.table_grid.add_widget(self.empty_label)

        self.table_scroll.add_widget(self.table_grid)
        table_wrap.add_widget(self.table_scroll)
        self.devices_view.add_widget(table_wrap)

        # --- Analytics view ---
        self.analytics_view = self._build_analytics_view()

        # --- Admin view ---
        self.admin_view = self._build_admin_view()

        self.content_area.add_widget(self.devices_view)
        self._current_tab = 'devices'
        root.add_widget(self.content_area)

        # ── BOTTOM BAR ────────────────────────────────────────
        bottom = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        self.scan_btn = Button(
            text="START SCAN", font_size=dp(13), bold=True,
            size_hint_x=0.22, background_normal='',
            background_color=(0.08, 0.52, 0.52, 1), color=(1, 1, 1, 1))
        with self.scan_btn.canvas.before:
            Color(0.08, 0.52, 0.52, 1)
            self._sb_bg = RoundedRectangle(
                pos=self.scan_btn.pos,
                size=self.scan_btn.size, radius=[dp(8)])
        self.scan_btn.bind(
            pos=lambda w, p: setattr(self._sb_bg, 'pos', p),
            size=lambda w, s: setattr(self._sb_bg, 'size', s))
        self.scan_btn.bind(on_press=self._on_scan)

        bottom.add_widget(self.scan_btn)
        bottom.add_widget(Widget(size_hint_x=0.63))
        ver = Label(text=f"v1.0  ·  Python {sys.version.split()[0]}",
                    font_size=dp(9), color=(0.28, 0.28, 0.34, 1),
                    halign='right', valign='center', size_hint_x=0.15)
        ver.bind(size=ver.setter('text_size'))
        bottom.add_widget(ver)
        root.add_widget(bottom)

        return root

    # ── BUILD ANALYTICS VIEW ──────────────────────────────────

    def _build_analytics_view(self):
        view = BoxLayout(orientation='vertical', spacing=dp(10))

        # ── Top row: Donut + RSSI bars ────────────────────────
        top_row = BoxLayout(spacing=dp(12), size_hint_y=0.55)

        # Donut chart card
        donut_card = BoxLayout(orientation='vertical', size_hint_x=0.4,
                               padding=dp(8))
        with donut_card.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._dc_bg = RoundedRectangle(
                pos=donut_card.pos, size=donut_card.size, radius=[dp(12)])
        donut_card.bind(
            pos=lambda w, p: setattr(self._dc_bg, 'pos', p),
            size=lambda w, s: setattr(self._dc_bg, 'size', s))

        dc_title = Label(
            text="[b]DEVICE TYPE DISTRIBUTION[/b]", markup=True,
            font_size=dp(10), color=(0.5, 0.5, 0.58, 1),
            size_hint_y=None, height=dp(24), halign='left')
        dc_title.bind(size=dc_title.setter('text_size'))
        donut_card.add_widget(dc_title)
        self.donut_chart = DonutChart()
        donut_card.add_widget(self.donut_chart)

        legend = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(16),
                           padding=(dp(12), 0))
        for txt, col in [("BLE", (0, 0.85, 0.42, 1)),
                         ("Classic", (0.85, 0.72, 0.12, 1)),
                         ("Threats", (0.92, 0.22, 0.22, 1))]:
            lb = BoxLayout(size_hint_x=None, width=dp(80), spacing=dp(4))
            dot = Label(text="●", font_size=dp(10), color=col,
                        size_hint_x=None, width=dp(14))
            name_l = Label(text=txt, font_size=dp(9),
                           color=(0.5, 0.5, 0.58, 1))
            lb.add_widget(dot)
            lb.add_widget(name_l)
            legend.add_widget(lb)
        donut_card.add_widget(legend)
        top_row.add_widget(donut_card)

        # RSSI bar chart card
        rssi_card = BoxLayout(orientation='vertical', size_hint_x=0.6,
                              padding=dp(8))
        with rssi_card.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._rc_bg = RoundedRectangle(
                pos=rssi_card.pos, size=rssi_card.size, radius=[dp(12)])
        rssi_card.bind(
            pos=lambda w, p: setattr(self._rc_bg, 'pos', p),
            size=lambda w, s: setattr(self._rc_bg, 'size', s))
        self.rssi_chart = HBarChart()
        rssi_card.add_widget(self.rssi_chart)
        top_row.add_widget(rssi_card)

        view.add_widget(top_row)

        # ── Bottom row: Scores + Pipeline flow ────────────────
        bottom_row = BoxLayout(spacing=dp(12), size_hint_y=0.45)

        # Anomaly score bars
        score_card = BoxLayout(orientation='vertical', size_hint_x=0.5,
                               padding=dp(8))
        with score_card.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._sc_bg = RoundedRectangle(
                pos=score_card.pos, size=score_card.size, radius=[dp(12)])
        score_card.bind(
            pos=lambda w, p: setattr(self._sc_bg, 'pos', p),
            size=lambda w, s: setattr(self._sc_bg, 'size', s))
        self.score_chart = HBarChart()
        score_card.add_widget(self.score_chart)
        bottom_row.add_widget(score_card)

        # Pipeline flow diagram
        flow_card = BoxLayout(orientation='vertical', size_hint_x=0.5,
                              padding=dp(8))
        with flow_card.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._fc_bg = RoundedRectangle(
                pos=flow_card.pos, size=flow_card.size, radius=[dp(12)])
        flow_card.bind(
            pos=lambda w, p: setattr(self._fc_bg, 'pos', p),
            size=lambda w, s: setattr(self._fc_bg, 'size', s))

        fc_title = Label(
            text="[b]PIPELINE FLOW[/b]", markup=True,
            font_size=dp(10), color=(0.5, 0.5, 0.58, 1),
            size_hint_y=None, height=dp(24), halign='left')
        fc_title.bind(size=fc_title.setter('text_size'))
        flow_card.add_widget(fc_title)
        self.flow_diagram = FlowDiagram()
        flow_card.add_widget(self.flow_diagram)

        self.flow_diagram.set_phases([
            ("ETH Registry", "pending", [0.3, 0.3, 0.38, 1]),
            ("Dup MAC",      "pending", [0.3, 0.3, 0.38, 1]),
            ("AI Check",     "pending", [0.3, 0.3, 0.38, 1]),
            ("CLEARED",      "pending", [0.3, 0.3, 0.38, 1]),
        ])

        bottom_row.add_widget(flow_card)
        view.add_widget(bottom_row)

        return view

    # ── TAB SWITCHING ─────────────────────────────────────────

    def _switch_tab(self, tab):
        if tab == self._current_tab:
            return
        self.content_area.clear_widgets()

        _inactive = (0.1, 0.1, 0.14, 1)
        _inactive_text = (0.5, 0.5, 0.58, 1)
        _active = (0.12, 0.52, 0.52, 1)
        _active_text = (1, 1, 1, 1)

        # Reset all tabs
        for btn in (self.tab_devices_btn, self.tab_analytics_btn,
                    self.tab_admin_btn):
            btn.background_color = _inactive
            btn.color = _inactive_text

        if tab == 'devices':
            self.content_area.add_widget(self.devices_view)
            self.tab_devices_btn.background_color = _active
            self.tab_devices_btn.color = _active_text
        elif tab == 'analytics':
            self.content_area.add_widget(self.analytics_view)
            self.tab_analytics_btn.background_color = _active
            self.tab_analytics_btn.color = _active_text
        else:  # admin
            self.content_area.add_widget(self.admin_view)
            self.tab_admin_btn.background_color = (0.55, 0.22, 0.78, 1)
            self.tab_admin_btn.color = _active_text
            # Refresh ETH status every time admin tab is opened
            Clock.schedule_once(lambda dt: self._admin_refresh_status(), 0.1)

        self._current_tab = tab

    # ══════════════════════════════════════════════════════════
    #  ADMIN TAB
    # ══════════════════════════════════════════════════════════

    def _build_admin_view(self):
        """
        Admin panel for on-chain device registry management.
        Left column: ETH status + action buttons.
        Right column: Form inputs + scrollable transaction log.
        """
        view = BoxLayout(orientation='horizontal', spacing=dp(12))

        # ── LEFT COLUMN ───────────────────────────────────────
        left = BoxLayout(orientation='vertical', spacing=dp(10),
                         size_hint_x=0.36, padding=dp(4))

        # ETH status card
        status_card = BoxLayout(orientation='vertical', padding=dp(12),
                                spacing=dp(6), size_hint_y=None, height=dp(180))
        with status_card.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._asc_bg = RoundedRectangle(
                pos=status_card.pos, size=status_card.size, radius=[dp(12)])
        status_card.bind(
            pos=lambda w, p: setattr(self._asc_bg, 'pos', p),
            size=lambda w, s: setattr(self._asc_bg, 'size', s))

        sc_title = Label(
            text="[b]ETHEREUM STATUS[/b]", markup=True,
            font_size=dp(10), color=(0.5, 0.5, 0.58, 1),
            size_hint_y=None, height=dp(20), halign='left')
        sc_title.bind(size=sc_title.setter('text_size'))
        status_card.add_widget(sc_title)

        self.eth_dot = Label(
            text="● OFFLINE", font_size=dp(13), bold=True,
            color=(0.6, 0.6, 0.68, 1),
            size_hint_y=None, height=dp(24), halign='left')
        self.eth_dot.bind(size=self.eth_dot.setter('text_size'))
        status_card.add_widget(self.eth_dot)

        self.eth_info = Label(
            text="Set ETH_RPC_URL and\nCONTRACT_ADDRESS in .env",
            font_size=dp(9), color=(0.4, 0.4, 0.48, 1),
            halign='left', valign='top')
        self.eth_info.bind(size=self.eth_info.setter('text_size'))
        status_card.add_widget(self.eth_info)

        refresh_btn = self._make_btn("REFRESH STATUS", (0.18, 0.18, 0.24, 1),
                                     (0.7, 0.7, 0.78, 1), height=dp(32))
        refresh_btn.bind(on_press=lambda *_: self._admin_refresh_status())
        status_card.add_widget(refresh_btn)

        left.add_widget(status_card)

        # Action shortcut buttons
        actions_title = Label(
            text="[b]QUICK ACTIONS[/b]", markup=True,
            font_size=dp(10), color=(0.5, 0.5, 0.58, 1),
            size_hint_y=None, height=dp(24), halign='left')
        actions_title.bind(size=actions_title.setter('text_size'))
        left.add_widget(actions_title)

        btn_data = [
            ("REGISTER DEVICE",  (0.08, 0.36, 0.18, 1), (0, 0.85, 0.42, 1),  'register'),
            ("REVOKE DEVICE",    (0.36, 0.08, 0.08, 1), (0.92, 0.22, 0.22, 1), 'revoke'),
            ("CHECK DEVICE",     (0.06, 0.18, 0.36, 1), (0.18, 0.72, 0.92, 1), 'check'),
        ]
        for label_txt, bg, fg, mode in btn_data:
            b = self._make_btn(label_txt, bg, fg)
            b.bind(on_press=lambda *_, m=mode: self._admin_set_mode(m))
            left.add_widget(b)

        left.add_widget(Widget())  # spacer
        view.add_widget(left)

        # ── RIGHT COLUMN ──────────────────────────────────────
        right = BoxLayout(orientation='vertical', spacing=dp(10))

        # Form card
        form_card = BoxLayout(orientation='vertical', padding=dp(14),
                              spacing=dp(8), size_hint_y=None, height=dp(220))
        with form_card.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._afc_bg = RoundedRectangle(
                pos=form_card.pos, size=form_card.size, radius=[dp(12)])
        form_card.bind(
            pos=lambda w, p: setattr(self._afc_bg, 'pos', p),
            size=lambda w, s: setattr(self._afc_bg, 'size', s))

        self.admin_form_title = Label(
            text="[b]REGISTER DEVICE[/b]", markup=True,
            font_size=dp(11), color=(0, 0.85, 0.42, 1),
            size_hint_y=None, height=dp(24), halign='left')
        self.admin_form_title.bind(size=self.admin_form_title.setter('text_size'))
        form_card.add_widget(self.admin_form_title)

        # MAC input row
        mac_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        mac_lbl = Label(text="MAC Address", font_size=dp(10),
                        color=(0.55, 0.55, 0.62, 1), size_hint_x=0.28,
                        halign='right', valign='center')
        mac_lbl.bind(size=mac_lbl.setter('text_size'))
        self.admin_mac_input = TextInput(
            hint_text="AA:BB:CC:DD:EE:FF",
            font_size=dp(12), multiline=False,
            background_color=(0.12, 0.12, 0.17, 1),
            foreground_color=(0.92, 0.92, 0.95, 1),
            cursor_color=(0, 0.85, 0.42, 1),
            hint_text_color=(0.35, 0.35, 0.42, 1),
            padding=(dp(8), dp(8)),
            size_hint_x=0.72)
        mac_row.add_widget(mac_lbl)
        mac_row.add_widget(self.admin_mac_input)
        form_card.add_widget(mac_row)

        # Name input row (only shown for register)
        name_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        name_lbl = Label(text="Device Name", font_size=dp(10),
                         color=(0.55, 0.55, 0.62, 1), size_hint_x=0.28,
                         halign='right', valign='center')
        name_lbl.bind(size=name_lbl.setter('text_size'))
        self.admin_name_input = TextInput(
            hint_text="e.g. My Laptop",
            font_size=dp(12), multiline=False,
            background_color=(0.12, 0.12, 0.17, 1),
            foreground_color=(0.92, 0.92, 0.95, 1),
            cursor_color=(0, 0.85, 0.42, 1),
            hint_text_color=(0.35, 0.35, 0.42, 1),
            padding=(dp(8), dp(8)),
            size_hint_x=0.72)
        name_row.add_widget(name_lbl)
        name_row.add_widget(self.admin_name_input)
        self.admin_name_row = name_row
        form_card.add_widget(name_row)

        # Submit button
        self.admin_submit_btn = self._make_btn(
            "REGISTER ON-CHAIN", (0.06, 0.28, 0.12, 1), (0, 0.85, 0.42, 1))
        self.admin_submit_btn.bind(on_press=self._admin_submit)
        form_card.add_widget(self.admin_submit_btn)

        # Result label
        self.admin_result = Label(
            text="", font_size=dp(10), color=(0.5, 0.5, 0.58, 1),
            halign='left', valign='top', text_size=(None, None))
        self.admin_result.bind(size=self.admin_result.setter('text_size'))
        form_card.add_widget(self.admin_result)

        right.add_widget(form_card)

        # Transaction log
        log_card = BoxLayout(orientation='vertical', padding=dp(12),
                             spacing=dp(6))
        with log_card.canvas.before:
            Color(0.07, 0.07, 0.1, 1)
            self._alc_bg = RoundedRectangle(
                pos=log_card.pos, size=log_card.size, radius=[dp(12)])
        log_card.bind(
            pos=lambda w, p: setattr(self._alc_bg, 'pos', p),
            size=lambda w, s: setattr(self._alc_bg, 'size', s))

        log_title = Label(
            text="[b]TRANSACTION LOG[/b]", markup=True,
            font_size=dp(10), color=(0.5, 0.5, 0.58, 1),
            size_hint_y=None, height=dp(22), halign='left')
        log_title.bind(size=log_title.setter('text_size'))
        log_card.add_widget(log_title)

        log_scroll = ScrollView(do_scroll_x=False, bar_width=dp(3),
                                bar_color=(0.3, 0.3, 0.38, 0.5))
        self.admin_log_grid = GridLayout(cols=1, spacing=dp(2),
                                         size_hint_y=None, padding=dp(4))
        self.admin_log_grid.bind(
            minimum_height=self.admin_log_grid.setter('height'))
        self._admin_log_append("[READY] Admin panel loaded. "
                               "Connect Ethereum to enable on-chain actions.")
        log_scroll.add_widget(self.admin_log_grid)
        log_card.add_widget(log_scroll)

        right.add_widget(log_card)
        view.add_widget(right)

        # Internal state
        self._admin_mode = 'register'
        return view

    def _make_btn(self, text, bg, fg, height=dp(38)):
        """Helper: create a styled rounded button."""
        btn = Button(
            text=text, font_size=dp(11), bold=True,
            size_hint_y=None, height=height,
            background_normal='', background_color=bg, color=fg)
        with btn.canvas.before:
            Color(*bg)
            rr = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(7)])
        btn.bind(
            pos=lambda w, p, r=rr: setattr(r, 'pos', p),
            size=lambda w, s, r=rr: setattr(r, 'size', s))
        return btn

    def _admin_log_append(self, msg: str, color=(0.55, 0.55, 0.62, 1)):
        """Append a line to the transaction log (thread-safe via Clock)."""
        def _do(dt):
            from datetime import datetime
            ts = datetime.now().strftime("%H:%M:%S")
            lbl = Label(
                text=f"[{ts}] {msg}",
                font_size=dp(9), color=color,
                halign='left', valign='top',
                size_hint_y=None, height=dp(18))
            lbl.bind(size=lbl.setter('text_size'))
            self.admin_log_grid.add_widget(lbl)
            # Auto-scroll to bottom
            Clock.schedule_once(
                lambda dt2: setattr(
                    self.admin_log_grid.parent, 'scroll_y', 0), 0.05)
        Clock.schedule_once(_do, 0)

    def _admin_set_result(self, msg: str, ok: bool = True):
        color = (0, 0.85, 0.42, 1) if ok else (0.92, 0.22, 0.22, 1)
        Clock.schedule_once(
            lambda dt: setattr(self.admin_result, 'color', color), 0)
        Clock.schedule_once(
            lambda dt: setattr(self.admin_result, 'text', msg), 0)

    def _admin_set_mode(self, mode: str):
        """Switch form between register / revoke / check modes."""
        self._admin_mode = mode
        titles = {
            'register': ("[b]REGISTER DEVICE[/b]",
                         "REGISTER ON-CHAIN", (0.06, 0.28, 0.12, 1),
                         (0, 0.85, 0.42, 1), True),
            'revoke':   ("[b]REVOKE DEVICE[/b]",
                         "REVOKE ON-CHAIN", (0.28, 0.06, 0.06, 1),
                         (0.92, 0.22, 0.22, 1), False),
            'check':    ("[b]CHECK DEVICE[/b]",
                         "CHECK TRUST STATUS", (0.06, 0.18, 0.28, 1),
                         (0.18, 0.72, 0.92, 1), False),
        }
        title_txt, btn_txt, btn_bg, btn_fg, show_name = titles[mode]
        self.admin_form_title.text = title_txt
        self.admin_form_title.color = btn_fg
        self.admin_submit_btn.text  = btn_txt
        self.admin_submit_btn.background_color = btn_bg
        self.admin_submit_btn.color = btn_fg
        # Show/hide name field
        if show_name and self.admin_name_row not in \
                self.admin_name_row.parent.children:
            pass  # already visible
        self.admin_name_row.opacity = 1.0 if show_name else 0.0
        self.admin_name_row.disabled = not show_name
        self.admin_result.text = ""

    def _admin_refresh_status(self):
        """Fetch ETH status in background thread and update UI."""
        import threading
        threading.Thread(target=self._do_admin_refresh, daemon=True).start()

    def _do_admin_refresh(self):
        from blockchain.eth_registry import get_registry, eth_enabled
        reg = get_registry()
        if not reg.enabled:
            Clock.schedule_once(lambda dt: setattr(
                self.eth_dot, 'text', "● OFFLINE"), 0)
            Clock.schedule_once(lambda dt: setattr(
                self.eth_dot, 'color', (0.6, 0.6, 0.68, 1)), 0)
            Clock.schedule_once(lambda dt: setattr(
                self.eth_info, 'text',
                "Set ETH_RPC_URL and\nCONTRACT_ADDRESS in .env\n"
                "to enable Gate 1."), 0)
            self._admin_log_append("[ETH] Status: OFFLINE", (0.6, 0.6, 0.68, 1))
            return

        try:
            contract_addr = os.getenv('CONTRACT_ADDRESS', '')[:12] + '...'
            count  = reg._contract.functions.deviceCount().call()
            admin  = reg._contract.functions.admin().call()
            signer = reg._account.address if reg._account else 'NOT SET'
            is_admin = (reg._account and
                        reg._account.address.lower() == admin.lower())

            info = (f"Contract: {contract_addr}\n"
                    f"Registered: {count} device(s)\n"
                    f"Signer: {'ADMIN' if is_admin else 'READ-ONLY'}")
            dot_text  = "● CONNECTED (Sepolia)"
            dot_color = (0, 0.85, 0.42, 1)
            log_msg   = (f"[ETH] Connected  Contract: {contract_addr}  "
                         f"Devices: {count}  Signer: {'ADMIN' if is_admin else 'read-only'}")
            if not is_admin:
                info += "\n[WARN] Signer != admin, writes will revert"
                log_msg += "  [WARN] write-only"

            Clock.schedule_once(lambda dt: setattr(
                self.eth_dot, 'text', dot_text), 0)
            Clock.schedule_once(lambda dt: setattr(
                self.eth_dot, 'color', dot_color), 0)
            Clock.schedule_once(lambda dt: setattr(
                self.eth_info, 'text', info), 0)
            self._admin_log_append(log_msg, (0, 0.85, 0.42, 1))

        except Exception as e:
            self._admin_log_append(f"[ETH] Status error: {e}",
                                   (0.92, 0.22, 0.22, 1))

    def _admin_submit(self, *_):
        """Run admin action in background thread."""
        mac  = self.admin_mac_input.text.strip().upper()
        name = self.admin_name_input.text.strip()
        mode = self._admin_mode

        if not mac:
            self._admin_set_result("MAC address is required.", ok=False)
            return
        if mode == 'register' and not name:
            self._admin_set_result("Device name is required.", ok=False)
            return

        self.admin_submit_btn.disabled = True
        self._admin_set_result("Working...")

        import threading
        threading.Thread(
            target=self._do_admin_action,
            args=(mode, mac, name),
            daemon=True).start()

    def _do_admin_action(self, mode: str, mac: str, name: str):
        from blockchain.eth_registry import get_registry
        reg = get_registry()

        if not reg.enabled:
            self._admin_set_result(
                "Ethereum not configured.\nSet ETH_RPC_URL + "
                "CONTRACT_ADDRESS in .env", ok=False)
            self._admin_log_append("[ETH] Action failed: not configured",
                                   (0.92, 0.22, 0.22, 1))
            Clock.schedule_once(
                lambda dt: setattr(self.admin_submit_btn, 'disabled', False), 0)
            return

        try:
            if mode == 'register':
                tx = reg.register_device(mac, name)
                if tx:
                    short_tx = tx[:18] + '...'
                    self._admin_set_result(
                        f"Registered!\nTX: {short_tx}\n"
                        f"View: sepolia.etherscan.io/tx/{tx}", ok=True)
                    self._admin_log_append(
                        f"[REGISTER] {mac} ({name}) TX: {short_tx}",
                        (0, 0.85, 0.42, 1))
                else:
                    self._admin_set_result("Transaction failed. Check logs.",
                                           ok=False)
                    self._admin_log_append(
                        f"[REGISTER] FAILED for {mac}", (0.92, 0.22, 0.22, 1))

            elif mode == 'revoke':
                tx = reg.revoke_device(mac)
                if tx:
                    short_tx = tx[:18] + '...'
                    self._admin_set_result(
                        f"Revoked!\nTX: {short_tx}", ok=True)
                    self._admin_log_append(
                        f"[REVOKE] {mac} TX: {short_tx}",
                        (0.92, 0.72, 0.12, 1))
                else:
                    self._admin_set_result("Revoke failed. Check logs.",
                                           ok=False)
                    self._admin_log_append(
                        f"[REVOKE] FAILED for {mac}", (0.92, 0.22, 0.22, 1))

            elif mode == 'check':
                trusted = reg.is_trusted(mac)
                info    = reg.get_device(mac)
                if info and info.get('registered_at'):
                    from datetime import datetime
                    ts = datetime.utcfromtimestamp(
                        info['registered_at']).strftime('%Y-%m-%d %H:%M UTC')
                    dev_name = info.get('name') or '(unnamed)'
                    status_str = (
                        f"{'TRUSTED' if trusted else 'REVOKED/UNKNOWN'}\n"
                        f"Name: {dev_name}\n"
                        f"Registered: {ts}")
                else:
                    status_str = ("NOT REGISTERED\n"
                                  "This MAC is not in the on-chain registry.")
                self._admin_set_result(status_str, ok=trusted)
                color = ((0, 0.85, 0.42, 1) if trusted
                         else (0.92, 0.22, 0.22, 1))
                self._admin_log_append(
                    f"[CHECK] {mac} -> "
                    f"{'TRUSTED' if trusted else 'NOT TRUSTED'}", color)

        except Exception as e:
            self._admin_set_result(f"Error: {e}", ok=False)
            self._admin_log_append(f"[ERROR] {mode} {mac}: {e}",
                                   (0.92, 0.22, 0.22, 1))
        finally:
            Clock.schedule_once(
                lambda dt: setattr(self.admin_submit_btn, 'disabled', False), 0)

    # ── UPDATE ANALYTICS ──────────────────────────────────────

    def _update_analytics(self):
        data = self._scan_data
        if not data:
            return

        devices     = data.get('devices', [])
        scores      = data.get('scores', [])
        predictions = data.get('predictions', [])
        risks       = data.get('risks', [])
        names       = data.get('names', [])
        macs        = data.get('macs', [])

        ble_count     = sum(1 for d in devices if d.get('scan_type') == 'BLE')
        classic_count = sum(1 for d in devices if d.get('scan_type') == 'CLASSIC')
        threat_count  = int(sum(1 for p in predictions if p == -1))

        # Donut
        segments = []
        if ble_count:
            segments.append((ble_count, [0, 0.85, 0.42, 1]))
        if classic_count:
            segments.append((classic_count, [0.85, 0.72, 0.12, 1]))
        if threat_count:
            segments.append((threat_count, [0.92, 0.22, 0.22, 1]))
        self.donut_chart.set_data(segments, str(len(devices)), "devices")

        # RSSI bars (from raw scan devices)
        rssi_bars = []
        for d in devices[:10]:
            dname = (d.get('name') or d.get('mac', '??'))[:16]
            rssi  = d.get('rssi', -100)
            if rssi == -1:
                continue
            col = ([0, 0.85, 0.42, 1] if rssi > -50 else
                   [0.18, 0.72, 0.92, 1] if rssi > -70 else
                   [0.85, 0.72, 0.12, 1] if rssi > -85 else
                   [0.92, 0.22, 0.22, 1])
            rssi_bars.append((dname, rssi, -30, col))
        self.rssi_chart.set_data(rssi_bars, "SIGNAL STRENGTH (RSSI dBm)")

        # Risk score bars (from registry ML results)
        if len(scores) > 0 and len(names) > 0:
            score_bars = []
            for i in range(min(len(names), len(scores), 10)):
                dname = (names[i] or macs[i] if i < len(macs) else '??')[:16]
                risk  = float(risks[i]) if i < len(risks) else 0.0
                pred  = int(predictions[i]) if i < len(predictions) else 1
                col   = ([0.92, 0.22, 0.22, 1] if pred == -1 else
                         [0.92, 0.72, 0.12, 1] if risk >= 0.4 else
                         [0, 0.85, 0.42, 1])
                score_bars.append((dname, round(risk, 3), 1.0, col))
            self.score_chart.set_data(score_bars, "RISK SCORES (0-1)")

        # Pipeline flow - all done (matches paper Figure 5: 4 check gates)
        self.flow_diagram.set_phases([
            ("ETH Registry", "done", [0.6, 0.42, 0.92, 1]),
            ("Dup MAC",      "done", [0.92, 0.42, 0.12, 1]),
            ("AI Check",     "done", [0.85, 0.72, 0.12, 1]),
            ("CLEARED",      "done", [0, 0.85, 0.42, 1]),
        ])

    # ── UTILITIES ─────────────────────────────────────────────

    def _tick_time(self, dt):
        self.time_label.text = datetime.now().strftime("%a %d %b  %H:%M:%S")

    def _set_status(self, text, color):
        Clock.schedule_once(
            lambda dt: self._do_set_status(text, color), 0)

    def _do_set_status(self, text, color):
        self.status_label.text = f"  {text}  "
        self.status_label.color = color

    def _set_phase(self, text, progress):
        Clock.schedule_once(
            lambda dt: self._do_set_phase(text, progress), 0)

    def _do_set_phase(self, text, progress):
        self.phase_label.text = text
        anim = Animation(value=progress, duration=0.3)
        anim.start(self.prog_bar)

    def _set_metric(self, card, value, sub=""):
        Clock.schedule_once(
            lambda dt: self._do_set_metric(card, value, sub), 0)

    def _do_set_metric(self, card, value, sub):
        card.metric_value = str(value)
        if sub:
            card.metric_sub = sub

    def _add_device(self, name, mac, scan_type, score, pred, rssi, risk=0.0):
        Clock.schedule_once(lambda dt: self._do_add_device(
            name, mac, scan_type, score, pred, rssi, risk), 0)

    def _do_add_device(self, name, mac, scan_type, score, pred, rssi, risk=0.0):
        dist      = estimate_distance(rssi)
        zone      = get_proximity_zone(dist)
        z_color   = get_zone_color(zone)
        dist_text = format_distance_value(dist)
        if self.empty_label.parent:
            self.table_grid.remove_widget(self.empty_label)
        is_anomaly = (pred == -1)

        rlabel = risk_label(risk)
        if rlabel == "HIGH":
            r_col = [0.92, 0.22, 0.22, 1]
            r_bg  = [0.20, 0.06, 0.06, 1]
        elif rlabel == "MEDIUM":
            r_col = [0.92, 0.72, 0.12, 1]
            r_bg  = [0.18, 0.14, 0.04, 1]
        else:
            r_col = [0, 0.85, 0.42, 1]
            r_bg  = [0.04, 0.14, 0.06, 1]

        entry = DeviceEntry(
            name=name or "Unknown",
            mac=mac,
            scan_type=scan_type,
            score_text=f"{score:.4f}" if score > -900 else "—",
            action="THREAT" if is_anomaly else "SAFE",
            dot="▲" if is_anomaly else "●",
            dot_color=([0.92, 0.22, 0.22, 1] if is_anomaly
                       else [0, 0.85, 0.42, 1]),
            row_color=([0.12, 0.06, 0.06, 1] if is_anomaly
                       else [0.08, 0.08, 0.11, 1]),
            badge_bg=([0.2, 0.06, 0.06, 1] if is_anomaly
                      else [0.04, 0.14, 0.06, 1]),
            badge_text=([0.92, 0.22, 0.22, 1] if is_anomaly
                        else [0, 0.75, 0.38, 1]),
            risk_text=rlabel,
            risk_color=r_col,
            risk_bg=r_bg,
            rssi_text=f"{rssi} dBm" if rssi != -1 else "—",
            distance_text=dist_text,
            zone_text=zone,
            zone_color=z_color,
        )
        self.table_grid.add_widget(entry)

    def _update_flow_phase(self, phase_idx, status):
        """
        Update pipeline flow diagram during scan.
        4 gates matching paper Figure 5:
          0 = ETH Registry Check (Gate 1)
          1 = Duplicate MAC Detector (Gate 2)
          2 = AI IsolationForest Check (Gate 3)
          3 = Device CLEARED
        """
        phases = [
            ("ETH Registry", "pending", [0.3, 0.3, 0.38, 1]),
            ("Dup MAC",      "pending", [0.3, 0.3, 0.38, 1]),
            ("AI Check",     "pending", [0.3, 0.3, 0.38, 1]),
            ("CLEARED",      "pending", [0.3, 0.3, 0.38, 1]),
        ]
        done_colors = [
            [0.6, 0.42, 0.92, 1],   # ETH Registry - purple
            [0.92, 0.42, 0.12, 1],  # Dup MAC - orange
            [0.85, 0.72, 0.12, 1],  # AI Check - yellow
            [0, 0.85, 0.42, 1],     # CLEARED - green
        ]
        active_color = [0.18, 0.72, 0.92, 1]
        for i in range(4):
            if i < phase_idx:
                phases[i] = (phases[i][0], "done", done_colors[i])
            elif i == phase_idx:
                phases[i] = (phases[i][0], status,
                             active_color if status == "active"
                             else done_colors[i])
        Clock.schedule_once(
            lambda dt: self.flow_diagram.set_phases(phases), 0)

    # ── ACTIONS ───────────────────────────────────────────────

    def _on_scan(self, *args):
        if self._scanning:
            return
        self._scanning = True
        self.scan_btn.text = "SCANNING..."
        self.scan_btn.disabled = True
        self.scan_btn.background_color = (0.2, 0.2, 0.25, 1)
        self._set_status("SCANNING", [0.85, 0.72, 0.12, 1])

        self.table_grid.clear_widgets()
        self.table_grid.add_widget(self.empty_label)
        self.empty_label.text = "Scanning for nearby devices..."

        for c in [self.m_total, self.m_ble, self.m_classic,
                  self.m_anomalies, self.m_chain]:
            c.metric_value = "—"
            c.metric_sub = ""

        # Reset flow diagram
        self.flow_diagram.set_phases([
            ("ETH Registry", "pending", [0.3, 0.3, 0.38, 1]),
            ("Dup MAC",      "pending", [0.3, 0.3, 0.38, 1]),
            ("AI Check",     "pending", [0.3, 0.3, 0.38, 1]),
            ("CLEARED",      "pending", [0.3, 0.3, 0.38, 1]),
        ])

        thread = threading.Thread(target=self._pipeline, daemon=True)
        thread.start()

    def _scan_finished(self):
        self._scanning = False
        self.scan_btn.text = "START SCAN"
        self.scan_btn.disabled = False
        self.scan_btn.background_color = (0.08, 0.52, 0.52, 1)

    # ── PIPELINE ──────────────────────────────────────────────

    def _pipeline(self):
        try:
            self._execute()
        except Exception as e:
            err = str(e).lower()
            if ('bluetooth' in err or 'not powered' in err
                    or 'not available' in err):
                self._set_status("BT UNAVAILABLE",
                                 [0.92, 0.22, 0.22, 1])
                self._set_phase(
                    "Bluetooth is off — enable it in Settings", 0)
                Clock.schedule_once(lambda dt: setattr(
                    self.empty_label, 'text',
                    "Bluetooth is not available.\n"
                    "Enable Bluetooth in Settings and try again."), 0)
            else:
                self._set_status("ERROR", [0.92, 0.22, 0.22, 1])
                self._set_phase(f"Error: {e}", 0)
        finally:
            Clock.schedule_once(lambda dt: self._scan_finished(), 0)

    def _execute(self):
        """
        Defense-in-depth pipeline matching paper Figure 5:
          Gate 1 - ETH Registry Check (PRIMARY - Blockchain Registry Check)
          Gate 2 - Duplicate MAC Detector
          Gate 3 - AI IsolationForest Check
          Final  - Device CLEARED
        """
        import uuid as _uuid
        import time as _t
        t_start = _t.time()
        session_id = str(_uuid.uuid4())
        init_db()

        # ── BLE + Classic Scan ─────────────────────────────────
        self._set_phase("Scanning BLE + Classic Bluetooth...", 8)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices = loop.run_until_complete(
                scan(duration=SCAN_DURATION, verbose=False))
        finally:
            loop.close()

        ble_devices   = [d for d in devices if d.get('scan_type') == 'BLE']
        ble_count     = len(ble_devices)
        classic_count = len(devices) - ble_count
        total         = len(devices)

        self._set_metric(self.m_total, total,
                         f"{ble_count} BLE  {classic_count} Classic")
        self._set_metric(self.m_ble, ble_count)
        self._set_metric(self.m_classic, classic_count)

        if not devices:
            self._set_status("NO DEVICES", [0.85, 0.72, 0.12, 1])
            self._set_phase("No devices found - check Bluetooth", 0)
            Clock.schedule_once(lambda dt: setattr(
                self.empty_label, 'text',
                "No Bluetooth devices found.\n"
                "Make sure Bluetooth is on and devices are nearby."), 0)
            self._scan_data = {'devices': devices}
            Clock.schedule_once(lambda dt: self._update_analytics(), 0.1)
            return

        # ── Gate 1: ETH Registry Check ─────────────────────────
        self._set_phase(
            "Gate 1/3 — Blockchain Registry Check (Ethereum)...", 20)
        self._set_status("ETH CHECK", [0.6, 0.42, 0.92, 1])
        self._update_flow_phase(0, "active")

        ble_macs = [d['mac'] for d in ble_devices]
        trusted_map: dict = {}
        unknown_ble: list = []

        if eth_enabled() and ble_macs:
            trusted_map = eth_is_trusted_batch(ble_macs)
            unknown_ble = [m for m, ok in trusted_map.items() if not ok]
        else:
            trusted_map = {d['mac']: True for d in ble_devices}

        self._set_phase(
            f"Gate 1/3 — ETH: {len(ble_macs)-len(unknown_ble)} trusted, "
            f"{len(unknown_ble)} unknown", 28)
        self._update_flow_phase(0, "done")

        # ── Gate 2: Duplicate MAC Detector ────────────────────
        self._set_phase("Gate 2/3 — Duplicate MAC Detector...", 35)
        self._set_status("DUP CHECK", [0.92, 0.42, 0.12, 1])
        self._update_flow_phase(1, "active")

        dup_signals = detect_duplicate_macs(devices)
        dup_macs    = {s['mac'] for s in dup_signals}

        self._set_phase(
            f"Gate 2/3 — {len(dup_signals)} duplicate MAC signal(s)", 42)
        self._update_flow_phase(1, "done")

        # ── Registry upsert + behavioral history ───────────────
        self._set_phase("Updating behavioral registry...", 48)
        self._set_status("ANALYZING", [0.3, 0.6, 0.92, 1])

        spoofing_hits = len(dup_signals)
        with get_db() as conn:
            for record in devices:
                fp_id   = upsert_device(conn, record, session_id)
                signals = check_spoofing(conn, fp_id, record)
                spoofing_hits += len([s for s in signals
                                      if s['severity'] in ('WARN', 'ALERT')])

            fp_ids, names, macs, X = build_training_matrix(conn)

        if len(X) < 2:
            self._set_status("BUILDING HISTORY", [0.85, 0.72, 0.12, 1])
            self._set_phase(
                f"Need 2+ devices with scan history "
                f"({len(fp_ids)} so far - run more scans)", 50)
            Clock.schedule_once(lambda dt: setattr(
                self.empty_label, 'text',
                "Building device history...\n"
                "Run a few more scans so the AI has enough data.\n"
                f"({total} devices seen this session)"), 0)
            self._scan_data = {'devices': devices,
                               'fp_ids': [], 'scores': [], 'predictions': []}
            Clock.schedule_once(lambda dt: self._update_analytics(), 0.1)
            return

        # ── Gate 3: AI IsolationForest Check ──────────────────
        self._set_phase(
            f"Gate 3/3 — AI IsolationForest Check ({len(X)} devices)...", 62)
        self._set_status("AI CHECK", [0.85, 0.72, 0.12, 1])
        self._update_flow_phase(2, "active")

        try:
            model, scaler_obj = train(X)
            train_ocsvm(X)
            predictions, scores = predict_ensemble(X, model, scaler_obj)
            risks = normalize_risk(scores)
        except Exception as e:
            self._set_phase(f"AI model error: {e}", 0)
            return

        self._set_phase("Gate 3/3 — AI ensemble complete", 72)
        self._update_flow_phase(2, "done")

        # ── CLEARED + Blockchain ───────────────────────────────
        self._set_phase("Registering on local blockchain...", 82)
        self._set_status("SECURING", [0.6, 0.42, 0.92, 1])
        self._update_flow_phase(3, "active")

        bc            = Blockchain()
        anomaly_count = 0
        dev_lookup    = {d['mac']: d for d in devices}

        Clock.schedule_once(lambda dt: self.table_grid.clear_widgets(), 0)
        _time.sleep(0.05)

        with get_db() as conn:
            for i, fp_id in enumerate(fp_ids):
                mac        = macs[i]
                name       = names[i]
                pred       = int(predictions[i])
                score      = float(scores[i])
                risk       = float(risks[i])
                rlabel     = risk_label(risk)
                is_anomaly = pred == -1
                not_listed = mac in unknown_ble
                is_dup     = mac in dup_macs

                reason_parts = []
                if is_anomaly:
                    reason_parts.append("IF+OCSVM both flagged")
                if not_listed:
                    reason_parts.append("not in ETH whitelist")
                    if rlabel == 'LOW':
                        rlabel = 'MEDIUM'
                        risk   = max(risk, 0.4)
                if is_dup:
                    reason_parts.append("duplicate MAC (cloning)")
                    rlabel = 'HIGH'
                    risk   = max(risk, 0.7)
                if not reason_parts:
                    reason_parts.append("all gates passed")
                reason = "; ".join(reason_parts)

                try:
                    bc.add_device(fp_id, X[i].tolist())
                    trigger(mac, name, pred, score,
                            risk_score=risk, reason=reason)
                    update_anomaly_result(conn, fp_id, score, rlabel, is_anomaly)
                    if (is_anomaly or not_listed or is_dup) and eth_enabled():
                        eth_log_anomaly(mac, rlabel, reason)
                except Exception:
                    pass

                if is_anomaly:
                    anomaly_count += 1

                d = dev_lookup.get(mac, {})
                self._add_device(name, mac, d.get('scan_type', '-'),
                                 score, pred, d.get('rssi', -1), risk)

        self._set_metric(
            self.m_anomalies, anomaly_count,
            "threat(s)" if anomaly_count else "all clear")

        try:
            bc.verify_chain()
            self._set_metric(self.m_chain, len(bc.chain), "blocks")
        except Exception:
            pass

        self._update_flow_phase(3, "done")

        elapsed = _t.time() - t_start
        self._set_phase(f"Scan complete in {elapsed:.1f}s", 100)

        # Final status badge
        total_flags = anomaly_count + len(unknown_ble) + len(dup_signals)
        if anomaly_count > 0:
            self._set_status(f"{anomaly_count} AI THREAT(S)",
                             [0.92, 0.22, 0.22, 1])
        elif len(unknown_ble) > 0 or len(dup_signals) > 0:
            self._set_status(f"{total_flags} FLAG(S)",
                             [0.85, 0.72, 0.12, 1])
        else:
            self._set_status("ALL CLEAR", [0, 0.85, 0.42, 1])

        self._scan_data = {
            'devices':     devices,
            'fp_ids':      fp_ids,
            'scores':      scores,
            'predictions': predictions,
            'risks':       risks,
            'names':       names,
            'macs':        macs,
        }
        Clock.schedule_once(lambda dt: self._update_analytics(), 0.1)


if __name__ == '__main__':
    BLESecurityApp().run()
