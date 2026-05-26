# User Commands Log / 使用者指令記錄

Record of user commands that shaped this project. Each entry captures the original instruction and what it produced.

---

## Session 1 — 2026-05-26

### Command 1: Foundation & Theory Build

```
1. 先用gemini cli 搜尋並整理所有中國象棋規則
2. 用claude code cli 將當前資料夾內容進行整理，確認此專案知識與已完成部份的狀態
3. 建立擒王分數，核心概念來自於中國象棋唯一目的為攻擊或限制使將(黑方)帥(紅方)無法進行躲閉
   或符合規則的行動，所有棋子行動的最終目的即為擒王，以幾步(包含對方合理應對棋步)後可以擒王
   為分數排序
4. 在盤面分數套用子根理論，核心思想為棋子間的保護力加成，當我方持棋子P吃掉某個棋子A，P馬上
   被另一棋子B吃掉，並且對方不會因此丟失其他棋子，A就叫做有根棋子，如果B吃掉P之後，對方因此
   丟失其他棋子，則A稱之為虛根棋子，P吃掉A後不為被吃掉，則A稱之為無根棋子，
   有根棋子分數<虛根棋子分數<無根棋子分數
5. 參照中國象棋規則中的和棋局面，預先演練大量和局走法與巧勝走法，並放置於AI棋手記憶區
   AI_Memories的殘局譜參考(EndingStep)中，以強化殘局應對
6. 中局手段可以用gemini cli進行盤面設計，並優先以棋步順序來建立邏輯
7. 預設三名各種難度AI對手，最弱為初學者，其次參考柳大華快棋譜，最強參考胡榮華棋譜，
   包含開局、中局應變、殘局手段。
8. 完成對手設置後，由這三名AI對手對AI棋手進行訓練前，先建立遠端 public repo Chinese_Chess_AI，
   將本專案初始化為master分支，新增Caught_the_king分支，往後在新分支進行研發
```

**Result:**
- Gemini CLI researched complete Xiangqi rule set (all piece movements, special rules, draw conditions)
- Project state audit: identified basic engine, no positional theory, single AI
- Implemented 擒王分數 (Catch-the-King scoring): `MATE_SCORE - depth`, faster mates rank higher
- Implemented 子根理論 (Root Theory): SEE-based 有根/虛根/無根 classification with score adjustment
- Created `ai_memory.py` with 10 EndingStep endgame patterns, opening books, mid-game patterns
- Built three AI personalities: 初學者 (depth 1), 柳大華 (depth 3, tactical), 胡榮華 (depth 4, positional)
- Added difficulty selector UI (buttons without page reload)
- Created GitHub repo: https://github.com/sipurchen/Chinese_Chess_AI
- Initialized `master` branch, created `Caught_the_king` development branch

---

### Command 2: Self-Play Games & Documentation

```
1. 以初學者棋手和AI棋手下棋，在擒王分數重大轉折點截圖，將最終結果棋譜存入AI_Novice下
   做為AI_Novice棋譜參考
2. 以柳大華快棋手和AI棋手下棋，在擒王分數重大轉折點截圖，將最終結果棋譜存入AI_LiuDahua下
   做為AI_LiuDahua棋譜參考
3. 以胡榮華棋手和AI棋手下棋，在擒王分數重大轉折點截圖，將最終結果棋譜存入AI_HuRonghua下
   做為AI_HuRonghua棋譜參考
4. 將1~3的結果做為簡單介紹，更新README.MD，MIT授權，並建立Others_AI.MD 寫入專案最初到現在
   的整個思路和規劃，並將最近的使用者指令寫入UserCommand.MD
```

**Result:**
- Created `self_play.py`: AI vs AI simulation engine with PIL board renderer
- Ran three matchups: Novice/LiuDahua/HuRonghua each vs standard ChineseChessEngine
- Generated PNG board screenshots at 擒王分數 major turning points (score Δ > 40, mate-in ≤ 5, king capture)
- Saved `game_record.txt` and `game_record.json` for each matchup in `AI_Games/`
- Created `README.md` with project overview, feature table, getting started guide
- Added `LICENSE` (MIT, 2026)
- Created `Others_AI.MD` with full design history and technical architecture
- Created `UserCommand.MD` (this file)

---

### Command 3: Session 3 Enhancements

```
1. 殘局追加炮仕勝雙士、單傌勝單士、海底撈月(俥炮中帥勝單車)等知名殘局(gemini cli搜尋)
2. 殘局追加必和殘局(gemini cli搜尋)
3. 禁止著法提醒變著
4. 中局變化與開局定式增加橘中秘與夾炮屏風、反宮馬、五六炮、士角砲、龜背炮、卒底包、
   沿河十八打等開局變化，擒王系統僅記錄特殊開局陷阱棄傌陷車、重炮等(gemini cli搜尋)
5. 紅黑雙方顯示要更清晰
6. 截圖要更完整，顯示整個盤面，並加入到README.MD中
```

