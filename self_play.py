"""
Self-play simulation: named AI personality vs standard engine.
Captures board images at 擒王分數 (Catch-the-King score) turning points.
Saves game records into AI_Games/<personality>/ directories.
"""
import os
import json
import copy
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from engine import (
    ChineseChessEngine, BeginnerAI, LiuDahuaAI, HuRonghuaAI,
    MATE_SCORE
)

# ── Constants ──────────────────────────────────────────────────────────────────
CELL = 70          # pixels per cell (enlarged for clarity)
MARGIN = 55        # board margin
COLS, ROWS = 9, 10
W = CELL * (COLS - 1) + 2 * MARGIN     # 670 px
H = CELL * (ROWS - 1) + 2 * MARGIN     # 743 px
HEADER_H = 40                           # title bar height

BG_COLOR   = (222, 184, 135)            # burlywood board
LINE_COLOR = (92,  58,  33)
RED_FG     = (139,  0,   0)             # deep crimson for red pieces
RED_BG_C   = (255, 248, 200)            # warm ivory
BLACK_FG   = (240, 230, 210)            # cream for black piece text
BLACK_BG_C = (30,  30,  30)            # near-black
HIGHLIGHT  = (50,  200,  50, 160)

PIECE_NAMES_ZH = {
    'r':'車','n':'馬','b':'象','a':'士','k':'將','c':'砲','p':'卒',
    'R':'俥','N':'傌','B':'相','A':'仕','K':'帥','C':'炮','P':'兵',
}

TURNING_THRESHOLD = 40   # score change > this → turning point
MAX_MOVES = 150          # draw if no win by this many half-moves


# ── Font helper ────────────────────────────────────────────────────────────────

