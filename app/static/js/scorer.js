let currentPlayer = 1;
let players = [
    { name: 'Spieler 1', score: 501, history: [] },
    { name: 'Spieler 2', score: 501, history: [] }
];
let currentMultiplier = 1;
let currentThrow = 0;

function updateScoreDisplay() {
    document.querySelector(`#player${currentPlayer} .score`).textContent = players[currentPlayer - 1].score;
}

function switchPlayer() {
    document.querySelector(`#player${currentPlayer}`).classList.remove('active');
    currentPlayer = currentPlayer === 1 ? 2 : 1;
    document.querySelector(`#player${currentPlayer}`).classList.add('active');
    currentThrow = 0;
}

function updateMultiplier(multiplier) {
    currentMultiplier = multiplier;
    document.querySelectorAll('.multiplier-buttons button').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${['single', 'double', 'triple'][multiplier - 1]}-btn`).classList.add('active');
}

function submitScore() {
    const buttons = document.querySelectorAll('.number-btn');
    const selectedButton = Array.from(buttons).find(btn => btn.classList.contains('selected'));
    
    if (selectedButton) {
        const value = parseInt(selectedButton.dataset.value);
        const points = value * currentMultiplier;
        const player = players[currentPlayer - 1];
        
        if (player.score - points >= 0) {
            player.score -= points;
            player.history.push(points);
            updateScoreDisplay();
            
            currentThrow++;
            if (currentThrow === 3) {
                switchPlayer();
            }
            
            if (player.score === 0) {
                alert(`${player.name} hat gewonnen!`);
                endGame(currentPlayer);
            }
        } else {
            alert('Ungültiger Wurf!');
        }
        
        selectedButton.classList.remove('selected');
    }
}

function undo() {
    const player = players[currentPlayer - 1];
    if (player.history.length > 0) {
        const lastScore = player.history.pop();
        player.score += lastScore;
        updateScoreDisplay();
        currentThrow--;
        if (currentThrow < 0) {
            switchPlayer();
            currentThrow = 2;
        }
    }
}

function endGame(winnerId) {
    const gameData = {
        player2_id: 2,  // Hier müssen Sie die tatsächliche ID des zweiten Spielers einfügen
        winner_id: winnerId,
        start_score: 501,
        player1_score: players[0].score,
        player2_score: players[1].score
    };

    fetch('/training/scorer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(gameData),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Spiel gespeichert! Spiel-ID: ${data.game_id}`);
        } else {
            alert('Fehler beim Speichern des Spiels');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function updateShortcuts(playerId) {
    fetch(`/api/player-shortcuts/${playerId}`)
        .then(response => response.json())
        .then(data => {
            const shortcutContainer = document.getElementById('shortcuts');
            shortcutContainer.innerHTML = '';
            data.shortcuts.forEach(shortcut => {
                const button = document.createElement('button');
                button.textContent = shortcut;
                button.onclick = () => addScore(shortcut);
                shortcutContainer.appendChild(button);
            });
        });
}

// Event Listeners
document.querySelectorAll('.number-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.number-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
    });
});

document.querySelectorAll('.multiplier-buttons button').forEach(btn => {
    btn.addEventListener('click', () => updateMultiplier(['single', 'double', 'triple'].indexOf(btn.id.split('-')[0]) + 1));
});

document.getElementById('submit-score').addEventListener('click', submitScore);
document.getElementById('undo-btn').addEventListener('click', undo);
document.getElementById('next-player-btn').addEventListener('click', switchPlayer);

// Initialisierung
updateScoreDisplay();

