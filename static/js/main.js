const board = document.getElementById('game-board');
const statusDiv = document.getElementById('status');
const resetBtn = document.getElementById('reset-btn');

// Board State (Red is uppercase, Black is lowercase)
let gameState = [
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
];

let selectedPiece = null;
let turn = 'red';
let hasGameStarted = false;

function initBoard() {
    renderGrid();
    renderBoard();
}

function renderGrid() {
    // 10 Horizontal Lines
    for (let r = 0; r < 10; r++) {
        const line = document.createElement('div');
        line.classList.add('grid-line', 'horizontal');
        line.style.top = `${r * 50 + 25}px`;
        board.appendChild(line);
    }

    // 9 Vertical Lines
    for (let c = 0; c < 9; c++) {
        if (c === 0 || c === 8) {
            // Full height for edges
            const line = document.createElement('div');
            line.classList.add('grid-line', 'vertical-full');
            line.style.left = `${c * 50 + 25}px`;
            board.appendChild(line);
        } else {
            // Split for river
            // Top half
            const lineTop = document.createElement('div');
            lineTop.classList.add('grid-line', 'vertical');
            lineTop.style.left = `${c * 50 + 25}px`;
            lineTop.style.top = '25px';
            board.appendChild(lineTop);

            // Bottom half
            const lineBot = document.createElement('div');
            lineBot.classList.add('grid-line', 'vertical');
            lineBot.style.left = `${c * 50 + 25}px`;
            lineBot.style.top = '275px'; // 25 + 5*50
            board.appendChild(lineBot);
        }
    }

    // Palace Diagonals
    drawDiagonal(175, 25, 275, 125);
    drawDiagonal(275, 25, 175, 125);
    drawDiagonal(175, 475, 275, 375);
    drawDiagonal(275, 475, 175, 375);

    // River Text
    const river = document.createElement('div');
    river.classList.add('river-text');
    river.innerText = "楚 河           漢 界";
    board.appendChild(river);
}

function drawDiagonal(x1, y1, x2, y2) {
    const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
    const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;

    const line = document.createElement('div');
    line.classList.add('diagonal');
    line.style.width = `${length}px`;
    line.style.left = `${x1}px`;
    line.style.top = `${y1}px`;
    line.style.transform = `rotate(${angle}deg)`;
    board.appendChild(line);
}

function renderBoard() {
    // Remove existing pieces only
    document.querySelectorAll('.piece').forEach(e => e.remove());

    // Render Pieces
    for (let r = 0; r < 10; r++) {
        for (let c = 0; c < 9; c++) {
            const pieceChar = gameState[r][c];
            if (pieceChar !== '.') {
                const piece = document.createElement('div');
                piece.classList.add('piece');
                piece.classList.add(isRed(pieceChar) ? 'red' : 'black');
                piece.innerText = getPieceSymbol(pieceChar);
                piece.style.left = `${c * 50 + 25 - 20}px`;
                piece.style.top = `${r * 50 + 25 - 20}px`;
                piece.dataset.r = r;
                piece.dataset.c = c;

                if (selectedPiece && selectedPiece.r === r && selectedPiece.c === c) {
                    piece.classList.add('selected');
                }

                board.appendChild(piece);
            }
        }
    }
    statusDiv.innerText = hasGameStarted ? (turn === 'red' ? "紅方回合" : "黑方回合") : "玩家先行 (請選擇棋子)";
}

// Add board click listener
board.addEventListener('click', handleBoardClick);

function handleBoardClick(e) {
    // Calculate grid coordinates
    const rect = board.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Each cell is 50x50. The grid intersections are at 25, 75, 125...
    // We want to find the closest intersection.
    // x = c * 50 + 25 => c = (x - 25) / 50
    const c = Math.round((x - 25) / 50);
    const r = Math.round((y - 25) / 50);

    if (c < 0 || c > 8 || r < 0 || r > 9) return;

    handleSquareClick(r, c);
}

