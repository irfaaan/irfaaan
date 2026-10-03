#!/usr/bin/env python3
"""Playable Connect 4 inside a GitHub profile README.

Triggered by a GitHub Actions workflow when someone opens an issue titled:
    connect4|drop|{col}     (col is 0-based, 0..6)
    connect4|reset

Human = 1 (🔴), Bot = 2 (🟡). Bot takes wins, blocks threats,
likes the center column, and runs 20% chaos mode.
State lives in an HTML comment inside README.md; the board is re-rendered
between <!--C4-BOARD-START--> ... <!--C4-BOARD-END--> markers.
"""
import json
import os
import random
import re
import urllib.parse

REPO = "irfaaan/irfaaan"
ROWS, COLS = 6, 7
HUMAN, BOT = 1, 2
EMOJI = {0: "⚪", 1: "🔴", 2: "🟡"}
KEYCAPS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
STATE_RE = re.compile(r"<!--C4-STATE:(.*?)-->", re.DOTALL)
BOARD_RE = re.compile(r"<!--C4-BOARD-START-->.*?<!--C4-BOARD-END-->", re.DOTALL)


def issue_url(title, body):
    q = urllib.parse.urlencode({"title": title, "body": body})
    return f"https://github.com/{REPO}/issues/new?{q}"


def fresh_state():
    return {"g": [[0] * COLS for _ in range(ROWS)], "over": False,
            "msg": "YOUR MOVE — you are 🔴, machine is 🟡. Click a number to drop.",
            "log": []}


def render(state):
    g = state["g"]
    if state["over"]:
        header = "| " + " | ".join(KEYCAPS) + " |"
    else:
        header = "| " + " | ".join(
            f"[{k}]({issue_url(f'connect4|drop|{c}', f'Connect 4: dropping a disc in column {c + 1}. Just hit Submit.')})"
            for c, k in enumerate(KEYCAPS)) + " |"
    rows = ["| " + " | ".join(EMOJI[g[r][c]] for c in range(COLS)) + " |"
            for r in range(ROWS)]
    board = header + "\n|" + "---|" * COLS + "\n" + "\n".join(rows)
    extra = ""
    if state.get("log"):
        extra += "\n\n**LAST MOVES**\n\n" + "\n".join(f"- {m}" for m in state["log"][-5:])
    if state["over"]:
        extra += (f"\n\n[🔄 NEW GAME]({issue_url('connect4|reset', 'Start a fresh game of Connect 4.')})"
                  " — the machine is already shuffling.")
    return ("<!--C4-BOARD-START-->\n" + board +
            f"\n\n**STATUS:** {state['msg']}" + extra +
            "\n<!--C4-BOARD-END-->")


def try_drop(g, col, who):
    """Row where `who` would land in col, or None if full."""
    for r in range(ROWS - 1, -1, -1):
        if g[r][col] == 0:
            return r
    return None


def drop(g, col, who):
    r = try_drop(g, col, who)
    if r is not None:
        g[r][col] = who
    return r


def winner(g):
    for r in range(ROWS):
        for c in range(COLS):
            v = g[r][c]
            if not v:
                continue
            if c + 3 < COLS and all(g[r][c + i] == v for i in range(4)):
                return v
            if r + 3 < ROWS and all(g[r + i][c] == v for i in range(4)):
                return v
            if r + 3 < ROWS and c + 3 < COLS and all(g[r + i][c + i] == v for i in range(4)):
                return v
            if r + 3 < ROWS and c - 3 >= 0 and all(g[r + i][c - i] == v for i in range(4)):
                return v
    return 0


def valid_cols(g):
    return [c for c in range(COLS) if g[0][c] == 0]


def wins_if(g, col, who):
    r = try_drop(g, col, who)
    if r is None:
        return False
    g[r][col] = who
    w = winner(g) == who
    g[r][col] = 0
    return w


def bot_col(g):
    cols = valid_cols(g)
    for c in cols:  # take the win
        if wins_if(g, c, BOT):
            return c
    for c in cols:  # block the human
        if wins_if(g, c, HUMAN):
            return c
    if random.random() < 0.2:  # chaos mode
        return random.choice(cols)
    for c in (3, 2, 4, 1, 5, 0, 6):  # center-first
        if c in cols:
            return c
    return cols[0]


def apply(state, title, user):
    parts = title.split("|")
    if parts == ["connect4", "reset"]:
        s = fresh_state()
        s["msg"] = f"NEW GAME — {user} reset the grid. YOUR MOVE."
        return s
    if len(parts) != 3 or parts[0] != "connect4" or parts[1] != "drop":
        return None  # not our issue
    col = int(parts[2])
    g = state["g"]
    if state["over"] or not (0 <= col < COLS) or try_drop(g, col, HUMAN) is None:
        return None  # game over / bad column / full column — ignore
    drop(g, col, HUMAN)
    state["log"].append(f"🔴 {user} → column {col + 1}")
    if winner(g) == HUMAN:
        state["over"] = True
        state["msg"] = f"🏆 {user} CONNECTED 4 — core breached! Rematch?"
        return state
    if not valid_cols(g):
        state["over"] = True
        state["msg"] = "🤝 GRID FULL — draw. Respect."
        return state
    bc = bot_col(g)
    drop(g, bc, BOT)
    state["log"].append(f"🟡 machine → column {bc + 1}")
    if winner(g) == BOT:
        state["over"] = True
        state["msg"] = "🤖 MACHINE CONNECTED 4 — firewall held. Human, you tried."
    elif not valid_cols(g):
        state["over"] = True
        state["msg"] = "🤝 GRID FULL — draw. Respect."
    else:
        state["msg"] = f"YOUR MOVE — {user}, machine dropped in column {bc + 1}."
    return state


def main(readme_path, title, user):
    with open(readme_path, encoding="utf-8") as f:
        md = f.read()
    m = STATE_RE.search(md)
    state = json.loads(m.group(1)) if m else fresh_state()
    new = apply(state, title, user)
    if new is None:
        return
    md = STATE_RE.sub(lambda _: "<!--C4-STATE:" + json.dumps(new, separators=(",", ":")) + "-->",
                      md, count=1)
    md = BOARD_RE.sub(lambda _: render(new), md, count=1)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md)


if __name__ == "__main__":
    main(os.environ.get("README_PATH", "README.md"),
         os.environ.get("ISSUE_TITLE", ""),
         os.environ.get("ISSUE_USER", "player"))
