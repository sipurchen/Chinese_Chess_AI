# 實作計劃 — 中國象棋 AI

> **Language / 語言：** [English](IMPLEMENTATION_PLAN.md) ｜ [中文](#實作計劃--中國象棋-ai)

---

## 一、架構總覽

```
┌─────────────────────────────────────────────────┐
│                 瀏覽器（前端）                    │
│  ┌──────────────────────────────────────────┐   │
│  │  Vanilla JS + DOM 渲染                   │   │
│  │  4 模式：人機 / AI賽 / 分析 / 殘局       │   │
│  └──────────────┬───────────────────────────┘   │
└─────────────────┼───────────────────────────────┘
                  │ HTTP / JSON（REST）
┌─────────────────▼───────────────────────────────┐
│              Flask 伺服器（app.py）              │
│  /move  /reset  /tournament/*  /endgame/*  ...  │
└──┬───────────┬───────────┬────────────┬─────────┘
   │           │           │            │
   ▼           ▼           ▼            ▼
engine.py  ai_memory.py  ai_tournament.py  ai_endgame.py
（搜索）    （知識庫）     （循環賽）       （殘局題庫）
```

**設計決策：**
- **無資料庫（MVP 階段）**：所有資料存於 `AI_Games/` 下的 JSON 檔案
- **無 React/Vue**：純 JS 確保專案自包含，快速迭代
- **個性化 AI**：每個個性獨立類別，共享搜索核心
- **所有路徑為相對路徑**：`os.path.dirname(__file__)` — 不含硬編碼磁碟代號

---

## 二、引擎設計（engine.py）

### 2.1 搜索流程

```
get_best_move(depth)
  │
  ├─ _find_mate_in_one()          ← O(著法數) 前置掃描；若找到立即返回
  │
  ├─ 清除殺手著法
  │
  └─ alpha_beta(board, depth, α, β, turn)
       │
       ├─ 置換表查找（TT_EXACT / TT_LOWER / TT_UPPER）
       │
       ├─ generate_legal_moves()
       │
       ├─ order_moves()            ← 吃子（SEE）> 殺手著法 > 靜著
       │
       ├─ 遍歷每步：
       │    make_move_internal()
       │    alpha_beta(depth-1, ...)   ← 遞歸
       │    還原棋盤
       │    Beta 截斷 → 記錄殺手著法
       │
       └─ 置換表儲存 + 返回最佳分數
```

### 2.2 評估函數

```python
evaluate_board(board, turn):
  score = 0
  for each piece:
    score += PIECE_VALUE[piece]
    score += POSITION_TABLE[piece][row][col]
    score += root_theory_adjust(piece)          # 子根理論
    if endgame: score += ENDGAME_VALUE_ADJUST   # 重子貶值
    if endgame: score += king_activity_bonus()  # 將/帥活躍度
    if endgame: score += pawn_advance_bonus()   # 深入兵加分
  if not endgame and not opening:
    score += (己方著法數 - 對方著法數) // 4    # 機動性
  return score  # 從當前行棋方視角
```

### 2.3 關鍵常數

| 常數 | 值 | 用途 |
|------|-----|------|
| `MATE_SCORE` | 30 000 | 將殺基礎分數 |
| `MAX_TT_SIZE` | 150 000 | 置換表容量上限 |
| `TT_EXACT/LOWER/UPPER` | 0/1/2 | 置換表條目旗標類型 |
| `MAX_QUIESCENCE_DEPTH` | 4 | 靜止搜索最大額外層數 |

---

## 三、AI 個性實作

### 3.1 類別層次

```
ChineseChessEngine          ← 核心規則、搜索、評估
  ├── BeginnerAI             ← depth=1，前三名隨機選
  ├── LiuDahuaAI             ← depth=3，開局書（積極型）
  └── HuRonghuaAI            ← depth=4，開局書（陣地型）
```

### 3.2 開局書（顏色無關）

```python
def _try_opening_move(self, max_moves: int):
    book = self.OPENING_BOOK           # [(from, to), ...] 紅方視角
    if self.turn == 'black':
        book = mirror(book)            # (9-r, 8-c) 座標翻轉
    move_idx = count_moves_played()
    if move_idx < max_moves and book[move_idx] is legal:
        return book[move_idx]
    return None                        # 轉交搜索處理
```

### 3.3 個性思考輸出

每次 `get_best_move()` 調用填入 `self.thought`：
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

## 四、Flask API 路由

| 路由 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 提供 index.html |
| `/set_difficulty` | POST | 切換 AI 個性 |
| `/move` | POST | 走棋；返回棋盤 + AI 應對 |
| `/reset` | POST | 重置棋盤至初始局面 |
| `/tournament/start` | POST | 在 daemon 執行緒中啟動三方循環賽 |
| `/tournament/status/<sid>` | GET | 輪詢賽事進度 |
| `/tournament/sessions` | GET | 列出歷史賽事場次 |
| `/tournament/replay/<sid>/<fname>` | GET | 載入指定局回放 |
| `/games/list` | GET | 列出已儲存的棋譜檔案 |
| `/games/load` | POST | 載入棋譜供分析 |
| `/analyze` | POST | AI 分析指定局面 |
| `/endgame/library` | GET | 內建 + 已儲存殘局題庫 |
| `/endgame/solve` | POST | AI 求解局面 |
| `/endgame/save` | POST | 儲存使用者提交的殘局 |
| `/endgame/similar` | POST | 尋找相似殘局（Dice 相似度） |

---

## 五、前端架構（static/js/main.js）

### 5.1 模式系統

```javascript
let currentMode = 'human';   // 'human' | 'tournament' | 'analysis' | 'endgame'

function switchMode(mode) {
    document.querySelectorAll('[data-panel]').forEach(hide);
    document.querySelectorAll('[data-ctrl]').forEach(hide);
    document.querySelectorAll('[data-mode]').forEach(show if matches);
    currentMode = mode;
}
```

### 5.2 棋盤渲染

- 在 `<canvas>` 元素上繪製 9×10 格線
- 棋子渲染為帶漢字的圓形
- 高亮顯示：選中棋子（綠）、最後一步（黃）、合法著法（圓點）
- 點擊 → 選棋子 → 點擊目標格 → POST `/move`

### 5.3 主要資料流

```
模式 1（人機對弈）：
  點擊格子 → selectPiece() → clickTarget() → POST /move → renderBoard()

模式 2（AI 對弈）：
  startTournament() → POST /tournament/start
  輪詢間隔 → GET /tournament/status → updateStandings()
  replayGame() → GET /tournament/replay → precomputeBoards() → 步驟導航

模式 3（分析棋局）：
  loadGameList() → GET /games/list → 填充下拉選單
  loadGame() → GET /games/load → 步驟導航
  analyzePosition() → POST /analyze → displayThought()

模式 4（試解殘局）：
  調色盤點擊 → activePiece → 棋盤點擊 → placePiece()
  solvePuzzle() → POST /endgame/solve → displaySolution()
  savePuzzle() → POST /endgame/save
  findSimilar() → POST /endgame/similar → displayMatches()
```

---

## 六、資料儲存結構

```
AI_Games/
├── AI_Novice/
│   ├── game_record_<時間戳>.txt
│   ├── game_record_<時間戳>.json
│   └── <時間戳>_turn_XXX_TurningPoint.png
├── AI_LiuDahua/        （相同結構）
├── AI_HuRonghua/       （相同結構）
├── tournament/
│   └── <session_id>/
│       ├── summary.json
│       └── <對組>_game_<n>.json
└── endgame_puzzles.json
```

---

## 七、自對弈渲染器（self_play.py）

### 7.1 字體載入（跨平台）

```python
if sys.platform == 'win32':
    _win_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    candidates = [os.path.join(_win_fonts, f) for f in CJK_FONT_NAMES]
elif sys.platform == 'darwin':
    candidates = ['/System/Library/Fonts/STHeiti Light.ttc', ...]
else:
    candidates = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', ...]
```

### 7.2 轉折點偵測

滿足以下任一條件即截圖：
- 分差 > `TURNING_THRESHOLD`（40 分）
- 偵測到殺局威脅（`mate_in ≤ 5`）
- 先手優勢翻轉（正 → 負 或 負 → 正）
- 重子被吃（俥 / 將帥）

---

## 八、已完成 Session 紀錄

| Session | 日期 | 交付成果 |
|---------|------|---------|
| 1 | 2026-05-26 | 引擎基礎、擒王分數、子根理論、3 AI 個性、GitHub Repo |
| 2 | 2026-05-26 | 自對弈棋譜、棋盤渲染器、棋局記錄 |
| 3 | 2026-05-26 | 禁著偵測、殘局擴充、開局書、UI 優化 |
| 4 | 2026-05-27 | 新開局（盤頭馬/梅花譜）、雙方先手、解殺還殺、時間戳檔名 |
| 5 | 2026-05-27 | 棋手維基、百局賽事、四模式 UI、殘局題庫管理、武俠規劃 |
| 6 | 2026-05-27 | 置換表、殺手著法、一步殺捷徑、殘局模式、機動性評分 |
| 7 | 2026-05-28 | 分支重組、路徑隱私清潔、雙語文件 |

---

## 九、第二階段實作計劃（武俠仙人對弈 WebUI）

詳見 [`Others_AI_Planning.md`](../Others_AI_Planning.md)。

### 計劃新增模組

| 檔案 | 用途 |
|------|------|
| `user_profile.py` | 用戶資料、棋道點數、成就 |
| `ai_advisor.py` | 武俠風格走棋建議（Claude API） |
| `image_gen.py` | Gemini Vision — 水墨頭像生成 |

### 前端組件（React 或 Vite）

| 組件 | 用途 |
|------|------|
| `Board.jsx` | 帶武俠動效的 Canvas 棋盤 |
| `PaperDoll.jsx` | 分層頭像自訂 |
| `FaceCapture.jsx` | 網路攝影機 → Gemini 水墨頭像 |
| `Shop.jsx` | 棋道點數商店 |
| `EventCard.jsx` | 對局中特殊事件彈窗 |
| `AdvisorChat.jsx` | AI 仙師問答面板 |

---

*文件版本：2026-05-28 ｜ 分支：Caught_the_king_dev*
