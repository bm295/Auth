const NUMBER_NAMES = {
    '1': 'Nhất', '2': 'Nhị', '3': 'Tam', '4': 'Tứ', '5': 'Ngũ',
    '6': 'Lục', '7': 'Thất', '8': 'Bát', '9': 'Cửu'
};
const SUIT_NAMES = { 'B': 'Sách', 'C': 'Văn', 'D': 'Vạn' };

function toVietnamese(tile) {
    const num = tile.charAt(0);
    const suit = tile.charAt(1);
    return `${NUMBER_NAMES[num]} ${SUIT_NAMES[suit]}`;
}

class Player {
    constructor(name, isHuman=false) {
        this.name = name;
        this.isHuman = isHuman;
        this.hand = [];
    }

    drawTile(deck) {
        if (deck.length) this.hand.push(deck.pop());
    }

    discardRandom() {
        if (!this.hand.length) return null;
        const idx = Math.floor(Math.random() * this.hand.length);
        return this.hand.splice(idx, 1)[0];
    }
}

class MahjongGame {
    constructor() {
        this.deck = this.createTiles();
        this.players = [
            new Player('Bạn', true),
            new Player('Máy 1'),
            new Player('Máy 2'),
            new Player('Máy 3')
        ];
        for (let i = 0; i < 13; i++) {
            this.players.forEach(p => p.drawTile(this.deck));
        }
        this.current = 0;
        this.selectedIdx = null;
        this.messageEl = document.getElementById('message');
        this.handEl = document.getElementById('player-hand');
        this.aiEl = document.getElementById('ai-players');
        document.getElementById('discard-btn').addEventListener('click', () => this.discardSelected());
        this.render();
    }

    createTiles() {
        const suits = ['B','C','D'];
        const numbers = ['1','2','3','4','5','6','7','8','9'];
        const deck = [];
        suits.forEach(s => numbers.forEach(n => { for (let i=0;i<4;i++) deck.push(n+s); }));
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        return deck;
    }

    currentPlayer() { return this.players[this.current]; }

    nextTurn() {
        this.current = (this.current + 1) % this.players.length;
        this.currentPlayer().drawTile(this.deck);
    }

    discardSelected() {
        if (this.currentPlayer().isHuman && this.selectedIdx !== null) {
            this.currentPlayer().hand.splice(this.selectedIdx, 1);
            this.nextTurn();
            this.selectedIdx = null;
            this.aiTurns();
            this.render();
        }
    }

    aiTurns() {
        while (!this.currentPlayer().isHuman) {
            this.currentPlayer().discardRandom();
            this.nextTurn();
        }
    }

    render() {
        this.aiEl.innerHTML = '';
        this.players.slice(1).forEach(p => {
            const div = document.createElement('div');
            div.className = 'ai-info';
            div.textContent = `${p.name}: ${p.hand.length} quân`;
            this.aiEl.appendChild(div);
        });

        this.handEl.innerHTML = '';
        this.currentPlayer().hand.forEach((tile, idx) => {
            const div = document.createElement('div');
            div.textContent = toVietnamese(tile);
            if (idx === this.selectedIdx) div.classList.add('selected');
            div.addEventListener('click', () => {
                this.selectedIdx = idx;
                Array.from(this.handEl.children).forEach(c => c.classList.remove('selected'));
                div.classList.add('selected');
            });
            this.handEl.appendChild(div);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => new MahjongGame());
