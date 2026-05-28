/* ════════════════════════════════════════════════════════════════════════════
   中國象棋 AI — main.js
   Four modes: human / tournament / analysis / endgame
   ════════════════════════════════════════════════════════════════════════════ */

// ── Constants ─────────────────────────────────────────────────────────────────

// Canonical initial board (deep copy each use)
function getInitialBoard() {
    return [
        ['r','n','b','a','k','a','b','n','r'],
        ['.','.','.','.','.','.','.','.','.'],
        ['.','c','.','.','.','.','.','c','.'],
        ['p','.','p','.','p','.','p','.','p'],
        ['.','.','.','.','.','.','.','.','.'],
        ['.','.','.','.','.','.','.','.','.'],
        ['P','.','P','.','P','.','P','.','P'],
        ['.','C','.','.','.','.','.','C','.'],
        ['.','.','.','.','.','.','.','.','.'],
        ['R','N','B','A','K','A','B','N','R'],
    ];
}

const PIECE_SYMBOLS = {
    'r':'車','n':'馬','b':'象','a':'士','k':'將','c':'砲','p':'卒',
    'R':'俥','N':'傌','B':'相','A':'仕','K':'帥','C':'炮','P':'兵',
};

const CELL = 50;   // px per cell
const MARGIN = 25; // px offset from board edge to first intersection

// ── Global mutable state ──────────────────────────────────────────────────────
let currentMode = 'human';

// Mode 1: Human vs AI
let gameState   = getInitialBoard();
let selectedPiece = null;
let turn        = 'red';
let hasGameStarted = false;
let isWaiting   = false;  // true while waiting for AI response (blocks human clicks)

// Mode 2: Tournament
const trn = {
    sessionId: null,
    pollTimer: null,
    replayBoards: [],   // pre-computed board at each step
    replayMoves: [],
    replayIdx: 0,
    autoTimer: null,
};

// Mode 3: Analysis
const ana = {
    boards: [],
    moves: [],
    idx: 0,
    autoTimer: null,
};

// Mode 4: Endgame
const eg = {
    board: getInitialBoard(),
    turn: 'red',
    activePiece: null,  // char to place, or null
};

// ── DOM refs ──────────────────────────────────────────────────────────────────
const boardEl    = document.getElementById('game-board');
const statusEl   = document.getElementById('status');
const forbidEl   = document.getElementById('forbidden-warning');

// ═════════════════════════════════════════════════════════════════════════════
//  BOARD RENDERING
// ═════════════════════════════════════════════════════════════════════════════

function initBoardGrid() {
    // Horizontal lines
    for (let r = 0; r < 10; r++) {
        const l = document.createElement('div');
        l.className = 'grid-line horizontal';
        l.style.top  = `${r * CELL + MARGIN}px`;
        boardEl.appendChild(l);
    }
    // Vertical lines
    for (let c = 0; c < 9; c++) {
        if (c === 0 || c === 8) {
            const l = document.createElement('div');
            l.className = 'grid-line vertical-full';
            l.style.left = `${c * CELL + MARGIN}px`;
            boardEl.appendChild(l);
        } else {
            ['top', 'bot'].forEach(half => {
                const l = document.createElement('div');
                l.className = 'grid-line vertical';
                l.style.left = `${c * CELL + MARGIN}px`;
                l.style.top  = half === 'top' ? `${MARGIN}px` : `${MARGIN + 5 * CELL}px`;
                boardEl.appendChild(l);
            });
        }
    }
    // Palace diagonals
    drawDiag(175, 25, 275, 125);
    drawDiag(275, 25, 175, 125);
    drawDiag(175, 475, 275, 375);
    drawDiag(275, 475, 175, 375);
    // River text
    const rv = document.createElement('div');
    rv.className   = 'river-text';
    rv.textContent = '楚 河           漢 界';
    boardEl.appendChild(rv);
}

function drawDiag(x1, y1, x2, y2) {
    const len   = Math.hypot(x2 - x1, y2 - y1);
    const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
    const el = document.createElement('div');
    el.className = 'diagonal';
    el.style.width     = `${len}px`;
    el.style.left      = `${x1}px`;
    el.style.top       = `${y1}px`;
    el.style.transform = `rotate(${angle}deg)`;
    boardEl.appendChild(el);
}

function renderPieces(board, interactive) {
    boardEl.querySelectorAll('.piece, .dot').forEach(e => e.remove());

    for (let r = 0; r < 10; r++) {
        for (let c = 0; c < 9; c++) {
            const ch = board[r][c];
            if (!ch || ch === '.') continue;

            const el = document.createElement('div');
            el.className = 'piece ' + (isRed(ch) ? 'red' : 'black');
            el.textContent = PIECE_SYMBOLS[ch] || ch;
            el.style.left  = `${c * CELL + MARGIN - 22}px`;
            el.style.top   = `${r * CELL + MARGIN - 22}px`;
            el.dataset.r   = r;
            el.dataset.c   = c;

            if (!interactive) el.style.cursor = 'default';

            if (selectedPiece && selectedPiece.r === r && selectedPiece.c === c) {
                el.classList.add('selected');
            }
            boardEl.appendChild(el);
        }
    }
}

