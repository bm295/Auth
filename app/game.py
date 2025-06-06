import random
from dataclasses import dataclass, field
from typing import List


SUITS = ['số']  # Tạm thời chỉ dùng một loại số
TILES_PER_SUIT = [str(i) for i in range(1, 10)]


def generate_tiles():
    tiles = []
    for suit in SUITS:
        for value in TILES_PER_SUIT:
            tiles.extend([f"{value}_{suit}" for _ in range(4)])
    return tiles


@dataclass
class Player:
    name: str
    hand: List[str] = field(default_factory=list)

    def draw(self, deck: List[str]):
        if deck:
            tile = deck.pop()
            self.hand.append(tile)
            return tile
        return None

    def discard(self) -> str:
        if not self.hand:
            return ''
        # AI: discard random tile; user will choose separately
        tile = random.choice(self.hand)
        self.hand.remove(tile)
        return tile


class Game:
    def __init__(self):
        self.deck = generate_tiles()
        random.shuffle(self.deck)
        self.players = [Player(name=f'Người chơi {i+1}') for i in range(4)]
        for player in self.players:
            for _ in range(13):
                player.draw(self.deck)
        self.turn = 0  # index of current player
        self.history = []

    @property
    def current_player(self) -> Player:
        return self.players[self.turn]

    def next_turn(self):
        self.turn = (self.turn + 1) % 4

    def ai_move(self):
        player = self.current_player
        player.draw(self.deck)
        discarded = player.discard()
        self.history.append(f"{player.name} bỏ {discarded}")
        self.next_turn()

    def user_draw(self) -> str:
        tile = self.current_player.draw(self.deck)
        self.history.append(f"Bạn rút {tile}")
        return tile

    def user_discard(self, tile: str):
        player = self.current_player
        if tile in player.hand:
            player.hand.remove(tile)
            self.history.append(f"Bạn bỏ {tile}")
        self.next_turn()