def _load_font(size):
    """Load CJK-capable font cross-platform; falls back to PIL default."""
    import sys
    candidates = []
    if sys.platform == "win32":
        _win_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        candidates = [
            os.path.join(_win_fonts, "simsun.ttc"),
            os.path.join(_win_fonts, "simhei.ttf"),
            os.path.join(_win_fonts, "msyh.ttc"),
            os.path.join(_win_fonts, "msjh.ttc"),
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    else:  # Linux / other
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
        ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


FONT_PIECE  = _load_font(22)
FONT_LABEL  = _load_font(13)
FONT_HEADER = _load_font(15)


# ── Board renderer ─────────────────────────────────────────────────────────────

def cell_to_pixel(r, c):
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return x, y


def draw_board(board, highlight_move=None, title="", score=None, mate_in=None):
    R_OUTER = int(CELL * 0.42)
    R_INNER = int(CELL * 0.38)
    R_HI    = int(CELL * 0.46)

    img = Image.new("RGB", (W, H + HEADER_H), BG_COLOR)
    d = ImageDraw.Draw(img, "RGBA")

    # Title bar
    d.rectangle([0, 0, W, HEADER_H - 2], fill=(92, 58, 33))
    ty = (HEADER_H - 15) // 2
    d.text((10, ty), title, fill="white", font=FONT_HEADER)
    if score is not None:
        score_str = f"Score: {score}"
        if mate_in:
            score_str += f"  ({'Win' if mate_in > 0 else 'Lose'} in {abs(mate_in)})"
        d.text((W - 200, ty), score_str, fill=(255, 220, 100), font=FONT_HEADER)

    offset_y = HEADER_H
    board_img = Image.new("RGB", (W, H), BG_COLOR)
    bd = ImageDraw.Draw(board_img, "RGBA")

    # Horizontal grid lines
    for r in range(ROWS):
        x0, y0 = cell_to_pixel(r, 0)
        x1, _  = cell_to_pixel(r, COLS - 1)
        bd.line([(x0, y0), (x1, y0)], fill=LINE_COLOR, width=1)

    # Vertical lines (split at river)
    for c in range(COLS):
        x, _ = cell_to_pixel(0, c)
        if c == 0 or c == COLS - 1:
            bd.line([(x, MARGIN), (x, MARGIN + (ROWS-1)*CELL)], fill=LINE_COLOR, width=1)
        else:
            bd.line([(x, MARGIN), (x, MARGIN + 4*CELL)], fill=LINE_COLOR, width=1)
            bd.line([(x, MARGIN + 5*CELL), (x, MARGIN + (ROWS-1)*CELL)], fill=LINE_COLOR, width=1)

    # Palace diagonals (top: rows 0-2 cols 3-5)
    def palace(r1, c1, r2, c2):
        x1,y1 = cell_to_pixel(r1, c1)
        x2,y2 = cell_to_pixel(r2, c2)
        bd.line([(x1,y1),(x2,y2)], fill=LINE_COLOR, width=1)
    palace(0,3,2,5); palace(0,5,2,3)
    palace(7,3,9,5); palace(7,5,9,3)

    # River text
    rx, ry = cell_to_pixel(4, 0)
    bd.text((rx + 10, ry + 10), "楚  河          漢  界", fill=LINE_COLOR, font=FONT_LABEL)

    # Highlight last move
    if highlight_move:
        (r1,c1),(r2,c2) = highlight_move
        for (hr,hc) in [(r1,c1),(r2,c2)]:
            hx,hy = cell_to_pixel(hr, hc)
            bd.ellipse([hx-R_HI,hy-R_HI,hx+R_HI,hy+R_HI], fill=(80,180,80,80))

    # Draw pieces
    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]
            if piece == '.':
                continue
            px, py = cell_to_pixel(r, c)
            is_red = piece.isupper()
            fg  = RED_FG   if is_red else BLACK_FG
            bg  = RED_BG_C if is_red else BLACK_BG_C
            # Outer circle
            bd.ellipse([px-R_OUTER,py-R_OUTER,px+R_OUTER,py+R_OUTER], fill=bg, outline=fg, width=2)
            # Inner circle
            bd.ellipse([px-R_INNER,py-R_INNER,px+R_INNER,py+R_INNER], outline=fg, width=1)
            # Piece character
            ch = PIECE_NAMES_ZH.get(piece, '?')
            bbox = bd.textbbox((0,0), ch, font=FONT_PIECE)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            bd.text((px - tw//2, py - th//2 - 1), ch, fill=fg, font=FONT_PIECE)

    img.paste(board_img, (0, offset_y))
    return img


# ── Game record ────────────────────────────────────────────────────────────────

class GameRecord:
    def __init__(self, red_name, black_name):
        self.red_name  = red_name
        self.black_name = black_name
        self.moves = []         # list of dicts
        self.turning_points = []  # indices of turning moves
        self.result = None

    def add_move(self, move_num, turn, piece_name, from_pos, to_pos,
                 score, prev_score, mate_in, captured):
        delta = score - prev_score
        self.moves.append({
            "move_num": move_num,
            "turn": turn,
            "piece": piece_name,
            "from": from_pos,
            "to": to_pos,
            "score": score,
            "score_delta": delta,
            "mate_in": mate_in,
            "captured": captured,
        })

    def to_text(self):
        lines = [
            f"=== 棋譜: {self.red_name}(紅) vs {self.black_name}(黑) ===",
            f"結果: {self.result}",
            "",
            f"{'步數':<5} {'方':<4} {'棋子':<8} {'起':<12} {'落':<12} {'分數':<8} {'±':<8} {'擒王'}",
            "-" * 70,
        ]
        for m in self.moves:
            mate_str = f"{m['mate_in']}步" if m['mate_in'] else ""
            cap_str = f"吃{m['captured']}" if m['captured'] else ""
            lines.append(
                f"{m['move_num']:<5} {'紅' if m['turn']=='red' else '黑':<4} "
                f"{m['piece']:<8} {str(m['from']):<12} {str(m['to']):<12} "
                f"{m['score']:<8} {m['score_delta']:+8} {mate_str:<6} {cap_str}"
            )
            if m['move_num'] in self.turning_points:
                lines.append("    *** 重大轉折點 ***")
        return "\n".join(lines)


# ── Self-play engine ───────────────────────────────────────────────────────────

class SelfPlay:
    def __init__(self, red_engine, black_engine, out_dir, title_prefix):
        self.red   = red_engine
        self.black = black_engine
        self.out_dir = out_dir
        self.title_prefix = title_prefix
        os.makedirs(out_dir, exist_ok=True)
        self.ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Share the same board state
        self.board = [row[:] for row in red_engine.board]
        self.record = GameRecord(
            getattr(red_engine,   'NAME', '紅AI'),
            getattr(black_engine, 'NAME', '黑AI'),
        )
        self.screenshots = []

    def _sync_board(self, engine):
        engine.board = [row[:] for row in self.board]
        engine.turn  = 'red' if engine == self.red else 'black'

    def _ai_move(self, engine, turn):
        """Ask engine for best move from current board position."""
        engine.board = [row[:] for row in self.board]
        engine.turn  = turn
        result = engine.get_best_move()
        if not result:
            return None, None
        m = result['move']
        t = result['thought']
        return m, t

    def save_screenshot(self, board, move, move_num, score, mate_in, label):
        title = f"{self.title_prefix} | 步{move_num} | {label}"
        img = draw_board(board, highlight_move=move, title=title,
                         score=score, mate_in=mate_in)
        fname = os.path.join(self.out_dir, f"{self.ts}_turn_{move_num:03d}_{label}.png")
        img.save(fname)
        self.screenshots.append(fname)
        print(f"  [SCREENSHOT] {fname}")
        return fname

    def play(self):
        turn_order = ['red', 'black']
        engines    = {'red': self.red, 'black': self.black}
        prev_score = 0
        move_num   = 0
        result     = "Unfinished"

        # ── 雙方先手追蹤 ─────────────────────────────────────────
        # 分別記錄紅黑上次的 mate_in 與 initiative_advantage，
        # 偵測先手方向是否易手或差距突然拉大。
        last_mate   = {'red': None, 'black': None}
        last_init   = {'red': None, 'black': None}

        for half_move in range(MAX_MOVES * 2):
            turn = turn_order[half_move % 2]
            engine = engines[turn]

            move, thought = self._ai_move(engine, turn)
            if not move:
                result = ('Black wins stalemate' if turn == 'red' else 'Red wins stalemate')
                break

            r1, c1 = move['r1'], move['c1']
            r2, c2 = move['r2'], move['c2']
            piece_char   = self.board[r1][c1]
            target_char  = self.board[r2][c2]
            captured     = PIECE_NAMES_ZH.get(target_char) if target_char != '.' else None
            move_num    += 1
            score        = thought['score'] if thought else 0
            mate_in      = thought.get('mate_in') if thought else None
            opp_threat   = thought.get('opponent_threat_in') if thought else None
            initiative   = thought.get('initiative_advantage') if thought else None

            # Apply move to shared board
            self.board[r2][c2] = self.board[r1][c1]
            self.board[r1][c1] = '.'

            delta = abs(score - prev_score)

            # ── 雙方先手轉折判斷（三個新條件）───────────────────────
            # ① 本方剛獲得擒王先手（上一步沒有，現在有）
            mate_gain = (mate_in is not None and last_mate[turn] is None)
            # ② 雙方擒王速度差距 ≥ 3 步（initiative_advantage 絕對值大）
            init_gap  = (initiative is not None and abs(initiative) >= 3)
            # ③ 先手方向易手（上一步正，現在負，或反之）
            init_flip = (
                initiative is not None
                and last_init[turn] is not None
                and initiative * last_init[turn] < 0
            )

            is_turning = (
                delta >= TURNING_THRESHOLD
                or (mate_in is not None and mate_in <= 5)
                or (captured in ('俥','車','帥','將'))
                or mate_gain
                or init_gap
                or init_flip
            )

            # 更新追蹤值（在 is_turning 判斷後更新）
            last_mate[turn] = mate_in
            last_init[turn] = initiative

            if is_turning:
                self.record.turning_points.append(move_num)
                # Determine specific label
                if captured in ('帥','將'):
                    label = "CatchKing"
                elif mate_in is not None and mate_in <= 3:
                    label = "MateIn3"
                elif init_flip:
                    label = "InitiativeFlip"
                elif init_gap and initiative is not None:
                    label = f"InitGap{initiative:+d}"
                elif mate_gain:
                    label = "MateGained"
                elif delta >= TURNING_THRESHOLD:
                    label = "TurningPoint"
                else:
                    label = "MateThread"

                self.save_screenshot(
                    copy.deepcopy(self.board),
                    ((r1,c1),(r2,c2)),
                    move_num, score, mate_in, label
                )

            self.record.add_move(
                move_num, turn,
                PIECE_NAMES_ZH.get(piece_char,'?'),
                (r1, c1), (r2, c2),
                score, prev_score, mate_in, captured
            )
            prev_score = score

            # Win check
            if target_char.lower() == 'k':
                winner = 'Red' if turn == 'red' else 'Black'
                result = f'{winner} wins by catching king'
                # Final screenshot
                self.save_screenshot(
                    copy.deepcopy(self.board),
                    ((r1,c1),(r2,c2)),
                    move_num, score, mate_in, "FinalMate"
                )
                break

            turn_char = 'R' if turn == 'red' else 'B'
            init_str  = f" init={initiative:+d}" if initiative is not None else ""
            opp_str   = f" opp={opp_threat}步殺" if opp_threat else ""
            turn_pt   = f" [TURN:{label}]" if is_turning else ""
            print(f"  {turn_char}{move_num:3d} {piece_char:2s} ({r1},{c1})->({r2},{c2})"
                  f"  score={score:+5d}{init_str}{opp_str}{turn_pt}")

        else:
            result = "Draw by move limit"

        self.record.result = result
        # Save text record
        txt_path = os.path.join(self.out_dir, f"game_record_{self.ts}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.record.to_text())
        # Save JSON record
        json_path = os.path.join(self.out_dir, f"game_record_{self.ts}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "red":    self.record.red_name,
                "black":  self.record.black_name,
                "result": result,
                "moves":  self.record.moves,
                "turning_points": self.record.turning_points,
                "screenshots": [os.path.basename(s) for s in self.screenshots],
            }, f, ensure_ascii=False, indent=2)

        print(f"\n  [DONE] {result}")
        print(f"  Turning points: {len(self.record.turning_points)}")
        print(f"  Screenshots:    {len(self.screenshots)}")
        print(f"  Record:         {txt_path}")
        return result


# ── Run all three matchups ─────────────────────────────────────────────────────

class HuRonghuaFast(HuRonghuaAI):
    """Depth-2 variant of HuRonghuaAI for self-play (depth 4 is ~100s/move)."""
    SEARCH_DEPTH = 2


def run_all():
    base_dir = os.path.join(os.path.dirname(__file__), "AI_Games")

    matchups = [
        ("AI_Novice",    BeginnerAI,      ChineseChessEngine, "Novice vs MainAI"),
        ("AI_LiuDahua",  LiuDahuaAI,     ChineseChessEngine, "LiuDahua vs MainAI"),
        ("AI_HuRonghua", HuRonghuaFast,  ChineseChessEngine, "HuRonghua vs MainAI"),
    ]

    summaries = {}
    for folder, RedClass, BlackClass, label in matchups:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")
        red_ai   = RedClass()
        black_ai = BlackClass()
        # Give black AI a NAME if missing
        if not hasattr(black_ai, 'NAME'):
            black_ai.NAME = "主AI"

        out_dir = os.path.join(base_dir, folder)
        game = SelfPlay(red_ai, black_ai, out_dir, label)
        result = game.play()
        summaries[folder] = {
            "label":  label,
            "result": result,
            "turns":  len(game.record.moves),
            "turning_points": len(game.record.turning_points),
            "screenshots": len(game.screenshots),
        }

    print("\n\n" + "="*60)
    print("  總結")
    print("="*60)
    for folder, s in summaries.items():
        print(f"  {s['label']:<20} | {s['result']:<15} | "
              f"{s['turns']} moves | {s['turning_points']} turning pts | {s['screenshots']} screenshots")
    return summaries


if __name__ == "__main__":
    run_all()
