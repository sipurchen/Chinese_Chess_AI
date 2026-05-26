# Chinese Chess AI — 完整設計思路與規劃

## 一、專案起源

本專案的起點是一個最基本的 Flask + 純 JavaScript 中國象棋遊戲，內含：
- 棋盤渲染（JavaScript DOM 操作）
- 基本棋子走法（Python 後端驗證）
- Alpha-Beta 搜尋（深度 3，無位置表，無優化）
- 單一 AI 強度，無個性差異

初始版本的評估函數只有簡單物料計算，沒有位置獎勵、沒有攻守理論、沒有殘局知識。

---

## 二、第一階段：規則整理與知識建立

### 2.1 象棋規則整理（Gemini CLI 協助）

系統性整理了中國象棋的完整規則，包含：
- 棋盤結構：9×10，楚河漢界，九宮
- 各棋子走法（帥/將、仕/士、相/象、俥/車、傌/馬、炮/砲、兵/卒）
- 特殊規則：飛將（王見王）、蹩馬腿、炮需跳吃、象不能過河
- 勝負判定：絕殺、困斃、認負
- **和棋規則**（關鍵）：長將、長捉、協議和棋、超步和棋
- 禁止著法：長將必變招、長捉必變招、循環重複

### 2.2 AI 記憶模組設計（`ai_memory.py`）

建立了 AI 棋手的「知識庫」，包含三個主要區塊：

**殘局譜（EndingStep）**：
預先編碼了 10 個殘局模式，分為巧勝類和守和類：
- 巧勝：單俥勝單將、俥炮傌三子聯攻、馬後砲絕殺、兵底將殺、悶宮殺
- 守和：單俥巡河和局、雙士守和技巧、長將逼和

**開局譜（Opening Books）**：
三名 AI 各有不同的開局傾向，參考棋手風格編碼。

**位置表（Positional Tables）**：
為兵、馬、俥、炮、帥分別建立 10×9 的位置獎勵矩陣，指導棋子走向有利格子。

---

## 三、第二階段：核心評估理論

### 3.1 擒王分數（Catch-the-King Score）

**核心概念**：中國象棋的唯一目的是擒王（將死對方的帥/將）。

**設計原則**：
- 強制將死分數 = `MATE_SCORE(30000) - 距離擒王步數`
- 越快的強制將死排名越高
- 對方最佳應對透過 Alpha-Beta 框架自動計算
- `calculate_mate_in(score)` 將分數轉換為「幾步擒王」的人類可讀格式
- 在 Alpha-Beta 中加入「距離懲罰」：更快的將死優先，延後的將死分數遞減

**實現位置**：`engine.py` — `alpha_beta()`, `mate_score()`, `calculate_mate_in()`

### 3.2 子根理論（Root Theory）

**核心概念**：棋子間的保護力加成。

**三種分類**：

| 類型 | 定義 | 說明 |
|------|------|------|
| **有根棋子** | 我方棋子 P 吃掉 A，P 立即被 B 吃掉，且對方不因此丟失其他棋子 | A 有良好防守，不宜輕易動它 |
| **虛根棋子** | A 看似有防守，但 B 吃 P 之後對方因此丟失其他棋子 | A 的防守是虛假的 |
| **無根棋子** | P 吃掉 A 後不會被吃掉 | A 完全暴露，可自由吃取 |

**分數調整**：
- 有根 < 虛根 < 無根（對我方威脅程度）
- 無根棋子：我方評估 -8（對方可免費吃取）
- 虛根棋子：我方評估 -3

**實現**：靜態交換評估（SEE）— `static_exchange_evaluation()` 模擬完整的吃子序列

---

## 四、第三階段：AI 棋手個性化

### 4.1 三名 AI 棋手設計

#### 初學者（BeginnerAI）
- 搜尋深度：1（只看一步）
- 評估：純物料計算，無位置表
- 特色：從最優前 3 步中隨機選擇，模擬真實初學者的不穩定性
- 學習目的：理解基本攻防，建立初學者棋譜參考

