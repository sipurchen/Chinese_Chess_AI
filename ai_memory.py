# AI Memory: Opening books, endgame patterns, and mid-game references
# EndingStep entries derived from classic Chinese chess endgame theory
# Draw situations (和局) and clever winning lines (巧勝) pre-catalogued

# Board notation: (r, c) with r=0 top (black side), r=9 bottom (red side)
# Piece codes: r=黑車 n=黑馬 b=黑象 a=黑士 k=黑將 c=黑砲 p=黑卒
#              R=紅俥 N=紅傌 B=紅相 A=紅仕 K=紅帥 C=紅炮 P=紅兵

PIECE_VALUES = {
    'k': 0,   'K': 0,
    'a': 20,  'A': 20,
    'b': 20,  'B': 20,
    'n': 40,  'N': 40,
    'r': 90,  'R': 90,
    'c': 45,  'C': 45,
    'p': 10,  'P': 10,
}

# ===== ENDGAME PATTERNS (殘局譜) =====
# Format: name, description, draw_or_win, key_moves (sequence of (from, to))
ENDING_STEPS = [
    {
        "name": "單車勝單士象全",
        "type": "win",
        "description": "俥勝單士雙象 - 車在底線配合將帥擒王",
        "key_moves": [
            # Rook controls the king's column, king advances
            ((9,4),(8,4)), ((0,4),(0,3)), ((9,0),(9,3)), ((0,3),(0,4)),
            ((9,3),(0,3)),  # Rook delivers checkmate
        ],
        "tags": ["車勝", "士象全", "殘局"]
    },
    {
        "name": "雙俥勝單將",
        "type": "win",
        "description": "雙車配合擒王基本法",
        "key_moves": [
            ((9,0),(9,4)), ((0,4),(1,4)), ((9,8),(0,8)), ((1,4),(1,3)),
            ((9,4),(1,4)),  # Checkmate
        ],
        "tags": ["雙車勝", "擒王"]
    },
    {
        "name": "馬後砲絕殺",
        "type": "win",
        "description": "馬踩宮心砲封將路 - 經典絕殺手筋",
        "key_moves": [
            ((7,4),(5,3)), ((0,4),(0,3)), ((7,7),(4,4)),  # 砲封將
        ],
        "tags": ["馬後砲", "絕殺", "中局"]
    },
    {
        "name": "單俥巡河和局",
        "type": "draw",
        "description": "殘局俥在河界巡邏，守和技巧",
        "key_moves": [
            ((5,0),(5,8)), ((5,8),(5,0)),  # Rook patrols river - draw by repetition avoidance
        ],
        "tags": ["和局", "巡河", "單車"]
    },
    {
        "name": "雙士守和車炮馬",
        "type": "draw",
        "description": "雙士守宮和局技巧 - 對方車炮馬難以突破",
        "key_moves": [
            ((9,3),(8,4)), ((9,5),(8,4)), ((8,4),(9,3)), ((8,4),(9,5)),
        ],
        "tags": ["和局", "雙士", "守和"]
    },
    {
        "name": "俥炮傌勝單將",
        "type": "win",
        "description": "車炮馬三子聯攻擒王",
        "key_moves": [
            ((7,4),(5,4)), ((0,4),(0,3)), ((7,7),(3,7)), ((0,3),(0,4)),
            ((5,4),(0,4)),  # Checkmate
        ],
        "tags": ["三子聯攻", "擒王"]
    },
    {
        "name": "長將逼和",
        "type": "draw",
        "description": "己方劣勢時用長將逼和 - 規則允許要求對方變招",
        "key_moves": [
            ((5,4),(0,4)), ((0,4),(1,4)), ((5,4),(1,4)), ((1,4),(0,4)),
        ],
        "tags": ["長將", "逼和", "戰術"]
    },
    {
        "name": "兵底將殺",
        "type": "win",
        "description": "過河兵在底線配合帥攻殺",
        "key_moves": [
            ((2,4),(1,4)), ((0,4),(0,3)), ((1,4),(0,4)),  # Pawn checkmate support
        ],
        "tags": ["兵殺", "殘局", "兵卒"]
    },
    {
        "name": "悶宮殺",
        "type": "win",
        "description": "棋子封死將帥所有出路後絕殺",
        "key_moves": [
            ((5,4),(0,4)),  # Rook enters palace
        ],
        "tags": ["悶宮", "絕殺", "戰術"]
    },
    {
        "name": "高車保兵勝",
        "type": "win",
        "description": "俥高位控制後配合過河兵勝",
        "key_moves": [
            ((5,0),(1,0)), ((0,4),(0,3)), ((1,0),(1,3)),
        ],
        "tags": ["高車", "兵勝", "殘局"]
    },
]

# ===== OPENING BOOKS =====
# Format: position_hash -> list of (move, weight) sorted by preference

# Beginner opening: basic development
OPENING_BEGINNER = {
    "start": [
        # 中炮開局
        (((7,1),(7,4)), 10),   # 炮二平五
        (((9,1),(7,2)), 8),    # 傌二進三
        (((6,2),(5,2)), 7),    # 兵三進一
    ]
}

# Liu Dahua style: quick tactical play
OPENING_LIU_DAHUA = {
    "start": [
        (((7,1),(7,4)), 15),   # 中炮
        (((9,1),(7,2)), 12),   # 傌二進三
        (((9,0),(9,3)), 10),   # 俥一平四
        (((6,4),(5,4)), 9),    # 中兵進一
    ],
    "response_to_screen_horse": [
        (((7,7),(7,4)), 12),   # 砲八平五 反宮馬
        (((9,8),(9,5)), 10),   # 俥九平六
    ]
}

