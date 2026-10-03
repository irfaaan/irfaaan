#!/usr/bin/env python3
"""Playable Tic-Tac-Toe inside a GitHub profile README.

Triggered by a GitHub Actions workflow when someone opens an issue titled:
    tictactoe|move|{row}|{col}      (row/col are 0-based)
    tictactoe|reset

Human = X, Bot = O (minimax, occasionally cocky for fun).
State lives in an HTML comment inside README.md; the board is re-rendered
between <!--TTT-BOARD-START--> ... <!--TTT-BOARD-END--> markers.
"""
import json
import os
import random
import re
import urllib.parse

REPO = "irfaaan/irfaaan"
HUMAN, BOT = "X", "O"
EMOJI = {"X": "❌", "O": "⭕", "": "⬜"}
STATE_RE = re.compile(r"<!--TTT-STATE:(.*?)-->", re.DOTALL)
BOARD_RE = re.compile(r"<!--TTT-BOARD-START-->.*?<!--TTT-BOARD-END-->", re.DOTALL)


def issue_url(title, body):
    q = urllib.parse.urlencode({"title": title, "body": body})
    return f"https://github.com/{REPO}/issues/new?{q}"


def fresh_state():
    return {"b": [""] * 9, "over": False,
            "msg": "YOUR MOVE — you are ❌, machine is ⭕",
            "log": []}


def cell(r, c, v):
    if v:
        return EMOJI[v]
    url = issue_url(
        f"tictactoe|move|{r}|{c}",
        f"Tic-Tac-Toe: placing X at row {r + 1}, column {c + 1}. "
        "Just hit Submit — the machine handles the rest.")
    return f"[⬜]({url})"


def render(state):
    b = state["b"]
    rows = ["| " + " | ".join(cell(r, c, b[r * 3 + c]) for c in range(3)) + " |"
            for r in range(3)]
    board = "|---|---|---|\n" + "\n".join(rows)
    extra = ""
    if state.get("log"):
        extra += "\n\n**LAST MOVES**\n\n" + "\n".join(f"- {m}" for m in state["log"][-5:])
    if state["over"]:
        extra += (f"\n\n[🔄 NEW GAME]({issue_url('tictactoe|reset', 'Start a fresh game of Tic-Tac-Toe.')})"
                  " — rematch? the machine is waiting.")
    return ("<!--TTT-BOARD-START-->\n" + board +
            f"\n\n**STATUS:** {state['msg']}" + extra +
            "\n<!--TTT-BOARD-END-->")


def winner(b):
    for a, x, c in [(0, 1, 2), (3, 4, 5), (6, 7, 8),
                    (0, 3, 6), (1, 4, 7), (2, 5, 8),
                    (0, 4, 8), (2, 4, 6)]:
        if b[a] and b[a] == b[x] == b[c]:
            return b[a]
    return None


def minimax(b, turn):
    w = winner(b)
    if w == BOT:
        return (1, None)
    if w == HUMAN:
        return (-1, None)
    empty = [i for i, v in enumerate(b) if not v]
    if not empty:
        return (0, None)
    best = (-2, None) if turn == BOT else (2, None)
    for i in empty:
        b[i] = turn
        score = minimax(b, HUMAN if turn == BOT else BOT)[0]
        b[i] = ""
        if turn == BOT and score > best[0]:
            best = (score, i)
        if turn == HUMAN and score < best[0]:
            best = (score, i)
    return best


def bot_move(b):
    empty = [i for i, v in enumerate(b) if not v]
    if not empty:
        return None
    if random.random() < 0.25:  # occasionally the machine gets cocky
        return random.choice(empty)
    return minimax(b, BOT)[1]


def apply(state, title, user):
    parts = title.split("|")
    if parts == ["tictactoe", "reset"]:
        s = fresh_state()
        s["msg"] = f"NEW GAME — {user} reset the board. YOUR MOVE."
        return s
    if len(parts) != 4 or parts[0] != "tictactoe" or parts[1] != "move":
        return None  # not our issue
    r, c = int(parts[2]), int(parts[3])
    idx = r * 3 + c
    if state["over"] or state["b"][idx]:
        return None  # game over or stale/occupied cell — ignore
    state["b"][idx] = HUMAN
    state["log"].append(f"❌ {user} → row {r + 1}, col {c + 1}")
    if winner(state["b"]) == HUMAN:
        state["over"] = True
        state["msg"] = f"🏆 {user} WINS — system breached! The machine demands a rematch."
        return state
    if all(state["b"]):
        state["over"] = True
        state["msg"] = "🤝 DRAW — even match. The machine respects you."
        return state
    m = bot_move(state["b"])
    state["b"][m] = BOT
    state["log"].append(f"⭕ machine → row {m // 3 + 1}, col {m % 3 + 1}")
    if winner(state["b"]) == BOT:
        state["over"] = True
        state["msg"] = "🤖 MACHINE WINS — firewall held. Better luck next time, human."
    elif all(state["b"]):
        state["over"] = True
        state["msg"] = "🤝 DRAW — even match. The machine respects you."
    else:
        state["msg"] = f"YOUR MOVE — {user}, the machine has answered."
    return state


def main(readme_path, title, user):
    with open(readme_path, encoding="utf-8") as f:
        md = f.read()
    m = STATE_RE.search(md)
    state = json.loads(m.group(1)) if m else fresh_state()
    new = apply(state, title, user)
    if new is None:
        return
    md = STATE_RE.sub(lambda _: "<!--TTT-STATE:" + json.dumps(new, separators=(",", ":")) + "-->",
                      md, count=1)
    md = BOARD_RE.sub(lambda _: render(new), md, count=1)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md)


if __name__ == "__main__":
    main(os.environ.get("README_PATH", "README.md"),
         os.environ.get("ISSUE_TITLE", ""),
         os.environ.get("ISSUE_USER", "player"))