function getPieceSymbol(char) {
    const symbols = {
        'r': '車', 'n': '馬', 'b': '象', 'a': '士', 'k': '將', 'c': '砲', 'p': '卒',
        'R': '俥', 'N': '傌', 'B': '相', 'A': '仕', 'K': '帥', 'C': '炮', 'P': '兵'
    };
    return symbols[char] || '';
}

function isRed(char) {
    return char === char.toUpperCase();
}

function handleSquareClick(r, c) {
    const piece = gameState[r][c];

    if (selectedPiece) {
        // Try to move
        if (selectedPiece.r === r && selectedPiece.c === c) {
            // Deselect
            selectedPiece = null;
            renderBoard();
        } else {
            // Move logic
            // If clicking on another own piece, switch selection
            if (piece !== '.' && (isRed(piece) === (turn === 'red') || (!hasGameStarted && isRed(piece) !== (turn === 'red')))) {
                // Special case for first move: if we haven't started, we can switch selection to any piece
                // But wait, if we haven't started, `turn` is 'red'.
                // If I select Black, `isRed(piece)` is false. `turn` is red. Match is false.
                // So the condition `isRed(piece) === (turn === 'red')` handles normal turns.

                // If game hasn't started, we allow selecting ANY piece.
                if (!hasGameStarted || isRed(piece) === (turn === 'red')) {
                    selectedPiece = { r, c };
                    renderBoard();
                }
            } else {
                movePiece(selectedPiece.r, selectedPiece.c, r, c);
            }
        }
    } else {
        // Select
        // Allow selection if it's the correct turn OR if game hasn't started (Player First Rule)
        if (piece !== '.') {
            if (!hasGameStarted || isRed(piece) === (turn === 'red')) {
                selectedPiece = { r, c };
                renderBoard();
            }
        }
    }
}

function movePiece(r1, c1, r2, c2) {
    const piece = gameState[r1][c1];
    const movedColor = isRed(piece) ? 'red' : 'black';

    // Handle First Move Logic
    if (!hasGameStarted) {
        hasGameStarted = true;
        // If player moved Black, next turn is Red (AI).
        // If player moved Red, next turn is Black (AI).
        turn = movedColor === 'red' ? 'black' : 'red';
    } else {
        // Standard turn switch
        turn = turn === 'red' ? 'black' : 'red';
    }

    // Optimistic update
    gameState[r2][c2] = gameState[r1][c1];
    gameState[r1][c1] = '.';
    selectedPiece = null;

    renderBoard();

    // Send to backend
    fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ move: { r1, c1, r2, c2 } })
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'game_over') {
                alert(`遊戲結束! ${data.winner === 'red' ? '紅方' : '黑方'} 獲勝!`);
                statusDiv.innerText = `遊戲結束! ${data.winner === 'red' ? '紅方' : '黑方'} 獲勝!`;
                // Disable board?
                hasGameStarted = false;
                return;
            }

            // Show forbidden warning if any
            showForbiddenWarning(data.forbidden_warning);

            if (data.in_check) {
                statusDiv.innerText = "將軍！";
                document.body.style.backgroundColor = "#ffcccc";
                setTimeout(() => document.body.style.backgroundColor = "#f0e6d2", 600);
            } else {
                statusDiv.innerText = turn === 'red' ? "紅方回合" : "黑方回合";
            }

            if (data.move) {
                // Apply AI move
                const aiMove = data.move;
                const ar1 = aiMove.r1;
                const ac1 = aiMove.c1;
                const ar2 = aiMove.r2;
                const ac2 = aiMove.c2;

                gameState[ar2][ac2] = gameState[ar1][ac1];
                gameState[ar1][ac1] = '.';

                // AI moved. Update turn.
                turn = turn === 'red' ? 'black' : 'red';

                renderBoard();

                // Display Thoughts
                if (data.black_thought) {
                    updateThoughtPanel('black-thought', data.black_thought);
                }
                if (data.red_thought) {
                    updateThoughtPanel('red-thought', data.red_thought);
                }

                // Forbidden move warning
                showForbiddenWarning(data.forbidden_warning);

                // Check status again after AI move (if AI wins or checks)
                if (data.game_over) {
                    statusDiv.innerText = `遊戲結束! ${data.winner === 'red' ? '紅方' : '黑方'} 獲勝!`;
                    hasGameStarted = false;
                } else if (data.in_check) {
                    statusDiv.innerText = "將軍！";
                    document.body.style.backgroundColor = "#ffcccc";
                    setTimeout(() => document.body.style.backgroundColor = "#f0e6d2", 600);
                }
            }
        });
}

