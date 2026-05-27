# Implementation Plan — Chinese Chess AI

> **Language / 語言：** [English](#implementation-plan--chinese-chess-ai) ｜ [中文](IMPLEMENTATION_PLAN_ZH.md)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Browser (Client)                │
│  ┌──────────────────────────────────────────┐   │
│  │  vanilla JS + DOM rendering              │   │
│  │  4 modes: 人機 / AI賽 / 分析 / 殘局      │   │
│  └──────────────┬───────────────────────────┘   │
└─────────────────┼───────────────────────────────┘
                  │ HTTP / JSON (REST)
┌─────────────────▼───────────────────────────────┐
│                Flask Server (app.py)             │
│  /move  /reset  /tournament/*  /endgame/*  ...  │
└──┬───────────┬───────────┬────────────┬─────────┘
   │           │           │            │
   ▼           ▼           ▼            ▼
engine.py  ai_memory.py  ai_tournament.py  ai_endgame.py
(search)   (knowledge)   (round-robin)     (puzzles)
```

**Design Decisions:**
- **No database (MVP)**: all data in JSON files under `AI_Games/`
- **No React/Vue**: plain JS keeps the project self-contained and fast to iterate
- **Personality-based AI**: separate class per personality, shared search core
- **All paths relative**: `os.path.dirname(__file__)` — no hardcoded drive letters

---

## 2. Engine Design (`engine.py`)

### 2.1 Search Stack

```
get_best_move(depth)
  │
  ├─ _find_mate_in_one()          ← O(moves) pre-scan; returns immediately if found
  │
  ├─ clear killers
  │
  └─ alpha_beta(board, depth, α, β, turn)
       │
       ├─ TT lookup (TT_EXACT / TT_LOWER / TT_UPPER)
       │
       ├─ generate_legal_moves()
       │
       ├─ order_moves()            ← captures (SEE) > killers > quiet
       │
       ├─ for each move:
       │    make_move_internal()
       │    alpha_beta(depth-1, ...)   ← recursive
       │    undo / copy-make
       │    beta-cut → record killer
       │
       └─ TT store + return best score
```

### 2.2 Evaluation Function

```python
evaluate_board(board, turn):
  score = 0
  for each piece:
    score += PIECE_VALUE[piece]
    score += POSITION_TABLE[piece][row][col]
    score += root_theory_adjust(piece)          # 子根理論
    if endgame: score += ENDGAME_VALUE_ADJUST   # heavy-piece devalue
    if endgame: score += king_activity_bonus()  # centralised king
    if endgame: score += pawn_advance_bonus()   # deep pawns
  if not endgame and not opening:
    score += (my_moves - opp_moves) // 4        # mobility
  return score from current player's perspective
```

### 2.3 Key Constants

| Constant | Value | Purpose |
|---------|-------|---------|
| `MATE_SCORE` | 30 000 | Checkmate base score |
| `MAX_TT_SIZE` | 150 000 | Transposition table cap |
| `TT_EXACT/LOWER/UPPER` | 0/1/2 | TT entry flag types |
| `MAX_QUIESCENCE_DEPTH` | 4 | Max extra plies in quiescence |

---

## 3. AI Personality Implementation

### 3.1 Class Hierarchy

```
ChineseChessEngine          ← core rules, search, eval
  ├── BeginnerAI             ← depth=1, random from top-3
  ├── LiuDahuaAI             ← depth=3, opening book (aggressive)
  └── HuRonghuaAI            ← depth=4, opening book (positional)
```

### 3.2 Opening Book (Colour-Independent)

```python
def _try_opening_move(self, max_moves: int):
    book = self.OPENING_BOOK           # [(from, to), ...] for Red
    if self.turn == 'black':
        book = mirror(book)            # (9-r, 8-c) coordinate flip
    move_idx = count_moves_played()
    if move_idx < max_moves and book[move_idx] is legal:
        return book[move_idx]
    return None                        # fall through to search
```

### 3.3 Personality Thought Output

Every `get_best_move()` call populates `self.thought`:
```json
{
  "score": 120,
  "mate_in": null,
  "depth": 3,
  "opening_tag": "central_cannon",
  "opening_name": "當頭炮",
  "source": "opening_book",
  "initiative": "red",
  "dual_threat": false
}
```

---

## 4. Flask API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Serve index.html |
| `/set_difficulty` | POST | Switch AI personality |
| `/move` | POST | Make a move; returns board + AI reply |
| `/reset` | POST | Reset board to starting position |
| `/tournament/start` | POST | Start 3-way round-robin in daemon thread |
| `/tournament/status/<sid>` | GET | Poll tournament progress |
| `/tournament/sessions` | GET | List past tournament sessions |
| `/tournament/replay/<sid>/<fname>` | GET | Load specific game for replay |
| `/games/list` | GET | List saved game files |
| `/games/load` | POST | Load a game file for analysis |
| `/analyze` | POST | AI analysis of a given position |
| `/endgame/library` | GET | Built-in + saved puzzles |
| `/endgame/solve` | POST | AI solve a position |
| `/endgame/save` | POST | Save user-submitted puzzle |
| `/endgame/similar` | POST | Find similar puzzles (Dice similarity) |

---

## 5. Frontend Architecture (`static/js/main.js`)

### 5.1 Mode System

```javascript
let currentMode = 'human';   // 'human' | 'tournament' | 'analysis' | 'endgame'

function switchMode(mode) {
    document.querySelectorAll('[data-panel]').forEach(hide);
    document.querySelectorAll('[data-ctrl]').forEach(hide);
    document.querySelectorAll('[data-mode]').forEach(show if matches);
    currentMode = mode;
}
```

### 5.2 Board Rendering

- 9×10 grid drawn on `<canvas>` element
- Pieces rendered as circles with Chinese characters
- Highlights: selected piece (green), last move (yellow), legal moves (dots)
- Click → select piece → click destination → POST `/move`

### 5.3 Key Data Flows

```
Mode 1 (Human vs AI):
  click square → selectPiece() → clickTarget() → POST /move → renderBoard()

Mode 2 (Tournament):
  startTournament() → POST /tournament/start
  pollInterval → GET /tournament/status → updateStandings()
  replayGame() → GET /tournament/replay → precomputeBoards() → stepNavigation()

Mode 3 (Analysis):
  loadGameList() → GET /games/list → populate dropdown
  loadGame() → GET /games/load → stepNavigation()
  analyzePosition() → POST /analyze → displayThought()

Mode 4 (Endgame):
  paletteClick() → activePiece → boardClick → placePiece()
  solvePuzzle() → POST /endgame/solve → displaySolution()
  savePuzzle() → POST /endgame/save
  findSimilar() → POST /endgame/similar → displayMatches()
```

---

## 6. Data Storage Layout

```
AI_Games/
├── AI_Novice/
│   ├── game_record_<timestamp>.txt
│   ├── game_record_<timestamp>.json
│   └── <timestamp>_turn_XXX_TurningPoint.png
├── AI_LiuDahua/       (same structure)
├── AI_HuRonghua/      (same structure)
├── tournament/
│   └── <session_id>/
│       ├── summary.json
│       └── <pair>_game_<n>.json
└── endgame_puzzles.json
```

---

## 7. Self-Play Renderer (`self_play.py`)

### 7.1 Font Loading (Cross-Platform)

```python
if sys.platform == 'win32':
    _win_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    candidates = [os.path.join(_win_fonts, f) for f in CJK_FONT_NAMES]
elif sys.platform == 'darwin':
    candidates = ['/System/Library/Fonts/STHeiti Light.ttc', ...]
else:
    candidates = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', ...]
```

### 7.2 Turning Point Detection

A screenshot is saved when **any** of:
- Score delta > `TURNING_THRESHOLD` (40 pts)
- Mate threat detected (`mate_in ≤ 5`)
- Initiative advantage flips (positive→negative or vice versa)
- Heavy piece captured (rook / king)

---

## 8. Completed Sessions

| Session | Date | Deliverables |
|---------|------|-------------|
| 1 | 2026-05-26 | Engine foundation, 擒王分數, 子根理論, 3 AI personalities, GitHub repo |
| 2 | 2026-05-26 | Self-play games, board renderer, game records |
| 3 | 2026-05-26 | Forbidden-move detection, expanded endgames, opening books, UI polish |
| 4 | 2026-05-27 | New openings (盤頭馬/梅花譜), 雙方先手, 解殺還殺, timestamp filenames |
| 5 | 2026-05-27 | AI wikis, 100-game tournament, 4-mode UI, endgame puzzle manager, Wuxia planning |
| 6 | 2026-05-27 | Transposition table, killer moves, mate-in-1 shortcut, endgame mode, mobility scoring |
| 7 | 2026-05-28 | Branch restructure, path privacy fix, bilingual docs |

---

## 9. Phase 2 Implementation Plan (Wuxia WebUI)

See [`Others_AI_Planning.md`](../Others_AI_Planning.md) for full spec.

### Planned New Modules

| File | Purpose |
|------|---------|
| `user_profile.py` | User data, 棋道點數, achievements |
| `ai_advisor.py` | Wuxia-style move suggestions via Claude API |
| `image_gen.py` | Gemini Vision — ink-wash avatar generation |

### Frontend Components (React or Vite)

| Component | Purpose |
|-----------|---------|
| `Board.jsx` | Canvas board with wuxia animations |
| `PaperDoll.jsx` | Layered avatar customisation |
| `FaceCapture.jsx` | Webcam → Gemini ink-wash portrait |
| `Shop.jsx` | 棋道點數 store |
| `EventCard.jsx` | Mid-game special event popups |
| `AdvisorChat.jsx` | AI Advisor chat panel |

---

*Document version: 2026-05-28 | Branch: Caught_the_king_dev*