// ═════════════════════════════════════════════════════════════════════════════
//  UTILITY
// ═════════════════════════════════════════════════════════════════════════════

function isRed(ch) { return ch === ch.toUpperCase() && ch !== '.'; }

function boardCoordFromClick(e) {
    const rect = boardEl.getBoundingClientRect();
    // Compensate for CSS zoom on #center-panel (mobile responsive scaling)
    const centerPanel = document.getElementById('center-panel');
    const zoom = parseFloat(window.getComputedStyle(centerPanel).zoom) || 1;
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;
    const c = Math.round((x - MARGIN) / CELL);
    const r = Math.round((y - MARGIN) / CELL);
    return { r, c };
}

function deepCopyBoard(b) { return b.map(row => [...row]); }

// Apply move {r1,c1,r2,c2} on board copy, return new board
function applyMoveLocal(board, mv) {
    const nb = deepCopyBoard(board);
    nb[mv.r2][mv.c2] = nb[mv.r1][mv.c1];
    nb[mv.r1][mv.c1] = '.';
    return nb;
}

// Pre-compute all board states from initial + move list
function precomputeBoards(moves) {
    const boards = [getInitialBoard()];
    for (const mv of moves) {
        const prev = boards[boards.length - 1];
        const [r1, c1] = mv.from;
        const [r2, c2] = mv.to;
        boards.push(applyMoveLocal(prev, { r1, c1, r2, c2 }));
    }
    return boards;
}

function showForbiddenWarning(warning) {
    if (!warning) { forbidEl.classList.remove('show'); forbidEl.textContent = ''; return; }
    const name   = warning.name   || '禁止著法';
    const advice = warning.advice || '必須變著！';
    const mover  = warning.mover  === 'red' ? '紅方' : '黑方';
    forbidEl.textContent = `⚠ ${name}！${mover}${advice}`;
    forbidEl.classList.add('show');
    setTimeout(() => forbidEl.classList.remove('show'), 5000);
}

// ── Thought-panel renderer (shared) ──────────────────────────────────────────
function pvStepText(step, idx) {
    // Build clean "N. 棋子 (r1,c1)→(r2,c2)" string from step data
    const piece = step.piece || '';
    if (step.from && step.to) {
        const f = step.from;
        const t = step.to;
        return `${idx + 1}. ${piece} (${f[0]},${f[1]})→(${t[0]},${t[1]})`;
    }
    return `${idx + 1}. ${step.move_str || JSON.stringify(step)}`;
}

function renderThought(container, thought) {
    if (!container) return;
    if (!thought) { container.textContent = '等待中…'; return; }

    const frag = document.createDocumentFragment();

    // ── 1. Score ─────────────────────────────────────────────────────────────
    const scoreLine = document.createElement('div');
    scoreLine.className = 'thought-score';
    const delta = thought.score_change ?? 0;
    const sc = thought.score;
    const scoreDisp = sc >= 29000
        ? `擒王 ${30000 - sc} 步殺 (${sc})`
        : sc <= -29000
        ? `被擒王 ${30000 + sc} 步 (${sc})`
        : sc;
    scoreLine.textContent = `分數: ${scoreDisp}  (${delta >= 0 ? '+' : ''}${delta})`;
    frag.appendChild(scoreLine);

    // ── 2. Mate / threat ─────────────────────────────────────────────────────
    if (thought.mate_in != null) {
        const ml = document.createElement('div');
        ml.className = 'thought-mate';
        const steps = Math.abs(thought.mate_in);
        ml.textContent = thought.mate_in > 0
            ? `⚔ 擒王在 ${steps} 步內！`
            : `⚠ 被擒王威脅（${steps} 步）`;
        frag.appendChild(ml);
    }

    if (thought.opponent_threat_in != null) {
        const ot = document.createElement('div');
        ot.className = 'thought-opp';
        ot.textContent = `↩ 對方可 ${thought.opponent_threat_in} 步內反擊`;
        frag.appendChild(ot);
    }

    // ── 3. Initiative ────────────────────────────────────────────────────────
    if (thought.initiative_advantage != null) {
        const il = document.createElement('div');
        il.className = 'thought-score';
        const ia = thought.initiative_advantage;
        const label = ia > 0 ? '我方先手 +' : ia < 0 ? '對方先手 ' : '先手均衡 ';
        il.textContent = `先手: ${label}${ia}`;
        frag.appendChild(il);
    }

    // ── 4. Source / opening ──────────────────────────────────────────────────
    const src = thought.source || 'search';
    const srcEl = document.createElement('div');
    srcEl.className = 'thought-source';
    if (src === 'opening_book') {
        srcEl.textContent = `📖 開局書: ${thought.opening_name || '?'}`;
    } else if (src === 'mate_in_1') {
        srcEl.textContent = '⚡ 一步殺捷徑';
    } else {
        srcEl.textContent = `🔍 Alpha-Beta 搜索`;
        if (thought.opening_name) {
            srcEl.textContent += `  [${thought.opening_name}]`;
        }
    }
    frag.appendChild(srcEl);

    // ── 5. PV (推衍路線) ─────────────────────────────────────────────────────
    if (thought.detailed_pv && thought.detailed_pv.length > 0) {
        const aiTurn = thought.turn;  // 'red' or 'black'
        const pvHeader = document.createElement('div');
        pvHeader.className = 'thought-pv-header';
        const pvLen = Math.min(thought.detailed_pv.length, 8);
        pvHeader.textContent = `推衍路線 (${pvLen}步):`;
        frag.appendChild(pvHeader);

        thought.detailed_pv.slice(0, 8).forEach((step, i) => {
            const l = document.createElement('div');
            // Even idx = AI's move, odd idx = opponent's predicted response
            const isAI = (i % 2 === 0);
            const stepTurn = isAI ? aiTurn : (aiTurn === 'red' ? 'black' : 'red');
            l.className = stepTurn === 'red' ? 'thought-pv-red' : 'thought-pv-black';
            l.textContent = '  ' + pvStepText(step, i);
            frag.appendChild(l);
        });
    }

    // ── 6. Warnings ──────────────────────────────────────────────────────────
    if (thought.forbidden_warning) {
        const wl = document.createElement('div');
        wl.className = 'thought-trap';
        wl.textContent = `⚠ ${thought.forbidden_warning.name}: ${thought.forbidden_warning.advice}`;
        frag.appendChild(wl);
    }

    if (thought.repetition_move) {
        const wl = document.createElement('div');
        wl.className = 'thought-trap';
        wl.textContent = '※ 此步造成局面重複，AI已改選其他著法';
        frag.appendChild(wl);
    }

    container.innerHTML = '';
    container.appendChild(frag);
}

