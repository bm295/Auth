import random
from dataclasses import dataclass, field
from typing import List


# Các hàng cơ bản: Vạn, Sách, Văn (Characters, Bamboo, Dots)
SUITS = ['vạn', 'sách', 'văn']
TILES_PER_SUIT = [str(i) for i in range(1, 10)]

# Các nhóm bài đặc biệt
WINDS = ['đông', 'tây', 'nam', 'bắc']  # Đông Tây Nam Bắc
DRAGONS = ['trung', 'phát', 'bạch']  # Trung Phát Bạch

# Bộ Hoa gồm 4 loại: Mai, Lan, Cúc, Trúc
FLOWERS = ['mai', 'lan', 'cúc', 'trúc']
# Bộ Bốn mùa: Xuân, Hạ, Thu, Đông
SEASONS = ['xuân', 'hạ', 'thu', 'đông']
# Tứ Hoàng (Vương) đánh số 1 đến 4
KINGS = [f'vương{i}' for i in range(1, 5)]
# Tứ Hậu đánh số 1 đến 4
QUEENS = [f'hậu{i}' for i in range(1, 5)]
# Khung Xanh
BLUE_FRAME = ['tổng', 'thùng', 'soọc', 'màn']
# Khung Đỏ
RED_FRAME = ['hoa', 'hỷ', 'nguyên', 'hợp']


def generate_tiles():
    tiles = []
    # 108 quân nạc: ba hàng Vạn, Sách, Văn (1-9, mỗi quân 4 bản)
    for suit in SUITS:
        for value in TILES_PER_SUIT:
            tiles.extend([f"{value}_{suit}" for _ in range(4)])

    # Gió và rồng (mỗi quân 4 bản)
    for wind in WINDS:
        tiles.extend([f"{wind}_gio" for _ in range(4)])
    for dragon in DRAGONS:
        tiles.extend([f"{dragon}_rong" for _ in range(4)])

    # Hoa: Mai, Lan, Cúc, Trúc (mỗi loại 1 quân)
    for flower in FLOWERS:
        tiles.append(f"{flower}_hoa")
    # Các nhóm quân đặc biệt (mỗi quân 1 bản)
    tiles.extend(SEASONS)
    tiles.extend(KINGS)
    tiles.extend(QUEENS)
    tiles.extend(BLUE_FRAME)
    tiles.extend(RED_FRAME)
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

