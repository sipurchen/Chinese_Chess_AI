"""
AI Tournament Runner — three-way round-robin, each pair plays N games.
Results stored in AI_Games/tournament/<session_id>/
The main ChineseChessEngine acts as "spectator analyst" recording turning points.
"""
import os, json, copy, threading, time
from datetime import datetime
from collections import defaultdict
from engine import (
    BeginnerAI, LiuDahuaAI, HuRonghuaAI, ChineseChessEngine,
    MATE_SCORE
)

# ── Fast variants (depth-2 for tournament speed) ──────────────────────────────
class BeginnerTournament(BeginnerAI):
    NAME = "初學者"

class LiuTournament(LiuDahuaAI):
    SEARCH_DEPTH = 2
    NAME = "柳大華"

class HuTournament(HuRonghuaAI):
    SEARCH_DEPTH = 2
    NAME = "胡榮華"

# ── Global tournament state ───────────────────────────────────────────────────
_sessions: dict = {}
_sessions_lock = threading.Lock()

PIECE_NAMES = {
    'r': '黑車', 'n': '黑馬', 'b': '黑象', 'a': '黑士', 'k': '黑將', 'c': '黑砲', 'p': '黑卒',
    'R': '紅俥', 'N': '紅傌', 'B': '紅相', 'A': '紅仕', 'K': '紅帥', 'C': '紅炮', 'P': '紅兵',
}

MAX_HALF_MOVES = 200  # draw limit