// ═════════════════════════════════════════════════════════════════════════════
//  MODE SWITCHING
// ═════════════════════════════════════════════════════════════════════════════

function switchMode(mode) {
    currentMode = mode;

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Panel blocks
    document.querySelectorAll('[data-panel]').forEach(el => {
        el.classList.toggle('hidden', el.dataset.panel !== mode);
    });

    // Mode controls below board
    document.querySelectorAll('[data-ctrl]').forEach(el => {
        el.classList.toggle('hidden', el.dataset.ctrl !== mode);
    });

    // Stop any running replays/polls from other modes
    clearInterval(trn.autoTimer); trn.autoTimer = null;
    clearInterval(trn.pollTimer); trn.pollTimer = null;
    clearInterval(ana.autoTimer); ana.autoTimer = null;

    // Board click is always active; behaviour is gated by currentMode
    selectedPiece = null;

    if (mode === 'human') {
        renderPieces(gameState, true);
        updateHumanStatus();
    } else if (mode === 'tournament') {
        const b = trn.replayBoards.length
            ? trn.replayBoards[trn.replayIdx]
            : getInitialBoard();
        renderPieces(b, false);
        statusEl.textContent = 'AI 對弈觀戰模式';
        initTournamentMode();
    } else if (mode === 'analysis') {
        const b = ana.boards.length ? ana.boards[ana.idx] : getInitialBoard();
        renderPieces(b, false);
        statusEl.textContent = '分析棋局模式';
        initAnalysisMode();
    } else if (mode === 'endgame') {
        renderPieces(eg.board, false);
        statusEl.textContent = '殘局模式：點選棋盤格放置/移除棋子';
        initEndgameMode();
    }
}

// ═════════════════════════════════════════════════════════════════════════════
//  MODE 1 — HUMAN VS AI
// ═════════════════════════════════════════════════════════════════════════════

function updateHumanStatus() {
    if (isWaiting) {
        statusEl.textContent = 'AI 思考中…';
        return;
    }
    if (!hasGameStarted) {
        statusEl.textContent = '玩家先行 (請選擇棋子)';
    } else {
        statusEl.textContent = turn === 'red' ? '紅方回合 (請選擇棋子)' : '黑方回合';
    }
}

boardEl.addEventListener('click', (e) => {
    if (currentMode === 'human')     handleHumanClick(e);
    else if (currentMode === 'endgame') handleEndgameClick(e);
});

boardEl.addEventListener('contextmenu', (e) => {
    if (currentMode === 'endgame') {
        e.preventDefault();
        handleEndgameRightClick(e);
    }
});

function handleHumanClick(e) {
    const { r, c } = boardCoordFromClick(e);
    if (r < 0 || r > 9 || c < 0 || c > 8) return;
    handleSquareClick(r, c);
}

function handleSquareClick(r, c) {
    if (isWaiting) return;  // block clicks while AI is computing
    const piece = gameState[r][c];

    if (selectedPiece) {
        // Deselect if same square clicked again
        if (selectedPiece.r === r && selectedPiece.c === c) {
            selectedPiece = null;
            renderPieces(gameState, true);
            return;
        }
        // Re-select if clicking another own (red) piece
        const ownPiece = piece !== '.' && isRed(piece);
        if (ownPiece) {
            selectedPiece = { r, c };
            renderPieces(gameState, true);
            return;
        }
        // Otherwise attempt move (to empty square or enemy capture)
        movePiece(selectedPiece.r, selectedPiece.c, r, c);
    } else {
        // Select only red pieces (human always plays red)
        if (piece !== '.' && isRed(piece)) {
            selectedPiece = { r, c };
            renderPieces(gameState, true);
        }
    }
}

