# Product Overview Document — Chinese Chess AI

> **Language / 語言：** [English](#product-overview-document--chinese-chess-ai) ｜ [中文](PRODUCT_OVERVIEW_ZH.md)

---

## 1. Vision

A web-based Chinese Chess (象棋 / Xiangqi) platform where every AI decision traces back to documented chess theory. Unlike opaque neural-network engines, this system exposes its reasoning — showing *why* a move is chosen through named theoretical frameworks.

The second phase targets an immersive **Wuxia Immortal Duel** (武俠仙人對弈) art style, wrapping the engine in a paper-doll character system, progressive difficulty unlocks, and a shared AI-collaboration workflow (Claude + Gemini + ChatGPT).

---

## 2. Problem Statement

| Pain Point | This Project's Response |
|-----------|------------------------|
| Chess AIs are black boxes | Named theory: 擒王分數 + 子根理論 explain every eval |
| No personality — all AIs play identically | 3 distinct personalities with documented historical styles |
| Static difficulty — can't grow with player | Progressive level unlock (Lv.0 Beginner → Lv.5 Immortal) |
| No structured learning path | Endgame puzzle library + AI advisor during game |
| Boring UI | Phase 2: Wuxia art direction, paper-doll avatar, special effects |

---

## 3. Core Theory

### 3.1 擒王分數 (Catch-the-King Score)

The only purpose of Chinese Chess is to capture the opponent's king. Every evaluation ultimately answers: **"How many moves until a side's king is caught?"**

```
Score = MATE_SCORE − depth_to_mate
```

Faster mates always rank higher. Opponent's best defences are fully accounted for through alpha-beta search.

### 3.2 子根理論 (Root Theory)

Static Exchange Evaluation (SEE) classifies every capturable piece:

| Class | 分類 | Condition | Eval Adjust |
|-------|------|-----------|-------------|
| **Rootless** | 無根 | Undefended; capturing profits | +15 |
| **False Root** | 虛根 | Appears defended; recapture still loses material | +5 |
| **Rooted** | 有根 | Well-defended; capturing loses | −5 |

### 3.3 解殺還殺 (Counter-Check Priority)

When in check, legal counter-checks are prioritised in move ordering — avoiding passive defence, forcing the opponent to solve their own threats.

### 3.4 雙方先手 (Mutual Initiative)

`_quick_mate_threat()` compares both sides' fastest forced-mate depth. If both have threats, the side with the shorter path wins the initiative analysis.

---

## 4. Feature Set

### 4.1 Core Engine (`engine.py`)

| Feature | Details |
|---------|---------|
| Rules | All 7 piece types, flying general, hobbled horse, cannon screen, palace restrictions |
| Search | Alpha-beta + quiescence search + iterative deepening |
| Transposition Table | 150 K entries, TT_EXACT / TT_LOWER / TT_UPPER flags |
| Killer Moves | 2 killers per depth, cleared per search |
| Mate-in-1 Shortcut | O(legal_moves) pre-scan before full search |
| Endgame Mode | `is_endgame()` — heavy pieces ≤ 3; piece-value adjustments |
| Opening Classifier | Detects 當頭炮 / 過宮炮 / 飛相局 |
| Mid-game Mobility | `(my_moves − opp_moves) // 4` bonus |

### 4.2 AI Personalities

| Name | Style | Depth | Opening Book |
|------|-------|-------|-------------|
| 初學者 (Beginner) | Random from top-3 moves | 1 | None |
| 柳大華 (Liu Dahua) | Tactical, quick-attack | 3 | 橘中秘 + 夾炮屏風 + 反宮馬 |
| 胡榮華 (Hu Ronghua) | Positional, endgame-precise | 4 | 五六炮 + 士角炮 + 龜背炮 + 卒底炮 |

### 4.3 Knowledge Base (`ai_memory.py`)

- **14 Endgame Win patterns**: 雙俥錯殺, 馬後炮, 臥槽馬, 海底撈月, 重炮殺法 …
- **10 Endgame Draw patterns**: 車炮萬年和, 馬炮對車, 士象全守和 …
- **8 Opening books** (colour-independent via coordinate mirroring)
- **Mid-game tactical patterns** + positional tables

### 4.4 4-Mode Web UI

| Mode | Purpose |
|------|---------|
| 人機對弈 | Human vs AI — real-time play |
| AI 對弈 | Watch 3-way round-robin tournament (100 games) |
| 分析棋局 | Load saved game, step through, request AI analysis |
| 試解殘局 | Set up any position, AI solves, save / find similar puzzles |

### 4.5 Support Systems

- **Tournament** (`ai_tournament.py`): daemon-threaded 3-way round-robin, JSON summaries
- **Endgame Library** (`ai_endgame.py`): 5 built-in puzzles + user-saved, Sørensen-Dice similarity
- **Self-Play** (`self_play.py`): board-image renderer (cross-platform fonts), turning-point detection
- **AI Wikis** (`ai_wiki/`): 柳大華 and 胡榮華 style analysis, representative games

---

## 5. Technical Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.8+, Flask |
| Frontend | Vanilla JS (DOM), HTML5 Canvas (board rendering) |
| AI Search | Custom alpha-beta, quiescence, TT, killers |
| Image Rendering | Pillow (PIL) — cross-platform CJK fonts |
| Data Storage | JSON files (games, puzzles, tournament results) |
| Version Control | Git / GitHub (`sipurchen/Chinese_Chess_AI`) |

---

## 6. Target Users

| User Type | Use Case |
|-----------|---------|
| Casual chess players | Play against personality-based AI at chosen difficulty |
| Chess students | Study endgame puzzles, analyse saved games |
| AI/ML enthusiasts | Examine theory-driven evaluation, opening books |
| Developers | Extend engine, add new personalities or UI modes |

---

## 7. Branch Strategy

| Branch | Role |
|--------|------|
| `Caught_the_king_master` | Stable releases (default branch) |
| `Caught_the_king_dev` | 擒王理論 R&D — engine research |
| `Web_UI_App` | Wuxia WebUI App development |

---

## 8. Phase Roadmap

### Phase 1 (Completed — Sessions 1–7)
- Core engine + 3 AI personalities
- Knowledge base (endgames, openings, tactics)
- 4-mode web UI
- Tournament + endgame puzzle systems
- Branch restructure + privacy-clean codebase

### Phase 2 — Wuxia WebUI App (2026 Q3–Q4)
See [`Others_AI_Planning.md`](../Others_AI_Planning.md) for full spec.

- 水墨 ink-wash art direction (board, pieces, backgrounds)
- Paper-doll avatar system + Gemini face-generation
- 棋道點數 (Chess-Path Points) economy and shop
- Progressive difficulty unlock (Lv.0 → Lv.5)
- AI Advisor chat (Claude API — wuxia-style advice)
- Social: leaderboard, game sharing, user accounts

---

*Document version: 2026-05-28 | Project: Chinese Chess AI*