_INITIAL_BOARD = [
    ['r', 'n', 'b', 'a', 'k', 'a', 'b', 'n', 'r'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', 'c', '.', '.', '.', '.', '.', 'c', '.'],
    ['p', '.', 'p', '.', 'p', '.', 'p', '.', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', '.', 'P', '.', 'P', '.', 'P', '.', 'P'],
    ['.', 'C', '.', '.', '.', '.', '.', 'C', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['R', 'N', 'B', 'A', 'K', 'A', 'B', 'N', 'R'],
]


def _run_single_game(red_class, black_class, spectator: ChineseChessEngine):
    """Play one game between red_class and black_class. Returns game dict."""
    red   = red_class()
    black = black_class()
    board = [row[:] for row in _INITIAL_BOARD]

    moves_log  = []
    result     = 'draw'
    analysis   = []   # spectator observations
    turn_order = ['red', 'black']
    engines    = {'red': red, 'black': black}
    prev_score = 0

    for half in range(MAX_HALF_MOVES):
        turn   = turn_order[half % 2]
        engine = engines[turn]
        engine.board = [row[:] for row in board]
        engine.turn  = turn

        result_data = engine.get_best_move()
        if not result_data:
            result = 'black_stalemate' if turn == 'red' else 'red_stalemate'
            break

        mv      = result_data['move']
        thought = result_data.get('thought', {})
        score   = thought.get('score', 0) if thought else 0
        mate_in = thought.get('mate_in') if thought else None
        initiative = thought.get('initiative_advantage') if thought else None

        r1, c1, r2, c2 = mv['r1'], mv['c1'], mv['r2'], mv['c2']
        captured = board[r2][c2]
        board[r2][c2] = board[r1][c1]
        board[r1][c1] = '.'

        delta  = abs(score - prev_score)
        is_key = (
            delta > 40
            or (mate_in is not None and mate_in <= 5)
            or (initiative is not None and abs(initiative) >= 3)
        )

        moves_log.append({
            'half':     half + 1,
            'turn':     turn,
            'piece':    PIECE_NAMES.get(board[r2][c2], '?'),
            'from':     [r1, c1],
            'to':       [r2, c2],
            'captured': PIECE_NAMES.get(captured) if captured != '.' else None,
            'score':    score,
            'mate_in':  mate_in,
            'initiative': initiative,
            'is_key':   is_key,
        })

        # Spectator analysis at key moments
        if is_key:
            spectator.board = [row[:] for row in board]
            spectator.turn  = 'red' if turn == 'black' else 'black'
            sp_result = spectator.get_best_move(depth=2)
            sp_score  = (
                sp_result['thought']['score']
                if sp_result and sp_result.get('thought')
                else 0
            )
            analysis.append({
                'half':            half + 1,
                'board':           [row[:] for row in board],
                'spectator_score': sp_score,
                'spectator_best':  sp_result['move'] if sp_result else None,
                'delta':           delta,
                'mate_in':         mate_in,
            })

        prev_score = score
        if captured.lower() == 'k':
            result = f'{turn}_wins'
            break

    return {
        'result':     result,
        'moves':      moves_log,
        'analysis':   analysis,
        'red_name':   getattr(red,   'NAME', '紅'),
        'black_name': getattr(black, 'NAME', '黑'),
    }


def start_tournament(session_id: str, games_per_pair: int = 10, out_base: str = None):
    """
    Start a tournament session in background.
    games_per_pair: games between each pair (default 10; 3 pairs x 10 = 30 total)
    """
    if out_base is None:
        out_base = os.path.join(
            os.path.dirname(__file__), 'AI_Games', 'tournament', session_id
        )
    os.makedirs(out_base, exist_ok=True)

    PAIRS = [
        (BeginnerTournament, LiuTournament,  '初學者 vs 柳大華'),
        (BeginnerTournament, HuTournament,   '初學者 vs 胡榮華'),
        (LiuTournament,      HuTournament,   '柳大華 vs 胡榮華'),
    ]
    total = len(PAIRS) * games_per_pair

    with _sessions_lock:
        _sessions[session_id] = {
            'status':     'running',
            'total':      total,
            'done':       0,
            'results':    defaultdict(lambda: {'wins_red': 0, 'wins_black': 0, 'draws': 0}),
            'games':      [],
            'errors':     [],
            'out_dir':    out_base,
            'started_at': datetime.now().isoformat(),
        }

    def _worker():
        spectator = ChineseChessEngine()
        state     = _sessions[session_id]
        game_idx  = 0

        for red_class, black_class, label in PAIRS:
            for g in range(games_per_pair):
                try:
                    game = _run_single_game(red_class, black_class, spectator)
                    ts   = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]
                    fname  = f'{label.replace(" ", "_")}_{g + 1:03d}_{ts}.json'
                    fpath  = os.path.join(out_base, fname)
                    with open(fpath, 'w', encoding='utf-8') as f:
                        json.dump(game, f, ensure_ascii=False, indent=2)

                    # Tally results
                    r = game['result']
                    if r == 'red_wins':
                        state['results'][label]['wins_red'] += 1
                    elif r == 'black_wins':
                        state['results'][label]['wins_black'] += 1
                    else:
                        state['results'][label]['draws'] += 1

                    state['games'].append({
                        'label':  label,
                        'game':   g + 1,
                        'result': r,
                        'file':   fname,
                    })
                    state['done'] += 1
                    game_idx += 1
                except Exception as e:
                    state['errors'].append({'game': game_idx, 'error': str(e)})
                    state['done'] += 1

        state['status']      = 'done'
        state['finished_at'] = datetime.now().isoformat()

        # Save summary
        summary_path = os.path.join(out_base, 'summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id':  session_id,
                'total':       total,
                'results':     dict(state['results']),
                'games':       state['games'],
                'started_at':  state['started_at'],
                'finished_at': state['finished_at'],
            }, f, ensure_ascii=False, indent=2)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return session_id


def get_status(session_id: str) -> dict:
    with _sessions_lock:
        state = _sessions.get(session_id)
    if not state:
        return {'error': 'session not found'}
    return {
        'status':       state['status'],
        'total':        state['total'],
        'done':         state['done'],
        'pct':          round(state['done'] / max(state['total'], 1) * 100, 1),
        'results':      dict(state['results']),
        'recent_games': state['games'][-5:],
        'errors':       state['errors'][-3:],
    }


def list_tournament_games(out_base: str = None) -> list:
    """List all tournament game files."""
    if out_base is None:
        out_base = os.path.join(
            os.path.dirname(__file__), 'AI_Games', 'tournament'
        )
    games = []
    if not os.path.exists(out_base):
        return games
    for d in sorted(os.listdir(out_base)):
        session_dir = os.path.join(out_base, d)
        if os.path.isdir(session_dir):
            summary = os.path.join(session_dir, 'summary.json')
            if os.path.exists(summary):
                with open(summary, encoding='utf-8') as f:
                    games.append({'session': d, 'summary': json.load(f)})
    return games


def load_tournament_game(session_id: str, filename: str, out_base: str = None) -> dict:
    if out_base is None:
        out_base = os.path.join(
            os.path.dirname(__file__), 'AI_Games', 'tournament'
        )
    path = os.path.join(out_base, session_id, filename)
    with open(path, encoding='utf-8') as f:
        return json.load(f)