function movePiece(r1, c1, r2, c2) {
    const piece = gameState[r1][c1];
    const movedColor = isRed(piece) ? 'red' : 'black';

    if (!hasGameStarted) {
        hasGameStarted = true;
        turn = movedColor === 'red' ? 'black' : 'red';
    } else {
        turn = turn === 'red' ? 'black' : 'red';
    }

    // Optimistic update
    gameState[r2][c2] = gameState[r1][c1];
    gameState[r1][c1] = '.';
    selectedPiece = null;
    isWaiting = true;  // lock board while AI computes
    renderPieces(gameState, true);
    updateHumanStatus();

    fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ move: { r1, c1, r2, c2 } }),
    })
    .then(r => r.json())
    .then(data => {
        isWaiting = false;  // unlock board

        if (data.game_over || (data.status === 'game_over')) {
            // Apply AI move if present
            if (data.move) {
                const m = data.move;
                gameState[m.r2][m.c2] = gameState[m.r1][m.c1];
                gameState[m.r1][m.c1] = '.';
                renderPieces(gameState, true);
                renderThought(document.getElementById('black-thought'), data.black_thought);
                renderThought(document.getElementById('red-thought'),   data.red_thought);
            }
            statusEl.textContent = `遊戲結束！${data.winner === 'red' ? '紅方' : '黑方'} 獲勝！`;
            hasGameStarted = false;
            turn = 'red';  // reset so next game starts clean
            return;
        }

        showForbiddenWarning(data.forbidden_warning);

        if (data.in_check) {
            statusEl.textContent = '將軍！';
            document.body.style.backgroundColor = '#ffcccc';
            setTimeout(() => document.body.style.backgroundColor = '#f0e6d2', 600);
        }

        if (data.move) {
            const m = data.move;
            gameState[m.r2][m.c2] = gameState[m.r1][m.c1];
            gameState[m.r1][m.c1] = '.';
            turn = 'red';  // human always plays red; after AI moves it's red's turn
            renderPieces(gameState, true);
            renderThought(document.getElementById('black-thought'), data.black_thought);
            renderThought(document.getElementById('red-thought'),   data.red_thought);
            showForbiddenWarning(data.forbidden_warning);

            if (data.in_check) {
                statusEl.textContent = '將軍！';
            } else {
                updateHumanStatus();
            }
        } else {
            // Server responded but no AI move (unexpected) — restore turn so player can move
            turn = 'red';
            updateHumanStatus();
        }
    })
    .catch(err => {
        console.error('move error:', err);
        isWaiting = false;  // always unlock on error
        turn = 'red';       // restore player turn
        updateHumanStatus();
    });
}

// Difficulty buttons
document.querySelectorAll('.diff-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        fetch('/set_difficulty', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ difficulty: btn.dataset.diff }),
        })
        .then(r => r.json())
        .then(data => {
            document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('ai-label').textContent = `當前AI：${data.ai_name}`;
            fetch('/reset', { method: 'POST' }).then(() => resetHuman());
        });
    });
});

// Reset button
document.getElementById('reset-btn').addEventListener('click', () => {
    fetch('/reset', { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        document.getElementById('ai-label').textContent = `當前AI：${data.ai_name}`;
        resetHuman();
    });
});

function resetHuman() {
    gameState     = getInitialBoard();
    selectedPiece = null;
    turn          = 'red';
    hasGameStarted = false;
    isWaiting     = false;
    renderPieces(gameState, true);
    updateHumanStatus();
    document.getElementById('black-thought').textContent = '等待中…';
    document.getElementById('red-thought').textContent   = '等待中…';
}

// ═════════════════════════════════════════════════════════════════════════════
//  MODE 2 — TOURNAMENT / AI VS AI
// ═════════════════════════════════════════════════════════════════════════════

function initTournamentMode() {
    loadTournamentSessions();
}

function loadTournamentSessions() {
    fetch('/tournament/sessions')
    .then(r => r.json())
    .then(sessions => {
        const sessListEl = document.getElementById('trn-session-list');
        if (!sessions || sessions.length === 0) {
            sessListEl.textContent = '尚無賽事記錄';
            return;
        }
        sessListEl.innerHTML = '';
        sessions.slice(-8).reverse().forEach(s => {
            const item = document.createElement('div');
            item.className = 'file-item';
            const ts = s.session || '—';
            const tot = s.summary?.total || 0;
            item.textContent = `${ts}（${tot} 局）`;
            item.addEventListener('click', () => loadTournamentSession(s));
            sessListEl.appendChild(item);
        });
    })
    .catch(() => {});
}

function loadTournamentSession(sessionData) {
    // Build game list from summary
    const gameListEl = document.getElementById('trn-game-list');
    gameListEl.innerHTML = '';
    const games = sessionData.summary?.games || [];
    if (games.length === 0) {
        gameListEl.textContent = '此賽事無對局記錄';
        return;
    }

    // Show standings
    renderStandings(sessionData.summary?.results || {});

    games.forEach(g => {
        const item = document.createElement('div');
        item.className = 'file-item';
        const res = g.result === 'red_wins' ? '紅勝' : g.result === 'black_wins' ? '黑勝' : '和';
        item.textContent = `${g.label} 第${g.game}局 [${res}]`;
        item.addEventListener('click', () => loadTournamentReplay(sessionData.session, g.file));
        gameListEl.appendChild(item);
    });
}

