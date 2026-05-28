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

## 十二、下一階段：武俠仙人對弈 WebUI App（完整規劃）

> **協作 AI**：Claude (Anthropic) × Codex / ChatGPT-5.4 (OpenAI) × Gemini 3 Flash (Google)
> **文件更新**：2026-05-27

### 12.1 願景概述

現有引擎已具備完整規則、三種個性 AI、開局書庫、殘局記憶與賽事系統。下一階段目標：包裝成**武俠仙人對弈**風格 Web App，融合：

- **視覺沉浸**：水墨山水、仙人棋局、飄逸棋子動畫
- **角色扮演**：紙娃娃系統 + 自拍臉部生成，讓玩家化身棋道修行者
- **進度解鎖**：難度關卡、棋道點數商店、特殊殘局事件
- **多 AI 協作**：Claude 負責邏輯/架構、ChatGPT 負責對話/劇情、Gemini 負責圖像生成/風格描述

### 12.2 美術方向

| 元素 | 說明 |
|------|------|
| 棋盤 | 古桐木紋理，帶水墨暈染邊框，河界以毛筆字呈現 |
| 棋子 | 玉石感圓形，紅方暖玉、黑方墨玉，帶微光動效 |
| 背景 | 雲霧繚繞山水畫，隨局勢變化（佔優→晴天；劣勢→烏雲） |
| 音效 | 古琴作背景，落子聲為石落玉盤，將軍時鐘聲 |
| 字體 | 標題書法字，UI 仿宋/楷書 |

**場景設計：**
- **主大廳**：雲上亭台，遠山疊嶂，「棋道修行者」NPC 坐鎮
- **對弈場**：古木棋桌，兩側燭台，獲勝後仙鶴/金光特效
- **殘局洞**：石窟場景，石壁刻殘局圖，AI 仙師講解
- **藏寶閣**：棋道點數商店，陳列皮膚/特效/服裝

### 12.3 角色系統

**紙娃娃 (Paper Doll) 層次（從底到頂）：**
```
1. 身形輪廓（男/女/中性，5 種體型）
2. 服裝（道袍/儒服/俠客裝/仙女衣 等 20+ 款）
3. 頭部 → 臉部
4. 髮型 + 髮飾
5. 配件（拂塵/書卷/玉佩/寶劍 等）
6. 特效光暈（初學者=無 / 柳大華=藍光 / 胡榮華=金光）
```

**臉部生成（自拍功能）技術方案：**
```
A. 基礎版（MVP）：
   - 前端擷取自拍 (canvas.getContext('2d'))
   - 後端送至 Gemini Vision：「將此人臉轉換為水墨武俠風格頭像，保留面部特徵，筆觸寫意」
   - 生成結果疊加到紙娃娃上

B. 進階版：
   - MediaPipe FaceMesh 偵測臉部關鍵點
   - 映射至預設臉型模板（圓/方/瓜子臉 × 3 眼型 × 3 嘴型）
   - 組合生成個人化臉部，套用水墨濾鏡
```

### 12.4 遊戲模式與難度解鎖

**難度關卡體系：**
```
等級    稱號          條件             對手
──────────────────────────────────────────────────────
Lv.0   棋道初學者     初始解鎖         初學者 AI (depth=1)
Lv.1   棋道學徒       累計勝 5 局      + 柳大華 AI (depth=3)
Lv.2   棋道門生       累計勝 20 局     + 胡榮華 AI (depth=4)
Lv.3   棋道高手       完成 10 個殘局   特殊殘局事件解鎖
Lv.4   棋道宗師       擊敗仙人 AI      AI 對決模式全開
Lv.5   象棋仙人       完成所有成就     隱藏對手「仙人AI」解鎖
```

**成就系統：**

| 成就名稱 | 觸發條件 | 獎勵 |
|----------|----------|------|
| 初出茅廬 | 完成第一局 | 100 棋道點 |
| 快刀斬亂麻 | 20 步內獲勝 | 500 棋道點 |
| 老謀深算 | 逆轉局面（曾落後 >50 分）獲勝 | 800 棋道點 |
| 殘局達人 | 解開 10 道殘局 | 特效：金色棋子 |
| 擒王術 | 擒王系統 5 步內殺局 | 稱號：「擒王者」|
| 柳大華傳人 | 柳大華開局書庫連贏 3 局 | 特效：柳大華頭像框 |
| 胡榮華弟子 | 胡榮華開局書庫連贏 5 局 | 特效：胡榮華頭像框 |

**棋道點數商店：**
```
商品分類        名稱               價格（棋道點）
────────────────────────────────────────────────
棋子皮膚        翡翠棋子            2000
                黃金棋子            5000
                水晶棋子            3500
棋盤皮膚        宋朝古棋盤          1500
                雲霧仙境棋盤        4000
服裝（角色）    道家長袍            1000
                武林俠客裝          2000
                仙女霓裳            3000
臉部濾鏡        水墨風              免費
                赤霞仙氣            1500
特殊殘局        秘傳殘局（胡榮華）  800
                古譜密題（梅花譜）  1200
特效            落子煙火特效        2500
                勝利仙鶴特效        4000
```

### 12.5 特殊殘局事件

```python
SPECIAL_EVENTS = [
    {
        "id": "xian_ren_zhi_lu",
        "name": "仙人指路",
        "trigger": "雙方兵力相差<5分 且 超過40步",
        "effect": "出現殘局提示卡，可選擇接受仙師指點",
        "reward": 200,
    },
    {
        "id": "sha_ji",
        "name": "殺機突現",
        "trigger": "我方擒王威脅 <= 3步",
        "effect": "背景轉為雷電特效，棋子閃爍",
        "reward": 0,
    },
    {
        "id": "ni_zhuan",
        "name": "乾坤大挪移",
        "trigger": "initiative_advantage 翻轉（正→負 或 負→正）",
        "effect": "旋風動畫，棋盤短暫震動",
        "reward": 50,
    },
]
```

