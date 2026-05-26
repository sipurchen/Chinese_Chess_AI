"""
Flask application — 4-mode Chinese Chess AI
Modes: 人機對弈 / AI對弈 / 分析棋局 / 試解殘局
"""
import os
import json
import uuid
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from engine import create_ai, ChineseChessEngine
import ai_tournament
import ai_endgame

app = Flask(__name__)

# ── Human vs AI engine (shared mutable state) ─────────────────────────────────
engine = create_ai('medium')

# ═══════════════════════════════════════════════════════════════════════════════
#  CORE / HUMAN VS AI
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    global engine
    data = request.json or {}
    difficulty = data.get('difficulty', 'medium')
    if difficulty not in ('easy', 'medium', 'hard'):
        return jsonify({'error': 'Invalid difficulty'}), 400
    engine = create_ai(difficulty)
    names = {'easy': '初學者', 'medium': '柳大華', 'hard': '胡榮華'}
    return jsonify({
        'status': 'ok',
        'ai_name': names[difficulty],
        'difficulty': difficulty,
    })


@app.route('/move', methods=['POST'])
def move():
    data = request.json or {}
    move_data = data.get('move')

    player_result = {}
    if move_data:
        player_result = engine.apply_move(move_data)
        if player_result.get('game_over'):
            return jsonify({
                'status': 'game_over',
                'winner': player_result['winner'],
                'move': None,
            })

    ai_move_data = engine.get_best_move()
    ai_move = ai_move_data.get('move') if ai_move_data else None
    black_thought = ai_move_data.get('thought') if ai_move_data else None

    ai_result = {}
    red_thought = None
    if ai_move:
        ai_result = engine.apply_move(ai_move)
        if not ai_result.get('game_over'):
            red_analysis = engine.get_best_move()
            if red_analysis:
                red_thought = red_analysis.get('thought')

    forbidden = (
        player_result.get('forbidden_warning') or
        ai_result.get('forbidden_warning')
    )

    return jsonify({
        'status': 'game_over' if ai_result.get('game_over') else 'ok',
        'move': ai_move,
        'black_thought': black_thought,
        'red_thought': red_thought,
        'game_over': ai_result.get('game_over', False),
        'winner': ai_result.get('winner'),
        'in_check': (
            ai_result.get('in_check', False) or
            player_result.get('in_check', False)
        ),
        'ai_name': getattr(engine, 'NAME', 'AI'),
        'forbidden_warning': forbidden,
    })


@app.route('/reset', methods=['POST'])
def reset():
    engine.reset_board()
    if hasattr(engine, 'opening_moves_used'):
        engine.opening_moves_used = 0
    return jsonify({'status': 'reset', 'ai_name': getattr(engine, 'NAME', 'AI')})


# ═══════════════════════════════════════════════════════════════════════════════
#  TOURNAMENT  (AI 對弈)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/tournament/start', methods=['POST'])
def tournament_start():
    data = request.json or {}
    try:
        gpp = max(1, min(int(data.get('games_per_pair', 10)), 50))
    except (TypeError, ValueError):
        gpp = 10

    sid = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]
    ai_tournament.start_tournament(sid, games_per_pair=gpp)
    return jsonify({'status': 'ok', 'session_id': sid})


@app.route('/tournament/status/<sid>')
def tournament_status(sid):
    s = ai_tournament.get_status(sid)
    if s.get('error'):
        return jsonify(s), 404
    return jsonify(s)


@app.route('/tournament/sessions')
def tournament_sessions():
    return jsonify(ai_tournament.list_tournament_games())


@app.route('/tournament/replay/<sid>/<path:fname>')
def tournament_replay(sid, fname):
    # Security: no path traversal
    if '..' in sid or '..' in fname:
        return jsonify({'error': 'Invalid path'}), 400
    try:
        game = ai_tournament.load_tournament_game(sid, fname)
        return jsonify(game)
    except FileNotFoundError:
        return jsonify({'error': 'Game not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME ANALYSIS  (分析棋局)
# ═══════════════════════════════════════════════════════════════════════════════

_GAMES_BASE = os.path.join(os.path.dirname(__file__), 'AI_Games')


@app.route('/games/list')
def games_list():
    result = []
    if not os.path.exists(_GAMES_BASE):
        return jsonify(result)
    for root, _, files in os.walk(_GAMES_BASE):
        for f in sorted(files, reverse=True):
            if f.endswith('.json') and ('game_record' in f or f == 'summary.json'):
                rel = os.path.relpath(os.path.join(root, f), _GAMES_BASE)
                result.append(rel.replace('\\', '/'))
    result.sort(reverse=True)
    return jsonify(result[:100])  # cap at 100 entries


@app.route('/games/load', methods=['POST'])
def games_load():
    data = request.json or {}
    rel = data.get('file', '')
    if not rel:
        return jsonify({'error': 'No file specified'}), 400
    path = os.path.normpath(os.path.join(_GAMES_BASE, rel))
    # Security: must stay inside AI_Games
    if not path.startswith(os.path.normpath(_GAMES_BASE)):
        return jsonify({'error': 'Invalid path'}), 400
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json or {}
    board = data.get('board')
    turn = data.get('turn', 'red')
    try:
        depth = max(1, min(int(data.get('depth', 3)), 5))
    except (TypeError, ValueError):
        depth = 3

    if not board:
        return jsonify({'error': 'No board provided'}), 400

    eng = ChineseChessEngine()
    eng.board = board
    eng.turn = turn
    result = eng.get_best_move(depth=depth)
    if not result:
        return jsonify({'success': False, 'message': '局面無合法著法'})
    return jsonify({
        'success': True,
        'move': result.get('move'),
        'thought': result.get('thought'),
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  ENDGAME PUZZLES  (試解殘局)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/endgame/library')
def endgame_library():
    return jsonify(ai_endgame.get_library())


@app.route('/endgame/solve', methods=['POST'])
def endgame_solve():
    data = request.json or {}
    board = data.get('board')
    turn = data.get('turn', 'red')
    try:
        depth = max(1, min(int(data.get('depth', 4)), 5))
    except (TypeError, ValueError):
        depth = 4
    if not board:
        return jsonify({'error': 'No board provided'}), 400
    return jsonify(ai_endgame.solve_puzzle(board, turn, depth))


@app.route('/endgame/save', methods=['POST'])
def endgame_save():
    data = request.json or {}
    board = data.get('board')
    turn = data.get('turn', 'red')
    name = (data.get('name') or '').strip()
    if not board or not name:
        return jsonify({'error': '缺少棋盤或名稱'}), 400
    puzzle = ai_endgame.save_puzzle(
        board=board,
        turn=turn,
        name=name,
        description=data.get('description', ''),
        tags=data.get('tags', []),
        solution_moves=data.get('solution_moves'),
        difficulty=data.get('difficulty', 'medium'),
    )
    return jsonify({'success': True, 'puzzle': puzzle})


@app.route('/endgame/similar', methods=['POST'])
def endgame_similar():
    data = request.json or {}
    board = data.get('board')
    if not board:
        return jsonify({'error': 'No board provided'}), 400
    return jsonify(ai_endgame.find_similar(board, max_results=5))


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True, port=5000)