function renderStandings(results) {
    const el = document.getElementById('trn-standings');
    if (!results || Object.keys(results).length === 0) { el.textContent = '—'; return; }

    // Aggregate per player
    const scores = {};
    for (const [label, tally] of Object.entries(results)) {
        const [rName, bName] = label.split(' vs ').map(s => s.trim());
        [rName, bName].forEach(n => { if (!scores[n]) scores[n] = { w:0, l:0, d:0 }; });
        scores[rName].w += tally.wins_red   || 0;
        scores[rName].l += tally.wins_black || 0;
        scores[rName].d += tally.draws      || 0;
        scores[bName].w += tally.wins_black || 0;
        scores[bName].l += tally.wins_red   || 0;
        scores[bName].d += tally.draws      || 0;
    }

    let html = '<table class="standings-table"><tr><th>選手</th><th>勝</th><th>負</th><th>和</th></tr>';
    for (const [name, s] of Object.entries(scores)) {
        html += `<tr><td>${name}</td><td>${s.w}</td><td>${s.l}</td><td>${s.d}</td></tr>`;
    }
    html += '</table>';
    el.innerHTML = html;
}

function loadTournamentReplay(sessionId, fname) {
    document.getElementById('trn-game-label').textContent = `載入中…${fname}`;
    fetch(`/tournament/replay/${sessionId}/${fname}`)
    .then(r => r.json())
    .then(game => {
        trn.replayMoves  = game.moves || [];
        trn.replayBoards = precomputeBoards(trn.replayMoves);
        trn.replayIdx    = 0;
        document.getElementById('trn-game-label').textContent =
            `${game.red_name || '紅'} vs ${game.black_name || '黑'} — 共 ${trn.replayMoves.length} 步`;
        updateReplay();
    })
    .catch(() => { document.getElementById('trn-game-label').textContent = '載入失敗'; });
}

function updateReplay() {
    const total = trn.replayBoards.length - 1;
    const idx   = trn.replayIdx;
    renderPieces(trn.replayBoards[idx], false);

    document.getElementById('rep-step-label').textContent = `${idx} / ${total}`;
    document.getElementById('rep-first').disabled = idx === 0;
    document.getElementById('rep-prev').disabled  = idx === 0;
    document.getElementById('rep-next').disabled  = idx === total;
    document.getElementById('rep-last').disabled  = idx === total;

    // Show spectator note if any
    const mv = trn.replayMoves[idx > 0 ? idx - 1 : 0];
    if (mv) {
        const isKey = mv.is_key;
        const spec  = document.getElementById('trn-spectator');
        const note  = `步 ${mv.half || '?'} | ${mv.turn === 'red' ? '紅' : '黑'}方 ${mv.piece || '?'}\n` +
                      `分數: ${mv.score ?? '?'}\n` +
                      (mv.mate_in    != null ? `擒王威脅: ${mv.mate_in} 步\n` : '') +
                      (mv.initiative != null ? `先手優勢: ${mv.initiative}\n` : '') +
                      (isKey ? '\n★ 重大轉折點！' : '');
        spec.textContent = note;
    }

    if (mv) {
        statusEl.textContent = (mv.turn === 'red' ? '紅方' : '黑方') +
            ` 走 ${mv.piece || ''}`;
    }
}

// Replay buttons
document.getElementById('rep-first').addEventListener('click', () => {
    clearInterval(trn.autoTimer); trn.autoTimer = null;
    trn.replayIdx = 0; updateReplay();
});
document.getElementById('rep-prev').addEventListener('click', () => {
    clearInterval(trn.autoTimer); trn.autoTimer = null;
    if (trn.replayIdx > 0) { trn.replayIdx--; updateReplay(); }
});
document.getElementById('rep-next').addEventListener('click', () => {
    clearInterval(trn.autoTimer); trn.autoTimer = null;
    if (trn.replayIdx < trn.replayBoards.length - 1) { trn.replayIdx++; updateReplay(); }
});
document.getElementById('rep-last').addEventListener('click', () => {
    clearInterval(trn.autoTimer); trn.autoTimer = null;
    trn.replayIdx = trn.replayBoards.length - 1; updateReplay();
});
document.getElementById('rep-play').addEventListener('click', () => {
    if (trn.autoTimer) {
        clearInterval(trn.autoTimer); trn.autoTimer = null;
        document.getElementById('rep-play').textContent = '▶';
    } else {
        document.getElementById('rep-play').textContent = '⏸';
        trn.autoTimer = setInterval(() => {
            if (trn.replayIdx < trn.replayBoards.length - 1) {
                trn.replayIdx++;
                updateReplay();
            } else {
                clearInterval(trn.autoTimer); trn.autoTimer = null;
                document.getElementById('rep-play').textContent = '▶';
            }
        }, 700);
    }
});

