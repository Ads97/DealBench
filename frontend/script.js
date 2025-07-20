const PROPERTY_COLORS = {
    BROWN: '#A52A2A',
    LIGHT_BLUE: '#ADD8E6',
    PINK: '#FFC0CB',
    ORANGE: '#FFA500',
    RED: '#FF0000',
    YELLOW: '#B8860B',
    GREEN: '#008000',
    DARK_BLUE: '#1E90FF',
    RAILROAD: '#AAAAAA',
    UTILITY: '#CCCCCC'
};
const WILD_PROPERTY_COLOR = '#efefef';

document.addEventListener('DOMContentLoaded', () => {
    fetch('/game_data')
        .then(response => response.json())
        .then(data => {
            const gameState = data.game_state;
            const actionDiv = document.getElementById('action-display');
            if (actionDiv && data.action) {
                actionDiv.textContent = data.action;
            }

            const gameBoard = document.getElementById('game-board');
            gameState.players.forEach(player => {
                const playerSection = document.createElement('div');
                playerSection.className = 'player-section';

                const playerName = document.createElement('h2');
                playerName.className = 'player-name';
                playerName.textContent = player.name;
                playerSection.appendChild(playerName);

                // Render Hand
                const handArea = createCardArea('Hand', player.hand_cards, getCardClass);
                playerSection.appendChild(handArea);

                // Render Bank
                const bankArea = createCardArea('Bank', player.banked_cards, getCardClass);
                playerSection.appendChild(bankArea);

                // Render Properties
                const propertiesArea = document.createElement('div');
                propertiesArea.className = 'card-area';
                const propertiesTitle = document.createElement('h3');
                propertiesTitle.textContent = 'Properties';
                propertiesArea.appendChild(propertiesTitle);

                for (const color in player.property_sets) {
                    const propSet = player.property_sets[color];
                    const propSetDiv = document.createElement('div');
                    propSetDiv.className = 'property-set';
                    if (PROPERTY_COLORS[color]) {
                        propSetDiv.style.borderColor = PROPERTY_COLORS[color];
                    }

                    const propSetTitle = document.createElement('h4');
                    propSetTitle.textContent = `${color} Set`;
                    if (PROPERTY_COLORS[color]) {
                        propSetTitle.style.color = PROPERTY_COLORS[color];
                    }
                    propSetDiv.appendChild(propSetTitle);

                    const propCardContainer = document.createElement('div');
                    propCardContainer.className = 'card-container';
                    propSet.cards.forEach(card => {
                        propCardContainer.appendChild(createCard(card, getCardClass));
                    });
                    propSetDiv.appendChild(propCardContainer);
                    propertiesArea.appendChild(propSetDiv);
                }
                playerSection.appendChild(propertiesArea);

                gameBoard.appendChild(playerSection);
            });
        });
});

function createCardArea(title, cards, cardClassFunc) {
    const area = document.createElement('div');
    area.className = 'card-area';

    const areaTitle = document.createElement('h3');
    areaTitle.textContent = title;
    area.appendChild(areaTitle);

    const cardContainer = document.createElement('div');
    cardContainer.className = 'card-container';
    cards.forEach(card => {
        cardContainer.appendChild(createCard(card, cardClassFunc));
    });
    area.appendChild(cardContainer);

    return area;
}

function createCard(card, cardClassFunc) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card ' + cardClassFunc(card);

    if (card.type.includes('PROPERTY_WILD')) {
        cardDiv.style.backgroundColor = WILD_PROPERTY_COLOR;
        cardDiv.style.borderColor = '#ccc';
    } else if (card.type.includes('PROPERTY')) {
        const colorKey = card.set_color || card.current_color;
        if (colorKey && PROPERTY_COLORS[colorKey]) {
            cardDiv.style.backgroundColor = PROPERTY_COLORS[colorKey];
            cardDiv.style.borderColor = PROPERTY_COLORS[colorKey];
        }
    }

    const cardName = document.createElement('div');
    cardName.style.fontWeight = 'bold';
    cardName.textContent = card.name;
    cardDiv.appendChild(cardName);

    const cardValue = document.createElement('div');
    cardValue.textContent = `Value: ${card.value}`;
    cardDiv.appendChild(cardValue);

    const cardType = document.createElement('div');
    cardType.textContent = `Type: ${card.type}`;
    cardDiv.appendChild(cardType);

    return cardDiv;
}

function getCardClass(card) {
    if (card.type.includes('MONEY')) return 'card-money';
    if (card.type.includes('PROPERTY')) return 'card-property';
    if (card.type.includes('ACTION')) return 'card-action';
    return '';
}