#### 柳大華（LiuDahuaAI）
- 搜尋深度：3
- 評估：繼承標準評估 + 攻擊加成（每個攻擊著法 +2 分）+ 機動性獎勵
- 特色：模擬柳大華快棋風格 — 主動進攻，追求戰術複雜性
- 開局書：中炮開局，快速出子
- 學習目的：戰術性中局棋譜，快棋應對模式

#### 胡榮華（HuRonghuaAI）
- 搜尋深度：4
- 評估：繼承標準評估 + 王安全加成 + 棋子協調加成 + 過河兵獎勵
- 特色：模擬胡榮華的精算風格 — 穩健、長線謀略、殘局精湛
- 開局書：較長的開局序列（8 步），更精細的發展策略
- 學習目的：穩健型棋局，精確殘局參考

### 4.2 訓練自對弈（Self-Play）

建立 `self_play.py`，讓三名 AI 各自與主 AI（標準 ChineseChessEngine）對弈：

**重大轉折點偵測**：
- 分數變化 > 40 分（物料重大得失）
- 出現「幾步擒王」（mate-in-N ≤ 5）
- 吃掉高價值棋子（俥/車、帥/將）

**產出**：
- PIL 渲染的棋盤截圖（每個轉折點）
- `game_record.txt`（帶分數的完整棋譜）
- `game_record.json`（機器可讀格式，含轉折點索引）

---

## 五、第四階段：GitHub 與分支策略

### 倉庫結構
- **GitHub**: https://github.com/sipurchen/Chinese_Chess_AI
- **`master` 分支**：穩定版本，初始提交包含所有核心功能
- **`Caught_the_king` 分支**：研發分支，往後所有新功能在此分支進行

### 分支命名意義
`Caught_the_king` — 呼應核心的「擒王分數」設計理念，所有研發的目標都是更精準地計算「擒王」路徑。

---

## 六、技術架構總覽

```
Flask Server (app.py)
    │
    ├── GET  /              → 棋盤介面
    ├── POST /move          → 接收玩家著法 → AI 應對 → 回傳分析
    ├── POST /reset         → 重置棋局
    └── POST /set_difficulty → 切換 AI 個性

Engine Layer (engine.py)
    │
    ├── ChineseChessEngine  (基礎引擎)
    │   ├── 合法著法生成（7 種棋子）
    │   ├── 飛將規則
    │   ├── Alpha-Beta + Quiescence Search
    │   ├── 擒王分數系統
    │   ├── 子根理論 (SEE)
    │   └── 位置表評估
    │
    ├── BeginnerAI  extends ChineseChessEngine
    ├── LiuDahuaAI  extends ChineseChessEngine
    └── HuRonghuaAI extends ChineseChessEngine

Knowledge Base (ai_memory.py)
    ├── ENDING_STEPS     殘局譜（10 個模式）
    ├── OPENING_*        三份開局書
    ├── MIDGAME_PATTERNS 中局戰術模式
    └── POS_TABLE_*      位置獎勵矩陣

Self-Play (self_play.py)
    ├── PIL 棋盤渲染（支援中文字體）
    ├── 轉折點自動偵測
    ├── GameRecord 棋譜記錄類
    └── AI_Games/ 目錄輸出
```

---

---

## 七、第三階段：古譜開局 + 雙方先手 + 解殺還殺 (Session 4)

### 7.1 古譜開局書庫擴充
新增 4 本古典棋譜的開局序列：

| 書名 | 出處 | 特點 | 步數 |
|------|------|------|------|
| 中炮盤頭馬 | 近代定式 | 雙馬並駐七路，俥縱突破 | 7步 |
| 梅花譜 | 清·王再越 | 炮讓路，俥飛車六格 | 7步 |
| 適情雅趣 | 明·徐芝 | 右翼傌俥速攻 | 7步 |
| 百局象棋譜 | 清·三樂居士 | 兵七先動，俥走帥道穩陣 | 7步 |

所有 28 步（含 Black 鏡像）通過合法性驗證。

### 7.2 雙方先手系統
```python
def _quick_mate_threat(self, board, turn, depth=2):
    # 淺度搜索，比較雙方擒王速度
    # initiative_advantage = opp_threat - my_mate_in
    # 正數 = 我方更快，負數 = 對方威脅更大
```