// Start tournament button
document.getElementById('trn-start-btn').addEventListener('click', () => {
    const gpp = parseInt(document.getElementById('trn-gpp').value, 10) || 10;
    document.getElementById('trn-start-btn').disabled = true;
    document.getElementById('trn-start-btn').textContent = '賽事進行中…';
    document.getElementById('trn-progress-wrap').classList.remove('hidden');

    fetch('/tournament/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ games_per_pair: gpp }),
    })
    .then(r => r.json())
    .then(data => {
        trn.sessionId = data.session_id;
        trn.pollTimer = setInterval(() => pollTournament(data.session_id), 2500);
    })
    .catch(err => {
        console.error(err);
        document.getElementById('trn-start-btn').disabled  = false;
        document.getElementById('trn-start-btn').textContent = '▶ 開始賽事';
    });
});

function pollTournament(sid) {
    fetch(`/tournament/status/${sid}`)
    .then(r => r.json())
    .then(s => {
        document.getElementById('trn-progress-label').textContent =
            `進度：${s.done} / ${s.total}（${s.pct}%）`;
        document.getElementById('trn-progress-bar').style.width = `${s.pct}%`;
        renderStandings(s.results);

        if (s.status === 'done') {
            clearInterval(trn.pollTimer); trn.pollTimer = null;
            document.getElementById('trn-start-btn').disabled  = false;
            document.getElementById('trn-start-btn').textContent = '▶ 開始賽事';
            statusEl.textContent = '賽事結束！';
            loadTournamentSessions();
        }
    })
    .catch(() => {});
}

// ═════════════════════════════════════════════════════════════════════════════
//  MODE 3 — GAME ANALYSIS
// ═════════════════════════════════════════════════════════════════════════════

function initAnalysisMode() {
    loadGamesList();
}

function loadGamesList() {
    fetch('/games/list')
    .then(r => r.json())
    .then(files => {
        const listEl = document.getElementById('ana-file-list');
        listEl.innerHTML = '';
        if (files.length === 0) { listEl.textContent = '尚無棋局記錄'; return; }
        files.forEach(f => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.textContent = f.split('/').pop();
            item.title = f;
            item.addEventListener('click', () => {
                listEl.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                loadAnalysisGame(f);
            });
            listEl.appendChild(item);
        });
    })
    .catch(() => {});
}

function loadAnalysisGame(filePath) {
    document.getElementById('ana-game-label').textContent = '載入中…';
    fetch('/games/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file: filePath }),
    })
    .then(r => r.json())
    .then(game => {
        // Support both tournament format and legacy format
        const moves = game.moves || [];
        ana.moves  = moves;
        ana.boards = precomputeBoards(moves);
        ana.idx    = 0;

        document.getElementById('ana-game-label').textContent =
            `${game.red_name || '紅'} vs ${game.black_name || '黑'} — ${moves.length} 步`;

        // Build move list on right panel
        buildAnalysisMoveList(moves);
        updateAnalysis();
    })
    .catch(() => {
        document.getElementById('ana-game-label').textContent = '載入失敗';
    });
}

function buildAnalysisMoveList(moves) {
    const listEl = document.getElementById('ana-movelist');
    listEl.innerHTML = '';
    moves.forEach((mv, i) => {
        const item = document.createElement('div');
        item.className = 'move-item' + (mv.is_key ? ' key' : '');
        item.dataset.idx = i + 1;
        const side = mv.turn === 'red' ? '紅' : '黑';
        const cap  = mv.captured ? ` 吃${mv.captured}` : '';
        item.textContent = `${i + 1}. ${side}${mv.piece || '?'}(${mv.from?.[0]},${mv.from?.[1]})→(${mv.to?.[0]},${mv.to?.[1]})${cap}`;
        item.addEventListener('click', () => {
            ana.idx = parseInt(item.dataset.idx, 10);
            updateAnalysis();
        });
        listEl.appendChild(item);
    });
}

function updateAnalysis() {
    const total = ana.boards.length - 1;
    const idx   = ana.idx;
    renderPieces(ana.boards[idx], false);

    // Sync move list highlight
    document.querySelectorAll('#ana-movelist .move-item').forEach(el => {
        el.classList.toggle('active', parseInt(el.dataset.idx, 10) === idx);
    });
    // Scroll active into view
    const activeEl = document.querySelector('#ana-movelist .move-item.active');
    if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });

    document.getElementById('ana-step-label').textContent = `${idx} / ${total}`;

    // Status from current move
    if (idx > 0) {
        const mv = ana.moves[idx - 1];
        statusEl.textContent = `${mv.turn === 'red' ? '紅' : '黑'}方 走 ${mv.piece || ''}`;
    } else {
        statusEl.textContent = '初始局面';
    }

    document.getElementById('ana-first').disabled = idx === 0;
    document.getElementById('ana-prev').disabled  = idx === 0;
    document.getElementById('ana-next').disabled  = idx === total;
    document.getElementById('ana-last').disabled  = idx === total;
}

