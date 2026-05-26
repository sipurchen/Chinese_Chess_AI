"""
AI Endgame Puzzle Manager — ai_endgame.py
Stores, retrieves, and categorises endgame puzzles.
Provides AI-driven solving, board similarity search, and puzzle persistence.
"""
import os
import json
import hashlib
from datetime import datetime
from engine import ChineseChessEngine

# ── Storage ───────────────────────────────────────────────────────────────────
_BASE = os.path.dirname(__file__)
PUZZLE_FILE = os.path.join(_BASE, 'AI_Games', 'endgame_puzzles.json')

# ── Built-in classic puzzles ──────────────────────────────────────────────────
# Board rows: row 0 = black back rank (top), row 9 = red back rank (bottom).
# Columns: col 0 = left edge, col 8 = right edge.
# Palace: rows 0-2 cols 3-5 (black); rows 7-9 cols 3-5 (red).
_BUILTIN = [
    {
        "id": "builtin_001",
        "name": "雙俥錯殺",
        "description": "紅方雙俥錯位，輪流攻殺，黑將無路可逃",
        "difficulty": "easy",
        "board": [
            ['.', '.', '.', '.', 'k', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', 'R', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['R', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', 'K', '.', '.', '.', '.', '.'],
        ],
        "turn": "red",
        "solution_moves": [
            {"r1": 2, "c1": 4, "r2": 0, "c2": 4}
        ],
        "tags": ["雙俥", "直殺", "一步殺"],
        "mate_in": 1,
        "source": "經典殘局"
    },
    {
        "id": "builtin_002",
        "name": "俥炮聯攻",
        "description": "俥炮協同，炮打底士後俥底殺",
        "difficulty": "medium",
        "board": [
            ['.', '.', '.', 'a', 'k', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', 'C', '.', '.', '.', '.'],
            ['.', '.', '.', 'K', 'R', '.', '.', '.', '.'],
        ],
        "turn": "red",
        "solution_moves": [
            {"r1": 8, "c1": 4, "r2": 0, "c2": 4},
            {"r1": 9, "c1": 4, "r2": 0, "c2": 4}
        ],
        "tags": ["俥炮", "聯攻", "炮底"],
        "mate_in": 2,
        "source": "殘局練習"
    },
    {
        "id": "builtin_003",
        "name": "馬後砲殺法",
        "description": "馬跳入位後炮打將，典型馬後砲殺法",
        "difficulty": "medium",
        "board": [
            ['.', '.', '.', 'a', 'k', 'a', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', 'N', '.', '.', '.'],
            ['.', '.', '.', '.', 'C', '.', '.', '.', '.'],
            ['.', '.', '.', 'K', '.', '.', '.', '.', '.'],
        ],
        "turn": "red",
        "solution_moves": [
            {"r1": 7, "c1": 5, "r2": 5, "c2": 4},
            {"r1": 8, "c1": 4, "r2": 1, "c2": 4}
        ],
        "tags": ["馬後砲", "先跳馬", "殺法"],
        "mate_in": 2,
        "source": "殘局經典"
    },
    {
        "id": "builtin_004",
        "name": "傌踩連環殺",
        "description": "傌連續踩將，對方無處躲閃",
        "difficulty": "hard",
        "board": [
            ['.', '.', '.', '.', 'k', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', 'N', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', 'K', '.', '.', '.', '.', '.'],
        ],
        "turn": "red",
        "solution_moves": [
            {"r1": 8, "c1": 2, "r2": 6, "c2": 3},
            {"r1": 6, "c1": 3, "r2": 4, "c2": 4},
            {"r1": 4, "c1": 4, "r2": 2, "c2": 3}
        ],
        "tags": ["傌踩", "連將", "三步殺"],
        "mate_in": 3,
        "source": "殘局練習"
    },
    {
        "id": "builtin_005",
        "name": "車馬協攻",
        "description": "車馬配合逼將，進行絕殺",
        "difficulty": "hard",
        "board": [
            ['.', '.', '.', '.', 'k', '.', '.', '.', '.'],
            ['.', '.', '.', '.', 'a', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', 'N', '.', '.', '.'],
            ['.', '.', '.', '.', 'R', '.', '.', '.', '.'],
            ['.', '.', '.', 'K', '.', '.', '.', '.', '.'],
        ],
        "turn": "red",
        "solution_moves": [],
        "tags": ["車馬", "協攻", "殘局"],
        "mate_in": None,
        "source": "殘局練習"
    },
]


# ── I/O helpers ───────────────────────────────────────────────────────────────

def _load_user_puzzles() -> list:
    if os.path.exists(PUZZLE_FILE):
        try:
            with open(PUZZLE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_user_puzzles(puzzles: list) -> None:
    os.makedirs(os.path.dirname(PUZZLE_FILE), exist_ok=True)
    with open(PUZZLE_FILE, 'w', encoding='utf-8') as f:
        json.dump(puzzles, f, ensure_ascii=False, indent=2)


# ── Public API ────────────────────────────────────────────────────────────────

def get_library() -> list:
    """Return all puzzles: built-ins first, then user-saved."""
    user = _load_user_puzzles()
    builtin_ids = {p['id'] for p in _BUILTIN}
    combined = list(_BUILTIN)
    for p in user:
        if p.get('id') not in builtin_ids:
            combined.append(p)
    return combined


def _piece_histogram(board: list) -> dict:
    hist: dict = {}
    for row in board:
        for ch in row:
            if ch != '.':
                hist[ch] = hist.get(ch, 0) + 1
    return hist


def find_similar(board: list, max_results: int = 5) -> list:
    """Return puzzles whose piece composition is most similar to the given board."""
    target = _piece_histogram(board)
    scored = []
    for p in get_library():
        pb = p.get('board')
        if not pb:
            continue
        ps = _piece_histogram(pb)
        # Sørensen-Dice coefficient on piece histograms
        common = sum(min(target.get(k, 0), ps.get(k, 0)) for k in target)
        total = sum(target.values()) + sum(ps.values())
        sim = 2 * common / total if total else 0.0
        scored.append((sim, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:max_results]]


def solve_puzzle(board: list, turn: str, depth: int = 4) -> dict:
    """
    Ask the engine to find the best move for a given position.
    Returns a dict with: success, move, score, mate_in, pv, initiative.
    """
    try:
        engine = ChineseChessEngine()
        engine.board = [row[:] for row in board]
        engine.turn = turn

        result = engine.get_best_move(depth=min(depth, 5))
        if not result:
            return {'success': False, 'message': '找不到合法著法，局面可能已結束'}

        move = result.get('move')
        thought = result.get('thought') or {}

        return {
            'success': True,
            'move': move,
            'score': thought.get('score', 0),
            'score_change': thought.get('score_change', 0),
            'mate_in': thought.get('mate_in'),
            'opponent_threat_in': thought.get('opponent_threat_in'),
            'initiative_advantage': thought.get('initiative_advantage'),
            'pv': thought.get('detailed_pv', []),
            'forbidden_warning': thought.get('forbidden_warning'),
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}


def save_puzzle(
    board: list,
    turn: str,
    name: str,
    description: str = '',
    tags: list = None,
    solution_moves: list = None,
    difficulty: str = 'medium',
    source: str = '用戶自製',
) -> dict:
    """Persist a new puzzle to the user library; return the saved puzzle dict."""
    puzzles = _load_user_puzzles()
    pid = 'user_' + datetime.now().strftime('%Y%m%d%H%M%S%f')
    puzzle = {
        'id': pid,
        'name': name,
        'description': description,
        'difficulty': difficulty,
        'board': board,
        'turn': turn,
        'solution_moves': solution_moves or [],
        'tags': tags or [],
        'source': source,
        'created_at': datetime.now().isoformat(),
    }
    puzzles.append(puzzle)
    _save_user_puzzles(puzzles)
    return puzzle


def board_fingerprint(board: list) -> str:
    """MD5 hash of the board state for quick identity checks."""
    flat = ''.join(''.join(row) for row in board)
    return hashlib.md5(flat.encode()).hexdigest()
