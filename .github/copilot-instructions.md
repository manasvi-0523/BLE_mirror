<!-- ACE:START -->
## AgentContext Engine (ACE) Instructions

**You are operating inside an ACE-managed project.**

ACE maintains a `.ace.json` file at the project root as the **single source of truth** for project state. You MUST:

1. **Read `.ace.json`** at the start of every session to understand the current goal,    state, next steps, and relevant files.
2. **Update `.ace.json`** (or call `ace save`) after meaningful progress by updating    `current_state` and `next_steps`.
3. **Never contradict `.ace.json`** — if you believe the state is stale, say so and    propose an update rather than ignoring it.
4. **Respect `relevant_files`** — always check these files before exploring others.

**Project:** BLE Behavioral Fingerprinting Security System
**Goal:** Real-time Bluetooth device security system combining BLE + Classic BT scanning, AI-based anomaly detection (Isolation Forest), and tamper-proof local blockchain to identify and flag rogue devices

You can also run:
- `ace load`  → print current context as a prompt block
- `ace save`  → save updated context back to `.ace.json`
<!-- ACE:END -->