// Analysis nav buttons
document.getElementById('ana-first').addEventListener('click', () => {
    clearInterval(ana.autoTimer); ana.autoTimer = null;
    ana.idx = 0; updateAnalysis();
});
document.getElementById('ana-prev').addEventListener('click', () => {
    clearInterval(ana.autoTimer); ana.autoTimer = null;
    if (ana.idx > 0) { ana.idx--; updateAnalysis(); }
});
document.getElementById('ana-next').addEventListener('click', () => {
    clearInterval(ana.autoTimer); ana.autoTimer = null;
    if (ana.idx < ana.boards.length - 1) { ana.idx++; updateAnalysis(); }
});
document.getElementById('ana-last').addEventListener('click', () => {
    clearInterval(ana.autoTimer); ana.autoTimer = null;
    ana.idx = ana.boards.length - 1; updateAnalysis();
});
document.getElementById('ana-play').addEventListener('click', () => {
    if (ana.autoTimer) {
        clearInterval(ana.autoTimer); ana.autoTimer = null;
        document.getElementById('ana-play').textContent = '▶';
    } else {
        document.getElementById('ana-play').textContent = '⏸';
        ana.autoTimer = setInterval(() => {
            if (ana.idx < ana.boards.length - 1) {
                ana.idx++;
                updateAnalysis();
            } else {
                clearInterval(ana.autoTimer); ana.autoTimer = null;
                document.getElementById('ana-play').textContent = '▶';
            }
        }, 800);
    }
});

// Refresh file list
document.getElementById('ana-refresh-btn').addEventListener('click', loadGamesList);

// AI analyse current position
document.getElementById('ana-analyze-btn').addEventListener('click', () => {
    if (!ana.boards.length) return;
    const board = ana.boards[ana.idx];
    const turn  = (ana.idx > 0 && ana.moves[ana.idx - 1])
        ? (ana.moves[ana.idx - 1].turn === 'red' ? 'black' : 'red')
        : 'red';

    document.getElementById('ana-thought').textContent = '分析中…';
    fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board, turn, depth: 3 }),
    })
    .then(r => r.json())
    .then(data => {
        renderThought(document.getElementById('ana-thought'), data.thought);
    })
    .catch(() => { document.getElementById('ana-thought').textContent = '分析失敗'; });
});

// ═════════════════════════════════════════════════════════════════════════════
//  MODE 4 — ENDGAME PUZZLES
// ═════════════════════════════════════════════════════════════════════════════

function initEndgameMode() {
    loadEndgameLibrary();
    renderPieces(eg.board, false);
    eg.activePiece = null;
    document.querySelectorAll('.pal-piece').forEach(p => p.classList.remove('selected'));
}

function loadEndgameLibrary() {
    fetch('/endgame/library')
    .then(r => r.json())
    .then(puzzles => {
        const listEl = document.getElementById('eg-lib-list');
        listEl.innerHTML = '';
        puzzles.forEach(p => {
            const item = document.createElement('div');
            item.className = 'file-item';
            const tag = p.mate_in ? `（${p.mate_in}步殺）` : '';
            item.textContent = `${p.name}${tag} — ${p.difficulty === 'easy' ? '簡' : p.difficulty === 'hard' ? '難' : '中'}`;
            item.title = p.description || '';
            item.addEventListener('click', () => {
                listEl.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                loadEndgamePuzzle(p);
            });
            listEl.appendChild(item);
        });
    })
    .catch(() => {});
}

function loadEndgamePuzzle(puzzle) {
    eg.board = deepCopyBoard(puzzle.board);
    eg.turn  = puzzle.turn || 'red';

    // Sync turn buttons
    document.querySelectorAll('.eg-turn-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.turn === eg.turn);
    });

    renderPieces(eg.board, false);
    document.getElementById('eg-result').textContent =
        `題目：${puzzle.name}\n${puzzle.description || ''}\n\n` +
        `先手：${eg.turn === 'red' ? '紅方' : '黑方'}\n` +
        (puzzle.mate_in ? `目標：${puzzle.mate_in} 步殺` : '');
    statusEl.textContent = `${puzzle.name} — 點 AI解題 查看答案`;
}

// Palette piece selection
document.querySelectorAll('.pal-piece').forEach(btn => {
    btn.addEventListener('click', () => {
        const piece = btn.dataset.piece;
        if (eg.activePiece === piece) {
            eg.activePiece = null;
            btn.classList.remove('selected');
        } else {
            document.querySelectorAll('.pal-piece').forEach(b => b.classList.remove('selected'));
            eg.activePiece = piece;
            btn.classList.add('selected');
        }
    });
});

