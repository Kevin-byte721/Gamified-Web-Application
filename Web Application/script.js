const gameContainer = document.querySelector('.game-container');
const matchesDisplay = document.getElementById('matches');
const resetButton = document.getElementById('reset-button');

const heroNames = ['rizal', 'bonifacio', 'mabini', 'aguinaldo', 'tandang_sora', 'silang'];
const MAX_MATCHES = heroNames.length; // 6
const POINTS_PER_MATCH = 10;

let cards = [];
let firstCard = null;
let secondCard = null;
let lockBoard = false;
let matchesFound = 0;

// ===============================================
// WIN CELEBRATION & REDIRECT TO TRAINING MODULE
// ===============================================
function handleGameWin() {
    const gamePoints = matchesFound * POINTS_PER_MATCH;

    // Save points from the memory game
    let user = JSON.parse(localStorage.getItem('cyber_student') || '{"score":0, "gamePoints":0}');
    user.gamePoints = gamePoints;     // Keep these for final results/certificate
    user.score = gamePoints;          // Temporary total (will be reset to 0 in index.html)
    localStorage.setItem('cyber_student', JSON.stringify(user));

    // Show win message (defined in game.html)
    const winMessage = document.getElementById('win-message');
    if (winMessage) winMessage.style.display = 'block';
}

// ===============================================
// SHUFFLE & BOARD SETUP
// ===============================================
function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function createBoard() {
    cards = [...heroNames, ...heroNames];
    shuffle(cards);

    gameContainer.innerHTML = '';
    matchesFound = 0;
    matchesDisplay.textContent = '0';

    // Hide win message on reset
    const winMessage = document.getElementById('win-message');
    if (winMessage) winMessage.style.display = 'none';

    cards.forEach(hero => {
        const card = document.createElement('div');
        card.classList.add('card');
        card.dataset.hero = hero;

        const back = document.createElement('div');
        back.classList.add('card-face', 'card-back');

        const front = document.createElement('div');
        front.classList.add('card-face', 'card-front');
        const img = document.createElement('img');
        img.src = `images/${hero}.png`;
        img.alt = hero.charAt(0).toUpperCase() + hero.slice(1).replace('_', ' ');
        front.appendChild(img);

        card.appendChild(back);
        card.appendChild(front);
        card.addEventListener('click', flipCard);
        gameContainer.appendChild(card);
    });
}

// ===============================================
// CARD FLIP LOGIC
// ===============================================
function flipCard() {
    if (lockBoard || this.classList.contains('matched')) return;
    if (this === firstCard) return;

    this.classList.add('flipped');

    if (!firstCard) {
        firstCard = this;
        return;
    }

    secondCard = this;
    lockBoard = true;
    checkForMatch();
}

function checkForMatch() {
    const isMatch = firstCard.dataset.hero === secondCard.dataset.hero;
    isMatch ? disableCards() : unflipCards();
}

function disableCards() {
    firstCard.classList.add('matched');
    secondCard.classList.add('matched');
    firstCard.removeEventListener('click', flipCard);
    secondCard.removeEventListener('click', flipCard);

    matchesFound++;
    matchesDisplay.textContent = matchesFound;

    if (matchesFound === MAX_MATCHES) {
        handleGameWin();
    }

    resetBoard();
}

function unflipCards() {
    setTimeout(() => {
        firstCard.classList.remove('flipped');
        secondCard.classList.remove('flipped');
        resetBoard();
    }, 1000);
}

function resetBoard() {
    [firstCard, secondCard, lockBoard] = [null, null, false];
}

// ===============================================
// INIT
// ===============================================
resetButton.addEventListener('click', createBoard);
createBoard();

function checkWin() {
  if (matchedPairs === totalPairs) {
    // existing win code ...

    // === ADD THIS BLOCK ===
    const USER_ID = "teacher_user_id_1";
    localStorage.setItem(USER_ID, JSON.stringify({
      score: 0,
      current_scenario_index: -1
    }));
    // === END OF BLOCK ===

    setTimeout(() => {
      if (confirm("Congratulations! You completed the memory game!\n\nGo back to the Cybersecurity Module?")) {
        window.location.href = "index.html";   // or whatever the module page is called
      }
    }, 1000);
  }
}
if (firstCard.dataset.hero === secondCard.dataset.hero) {
    // It's a match!
    firstCard.classList.add('matched');
    secondCard.classList.add('matched');
    matchedPairs++;
    // ... rest of win check
}