### 7.3 解殺還殺著法排序
當我方被將時，優先搜索反將著法（解殺還殺）：
```
1. 反將著法（解殺還殺）← 最高優先
2. 有利捕獲（SEE > 0）
3. 普通防守著法
```

---

## 八、第四階段：四模式 Flask UI + 賽事系統 + 殘局解題 (Session 5)

### 8.1 AI 棋手 Wiki
- `ai_wiki/LiuDahua_Wiki.md`：柳大華棋風、慣用開局、殘局技巧、代表對局
- `ai_wiki/HuRonghua_Wiki.md`：胡榮華棋風、10屆全冠分析、殘局精技

### 8.2 賽事系統 (ai_tournament.py)
```
三方循環賽：初學者 × 柳大華 × 胡榮華
→ 背景 daemon thread 執行
→ 重大轉折點（分差>40/擒王≤5/先手≥3）觸發觀戰分析
→ 結果儲存 AI_Games/tournament/<session_id>/
→ Flask API: /tournament/start|status|sessions|replay
```

### 8.3 殘局解題模組 (ai_endgame.py)
```python
get_library()      # 內建5道殘局 + 用戶自製殘局
solve_puzzle()     # 引擎解題（depth=1~5）
find_similar()     # Sørensen-Dice 相似度搜索
save_puzzle()      # 用戶殘局持久化
```

### 8.4 四模式 Flask UI
| 模式 | 功能 |
|------|------|
| 人機對弈 | 完整保留，難度選擇，思路面板 |
| AI 對弈 | 賽事啟動/進度輪詢/積分榜/回放 |
| 分析棋局 | 載入歷史棋局/步進/AI分析 |
| 試解殘局 | 調色盤擺棋/AI解題/相似搜索/儲存 |

---

## 九、第五階段：擒王理論深化 (Session 6)

### 9.1 轉置表（Transposition Table）
```python
TT_EXACT = 0 | TT_LOWER = 1 | TT_UPPER = 2
MAX_TT_SIZE = 150_000

# alpha_beta() 內部 TT 查詢/儲存
tt_key = (board_key(board), turn)
if tt_key in self.tt:
    tt_depth, tt_score, tt_flag, tt_pv = self.tt[tt_key]
    if tt_depth >= depth:
        # exact/alpha/beta 分支 → 直接返回
# ...
self.tt[tt_key] = (depth, best_score, flag, best_pv)
```
效能提升：深度4搜索速度提升約3~5倍（避免重複計算相同局面）。

### 9.2 擒王一步偵測（Mate-in-1 Shortcut）
```python
def _find_mate_in_one(self, board, turn):
    """在完整搜索前先掃描直接絕殺，O(legal_moves) 複雜度"""
    for move in generate_legal_moves(board, turn):
        nb = make_move_internal(board, move)
        if is_in_check(nb, opp) and not generate_legal_moves(nb, opp):
            return move  # 立即返回，不需深搜
    return None
```

### 9.3 殺手著法（Killer Moves）
```python
# killers[depth] = [move1, move2]  最多保留2個殺手著法
# 在beta cut時：若是安靜著法 → 記錄為殺手著法
# 在order_moves中：殺手著法優先於一般安靜著法
```
效果：在每個深度節點，以前造成剪枝的安靜著法優先搜索，提高 alpha-beta 剪枝效率。

### 9.4 殘局推衍（Endgame Mode）
```python
def is_endgame(self, board):
    # 重子（俥/炮）總數 ≤ 3 → 進入殘局模式
    
# evaluate_board 殘局調整：
_ENDGAME_VALUE_ADJUST = {
    'n/N': +10,  # 傌在殘局更強（跳格不需炮架）
    'c/C': -10,  # 炮在殘局較弱（屏風減少）
    'p/P': +5,   # 兵在殘局更寶貴
}
# 帥/將活躍度加分（距五路距離 + 前進深度）
# 過河兵深入敵陣加分 (+18)
```