// Turn buttons
document.querySelectorAll('.eg-turn-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        eg.turn = btn.dataset.turn;
        document.querySelectorAll('.eg-turn-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// Board clicks in endgame mode — place or remove pieces
function handleEndgameClick(e) {
    const { r, c } = boardCoordFromClick(e);
    if (r < 0 || r > 9 || c < 0 || c > 8) return;

    if (eg.activePiece === '.') {
        eg.board[r][c] = '.';
    } else if (eg.activePiece) {
        eg.board[r][c] = eg.activePiece;
    } else {
        // No palette selection → toggle removal
        eg.board[r][c] = '.';
    }
    renderPieces(eg.board, false);
}

function handleEndgameRightClick(e) {
    const { r, c } = boardCoordFromClick(e);
    if (r < 0 || r > 9 || c < 0 || c > 8) return;
    eg.board[r][c] = '.';
    renderPieces(eg.board, false);
}

// Solve button
document.getElementById('eg-solve-btn').addEventListener('click', () => {
    document.getElementById('eg-result').textContent = 'AI 解題中…';
    const depth = parseInt(document.getElementById('eg-depth').value, 10) || 4;

    fetch('/endgame/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board: eg.board, turn: eg.turn, depth }),
    })
    .then(r => r.json())
    .then(data => {
        const resultEl = document.getElementById('eg-result');
        if (!data.success) {
            resultEl.textContent = `失敗: ${data.message || '未知錯誤'}`;
            return;
        }
        const m = data.move;
        let text = '';
        if (m) {
            const piece = eg.board[m.r1][m.c1];
            text += `最佳著法: ${PIECE_SYMBOLS[piece] || piece} (${m.r1},${m.c1})→(${m.r2},${m.c2})\n`;
        }
        text += `分數: ${data.score ?? '?'}\n`;
        if (data.mate_in != null) text += `擒王: ${data.mate_in} 步\n`;
        if (data.initiative_advantage != null) text += `先手優勢: ${data.initiative_advantage}\n`;
        if (data.pv && data.pv.length > 0) {
            text += '\n思考路線:\n';
            data.pv.slice(0, 6).forEach((step, i) => {
                text += `  ${i + 1}. ${step.move_str || JSON.stringify(step)}\n`;
            });
        }
        resultEl.textContent = text;

        // Highlight best move on board
        if (m) {
            renderPieces(eg.board, false);
            flashCell(m.r1, m.c1, 'rgba(255,200,0,0.7)');
            setTimeout(() => flashCell(m.r2, m.c2, 'rgba(50,220,50,0.7)'), 300);
        }
    })
    .catch(() => { document.getElementById('eg-result').textContent = '請求失敗'; });
});

function flashCell(r, c, color) {
    const dot = document.createElement('div');
    dot.style.cssText = `
        position:absolute;
        left:${c * CELL + MARGIN - 22}px;
        top:${r * CELL + MARGIN - 22}px;
        width:44px; height:44px;
        border-radius:50%;
        background:${color};
        z-index:20;
        pointer-events:none;
        animation: fadeout 0.8s forwards;
    `;
    boardEl.appendChild(dot);
    setTimeout(() => dot.remove(), 900);
}

// Similar puzzles
document.getElementById('eg-similar-btn').addEventListener('click', () => {
    fetch('/endgame/similar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board: eg.board }),
    })
    .then(r => r.json())
    .then(puzzles => {
        const listEl = document.getElementById('eg-similar-list');
        listEl.innerHTML = '';
        if (!puzzles.length) { listEl.textContent = '無相似殘局'; return; }
        puzzles.forEach(p => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.textContent = `${p.name} (${p.difficulty || '?'})`;
            item.title = p.description || '';
            item.addEventListener('click', () => loadEndgamePuzzle(p));
            listEl.appendChild(item);
        });
    })
    .catch(() => {});
});

// Clear / reset board
document.getElementById('eg-clear-btn').addEventListener('click', () => {
    eg.board = Array.from({ length: 10 }, () => Array(9).fill('.'));
    renderPieces(eg.board, false);
    document.getElementById('eg-result').textContent = '棋盤已清空';
});
document.getElementById('eg-reset-btn').addEventListener('click', () => {
    eg.board = getInitialBoard();
    renderPieces(eg.board, false);
    document.getElementById('eg-result').textContent = '已恢復初始局面';
});

// Save puzzle
document.getElementById('eg-save-btn').addEventListener('click', () => {
    document.getElementById('eg-save-form').classList.toggle('hidden');
});
document.getElementById('eg-save-cancel-btn').addEventListener('click', () => {
    document.getElementById('eg-save-form').classList.add('hidden');
});
document.getElementById('eg-save-confirm-btn').addEventListener('click', () => {
    const name = document.getElementById('eg-save-name').value.trim();
    if (!name) { alert('請輸入殘局名稱'); return; }
    const tagsStr = document.getElementById('eg-save-tags').value;
    const tags    = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];

    fetch('/endgame/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            board: eg.board,
            turn:  eg.turn,
            name,
            description: document.getElementById('eg-save-desc').value.trim(),
            tags,
            difficulty:  document.getElementById('eg-save-diff').value,
        }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            document.getElementById('eg-save-form').classList.add('hidden');
            document.getElementById('eg-result').textContent = `殘局「${name}」已儲存！`;
            loadEndgameLibrary();
        }
    })
    .catch(() => {});
});

// Library refresh
document.getElementById('eg-lib-refresh').addEventListener('click', loadEndgameLibrary);

// ═════════════════════════════════════════════════════════════════════════════
//  INIT
// ═════════════════════════════════════════════════════════════════════════════

// Tab click handlers
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchMode(btn.dataset.mode));
});

// Add fadeout animation dynamically (for flashCell)
const style = document.createElement('style');
style.textContent = `@keyframes fadeout { from { opacity:1; } to { opacity:0; } }`;
document.head.appendChild(style);

// Boot
initBoardGrid();
renderPieces(gameState, true);
updateHumanStatus();
