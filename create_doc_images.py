"""
Generate 5 annotated board images for README.md documentation.
One image per theory concept: opening / catch-king / initiative / root-theory / endgame-mate.
Run from project root: python create_doc_images.py
"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from self_play import draw_board, FONT_HEADER, FONT_PIECE, FONT_LABEL, \
                     cell_to_pixel, CELL, MARGIN, W, H, HEADER_H, BG_COLOR, LINE_COLOR
from engine import ChineseChessEngine

OUT = os.path.join(os.path.dirname(__file__), "docs", "images")
os.makedirs(OUT, exist_ok=True)

# ── Helper: load a small bold font for annotations ─────────────────────────
def _anno_font(size=15):
    try:
        return FONT_HEADER  # reuse header font
    except Exception:
        return ImageFont.load_default()

def _label_font(size=13):
    return FONT_LABEL

def add_callout(img, r, c, text, color=(220, 60, 60), side="right"):
    """Draw a circle highlight + label on an existing board image."""
    d = ImageDraw.Draw(img)
    px, py = cell_to_pixel(r, c)
    py += HEADER_H
    R = int(CELL * 0.50)
    d.ellipse([px - R, py - R, px + R, py + R],
              outline=color, width=3)
    tx = px + R + 4 if side == "right" else px - R - 4
    anchor = "lm" if side == "right" else "rm"
    d.text((tx, py), text, fill=color, font=FONT_PIECE, anchor=anchor)
    return img

def add_banner(img, text, color=(50, 50, 50), bg=(255, 240, 180, 210)):
    """Paste a semi-transparent banner at the bottom of the image."""
    d = ImageDraw.Draw(img, "RGBA")
    banner_h = 34
    y0 = img.height - banner_h
    d.rectangle([0, y0, img.width, img.height], fill=bg)
    bbox = d.textbbox((0, 0), text, font=FONT_LABEL)
    tw = bbox[2] - bbox[0]
    d.text(((img.width - tw) // 2, y0 + 6), text, fill=color, font=FONT_LABEL)
    return img

# ── 1. 開局定式 — Opening Book ─────────────────────────────────────────────
def make_opening():
    """Board after 炮七平五 (Red) + 砲中平五 (Black) — canonical central cannon."""
    e = ChineseChessEngine()
    b = e.board
    # Apply Red: cannon (7,7) → (7,4)
    b[7][4] = b[7][7]; b[7][7] = '.'
    # Apply Black: cannon (2,1) → (2,4)
    b[2][4] = b[2][1]; b[2][1] = '.'

    img = draw_board(b,
                     highlight_move=((2, 1), (2, 4)),
                     title="開局定式｜Opening Book",
                     score=0)

    # Annotate Red's cannon
    add_callout(img, 7, 4, "炮七平五", color=(190, 60, 30), side="left")
    # Annotate Black's cannon
    add_callout(img, 2, 4, "砲中平五", color=(30, 30, 30), side="right")

    add_banner(img,
               "來源：開局書 [中炮盤頭馬]  Source: opening_book  Score: 0  step 1",
               color=(60, 40, 10),
               bg=(255, 235, 160, 220))

    path = os.path.join(OUT, "concept_opening.png")
    img.save(path)
    print("Saved:", path)

# ── 2. 擒王分數 — Catch-the-King Score annotation ─────────────────────────
def make_catch_king():
    """
    Reuse the existing score_29999_matein1.png, overlay formula box.
    """
    src = os.path.join(OUT, "score_29999_matein1.png")
    img = Image.open(src).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # Formula box
    bx, by, bw, bh = 10, HEADER_H + 8, 340, 70
    d.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0, 160))
    lines = [
        "擒王分數 = MATE_SCORE − depth_to_mate",
        "= 30,000 − 1  =  29,999",
        "Score: 29999  →  Win in 1 move (一步殺)",
    ]
    for i, line in enumerate(lines):
        d.text((bx + 8, by + 8 + i * 20), line, fill=(255, 220, 80), font=FONT_LABEL)

    img = img.convert("RGB")
    path = os.path.join(OUT, "concept_catch_king.png")
    img.save(path)
    print("Saved:", path)

# ── 3. 子根理論 — Root Theory (SEE classification) ─────────────────────────
def make_root_theory():
    """
    Mid-game position from game turn 15 (Red rook captured Black horse).
    Annotate a 無根 (undefended) piece and a 有根 (defended) piece.
    Board after turn 16: Black cannon just moved to (6,4) — now Red has pieces
    exposed. Use a simplified mid-game position to show the concept.
    """
    e = ChineseChessEngine()
    b = e.board

    # Simplified position: Red rook at (3,4), Red knight at (7,6),
    # Black cannon at (6,4) — undefended / only defended by king far away
    # Use a clean teaching position:
    # Red: 帥(9,4), 俥(3,2), 炮(7,4), 傌(7,6), 相(9,2)(9,6), 仕(9,3)(9,5), 兵(6,0)(6,8)
    # Black: 將(0,4), 士(0,3)(0,5), 砲(5,1)=unrooted, 砲(2,7)=rooted by rook, 馬(2,2), 車(1,8)

    # Build teaching board from scratch
    b2 = [['.' for _ in range(9)] for _ in range(10)]

    # Red pieces
    b2[9][4] = 'K'   # 帥
    b2[9][3] = 'A'; b2[9][5] = 'A'  # 仕
    b2[9][2] = 'B'; b2[9][6] = 'B'  # 相
    b2[9][8] = 'R'   # 俥 (right rook)
    b2[3][2]  = 'R'   # 俥 advanced
    b2[7][4]  = 'C'   # 炮 center
    b2[7][6]  = 'N'   # 傌
    b2[6][0]  = 'P'   # 兵

    # Black pieces
    b2[0][4] = 'k'   # 將
    b2[0][3] = 'a'; b2[0][5] = 'a'  # 士
    b2[2][2]  = 'n'   # 馬
    b2[1][8]  = 'r'   # 車
    b2[5][1]  = 'c'   # 砲 — UNROOTED (無根): no black piece defends it
    b2[3][7]  = 'c'   # 砲 — ROOTED (有根): defended by 車 at (1,8) through (2,8) area? no
    #   Actually make it clear: put black rook behind black cannon
    b2[1][7]  = 'r'   # 車 behind cannon at (3,7) → cannon IS rooted
    b2[3][7]  = 'c'   # 砲 rooted (車 at 1,7 behind it)
    b2[5][1]  = 'c'   # 砲 NOT rooted

    img = draw_board(b2,
                     title="子根理論｜Root Theory (SEE)",
                     score=None)

    # Mark 無根 cannon (5,1)
    add_callout(img, 5, 1, "無根 +15", color=(220, 50, 50), side="right")
    # Mark 有根 cannon (3,7) — defended by rook at (1,7)
    add_callout(img, 3, 7, "有根 −5",  color=(30, 120, 30), side="left")
    # Mark the defending rook
    add_callout(img, 1, 7, "守根",     color=(30, 120, 30), side="left")

    add_banner(img,
               "無根棋子（無人防守）評估+15 ｜ 有根棋子（有人防守）評估−5",
               color=(60, 30, 10),
               bg=(255, 245, 200, 220))

    path = os.path.join(OUT, "concept_root_theory.png")
    img.save(path)
    print("Saved:", path)

# ── 4. 先手分析 — Mutual Initiative ─────────────────────────────────────────
def make_initiative():
    """
    Use the game1 turn_043 board (score 291) and overlay initiative annotation.
    """
    src = os.path.join(OUT, "score_291_dominant.png")
    img = Image.open(src).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # Overlay box
    bx, by, bw, bh = 8, HEADER_H + 8, 380, 80
    d.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0, 165))
    lines = [
        "雙方先手分析  Mutual Initiative:",
        "紅方強殺深度：3 步  Red mate path: 3",
        "黑方強殺深度：∞     Black has no mate",
        "→ 紅方先手優勢  Red holds initiative",
    ]
    for i, line in enumerate(lines):
        color = (255, 180, 80) if i == 0 else \
                (255, 100, 80) if i == 1 else \
                (180, 180, 180) if i == 2 else (100, 255, 100)
        d.text((bx + 8, by + 6 + i * 18), line, fill=color, font=FONT_LABEL)

    img = img.convert("RGB")
    path = os.path.join(OUT, "concept_initiative.png")
    img.save(path)
    print("Saved:", path)

# ── 5. 殘局絕殺 — Endgame Forced Mate ─────────────────────────────────────
def make_endgame_mate():
    """
    Reuse score_29999_matein1.png as-is (already labelled Win in 1).
    Add 殘局絕殺 banner.
    """
    src = os.path.join(OUT, "score_29999_matein1.png")
    img = Image.open(src).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    bx, by, bw, bh = 8, HEADER_H + 8, 290, 46
    d.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0, 165))
    d.text((bx + 8, by + 6),  "殘局絕殺  Endgame Forced Mate", fill=(255, 220, 60), font=FONT_LABEL)
    d.text((bx + 8, by + 24), "俥 enters palace — 將 cornered", fill=(200, 200, 200), font=FONT_LABEL)

    img = img.convert("RGB")
    path = os.path.join(OUT, "concept_endgame_mate.png")
    img.save(path)
    print("Saved:", path)


if __name__ == "__main__":
    print("Generating concept images...")
    make_opening()
    make_catch_king()
    make_root_theory()
    make_initiative()
    make_endgame_mate()
    print("Done.")
