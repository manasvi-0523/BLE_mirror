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
from kivy.animation import Animation
from kivy.graphics import (Color, Rectangle, RoundedRectangle,
                            Line, Ellipse)
from kivy.metrics import dp

from scanner.ble_scanner import scan
from feature_engine.feature_extract import (load_data, extract_features,
                                            get_feature_matrix)
from ai_model.anomaly_detector import train, predict, label
from blockchain.blockchain import Blockchain
from alerts.alert_system import trigger

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
        size_hint_x: 0.32
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
        size_hint_x: 0.12
        Label:
            text: root.scan_type
            font_size: dp(10)
            bold: True
            color: (0.2, 0.78, 0.85, 1) if root.scan_type == 'BLE' else (0.82, 0.7, 0.15, 1)
            halign: 'center'
    BoxLayout:
        size_hint_x: 0.18
        Label:
            text: root.score_text
            font_size: dp(12)
            color: root.dot_color
            halign: 'center'
    BoxLayout:
        size_hint_x: 0.16
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
        size_hint_x: 0.14
        Label:
            text: root.rssi_text
            font_size: dp(10)
            color: 0.5, 0.5, 0.58, 1
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
    rssi_text = StringProperty("—")


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

        tab_row.add_widget(self.tab_devices_btn)
        tab_row.add_widget(self.tab_analytics_btn)
        tab_row.add_widget(Widget())
        root.add_widget(tab_row)

        # ── CONTENT AREA ──────────────────────────────────────
        self.content_area = BoxLayout()

        # --- Devices view ---
        self.devices_view = BoxLayout(orientation='vertical', spacing=dp(4))
        col_hdr = BoxLayout(size_hint_y=None, height=dp(28),
                            padding=(dp(16), 0), spacing=dp(6))
        hdrs = [("", 0.04), ("DEVICE", 0.32), ("TYPE", 0.12),
                ("SCORE", 0.18), ("STATUS", 0.16), ("RSSI", 0.14)]
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
            ("BT Scan", "pending", [0.3, 0.3, 0.38, 1]),
            ("Features", "pending", [0.3, 0.3, 0.38, 1]),
            ("AI Model", "pending", [0.3, 0.3, 0.38, 1]),
            ("Blockchain", "pending", [0.3, 0.3, 0.38, 1]),
        ])

        bottom_row.add_widget(flow_card)
        view.add_widget(bottom_row)

        return view

    # ── TAB SWITCHING ─────────────────────────────────────────

    def _switch_tab(self, tab):
        if tab == self._current_tab:
            return
        self.content_area.clear_widgets()
        if tab == 'devices':
            self.content_area.add_widget(self.devices_view)
            self.tab_devices_btn.background_color = (0.12, 0.52, 0.52, 1)
            self.tab_devices_btn.color = (1, 1, 1, 1)
            self.tab_analytics_btn.background_color = (0.1, 0.1, 0.14, 1)
            self.tab_analytics_btn.color = (0.5, 0.5, 0.58, 1)
        else:
            self.content_area.add_widget(self.analytics_view)
            self.tab_analytics_btn.background_color = (0.12, 0.52, 0.52, 1)
            self.tab_analytics_btn.color = (1, 1, 1, 1)
            self.tab_devices_btn.background_color = (0.1, 0.1, 0.14, 1)
            self.tab_devices_btn.color = (0.5, 0.5, 0.58, 1)
        self._current_tab = tab

    # ── UPDATE ANALYTICS ──────────────────────────────────────

    def _update_analytics(self):
        data = self._scan_data
        if not data:
            return

        devices = data.get('devices', [])
        scores = data.get('scores', [])
        predictions = data.get('predictions', [])
        features_df = data.get('features_df', None)

        ble_count = sum(1 for d in devices
                        if d.get('scan_type') == 'BLE')
        classic_count = sum(1 for d in devices
                            if d.get('scan_type') == 'CLASSIC')
        threat_count = sum(1 for p in predictions if p == -1)

        # Donut
        segments = []
        if ble_count:
            segments.append((ble_count, [0, 0.85, 0.42, 1]))
        if classic_count:
            segments.append((classic_count, [0.85, 0.72, 0.12, 1]))
        if threat_count:
            segments.append((threat_count, [0.92, 0.22, 0.22, 1]))
        self.donut_chart.set_data(
            segments, str(len(devices)), "devices")

        # RSSI bars
        rssi_bars = []
        for d in devices[:10]:
            name = (d.get('name') or d.get('mac', '??'))[:16]
            rssi = d.get('rssi', -100)
            if rssi > -50:
                col = [0, 0.85, 0.42, 1]
            elif rssi > -70:
                col = [0.18, 0.72, 0.92, 1]
            elif rssi > -85:
                col = [0.85, 0.72, 0.12, 1]
            else:
                col = [0.92, 0.22, 0.22, 1]
            rssi_bars.append((name, rssi, -30, col))
        self.rssi_chart.set_data(rssi_bars, "SIGNAL STRENGTH (RSSI dBm)")

        # Anomaly score bars
        if features_df is not None and len(scores) > 0:
            score_bars = []
            for i, row in features_df.iterrows():
                if i >= len(scores):
                    break
                name = (row.get('device_name', '')
                        or row.get('mac', '??'))[:16]
                sc = float(scores[i])
                pred = (predictions[i]
                        if i < len(predictions) else 1)
                col = ([0.92, 0.22, 0.22, 1] if pred == -1
                       else [0, 0.85, 0.42, 1])
                score_bars.append((name, sc, 1.0, col))
            self.score_chart.set_data(score_bars[:10], "ANOMALY SCORES")

        # Pipeline flow — all done
        self.flow_diagram.set_phases([
            ("BT Scan", "done", [0.18, 0.72, 0.92, 1]),
            ("Features", "done", [0, 0.85, 0.42, 1]),
            ("AI Model", "done", [0.85, 0.72, 0.12, 1]),
            ("Blockchain", "done", [0.6, 0.42, 0.92, 1]),
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

    def _add_device(self, name, mac, scan_type, score, pred, rssi):
        Clock.schedule_once(lambda dt: self._do_add_device(
            name, mac, scan_type, score, pred, rssi), 0)

    def _do_add_device(self, name, mac, scan_type, score, pred, rssi):
        if self.empty_label.parent:
            self.table_grid.remove_widget(self.empty_label)
        is_anomaly = (pred == -1)
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
            rssi_text=f"{rssi} dBm" if rssi != -1 else "—",
        )
        self.table_grid.add_widget(entry)

    def _update_flow_phase(self, phase_idx, status):
        """Update pipeline flow diagram during scan."""
        phases = [
            ("BT Scan", "pending", [0.3, 0.3, 0.38, 1]),
            ("Features", "pending", [0.3, 0.3, 0.38, 1]),
            ("AI Model", "pending", [0.3, 0.3, 0.38, 1]),
            ("Blockchain", "pending", [0.3, 0.3, 0.38, 1]),
        ]
        done_colors = [
            [0.18, 0.72, 0.92, 1],
            [0, 0.85, 0.42, 1],
            [0.85, 0.72, 0.12, 1],
            [0.6, 0.42, 0.92, 1],
        ]
        active_color = [0.92, 0.72, 0.12, 1]
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
            ("BT Scan", "pending", [0.3, 0.3, 0.38, 1]),
            ("Features", "pending", [0.3, 0.3, 0.38, 1]),
            ("AI Model", "pending", [0.3, 0.3, 0.38, 1]),
            ("Blockchain", "pending", [0.3, 0.3, 0.38, 1]),
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
        # Phase 1: Scan
        self._set_phase(
            "Phase 1/4 — Scanning nearby Bluetooth devices...", 10)
        self._update_flow_phase(0, "active")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices = loop.run_until_complete(
                scan(duration=SCAN_DURATION, verbose=False))
        finally:
            loop.close()

        ble_count = sum(1 for d in devices
                        if d.get('scan_type') == 'BLE')
        classic_count = sum(1 for d in devices
                            if d.get('scan_type') == 'CLASSIC')
        total = len(devices)

        self._set_metric(self.m_total, total,
                         f"{ble_count} BLE · {classic_count} Classic")
        self._set_metric(self.m_ble, ble_count)
        self._set_metric(self.m_classic, classic_count)
        self._set_phase(f"Phase 1/4 — Found {total} device(s)", 25)
        self._update_flow_phase(0, "done")

        if not devices:
            self._set_status("NO DEVICES", [0.85, 0.72, 0.12, 1])
            self._set_phase("No devices found — check Bluetooth", 0)
            Clock.schedule_once(lambda dt: setattr(
                self.empty_label, 'text',
                "No Bluetooth devices found.\n"
                "Make sure Bluetooth is on and devices are nearby."), 0)
            self._scan_data = {'devices': devices}
            Clock.schedule_once(
                lambda dt: self._update_analytics(), 0.1)
            return

        # Phase 2: Feature Extraction
        self._set_phase(
            "Phase 2/4 — Extracting behavioral fingerprints...", 40)
        self._set_status("ANALYZING", [0.6, 0.42, 0.92, 1])
        self._update_flow_phase(1, "active")

        try:
            raw_df = load_data()
        except FileNotFoundError:
            self._set_phase("Error: dataset not found", 0)
            return

        features_df = extract_features(raw_df)
        X = get_feature_matrix(features_df)
        self._set_phase(
            f"Phase 2/4 — {len(features_df)} fingerprint(s) extracted",
            50)
        self._update_flow_phase(1, "done")

        if len(X) < 2:
            self._set_status("DONE", [0.85, 0.72, 0.12, 1])
            self._set_phase(
                "Need 2+ devices for anomaly detection", 50)
            Clock.schedule_once(
                lambda dt: self.table_grid.clear_widgets(), 0)
            for _, row in features_df.iterrows():
                d = next((d for d in devices
                          if d['mac'] == row['mac']), {})
                self._add_device(
                    row['device_name'], row['mac'],
                    d.get('scan_type', '—'), -999, 1,
                    d.get('rssi', -1))
            self._scan_data = {
                'devices': devices,
                'features_df': features_df,
                'scores': [], 'predictions': []}
            Clock.schedule_once(
                lambda dt: self._update_analytics(), 0.1)
            return

        # Phase 3: AI Training
        self._set_phase(
            "Phase 3/4 — Training Isolation Forest model...", 65)
        self._update_flow_phase(2, "active")
        try:
            model, scaler_obj = train(X)
            predictions, scores = predict(X, model, scaler_obj)
        except Exception as e:
            self._set_phase(f"AI model error: {e}", 0)
            return
        self._set_phase(
            "Phase 3/4 — Anomaly detection complete", 75)
        self._update_flow_phase(2, "done")

        # Phase 4: Blockchain + Alerts
        self._set_phase(
            "Phase 4/4 — Registering on blockchain...", 85)
        self._set_status("SECURING", [0.6, 0.42, 0.92, 1])
        self._update_flow_phase(3, "active")
        bc = Blockchain()
        anomaly_count = 0

        Clock.schedule_once(
            lambda dt: self.table_grid.clear_widgets(), 0)
        _time.sleep(0.05)

        for i, row in features_df.iterrows():
            mac = row['mac']
            name = row['device_name']
            feature_vector = X[i].tolist()
            pred = predictions[i]
            score = float(scores[i])

            try:
                bc.add_device(mac, feature_vector)
                trigger(mac, name, pred, score)
            except Exception:
                continue

            if pred == -1:
                anomaly_count += 1

            d = next((d for d in devices if d['mac'] == mac), {})
            self._add_device(name, mac, d.get('scan_type', '—'),
                             score, pred, d.get('rssi', -1))

        self._set_metric(
            self.m_anomalies, anomaly_count,
            "threat(s) detected" if anomaly_count else "all clear")

        # Verify chain
        self._set_phase(
            "Phase 4/4 — Verifying blockchain integrity...", 95)
        try:
            bc.verify_chain()
            chain_len = len(bc.chain)
            self._set_metric(self.m_chain, chain_len, "blocks verified")
        except Exception:
            pass

        self._update_flow_phase(3, "done")

        # Done
        self._set_phase("Scan complete", 100)
        if anomaly_count > 0:
            self._set_status(
                f"{anomaly_count} THREAT(S)", [0.92, 0.22, 0.22, 1])
        else:
            self._set_status("ALL CLEAR", [0, 0.85, 0.42, 1])

        # Store for analytics
        self._scan_data = {
            'devices': devices,
            'features_df': features_df,
            'scores': scores,
            'predictions': predictions,
        }
        Clock.schedule_once(lambda dt: self._update_analytics(), 0.1)


if __name__ == '__main__':
    BLESecurityApp().run()