**Result:**
- `ai_memory.py` expanded to 14 winning endgame patterns (ENDING_STEPS_WIN):
  炮仕勝雙士, 單傌勝單士, 海底撈月, 重炮殺法, 臥槽馬殺法, 炮打底士接俥底殺, 釣魚馬殺法, 雙車錯殺
- `ai_memory.py` added 10 mandatory draw patterns (ENDING_STEPS_DRAW):
  單車對雙象守和, 單炮對單士, 雙馬對雙士(羊角士), 車炮萬年和, 馬炮對車, 士象全守和, etc.
- Added 禁止著法 (forbidden move) detection: 長將 / 長捉 / 長將捉; AI avoids repetition moves
- 8 new opening books added: 橘中秘, 夾炮屏風, 反宮馬, 五六炮, 士角炮, 龜背炮, 卒底炮, 沿河十八打
- `OPENING_TRAPS` added for 擒王系統: 棄傌陷車, 重炮殺局, 當頭炮陷阱 (each with catch_the_king_score)
- Red/black piece styling improved: red = gold gradient coins, black = dark slate coins, 3D shadow effect
- Board renderer enlarged: CELL=70 (was 60), MARGIN=55 (was 40), proportional piece radii
- `draw_board()` updated: HEADER_H=40px title bar, RED_BG_C/BLACK_BG_C piece backgrounds
- Forbidden move warning banner added to UI (red alert, auto-hide 5s, slide-in animation)
- Thought panels restructured with styled divs: score delta, mate-in threat, PV moves, trap warnings
- Self-play re-run with larger board size; screenshots added to README.md gallery section

---

### Command 4: 古譜開局 + 雙方先手 + 解殺還殺

```
1. 增加新譜：中炮盤頭馬  梅花譜 適情雅趣 百局象棋譜
2. 目前的重大轉折不夠重大，應該要增加計算雙方先手，
   即雙方擒王步數相比，何者更快則分數應有加成
3. 考慮解殺還殺(gemini cli搜尋並補足相關盤面)
```

**Result:**
- `ai_memory.py` 新增 4 本古譜開局書庫：
  - **中炮盤頭馬**: 雙傌並駐七路（盤頭），俥二縱深突破，7步合法棋步
  - **梅花譜**（清・王再越）: 炮八平九讓路→俥八進六飛車6格→邊炮跟進夾擊
  - **適情雅趣**（明・徐芝）: 右翼傌俥先發→俥縱深→炮八進四深入河界
  - **百局象棋譜**（清・三樂居士）: 兵七先動→俥走帥道穩陣，步步為營
  - 全部 28 步（含 Black 鏡像 28 步）均通過合法性驗證
- `ai_memory.py` MIDGAME_PATTERNS 新增解殺還殺系列（解殺還殺、棄子解殺還殺、雙將解殺、先手連將）
- `engine.py` 解殺還殺 (order_moves): 被將時先試算 counter_checks，排序最前
- `engine.py` 雙方先手 (get_best_move): _quick_mate_threat + thought 含 opponent_threat_in / initiative_advantage
- `self_play.py` 轉折點新增 mate_gain / init_gap / init_flip 三條件，截圖標籤升級
- LiuDahuaAI / HuRonghuaAI 每局隨機從 3 本兼容開局書庫中選一本
- 提交: 4fab33c → Caught_the_king

---

### Command 5: AI棋手Wiki + 賽事系統 + 四模式UI + 殘局解題 + 武俠規劃

```
1. 認真的用gemini cli查所有對局並記錄於柳大華和胡榮華兩位AI對手的棋譜，
   包含分析一併建構成微型wiki，讓兩位AI對手的棋力能夠有模仿對象的風格
2. 讓三位AI對手間互相對局練習100次並留下對局記錄，並由AI棋手在旁觀戰並分析學習，
   這個內容必須能夠在當前的flask UI上呈現和重現
3. 目前的UI介面應該要有人機對奕/AI對奕/AI棋手分析棋局/AI棋手試解殘局
4. AI棋手試解殘局的部份需要提供擺譜功能，並且要有讓AI對手和AI棋手試錯解局的選項，
   解開的殘局加入記憶中，並可在試解殘局中調閱解法，擺譜功能也可比對類似殘局提供選取
5. 開始準備跟其他AI(Codex ChatGPT5.4/Antigravity Gemini 3 flash)協作，
   以下一階段為武俠仙人對奕風格WebUI App進行規劃
```

**Result:**
- `ai_wiki/LiuDahua_Wiki.md` 建立柳大華微型wiki（棋風、慣用開局、中局手段、殘局技巧、代表對局）
- `ai_wiki/HuRonghua_Wiki.md` 建立胡榮華微型wiki（同上，含10屆全國冠軍風格分析）
- `ai_tournament.py` 賽事系統完成：
  - `BeginnerTournament/LiuTournament/HuTournament`（depth=2 快速版）
  - `start_tournament(session_id, games_per_pair)` → 背景 daemon thread
  - `get_status/list_tournament_games/load_tournament_game` API
  - 觀戰分析：ChineseChessEngine 在重大轉折點（分差>40/擒王≤5/先手≥3）介入分析
  - 結果儲存 `AI_Games/tournament/<session_id>/`