### 9.5 開局定式辨識（Opening Classifier）
```python
def classify_opening(self, board):
    # 辨識對手開局類型
    if board[7][4] == 'C': return 'red_central_cannon'  # 當頭炮
    if board[7][6/2] == 'C': return 'red_side_cannon'   # 過宮炮
    if board[5][2] == 'B': return 'red_elephant'          # 飛相局
    
# _try_opening_move() 共用方法：
# - 顏色無關（黑方自動鏡像）
# - 開局定式標記輸出（opening_tag + opening_name）
# - 對手偏離時自動轉入搜索
```

### 9.6 中局機動性評分
```python
# 中局階段（非開局非殘局）：
my_moves_count = len(generate_pseudo_legal_moves(board, turn))
opp_moves_count = len(generate_pseudo_legal_moves(board, opp))
score += (my_moves_count - opp_moves_count) // 4
# 己方行動力優於對方 → 加分
```

---

## 十、分支策略

| 分支 | 用途 |
|------|------|
| `master` | 穩定版本，初始核心功能 |
| `Caught_the_king` | 主研發分支（擒王理論、規則引擎、AI個性） |
| `Web_UI_App` | 武俠仙人對弈 WebUI 美術風格研發分支 |

---

## 十一、技術架構（當前版本）

```
Flask Server (app.py)
    ├── /              人機對弈介面
    ├── /move          玩家著法 → AI應對
    ├── /reset         重置
    ├── /set_difficulty 切換AI
    ├── /tournament/*  賽事系統
    ├── /games/*       棋局分析
    ├── /analyze       AI分析API
    └── /endgame/*     殘局解題

Engine Layer (engine.py)
    ├── ChineseChessEngine
    │   ├── 合法著法生成（7種棋子，含蹩馬腿/炮跳吃/象不過河）
    │   ├── 飛將規則檢測
    │   ├── Alpha-Beta + Quiescence Search
    │   ├── 轉置表 TT（150K條目）
    │   ├── 殺手著法（每深度2個）
    │   ├── 擒王分數系統（MATE_SCORE=30000）
    │   ├── 子根理論 SEE
    │   ├── 解殺還殺著法排序
    │   ├── 雙方先手比較
    │   ├── 殘局模式偵測 + 棋子值調整
    │   ├── 開局定式辨識
    │   └── 擒王一步偵測
    ├── BeginnerAI  (depth=1, 隨機化)
    ├── LiuDahuaAI  (depth=3, 戰術進攻, 5步開局書)
    └── HuRonghuaAI (depth=4, 位置精算, 8步開局書)

Knowledge Base (ai_memory.py)
    ├── PIECE_VALUES          棋子基礎值
    ├── ENDING_STEPS_WIN (14) 必勝殘局譜
    ├── ENDING_STEPS_DRAW (10)必和殘局譜
    ├── OPENING_* (8本)       開局書庫
    ├── OPENING_TRAPS         開局陷阱（擒王標記）
    ├── MIDGAME_PATTERNS      中局戰術模式
    └── POS_TABLE_*           位置獎勵矩陣

Tournament (ai_tournament.py)
    ├── BeginnerTournament/LiuTournament/HuTournament (depth=2)
    ├── start_tournament() → daemon thread
    ├── 觀戰分析 → ChineseChessEngine depth=2
    └── 結果 JSON → AI_Games/tournament/

Endgame Manager (ai_endgame.py)
    ├── get_library()  / save_puzzle()
    ├── solve_puzzle() → engine.get_best_move()
    └── find_similar() → Sørensen-Dice

Self-Play (self_play.py)
    └── PIL 渲染 + 轉折點偵測（分差/擒王/先手/雙方先手）
```

---

## 十二、下一階段：武俠仙人對弈 WebUI App

詳細規劃見 `Others_AI_Planning.md`，要點：
- 水墨山水棋盤美術風格
- 紙娃娃系統 + Gemini 水墨頭像生成
- 棋道點數解鎖難度 + 商店
- 三 AI 協作（Claude/ChatGPT-5.4/Gemini 3 Flash）
- 分支：`Web_UI_App`

---

*文件建立時間：2026-05-26 | 最後更新：2026-05-27*
*當前分支：`Caught_the_king` (引擎研發) / `Web_UI_App` (介面研發)*
