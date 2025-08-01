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

function playerId(name) {
  return 'player-' + name.replace(/[^a-zA-Z0-9_-]/g, '_');
}

function renderGame(gameState) {
  const board = document.getElementById('game-board');
  board.innerHTML = '';

  const actionsPlayed = gameState.actions_played_in_current_turn || 0;

  gameState.players.forEach(player => {
    const section = document.createElement('div');
    section.className = 'player';
    section.id = playerId(player.name);

    const title = document.createElement('h2');
    if (player.name === gameState.current_player_name) {
      title.textContent = `[${player.name}'s Turn]`;
    } else {
      title.textContent = player.name;
    }
    section.appendChild(title);

    const bankLine = document.createElement('div');
    bankLine.className = 'player-info';
    const bankCards = player.banked_cards.map(renderCardText).join(', ');
    bankLine.textContent = `Bank 🏦: ${bankCards}`;
    section.appendChild(bankLine);

    const propLine = document.createElement('div');
    propLine.className = 'player-info';
    const propSets = Object.values(player.property_sets || {}).map(set => {
      const squares = colorEmoji(set.set_color).repeat(set.cards.length);
      const status = set.is_full_set ? ' - Complete' : ` (${set.cards.length}/${set.number_for_full_set} ${set.set_color})`;
      return `${squares}${status}`;
    }).join(' | ');
    propLine.textContent = `Properties 🏠: ${propSets}`;
    section.appendChild(propLine);

    const actionsLine = document.createElement('div');
    actionsLine.textContent = `Actions played this turn: ${actionsPlayed}`;
    section.appendChild(actionsLine);

    const handLine = document.createElement('div');
    handLine.className = 'player-info';
    const handCards = player.hand_cards.map(renderCardText).join(' ');
    handLine.textContent = `Hand 🃏: ${handCards}`;
    section.appendChild(handLine);

    const reasoningLine = document.createElement('div');
    reasoningLine.className = 'reasoning';
    section.appendChild(reasoningLine);

    const actionLine = document.createElement('div');
    actionLine.className = 'action';
    section.appendChild(actionLine);

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


let winnerAnnounced = false;

function announceWinner(winner) {
  if (winnerAnnounced) return;
  winnerAnnounced = true;
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

function typeText(el, text) {
  const speed = 5; // ms per character
  let idx = 0;
  return new Promise(resolve => {
    function type() {
      if (idx < text.length) {
        el.textContent += text.charAt(idx++);
        setTimeout(type, speed);
      } else {
        resolve();
      }
    }
    type();
  });
}

function delay(ms) {
  return new Promise(res => setTimeout(res, ms));
}

async function loadGameData() {
  try {
    const resp = await fetch('/game_data');
    const data = await resp.json();
    if (data.game_state) {
      renderGame(data.game_state);
    }
    if (data.winner) {
      announceWinner(data.winner);
    }

    const playerName = data.game_state?.current_player_name;
    const reasoning = data.reasoning || '';
    const action = data.action ? `Action: ${data.action}` : '';
    if (playerName) {
      const section = document.getElementById(playerId(playerName));
      if (section) {
        const reasoningEl = section.querySelector('.reasoning');
        const actionEl = section.querySelector('.action');
        if (reasoningEl && actionEl) {
          reasoningEl.textContent = 'Reasoning: ';
          actionEl.textContent = '';
          await typeText(reasoningEl, reasoning);
          actionEl.textContent = action;
          await delay(2000);
          return loadGameData();
        }
      }
    }
    await delay(2000);
    return loadGameData();
  } catch (err) {
    if (typeof gameData !== 'undefined' && gameData.game_state) {
      renderGame(gameData.game_state);
      if (gameData.winner) {
        announceWinner(gameData.winner);
      }
    }
    await delay(2000);
    return loadGameData();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadGameData();
});