# Hu Ronghua style: deep positional, patient
OPENING_HU_RONGHUA = {
    "start": [
        (((7,1),(7,4)), 15),   # 中炮
        (((9,1),(7,2)), 12),   # 傌二進三
        (((7,7),(7,5)), 11),   # 炮八平六
        (((9,0),(8,0)), 10),   # 俥一進一
        (((6,6),(5,6)), 9),    # 兵七進一
    ],
    "endgame_preference": "positional",  # Prefers positional endgame over tactics
    "draw_threshold": -50,  # Will seek draw only if significantly behind
}

# ===== MID-GAME PATTERNS =====
# Key tactical sequences for mid-game play
MIDGAME_PATTERNS = [
    {
        "name": "閃將抽俥",
        "description": "利用將軍閃開後抽吃對方俥/車",
        "trigger": "own_piece_attacked",
        "tactic": "discovered_check",
        "tags": ["戰術", "中局", "閃將"]
    },
    {
        "name": "兌子入局",
        "description": "主動兌換棋子，換得有利殘局形式",
        "trigger": "endgame_conversion",
        "tactic": "exchange",
        "tags": ["殘局轉換", "兌子"]
    },
    {
        "name": "兩翼包抄",
        "description": "雙俥分兵兩路包抄對方將帥",
        "trigger": "rook_pair",
        "tactic": "double_rook_attack",
        "tags": ["雙車", "包抄", "攻王"]
    },
    {
        "name": "棄子攻王",
        "description": "主動棄子，換取直接攻王線路",
        "trigger": "king_attack",
        "tactic": "sacrifice",
        "tags": ["棄子", "攻王", "中局"]
    },
    {
        "name": "頓挫手段",
        "description": "將軍迫使對方應答後，再執行真正意圖",
        "trigger": "tempo_gain",
        "tactic": "zwischenzug",
        "tags": ["手筋", "頓挫"]
    },
]

# ===== POSITIONAL SCORE TABLES =====
# Per-square bonuses for each piece type (10 rows x 9 cols)
# Red perspective (row 9 = home side)

POS_TABLE_RED_PAWN = [
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 2,  0,  4,  0,  6,  0,  4,  0,  2],  # Just crossed river
    [18, 36, 36, 36, 45, 36, 36, 36, 18],  # Deep in enemy territory
    [28, 36, 36, 36, 45, 36, 36, 36, 28],
    [ 0, 36, 36, 36, 45, 36, 36, 36,  0],
    [ 0, 36, 36, 36, 45, 36, 36, 36,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],  # Own side (shouldn't be here)
]

POS_TABLE_RED_HORSE = [
    [ 4, 8, 16, 12,  4, 12, 16,  8,  4],
    [ 4,10, 28, 16,  8, 16, 28, 10,  4],
    [ 8,16, 20, 24, 24, 24, 20, 16,  8],
    [ 8,24, 32, 32, 32, 32, 32, 24,  8],
    [ 8,24, 32, 32, 32, 32, 32, 24,  8],
    [16,32, 28, 28, 32, 28, 28, 32, 16],
    [ 4,16, 24, 20, 20, 20, 24, 16,  4],
    [ 4, 8, 16, 24, 12, 24, 16,  8,  4],
    [ 4, 4,  8, 16,  4, 16,  8,  4,  4],
    [ 0, 4,  4,  4,  4,  4,  4,  4,  0],
]

POS_TABLE_RED_ROOK = [
    [14, 14, 12, 18, 16, 18, 12, 14, 14],
    [16, 20, 18, 24, 26, 24, 18, 20, 16],
    [12, 12, 12, 18, 15, 18, 12, 12, 12],
    [12, 18, 16, 22, 22, 22, 16, 18, 12],
    [12, 14, 12, 18, 15, 18, 12, 14, 12],
    [12, 16, 14, 20, 20, 20, 14, 16, 12],
    [14, 14, 14, 18, 20, 18, 14, 14, 14],
    [16, 20, 20, 26, 25, 26, 20, 20, 16],
    [14, 18, 16, 24, 24, 24, 16, 18, 14],
    [14, 14, 14, 16, 16, 16, 14, 14, 14],
]

POS_TABLE_RED_CANNON = [
    [ 6,  4,  0, -10,  -12, -10,  0,  4,  6],
    [ 2,  2,  0, -4,  -14,  -4,  0,  2,  2],
    [ 2,  2,  0, -10,  -8, -10,  0,  2,  2],
    [ 0,  0, -2,  4,   10,   4, -2,  0,  0],
    [ 0,  0,  0,  2,    8,   2,  0,  0,  0],
    [-2,  0,  4,  2,    6,   2,  4,  0, -2],
    [ 0,  0,  0, -2,    4,  -2,  0,  0,  0],
    [ 2,  2,  0,  2,    6,   2,  0,  2,  2],
    [ 2,  2,  0,  2,    6,   2,  0,  2,  2],
    [ 0,  0, -4,  0,    2,   0, -4,  0,  0],
]

POS_TABLE_RED_KING = [
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
    [ 0,  0,  0,  1,  1,  1,  0,  0,  0],
    [ 0,  0,  0,  2,  2,  2,  0,  0,  0],
    [ 0,  0,  0,  1,  3,  1,  0,  0,  0],
]
