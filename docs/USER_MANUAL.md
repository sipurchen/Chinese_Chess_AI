# User Manual — Chinese Chess AI

> **Language / 語言：** [English](#user-manual--chinese-chess-ai) ｜ [中文](USER_MANUAL.zh.md)

---

## 1. Installation

### Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.8+ | Runtime |
| Flask | any | Web server |
| Pillow | any | Board image rendering (self-play) |

### Setup

```bash
# Clone the repository
git clone https://github.com/sipurchen/Chinese_Chess_AI.git
cd Chinese_Chess_AI

# Install dependencies
pip install flask pillow

# Start the server
python app.py
```

Open your browser at: **http://localhost:5000**

> **Note:** The server binds to `0.0.0.0:5000` by default. Press `Ctrl+C` in the terminal to stop it.

---

## 2. Mode 1 — Human vs AI (人機對弈)

This is the default mode when you open the app.

### 2.1 Selecting Difficulty

Click one of the three buttons in the left panel:

| Button | AI Personality | Strength |
|--------|---------------|---------|
| **初學者** | Beginner | Easy — depth 1, random variation |
| **柳大華** | Liu Dahua | Medium — depth 3, tactical / aggressive |
| **胡榮華** | Hu Ronghua | Hard — depth 4, positional / endgame precision |

Difficulty can be changed at any time without resetting the board.

### 2.2 Making a Move

1. **Click** any of your pieces (Red side plays first)
2. The piece highlights in green; legal destination squares show as dots
3. **Click** a legal destination square to move
4. The AI immediately calculates and plays its response

### 2.3 Understanding the AI Thought Panel

After each AI move, the right panel shows:

| Field | Meaning |
|-------|---------|
| **Score** | Board evaluation in centipawns (positive = Red advantage) |
| **Mate in** | If set, forced mate detected in N moves |
| **Opening** | Opening name if still in book (e.g. 當頭炮) |
| **Source** | `opening_book` or `search` |
| **Initiative** | Which side has the faster forced-mate threat |

### 2.4 Controls

- **Reset** — returns board to starting position
- **Undo** — not yet implemented (planned for Phase 2)

---

## 3. Mode 2 — AI Tournament (AI 對弈)

Watch three AI personalities play a round-robin tournament.

### 3.1 Starting a Tournament

1. Click the **AI 對弈** tab
2. Set the number of games per pair (default: 10; max recommended: 50)
3. Click **開始賽事**

The tournament runs in a background thread. You can continue browsing while it plays.

### 3.2 Reading the Standings Table

| Column | Meaning |
|--------|---------|
| **棋手** | AI personality name |
| **勝 W** | Wins |
| **負 L** | Losses |
| **和 D** | Draws |
| **點** | Points (Win=2, Draw=1, Loss=0) |

Standings update in real time via polling.

### 3.3 Replaying a Game

1. Select a completed session from the session dropdown
2. Choose a specific game file
3. Click **載入回放**
4. Use **◀ ▶** buttons to step through moves
5. Use the **分析** button on any position to get AI evaluation

---

## 4. Mode 3 — Game Analysis (分析棋局)

Analyse any saved game file step-by-step.

### 4.1 Loading a Game

1. Click the **分析棋局** tab
2. Select a game from the **棋譜檔案** dropdown (lists all files in `AI_Games/`)
3. Click **載入**

### 4.2 Navigating Moves

| Button | Action |
|--------|--------|
| **◀◀** | Jump to start |
| **◀** | Previous move |
| **▶** | Next move |
| **▶▶** | Jump to end |

The board updates to show the position after each move. The last move is highlighted in yellow.

### 4.3 Requesting AI Analysis

Click **AI 分析** at any position. The engine evaluates the current board and shows:
- Score and mate-in (if any)
- Which opening this position belongs to
- Initiative assessment

---

## 5. Mode 4 — Endgame Puzzles (試解殘局)

Set up any position and let the AI solve it, or explore the built-in puzzle library.

### 5.1 Setting Up a Position

1. Click the **試解殘局** tab
2. The **piece palette** appears below the board
3. **Left-click** a piece in the palette to select it (it highlights)
4. **Left-click** a board square to place the piece
5. **Right-click** any piece on the board to remove it

> **Tip:** The board starts empty. You can also right-click all pieces to clear and start fresh.

### 5.2 Solving the Position

1. Select whose turn it is (**紅先** / **黑先**)
2. Click **AI 求解**
3. The AI searches for the best sequence and displays:
   - Best first move
   - Score / mate-in count
   - Principal variation (sequence of moves)

### 5.3 Built-in Puzzle Library

Click **載入題庫** to view the 5 built-in puzzles. Click any puzzle to load it onto the board, then click **AI 求解** to verify the solution.

### 5.4 Finding Similar Puzzles

After setting up a position, click **相似殘局** to find puzzles in the library with similar piece configurations (Sørensen-Dice similarity ≥ 0.5).

### 5.5 Saving a Puzzle

1. Set up the position
2. Fill in the **題目名稱** (puzzle name) and **解答說明** (solution notes) fields
3. Click **儲存殘局**

Saved puzzles are stored in `AI_Games/endgame_puzzles.json` and appear in future **載入題庫** listings.

---

## 6. Self-Play Simulation (`self_play.py`)

Generate AI vs AI game records with board screenshots.

```bash
python self_play.py
```

This runs three matches:
- 初學者 (Beginner) vs Main Engine
- 柳大華 (Liu Dahua) vs Main Engine
- 胡榮華 (Hu Ronghua) vs Main Engine

Output is saved to `AI_Games/<personality>/`:

| File | Contents |
|------|---------|
| `game_record_<timestamp>.txt` | Move-by-move text record with scores |
| `game_record_<timestamp>.json` | Machine-readable with turning-point index |
| `<timestamp>_turn_XXX_TurningPoint.png` | Board screenshot at key moments |

Screenshots are captured when:
- Score delta exceeds 40 points
- Forced mate (≤ 5 moves) is detected
- Initiative advantage flips
- A heavy piece (rook) is captured

---

## 7. Piece Reference

### Red Side (紅方)

| Symbol | Chinese | Piece |
|--------|---------|-------|
| `K` | 帥 | King |
| `A` | 仕 | Advisor |
| `B` | 相 | Elephant |
| `N` | 傌 | Horse |
| `R` | 俥 | Rook (Chariot) |
| `C` | 炮 | Cannon |
| `P` | 兵 | Pawn (Soldier) |

### Black Side (黑方)

| Symbol | Chinese | Piece |
|--------|---------|-------|
| `k` | 將 | King |
| `a` | 士 | Advisor |
| `b` | 象 | Elephant |
| `n` | 馬 | Horse |
| `r` | 車 | Rook (Chariot) |
| `c` | 砲 | Cannon |
| `p` | 卒 | Pawn (Soldier) |

---

## 8. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Board doesn't update | JS error | Open browser DevTools → Console tab; refresh |
| AI takes very long | High search depth | Switch to 初學者 or 柳大華 |
| Port 5000 in use | Another process | Change port: `python app.py --port 5001` |
| Chinese characters not rendering in PNG | Missing CJK fonts | Install SimSun / Noto CJK on your OS |
| Tournament doesn't start | Previous session still running | Refresh the page to kill the old thread |

---

## 9. File Structure Reference

```
chinese_chess_ai/
├── engine.py              ← Core engine (do not modify unless extending)
├── ai_memory.py           ← Knowledge base (endgames, openings)
├── ai_tournament.py       ← Tournament backend
├── ai_endgame.py          ← Puzzle library backend
├── app.py                 ← Flask server entry point
├── self_play.py           ← CLI: run AI vs AI games
├── docs/                  ← This documentation
├── AI_Games/              ← Generated game records
├── ai_wiki/               ← Personality style references
├── static/css/style.css   ← UI theme
├── static/js/main.js      ← All frontend logic
└── templates/index.html   ← Single-page app template
```

---

*Manual version: 2026-05-28*