function showForbiddenWarning(warning) {
    const el = document.getElementById('forbidden-warning');
    if (!el) return;
    if (!warning) {
        el.classList.remove('show');
        el.innerText = '';
        return;
    }
    const name = warning.name || '禁止著法';
    const advice = warning.advice || '必須變著！';
    const mover = warning.mover === 'red' ? '紅方' : '黑方';
    el.innerText = `⚠ ${name}！${mover}${advice}`;
    el.classList.add('show');
    // auto-hide after 5s
    setTimeout(() => el.classList.remove('show'), 5000);
}

function updateThoughtPanel(elementId, thought) {
    const panel = document.getElementById(elementId);
    if (!panel) return;

    panel.innerHTML = '';

    // Score line
    const scoreLine = document.createElement('div');
    scoreLine.className = 'thought-score';
    const delta = thought.score_change;
    scoreLine.textContent = `分數: ${thought.score}  (${delta >= 0 ? '+' : ''}${delta})`;
    panel.appendChild(scoreLine);

    // Mate-in line
    if (thought.mate_in !== null && thought.mate_in !== undefined) {
        const mateLine = document.createElement('div');
        mateLine.className = 'thought-mate';
        const steps = Math.abs(thought.mate_in);
        mateLine.textContent = thought.mate_in > 0
            ? `擒王在 ${steps} 步內！`
            : `被擒王威脅（${steps} 步）`;
        panel.appendChild(mateLine);
    }

    // PV moves
    if (thought.detailed_pv && thought.detailed_pv.length > 0) {
        const pvDiv = document.createElement('div');
        pvDiv.className = 'thought-pv';
        pvDiv.textContent = '思考路線:';
        panel.appendChild(pvDiv);
        thought.detailed_pv.forEach((step, i) => {
            const line = document.createElement('div');
            line.className = 'thought-pv';
            line.textContent = `  ${i + 1}. ${step.move_str}`;
            panel.appendChild(line);
        });
    }

    // Forbidden warning in panel too
    if (thought.forbidden_warning) {
        const warn = document.createElement('div');
        warn.className = 'thought-trap';
        warn.textContent = `⚠ ${thought.forbidden_warning.name}: ${thought.forbidden_warning.advice}`;
        panel.appendChild(warn);
    }

    // Trap warning (repetition_move)
    if (thought.repetition_move) {
        const warn = document.createElement('div');
        warn.className = 'thought-trap';
        warn.textContent = `※ 此步造成局面重複，AI已改選其他著法`;
        panel.appendChild(warn);
    }
}

resetBtn.addEventListener('click', () => {
    fetch('/reset', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.ai_name) {
                document.getElementById('ai-label').innerText = `當前AI：${data.ai_name}`;
            }
            window.location.reload();
        });
});

// Difficulty selector
document.querySelectorAll('.diff-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const diff = btn.dataset.diff;
        fetch('/set_difficulty', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ difficulty: diff })
        })
        .then(r => r.json())
        .then(data => {
            document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('ai-label').innerText = `當前AI：${data.ai_name}`;
            // Reset board after changing AI
            fetch('/reset', { method: 'POST' }).then(() => window.location.reload());
        });
    });
});

initBoard();
