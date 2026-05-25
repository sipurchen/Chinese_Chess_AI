# Chinese Chess AI / 中國象棋 AI

A web-based Chinese Chess (象棋/Xiangqi) game with an intelligent AI engine featuring advanced evaluation theory, three opponent personalities, and self-play training data.

## Features

### Core Engine
- **Complete rule implementation**: all 7 piece types with correct movement, flying general rule, hobbled horse, cannon screen-capture, and palace restrictions
- **Alpha-beta search** with quiescence search and move ordering (MVV-LVA)
- **Iterative deepening** ready; configurable search depth per personality

### 擒王分數 (Catch-the-King Score)
The primary scoring principle: every evaluation is ultimately about how many moves until one side's king is caught. Forced mates score `30000 - depth_to_mate`, so faster checkmates always rank above slower ones. The opponent's best defensive replies are fully accounted for through the alpha-beta framework.

### 子根理論 (Root Theory)
Piece-protection analysis that classifies every capturable piece:

| Type | 分類 | Description | Score Adjust |
|------|------|-------------|-------------|
| **無根** | Rootless | Capturing it is profitable — undefended or under-defended | +15 |
| **虛根** | False Root | Appears defended but recapture loses material | +5 |
| **有根** | Rooted | Well-defended; capturing it loses material | −5 |

Static Exchange Evaluation (SEE) computes the full capture exchange sequence to determine root type.

### Three AI Personalities

| Name | Difficulty | Style | Search Depth |
|------|-----------|-------|-------------|
| **初學者** (Beginner) | Easy | Shallow, random from top-3 | 1 |
| **柳大華** (Liu Dahua) | Medium | Tactical, aggressive, quick-play style | 3 |
| **胡榮華** (Hu Ronghua) | Hard | Positional, patient, endgame precision | 4 |

Switch between opponents using the in-game difficulty buttons without reloading.

### AI Memory Module (`ai_memory.py`)
- **EndingStep**: 10 pre-catalogued endgame patterns (殘局譜) — mate patterns, draw techniques, fortress defenses
- **Opening books** per personality — Liu Dahua central cannon aggression, Hu Ronghua patient development
- **Mid-game tactical patterns** — 閃將抽俥, 兌子入局, 兩翼包抄, 棄子攻王, 頓挫手段
- **Positional tables** for pawns, horses, rooks, cannons, and kings

### Self-Play Training Data (`AI_Games/`)
Three AI personalities played against the standard engine to generate reference game records:

| Folder | Matchup | Purpose |
|--------|---------|---------|
| `AI_Games/AI_Novice/` | 初學者 vs 主AI | Beginner-style game record |
| `AI_Games/AI_LiuDahua/` | 柳大華 vs 主AI | Tactical mid-game reference |
| `AI_Games/AI_HuRonghua/` | 胡榮華 vs 主AI | Positional endgame reference |

Each folder contains:
- `game_record.txt` — full move-by-move record with scores
- `game_record.json` — machine-readable with turning points indexed
- `turn_XXX_*.png` — board screenshots at 擒王分數 major turning points

## Getting Started

### Requirements
```
Python 3.8+
Flask
Pillow (PIL)
```

### Install
```bash
pip install flask pillow
```

### Run
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in a browser.

### Generate Self-Play Records
```bash
python self_play.py
```

## Project Structure

```
chinese_chess_ai/
├── engine.py          # Core rules engine + three AI personalities
├── ai_memory.py       # Endgame patterns, opening books, positional tables
├── app.py             # Flask server
├── self_play.py       # AI vs AI simulation + board renderer
├── AI_Games/
│   ├── AI_Novice/     # Beginner game records & screenshots
│   ├── AI_LiuDahua/   # Liu Dahua style records & screenshots
│   └── AI_HuRonghua/  # Hu Ronghua style records & screenshots
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    └── index.html
```

## Branches

| Branch | Purpose |
|--------|---------|
| `master` | Stable releases |
| `Caught_the_king` | Active R&D — new features, training, experiments |

## License

MIT License — see [LICENSE](LICENSE)

## References

- Liu Dahua (柳大華) quick-game style — aggressive tactical play
- Hu Ronghua (胡榮華) classical games — positional and endgame mastery
- Chinese Chess rule standard (中國象棋竟賽規則)