**師父問答系統（Claude 驅動）：**
前端呼叫 `/advisor` 路由 → 後端組合盤面 FEN + 上下文 → 呼叫 Anthropic API (claude-3-5-sonnet) 生成武俠風格建議。

### 12.6 技術架構

**後端（Python/Flask）：**
```
engine.py          現有象棋引擎
ai_memory.py       知識庫
ai_tournament.py   賽事系統
ai_endgame.py      殘局管理
user_profile.py    (新) 用戶資料/點數/成就
ai_advisor.py      (新) 仙師問答，呼叫 Claude API
image_gen.py       (新) 呼叫 Gemini Vision 生成頭像
```

**前端（React 或 vanilla JS + Vite）：**
```
components/
  Board.jsx        棋盤渲染（Canvas 2D 或 SVG）
  PaperDoll.jsx    紙娃娃系統
  FaceCapture.jsx  自拍功能
  Shop.jsx         棋道點數商店
  EventCard.jsx    特殊事件彈窗
  AdvisorChat.jsx  仙師對話框
styles/
  wuxia.css        武俠主題樣式
```

**資料儲存：**
```
MVP（無資料庫）：user_profile.json + LocalStorage
正式部署：SQLite → PostgreSQL / Redis / S3/GCS
```

**AI 協作分工：**
```
任務                    主要 AI         輔助 AI
─────────────────────────────────────────────────
象棋引擎邏輯           Claude          —
仙師建議文字           Claude          —
美術方向/提示詞        Gemini Flash    Claude
臉部風格遷移           Gemini Vision   —
劇情/NPC 對話          ChatGPT-5.4    Claude
程式碼評審             Claude          ChatGPT
API 整合測試           Claude Code     —
棋譜資料庫擴充         Gemini Flash   Claude
```

### 12.7 開發里程碑

| Phase | 目標 | 主要功能 |
|-------|------|---------|
| Phase 1 | 2026-06 基礎美化 | 水墨棋盤、棋子 3D 動畫、武俠 CSS、勝敗特效、古琴背景樂 |
| Phase 2 | 2026-07 角色系統 | 紙娃娃（5 套×2 性別）、Gemini 水墨頭像、棋道點數、5 個成就 |
| Phase 3 | 2026-08 進階互動 | 仙師問答（Claude API）、難度解鎖、點數商店（10 件）、殘局事件 |
| Phase 4 | 2026-09 社交/部署 | 用戶帳號、全球排行榜、棋局分享 PNG、雲端部署（Vercel/Railway）|

### 12.8 風險與注意事項

1. **臉部生成隱私**：自拍不儲存原始照片，明確告知用戶
2. **AI API 費用**：Gemini Vision + Claude API 需加快取和頻率限制
3. **象棋引擎授權**：目前為自製引擎，可安全開源；引入外部引擎需確認授權
4. **棋道點數防作弊**：MVP 本地儲存可被修改，正式版需後端驗證
5. **響應式設計**：武俠 UI 手機端需重新設計（棋盤縮小、控制項重排）

---

---

## 十三、Session 7 — 2026-05-28：分支策略重組 + 路徑隱私清潔

### 13.1 分支重組

| 操作 | 說明 |
|------|------|
| `Caught_the_king` → merge → `master` | Fast-forward merge（144 files，81f956b→615d59a）|
| `master` rename → `Caught_the_king_master` | 穩定版分支改名 |
| `Caught_the_king` 刪除 | Local + Remote 移除 |
| 新建 `Caught_the_king_dev` | 往後 擒王理論 主要研發分支 |

**新分支策略：**

```
Caught_the_king_master  ← 穩定版（原 master + Caught_the_king 合併）
Caught_the_king_dev     ← 擒王理論 R&D（主要工作分支）
Web_UI_App              ← 武俠仙人對弈 WebUI App
```

### 13.2 路徑隱私清潔

**問題**：`self_play.py` 硬編碼 Windows 字體路徑：
```python
# 原始（含本機隱私）
r"C:\Windows\Fonts\simsun.ttc"
r"C:\Windows\Fonts\simhei.ttf"
```

**修復**：改為跨平台動態路徑：
```python
import sys
if sys.platform == "win32":
    _win_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    candidates = [os.path.join(_win_fonts, f) for f in font_names]
elif sys.platform == "darwin":
    candidates = ["/System/Library/Fonts/...", ...]
else:  # Linux
    candidates = ["/usr/share/fonts/opentype/noto/...", ...]
```

- 不暴露本機磁碟代號 (E: C: D:)
- 使用 `%WINDIR%` 環境變數取得系統目錄
- 支援 Windows / macOS / Linux 三平台

### 13.3 已確認無本機路徑的模組

| 模組 | 路徑策略 |
|------|---------|
| `engine.py` | 無檔案 I/O |
| `ai_memory.py` | 無檔案 I/O |
| `ai_endgame.py` | `os.path.dirname(__file__)` 相對路徑 |
| `ai_tournament.py` | `os.path.dirname(__file__)` 相對路徑 |
| `app.py` | `os.path.dirname(__file__)` 相對路徑 |
| `self_play.py` | ✅ Session 7 已修復，改為跨平台字體查找 |

---

*文件建立時間：2026-05-26 | 最後更新：2026-05-28*
*當前分支：`Caught_the_king_dev` (擒王理論研發) / `Web_UI_App` (介面研發)*
