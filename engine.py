import copy
from ai_memory import (
    PIECE_VALUES, ENDING_STEPS, POS_TABLE_RED_PAWN, POS_TABLE_RED_HORSE,
    POS_TABLE_RED_ROOK, POS_TABLE_RED_CANNON, POS_TABLE_RED_KING,
    OPENING_BEGINNER, OPENING_LIU_DAHUA, OPENING_HU_RONGHUA
)

MATE_SCORE = 30000


class ChineseChessEngine:
    """Core rules engine: move generation, legal-move filtering, check detection."""

    def __init__(self):
        self.reset_board()

    def reset_board(self):
        self.board = [
            ['r', 'n', 'b', 'a', 'k', 'a', 'b', 'n', 'r'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', 'c', '.', '.', '.', '.', '.', 'c', '.'],
            ['p', '.', 'p', '.', 'p', '.', 'p', '.', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', '.', 'P', '.', 'P', '.', 'P', '.', 'P'],
            ['.', 'C', '.', '.', '.', '.', '.', 'C', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
            ['R', 'N', 'B', 'A', 'K', 'A', 'B', 'N', 'R']
        ]
        self.turn = 'red'
        self.history = []
        self.move_count = 0
        self.position_history = []

    # ── Board helpers ─────────────────────────────────────────────────────────

    def is_valid_pos(self, r, c):
        return 0 <= r < 10 and 0 <= c < 9

    def is_red_piece(self, piece):
        return piece.isupper()

    def is_own_piece(self, piece, turn):
        return piece.isupper() if turn == 'red' else piece.islower()

    def get_next_turn(self, turn):
        return 'black' if turn == 'red' else 'red'

    def board_key(self, board):
        return tuple(tuple(row) for row in board)

    # ── Move application ──────────────────────────────────────────────────────

    def make_move_internal(self, board, move):
        new_board = [row[:] for row in board]
        (r1, c1), (r2, c2) = move
        new_board[r2][c2] = new_board[r1][c1]
        new_board[r1][c1] = '.'
        return new_board

    def apply_move(self, move_dict):
        r1, c1 = move_dict['r1'], move_dict['c1']
        r2, c2 = move_dict['r2'], move_dict['c2']

        target_piece = self.board[r2][c2]
        game_over = target_piece.lower() == 'k'
        winner = self.turn if game_over else None

        self.board[r2][c2] = self.board[r1][c1]
        self.board[r1][c1] = '.'

        self.move_count += 1
        self.position_history.append(self.board_key(self.board))

        opponent = self.get_next_turn(self.turn)
        in_check = self.is_in_check(self.board, opponent)
        self.turn = opponent

        return {'game_over': game_over, 'winner': winner, 'in_check': in_check}

    def format_move(self, move):
        if not move:
            return None
        (r1, c1), (r2, c2) = move
        return {'r1': r1, 'c1': c1, 'r2': r2, 'c2': c2}

    def get_piece_name(self, char):
        names = {
            'r': '黑車', 'n': '黑馬', 'b': '黑象', 'a': '黑士', 'k': '黑將',
            'c': '黑砲', 'p': '黑卒',
            'R': '紅俥', 'N': '紅傌', 'B': '紅相', 'A': '紅仕', 'K': '紅帥',
            'C': '紅炮', 'P': '紅兵'
        }
        return names.get(char, '未知')

    # ── Check / king detection ─────────────────────────────────────────────────

    def find_king(self, board, color):
        king_char = 'K' if color == 'red' else 'k'
        for r in range(10):
            for c in range(9):
                if board[r][c] == king_char:
                    return (r, c)
        return None

    def is_in_check(self, board, color):
        king_pos = self.find_king(board, color)
        if not king_pos:
            return True

        # Flying-general rule
        opp_king = self.find_king(board, self.get_next_turn(color))
        if opp_king and king_pos[1] == opp_king[1]:
            min_r, max_r = sorted([king_pos[0], opp_king[0]])
            if not any(board[r][king_pos[1]] != '.' for r in range(min_r + 1, max_r)):
                return True

        opponent = self.get_next_turn(color)
        for move in self.generate_pseudo_legal_moves(board, opponent):
            if move[1] == king_pos:
                return True
        return False

    def is_in_checkmate(self, board, color):
        return not self.generate_legal_moves(board, color)

    # ── Move generation ───────────────────────────────────────────────────────

    def generate_legal_moves(self, board, turn):
        return [
            m for m in self.generate_pseudo_legal_moves(board, turn)
            if not self.is_in_check(self.make_move_internal(board, m), turn)
        ]

    def generate_all_moves(self, board, turn):
        return self.generate_legal_moves(board, turn)

    def generate_pseudo_legal_moves(self, board, turn):
        moves = []
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece != '.' and self.is_own_piece(piece, turn):
                    moves.extend(self.generate_moves_for_piece(board, r, c, piece))
        return moves

    def generate_moves_for_piece(self, board, r, c, piece):
        t = piece.lower()
        dispatch = {
            'k': self.get_king_moves, 'a': self.get_advisor_moves,
            'b': self.get_elephant_moves, 'n': self.get_horse_moves,
            'r': self.get_rook_moves, 'c': self.get_cannon_moves,
            'p': self.get_pawn_moves,
        }
        return dispatch[t](board, r, c, piece) if t in dispatch else []

    def get_king_moves(self, board, r, c, piece):
        moves = []
        is_red = piece.isupper()
        r_min, r_max = (7, 9) if is_red else (0, 2)
        color = 'red' if is_red else 'black'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            if self.is_valid_pos(nr,nc) and r_min<=nr<=r_max and 3<=nc<=5:
                t = board[nr][nc]
                if t == '.' or not self.is_own_piece(t, color):
                    moves.append(((r,c),(nr,nc)))
        return moves

    def get_advisor_moves(self, board, r, c, piece):
        moves = []
        is_red = piece.isupper()
        r_min, r_max = (7, 9) if is_red else (0, 2)
        color = 'red' if is_red else 'black'
        for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            nr, nc = r+dr, c+dc
            if self.is_valid_pos(nr,nc) and r_min<=nr<=r_max and 3<=nc<=5:
                t = board[nr][nc]
                if t == '.' or not self.is_own_piece(t, color):
                    moves.append(((r,c),(nr,nc)))
        return moves

    def get_elephant_moves(self, board, r, c, piece):
        moves = []
        is_red = piece.isupper()
        color = 'red' if is_red else 'black'
        for (dr,dc),(er,ec) in [((2,2),(1,1)),((2,-2),(1,-1)),((-2,2),(-1,1)),((-2,-2),(-1,-1))]:
            nr, nc = r+dr, c+dc
            if is_red and nr < 5: continue
            if not is_red and nr > 4: continue
            if self.is_valid_pos(nr,nc) and board[r+er][c+ec] == '.':
                t = board[nr][nc]
                if t == '.' or not self.is_own_piece(t, color):
                    moves.append(((r,c),(nr,nc)))
        return moves

    def get_horse_moves(self, board, r, c, piece):
        moves = []
        is_red = piece.isupper()
        color = 'red' if is_red else 'black'
        jumps = [(-2,-1,-1,0),(-2,1,-1,0),(2,-1,1,0),(2,1,1,0),
                 (-1,-2,0,-1),(1,-2,0,-1),(-1,2,0,1),(1,2,0,1)]
        for dr,dc,lr,lc in jumps:
            nr, nc = r+dr, c+dc
            leg_r, leg_c = r+lr, c+lc
            if self.is_valid_pos(nr,nc) and self.is_valid_pos(leg_r,leg_c):
                if board[leg_r][leg_c] == '.':
                    t = board[nr][nc]
                    if t == '.' or not self.is_own_piece(t, color):
                        moves.append(((r,c),(nr,nc)))
        return moves

    def get_rook_moves(self, board, r, c, piece):
        moves = []
        is_red = piece.isupper()
        color = 'red' if is_red else 'black'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            while self.is_valid_pos(nr, nc):
                t = board[nr][nc]
                if t == '.':
                    moves.append(((r,c),(nr,nc)))
                else:
                    if not self.is_own_piece(t, color):
                        moves.append(((r,c),(nr,nc)))
                    break
                nr += dr; nc += dc
        return moves

    def get_cannon_moves(self, board, r, c, piece):
        moves = []
        is_red = piece.isupper()
        color = 'red' if is_red else 'black'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            screen = False
            while self.is_valid_pos(nr, nc):
                t = board[nr][nc]
                if not screen:
                    if t == '.':
                        moves.append(((r,c),(nr,nc)))
                    else:
                        screen = True
                else:
                    if t != '.':
                        if not self.is_own_piece(t, color):
                            moves.append(((r,c),(nr,nc)))
                        break
                nr += dr; nc += dc
        return moves

    def get_pawn_moves(self, board, r, c, piece):
        moves = []
        is_red = piece.isupper()
        color = 'red' if is_red else 'black'
        dr = -1 if is_red else 1
        # Forward
        nr, nc = r+dr, c
        if self.is_valid_pos(nr, nc):
            t = board[nr][nc]
            if t == '.' or not self.is_own_piece(t, color):
                moves.append(((r,c),(nr,nc)))
        # Sideways after crossing river
        crossed = (r <= 4) if is_red else (r >= 5)
        if crossed:
            for dc in [-1, 1]:
                nr2, nc2 = r, c+dc
                if self.is_valid_pos(nr2, nc2):
                    t = board[nr2][nc2]
                    if t == '.' or not self.is_own_piece(t, color):
                        moves.append(((r,c),(nr2,nc2)))
        return moves

    # ── 擒王分數: Mate-in-N scoring ───────────────────────────────────────────
    #
    # The "Caught-the-King" score ranks moves by how quickly they force checkmate
    # considering the opponent's best defensive replies.
    # Score returned: MATE_SCORE - depth_to_mate (higher = faster mate)
    # Non-mate positions use material+positional evaluation.

    def mate_score(self, depth_remaining):
        """Score for forced mate: closer mate = higher score."""
        return MATE_SCORE - (10 - depth_remaining)

    def calculate_mate_in(self, score):
        if score > MATE_SCORE - 100:
            return MATE_SCORE - score
        if score < -(MATE_SCORE - 100):
            return -(score + MATE_SCORE)
        return None

    # ── 子根理論: Root theory piece valuation ──────────────────────────────────
    #
    # Given a target piece A at (ar, ac):
    #   - "有根" (rooted): A is defended; capturing A with P leads to P being
    #     captured and no further material loss for the capturer.
    #   - "虛根" (false root): A appears defended but the defender loses more
    #     material if it recaptures.
    #   - "無根" (rootless): A is undefended; P can capture A safely.
    #
    # Score multipliers:  有根 < 虛根 < 無根
    # This informs the SEE (Static Exchange Evaluation) used in quiescence search.

    def get_attackers(self, board, r, c, color):
        """Return list of (piece, from_pos) that can attack square (r,c) for color."""
        attackers = []
        dummy_board = [row[:] for row in board]
        dummy_board[r][c] = '.' if board[r][c] == '.' else board[r][c]

        for pr in range(10):
            for pc in range(9):
                piece = board[pr][pc]
                if piece == '.' or not self.is_own_piece(piece, color):
                    continue
                pseudo = self.generate_moves_for_piece(board, pr, pc, piece)
                if any(m[1] == (r, c) for m in pseudo):
                    attackers.append((piece, (pr, pc)))
        return attackers

    def static_exchange_evaluation(self, board, move, turn):
        """
        子根理論 SEE: estimates material gain/loss from a capture sequence.
        Returns net material gain for `turn` from executing `move`.
        Positive = profitable capture (無根/虛根 target).
        Negative = losing capture (有根 target).
        """
        (r1, c1), (r2, c2) = move
        target = board[r2][c2]
        if target == '.':
            return 0

        gain = [0] * 32
        gain[0] = PIECE_VALUES.get(target, 0)

        temp_board = [row[:] for row in board]
        temp_board[r2][c2] = temp_board[r1][c1]
        temp_board[r1][c1] = '.'

        attacker_piece = board[r1][c1]
        current_turn = self.get_next_turn(turn)
        d = 1

        while True:
            attackers = self.get_attackers(temp_board, r2, c2, current_turn)
            if not attackers:
                break

            # Pick least valuable attacker
            attackers.sort(key=lambda x: PIECE_VALUES.get(x[0], 0))
            atk_piece, atk_pos = attackers[0]
            gain[d] = PIECE_VALUES.get(attacker_piece, 0) - gain[d-1]

            temp_board[r2][c2] = atk_piece
            temp_board[atk_pos[0]][atk_pos[1]] = '.'
            attacker_piece = atk_piece
            current_turn = self.get_next_turn(current_turn)
            d += 1

        # Propagate negamax through exchange sequence
        while d > 1:
            d -= 1
            gain[d-1] = max(-gain[d], gain[d-1])

        return gain[0]

    def root_type(self, board, r, c, turn):
        """
        Classify piece at (r,c) by 子根理論.
        Returns: 'rootless'(無根), 'false_root'(虛根), 'rooted'(有根)
        """
        piece = board[r][c]
        if piece == '.':
            return None

        # Build a dummy move: our weakest attacker captures this piece
        opponent = self.get_next_turn(turn)
        our_attackers = self.get_attackers(board, r, c, turn)
        if not our_attackers:
            return None  # We can't even capture it

        our_attackers.sort(key=lambda x: PIECE_VALUES.get(x[0], 0))
        _, atk_pos = our_attackers[0]
        move = (atk_pos, (r, c))

        see = self.static_exchange_evaluation(board, move, turn)

        if see > 0:
            return 'rootless'   # 無根: profitable to capture
        elif see == 0:
            return 'false_root' # 虛根: even exchange
        else:
            return 'rooted'     # 有根: losing to capture

    def root_bonus(self, root_type):
        """Score bonus for capturing based on root classification."""
        return {'rootless': 15, 'false_root': 5, 'rooted': -5}.get(root_type, 0)

    # ── Board evaluation ───────────────────────────────────────────────────────

    def get_pos_bonus(self, piece, r, c):
        """Positional table lookup for piece at (r,c)."""
        p = piece.lower()
        is_red = piece.isupper()

        # Mirror rows for black pieces (black home = rows 0-4)
        row = r if is_red else (9 - r)

        if p == 'p':
            return POS_TABLE_RED_PAWN[row][c]
        elif p == 'n':
            return POS_TABLE_RED_HORSE[row][c]
        elif p == 'r':
            return POS_TABLE_RED_ROOK[row][c]
        elif p == 'c':
            return POS_TABLE_RED_CANNON[row][c]
        elif p == 'k':
            return POS_TABLE_RED_KING[row][c]
        return 0

    def count_pieces(self, board, turn):
        return sum(
            1 for r in range(10) for c in range(9)
            if board[r][c] != '.' and self.is_own_piece(board[r][c], turn)
        )

    def evaluate_board(self, board, turn, force_draw_mode=False):
        red_king = black_king = False
        score = 0

        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece == '.':
                    continue
                p = piece.lower()
                if p == 'k':
                    if piece.isupper():
                        red_king = True
                    else:
                        black_king = True
                    continue

                val = PIECE_VALUES.get(piece, 0) + self.get_pos_bonus(piece, r, c)

                # 子根理論: adjust value by defender presence
                opponent = 'black' if piece.isupper() else 'red'
                rt = self.root_type(board, r, c, opponent)
                # Opponent capturing this piece: rootless means we're in danger
                if rt == 'rootless':
                    val -= 8   # This piece can be captured freely → reduce its contribution
                elif rt == 'false_root':
                    val -= 3

                if self.is_own_piece(piece, turn):
                    score += val
                else:
                    score -= val

        if turn == 'red':
            if not red_king:   return -MATE_SCORE
            if not black_king: return  MATE_SCORE
        else:
            if not black_king: return -MATE_SCORE
            if not red_king:   return  MATE_SCORE

        if force_draw_mode:
            score += self.count_pieces(board, turn) * 5

        return score

    # ── Alpha-beta search ─────────────────────────────────────────────────────

    def order_moves(self, board, moves, turn):
        """Move ordering: captures first, then checks, then quiet moves."""
        def priority(move):
            (r1,c1),(r2,c2) = move
            target = board[r2][c2]
            if target != '.':
                # MVV-LVA: most valuable victim, least valuable attacker
                see = self.static_exchange_evaluation(board, move, turn)
                return (0, -see)  # captures first, good captures before bad
            return (1, 0)  # quiet moves last
        return sorted(moves, key=priority)

    def quiescence(self, board, alpha, beta, turn, force_draw_mode, qdepth=4):
        stand_pat = self.evaluate_board(board, turn, force_draw_mode)
        if abs(stand_pat) > MATE_SCORE - 100:
            return stand_pat
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        if qdepth <= 0:
            return alpha

        moves = self.generate_legal_moves(board, turn)
        captures = [m for m in moves if board[m[1][0]][m[1][1]] != '.']
        captures = self.order_moves(board, captures, turn)

        for move in captures:
            # Delta pruning: skip if even best capture can't improve alpha
            target_val = PIECE_VALUES.get(board[move[1][0]][move[1][1]], 0)
            if stand_pat + target_val + 50 < alpha:
                continue

            new_board = self.make_move_internal(board, move)
            score = -self.quiescence(new_board, -beta, -alpha,
                                     self.get_next_turn(turn), force_draw_mode, qdepth-1)
            if score >= beta:
                return beta
            alpha = max(alpha, score)

        return alpha

    def alpha_beta(self, board, depth, alpha, beta, turn, force_draw_mode, pv_line=None):
        if depth == 0:
            return self.quiescence(board, alpha, beta, turn, force_draw_mode), []

        moves = self.generate_legal_moves(board, turn)
        if not moves:
            # No legal moves: checkmate or stalemate
            if self.is_in_check(board, turn):
                return -(MATE_SCORE - (10 - depth)), []  # Checkmate: closer = worse
            return 0, []  # Stalemate/困斃 = draw

        moves = self.order_moves(board, moves, turn)

        best_score = -float('inf')
        best_pv = []

        for move in moves:
            new_board = self.make_move_internal(board, move)
            score, pv = self.alpha_beta(new_board, depth-1, -beta, -alpha,
                                        self.get_next_turn(turn), force_draw_mode)
            score = -score

            # Distance-to-mate adjustment (prefer faster mates)
            if score > MATE_SCORE - 100:
                score -= 1
            elif score < -(MATE_SCORE - 100):
                score += 1

            if score > best_score:
                best_score = score
                best_pv = [move] + pv
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score, best_pv

    def get_best_move(self, depth=3):
        moves = self.generate_legal_moves(self.board, self.turn)
        if not moves:
            return None

        current_eval = self.evaluate_board(self.board, self.turn)
        force_draw_mode = current_eval < -200

        best_move = None
        best_score = -float('inf')
        best_pv = []
        alpha, beta = -float('inf'), float('inf')

        moves = self.order_moves(self.board, moves, self.turn)

        for move in moves:
            new_board = self.make_move_internal(self.board, move)
            score, pv = self.alpha_beta(new_board, depth-1, -beta, -alpha,
                                        self.get_next_turn(self.turn), force_draw_mode)
            score = -score

            if score > best_score:
                best_score = score
                best_move = move
                best_pv = [move] + pv
            alpha = max(alpha, score)

        # Build detailed PV for logging
        detailed_pv = []
        temp = [row[:] for row in self.board]
        for m in best_pv:
            (r1,c1),(r2,c2) = m
            detailed_pv.append({
                'piece': self.get_piece_name(temp[r1][c1]),
                'from': (r1,c1), 'to': (r2,c2),
                'move_str': f"{self.get_piece_name(temp[r1][c1])} ({r1},{c1})->({r2},{c2})"
            })
            temp[r2][c2] = temp[r1][c1]; temp[r1][c1] = '.'

        thought = {
            'turn': self.turn,
            'best_move': self.format_move(best_move),
            'score': best_score,
            'score_change': best_score - current_eval,
            'pv': [self.format_move(m) for m in best_pv],
            'detailed_pv': detailed_pv,
            'mate_in': self.calculate_mate_in(best_score),
        }
        self.history.append(thought)
        self.save_log()

        return {'move': self.format_move(best_move), 'thought': thought}

    def save_log(self):
        with open('game_logic.txt', 'w', encoding='utf-8') as f:
            for entry in self.history:
                f.write(f"Turn: {entry['turn']}\n")
                f.write(f"Best Move: {entry['best_move']}\n")
                f.write(f"Score: {entry['score']}\n")
                if entry['mate_in']:
                    f.write(f"Mate in: {entry['mate_in']} steps\n")
                f.write(f"PV: {entry['pv']}\n")
                f.write("-" * 30 + "\n")


# ── AI Opponents ──────────────────────────────────────────────────────────────
#
# Three opponents with different personalities:
#   BeginnerAI   - shallow search, no opening book, weak evaluation
#   LiuDahuaAI  - medium depth, tactical/quick-play style (Liu Dahua 快棋)
#   HuRonghuaAI - deepest search, positional endgame, patient (Hu Ronghua)

class BeginnerAI(ChineseChessEngine):
    """
    初學者 AI: depth 1, no positional tables, random from top-3 moves.
    Simulates a beginner who sees only one move ahead.
    """
    SEARCH_DEPTH = 1
    NAME = "初學者"

    def __init__(self):
        super().__init__()

    def evaluate_board(self, board, turn, force_draw_mode=False):
        # Simplified: only material count, no positional tables, no root theory
        red_king = black_king = False
        score = 0
        weights = {'a':20,'b':20,'n':35,'r':90,'c':45,'p':8}
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece == '.': continue
                p = piece.lower()
                if p == 'k':
                    if piece.isupper(): red_king = True
                    else: black_king = True
                    continue
                val = weights.get(p, 0)
                if self.is_own_piece(piece, turn): score += val
                else: score -= val

        if turn == 'red':
            if not red_king:   return -MATE_SCORE
            if not black_king: return  MATE_SCORE
        else:
            if not black_king: return -MATE_SCORE
            if not red_king:   return  MATE_SCORE
        return score

    def get_best_move(self, depth=None):
        import random
        depth = self.SEARCH_DEPTH
        moves = self.generate_legal_moves(self.board, self.turn)
        if not moves:
            return None

        scored = []
        for move in moves:
            new_board = self.make_move_internal(self.board, move)
            score, _ = self.alpha_beta(new_board, depth-1, -float('inf'), float('inf'),
                                       self.get_next_turn(self.turn), False)
            scored.append((move, -score))

        scored.sort(key=lambda x: x[1], reverse=True)
        # Randomly pick from top 3 to simulate imperfect play
        top = scored[:3]
        best_move, best_score = random.choice(top)

        thought = {
            'turn': self.turn,
            'best_move': self.format_move(best_move),
            'score': best_score,
            'score_change': 0,
            'pv': [self.format_move(best_move)],
            'detailed_pv': [],
            'mate_in': self.calculate_mate_in(best_score),
        }
        self.history.append(thought)
        self.save_log()
        return {'move': self.format_move(best_move), 'thought': thought}


class LiuDahuaAI(ChineseChessEngine):
    """
    柳大華快棋風格 AI: depth 3, tactical, prefers active pieces and quick attack.
    Opening book based on central cannon + aggressive development.
    Reference: Liu Dahua's rapid-game style - direct, tactical, forcing variations.
    """
    SEARCH_DEPTH = 3
    NAME = "柳大華"

    def __init__(self):
        super().__init__()
        self.opening_book = OPENING_LIU_DAHUA
        self.opening_moves_used = 0

    def evaluate_board(self, board, turn, force_draw_mode=False):
        score = super().evaluate_board(board, turn, force_draw_mode)

        # Tactical bonus: reward attacks on opponent pieces
        opponent = self.get_next_turn(turn)
        my_moves = self.generate_pseudo_legal_moves(board, turn)
        attacks = sum(1 for m in my_moves if board[m[1][0]][m[1][1]] != '.')
        score += attacks * 2  # Liu Dahua rewards active attacking moves

        # Mobility: more moves = better
        score += len(my_moves) // 3

        return score

    def get_best_move(self, depth=None):
        depth = self.SEARCH_DEPTH

        # Opening book: first 5 moves
        if self.opening_moves_used < 5 and self.turn == 'black':
            book_moves = self.opening_book.get("start", [])
            if book_moves and self.opening_moves_used < len(book_moves):
                move_tuple, weight = book_moves[self.opening_moves_used]
                r1,c1 = move_tuple[0]
                r2,c2 = move_tuple[1]
                piece = self.board[r1][c1]
                # Validate book move is legal
                legal = self.generate_legal_moves(self.board, self.turn)
                if move_tuple in legal:
                    self.opening_moves_used += 1
                    fmt = {'r1':r1,'c1':c1,'r2':r2,'c2':c2}
                    thought = {
                        'turn': self.turn, 'best_move': fmt, 'score': 0,
                        'score_change': 0, 'pv': [fmt], 'detailed_pv': [],
                        'mate_in': None, 'source': 'opening_book'
                    }
                    self.history.append(thought)
                    return {'move': fmt, 'thought': thought}

        return super().get_best_move(depth)


class HuRonghuaAI(ChineseChessEngine):
    """
    胡榮華棋譜風格 AI: depth 4, deep positional play, patient endgame technique.
    Reference: Hu Ronghua's style - precise calculation, strong endgame, strategic.
    Prefers positional sacrifices and long-term planning over short-term tactics.
    """
    SEARCH_DEPTH = 4
    NAME = "胡榮華"

    def __init__(self):
        super().__init__()
        self.opening_book = OPENING_HU_RONGHUA
        self.opening_moves_used = 0

    def evaluate_board(self, board, turn, force_draw_mode=False):
        score = super().evaluate_board(board, turn, force_draw_mode)

        # Positional refinement: king safety bonus (keep own king defended)
        king_pos = self.find_king(board, turn)
        if king_pos:
            kr, kc = king_pos
            defenders = self.get_attackers(board, kr, kc, turn)
            score += len(defenders) * 3  # Reward king defenders

        # Endgame: reward passed pawns deep in enemy territory
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece == 'P' and r <= 2:  # Red pawn in enemy palace area
                    score += 20
                elif piece == 'p' and r >= 7:  # Black pawn in enemy palace area
                    if not self.is_own_piece(piece, turn):
                        score -= 20

        # Connectivity: reward pieces that protect each other
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece != '.' and self.is_own_piece(piece, turn):
                    defenders = self.get_attackers(board, r, c, turn)
                    if len(defenders) > 1:
                        score += 2  # Hu Ronghua values solid piece coordination

        return score

    def get_best_move(self, depth=None):
        depth = self.SEARCH_DEPTH

        # Opening book: first 8 moves
        if self.opening_moves_used < 8 and self.turn == 'black':
            book_moves = self.opening_book.get("start", [])
            if book_moves and self.opening_moves_used < len(book_moves):
                move_tuple, weight = book_moves[self.opening_moves_used]
                legal = self.generate_legal_moves(self.board, self.turn)
                if move_tuple in legal:
                    self.opening_moves_used += 1
                    r1,c1 = move_tuple[0]
                    r2,c2 = move_tuple[1]
                    fmt = {'r1':r1,'c1':c1,'r2':r2,'c2':c2}
                    thought = {
                        'turn': self.turn, 'best_move': fmt, 'score': 0,
                        'score_change': 0, 'pv': [fmt], 'detailed_pv': [],
                        'mate_in': None, 'source': 'opening_book'
                    }
                    self.history.append(thought)
                    return {'move': fmt, 'thought': thought}

        return super().get_best_move(depth)


# ── Factory ────────────────────────────────────────────────────────────────────

def create_ai(difficulty='medium'):
    """
    Factory: returns an AI engine by difficulty.
    'easy'   -> BeginnerAI (初學者)
    'medium' -> LiuDahuaAI (柳大華快棋風格)
    'hard'   -> HuRonghuaAI (胡榮華棋譜風格)
    """
    return {
        'easy':   BeginnerAI,
        'medium': LiuDahuaAI,
        'hard':   HuRonghuaAI,
    }.get(difficulty, LiuDahuaAI)()