- `ai_endgame.py` 殘局管理器新建：
  - 5 道內建經典殘局（雙俥錯、俥炮聯攻、馬後砲、傌踩連環、車馬協攻）
  - `solve_puzzle(board, turn, depth)` → 引擎解題
  - `find_similar(board)` → Sørensen-Dice 相似度搜索
  - `save_puzzle/get_library` → 使用者殘局持久化
- `app.py` 全面重寫，新增路由：
  - `/tournament/start|status|sessions|replay`
  - `/games/list|load` + `/analyze`
  - `/endgame/library|solve|save|similar`
- `templates/index.html` 全面重寫：四模式標籤頁、三欄佈局、棋子調色盤
- `static/css/style.css` 全面更新：武俠紅金主題 Header、棋子調色盤、進度條、走法列表
- `static/js/main.js` 全面重寫（750行+）：
  - Mode 1（人機對弈）：完整保留原有功能
  - Mode 2（AI對弈）：賽事啟動、輪詢進度、對局回放（precomputeBoards + 步進/自動播放）
  - Mode 3（分析棋局）：載入棋局、步進導航、一鍵AI分析
  - Mode 4（試解殘局）：棋子調色盤擺棋（左鍵放、右鍵刪）、AI解題、相似殘局、儲存
- `Others_AI_Planning.md` 武俠仙人對弈 WebUI App 完整規劃文件（美術方向/角色系統/棋道點數/技術架構/里程碑）

---

### Command 6: 規劃文件更新 + 擒王理論深化 + Web_UI_App 分支

```
1. 將規劃寫入Others_AI.MD 和 UserCommand.MD中，完成後git commit push，
   開新分支Web_UI_App 切分出去
2. 繼續完善擒王理論部份，確認AI棋手是依照棋規和理論與AI對手進行對局後，
   再加入開局定式、中局變化和殘局推衍輔助
```

**Result:**
- `Others_AI.MD` 全面更新，新增第七~十二章：
  - Session 4（古譜/雙方先手/解殺還殺）詳解
  - Session 5（Wiki/賽事/四模式UI/殘局）詳解
  - Session 6（擒王理論深化）完整技術說明
  - 分支策略表（master/Caught_the_king/Web_UI_App）
  - 當前技術架構全覽（含所有模組/路由/評估層）
  - 武俠 App 下一階段預告
- `UserCommand.MD` 新增 Session 6 記錄
- `engine.py` 擒王理論深化，7項改進：

  **1. 轉置表（TT）**
  - `TT_EXACT/TT_LOWER/TT_UPPER` 標記
  - `MAX_TT_SIZE = 150_000` 條目
  - `alpha_beta()` 內查詢 + 儲存；TT最佳著法優先排序
  - 預估深度4速度提升 3~5×

  **2. 擒王一步偵測**
  - `_find_mate_in_one()` — O(legal_moves) 快速掃描
  - `get_best_move()` 開頭先呼叫，立即返回絕殺著法
  - thought 標記 `source='mate_in_1'`, `mate_in=1`

  **3. 殺手著法（Killer Moves）**
  - `self.killers = {}` 每次搜索清空
  - beta cut + 安靜著法 → 記錄至 `killers[depth]`（最多2個）
  - `order_moves(depth=0)` 加入 killer 優先層

  **4. 殘局模式偵測**
  - `is_endgame()` — 重子（俥/炮）≤3 即殘局
  - `_ENDGAME_VALUE_ADJUST`：傌+10/炮-10/兵+5
  - 殘局帥將活躍度加分（中路距離 + 推進距離）
  - 過河深兵加分 +18

  **5. 開局定式辨識**
  - `classify_opening()` — 偵測當頭炮/過宮炮/飛相局
  - `opening_phase()` — 開局判斷（主力棋子≥14在初始區）
  - 開局書 thought 輸出 `opening_tag` + `opening_name`

  **6. 中局機動性評分**
  - 非開局非殘局：`(my_moves - opp_moves) // 4` 加分

  **7. 共用開局書方法**
  - `_try_opening_move(max_moves)` 消除 Liu/Hu 重複代碼
  - 顏色無關（黑方自動鏡像），偏離時自動轉搜索

- **新建分支 `Web_UI_App`**（從 Caught_the_king 切出），供武俠 WebUI App 研發使用

---

## Conventions

- All new R&D happens on branch `Caught_the_king`
- Stable releases merged to `master`
- Game records in `AI_Games/<personality>/` serve as training reference for each AI personality
- `ai_memory.py` is the central knowledge store — EndingStep, opening books, tactical patterns
