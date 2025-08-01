function colorEmoji(color) {
  const map = {
    RED: '🟥',
    GREEN: '🟩',
    BLUE: '🟦',
    DARK_BLUE: '🟦',
    LIGHT_BLUE: '🟦',
    PINK: '🟪',
    ORANGE: '🟧',
    YELLOW: '🟨',
    BROWN: '🟫',
    RAILROAD: '⬜',
    UTILITY: '⬛'
  };
  return map[color] || '';
}

function renderCardText(card) {
  if (card.type && card.type.includes('MONEY')) {
    return `💰$${card.value}M`;
  }
  if (card.type && card.type.includes('PROPERTY')) {
    const emoji = colorEmoji(card.set_color || card.current_color);
    return `${emoji}`;
  }
  if (card.type && card.type.includes('ACTION')) {
    return `🎴${card.name}`;
  }
  return card.name;
}

function renderGame(gameState) {
  const board = document.getElementById('game-board');
  board.innerHTML = '';

  gameState.players.forEach(player => {
    const section = document.createElement('div');
    section.className = 'player';

    const title = document.createElement('h2');
    if (player.name === gameState.current_player_name) {
      title.textContent = `[${player.name}'s Turn]`;
    } else {
      title.textContent = player.name;
    }
    section.appendChild(title);

    const bankLine = document.createElement('div');
    const bankCards = player.banked_cards.map(renderCardText).join(', ');
    bankLine.textContent = `Bank 🏦: ${bankCards}`;
    section.appendChild(bankLine);

    const propLine = document.createElement('div');
    const propSets = Object.values(player.property_sets || {}).map(set => {
      const squares = colorEmoji(set.set_color).repeat(set.cards.length);
      const status = set.is_full_set ? ' - Complete' : ` (${set.cards.length}/${set.number_for_full_set} ${set.set_color})`;
      return `${squares}${status}`;
    }).join(' | ');
    propLine.textContent = `Properties 🏠: ${propSets}`;
    section.appendChild(propLine);

    const handLine = document.createElement('div');
    const handCards = player.hand_cards.map(renderCardText).join(' ');
    handLine.textContent = `Hand 🃏: ${handCards}`;
    section.appendChild(handLine);

    board.appendChild(section);
  });
}

function launchConfetti() {
  const colors = ['#bb0000', '#00bb00', '#0000bb', '#bbbb00', '#bb00bb', '#00bbbb'];
  for (let i = 0; i < 100; i++) {
    const conf = document.createElement('div');
    conf.className = 'confetti';
    conf.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    conf.style.left = Math.random() * 100 + '%';
    conf.style.top = '-10px';
    conf.style.opacity = '1';
    document.body.appendChild(conf);
    const fall = 3000 + Math.random() * 1000;
    conf.animate([
      { transform: `rotate(${Math.random() * 360}deg)`, top: '-10px', opacity: 1 },
      { transform: `rotate(${Math.random() * 360}deg)`, top: '110%', opacity: 0 }
    ], { duration: fall });
    setTimeout(() => conf.remove(), fall);
  }
}

function announceWinner(winner) {
  const modal = document.getElementById('winner-modal');
  const message = document.getElementById('winner-message');
  if (modal && message) {
    message.textContent = `${winner} wins!`;
    modal.style.display = 'flex';
    modal.addEventListener('click', () => {
      modal.style.display = 'none';
    }, { once: true });
    launchConfetti();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (typeof gameData !== 'undefined' && gameData.game_state) {
    renderGame(gameData.game_state);
    if (gameData.winner) {
      announceWinner(gameData.winner);
    }
  }
});
