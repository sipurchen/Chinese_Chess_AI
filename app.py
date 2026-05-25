from flask import Flask, render_template, request, jsonify
from engine import create_ai, ChineseChessEngine

app = Flask(__name__)

# Active engine instance - default medium difficulty
engine = create_ai('medium')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    global engine
    data = request.json
    difficulty = data.get('difficulty', 'medium')
    if difficulty not in ('easy', 'medium', 'hard'):
        return jsonify({'error': 'Invalid difficulty'}), 400
    engine = create_ai(difficulty)
    names = {'easy': '初學者', 'medium': '柳大華', 'hard': '胡榮華'}
    return jsonify({'status': 'ok', 'ai_name': names[difficulty], 'difficulty': difficulty})

@app.route('/move', methods=['POST'])
def move():
    data = request.json
    move_data = data.get('move')

    # Apply player move
    player_result = {}
    if move_data:
        player_result = engine.apply_move(move_data)
        if player_result.get('game_over'):
            return jsonify({
                'status': 'game_over',
                'winner': player_result['winner'],
                'move': None
            })

    # AI responds
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

    return jsonify({
        'status': 'game_over' if ai_result.get('game_over') else 'ok',
        'move': ai_move,
        'black_thought': black_thought,
        'red_thought': red_thought,
        'game_over': ai_result.get('game_over', False),
        'winner': ai_result.get('winner'),
        'in_check': ai_result.get('in_check', False) or player_result.get('in_check', False),
        'ai_name': getattr(engine, 'NAME', 'AI'),
    })

@app.route('/reset', methods=['POST'])
def reset():
    engine.reset_board()
    if hasattr(engine, 'opening_moves_used'):
        engine.opening_moves_used = 0
    return jsonify({'status': 'reset', 'ai_name': getattr(engine, 'NAME', 'AI')})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
