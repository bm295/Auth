"""
Simple Vietnamese Mahjong game using Pygame.
A human player competes against three AI opponents.
"""

import pygame
import random
import sys

WIDTH, HEIGHT = 800, 600
TILE_W, TILE_H = 80, 60
MARGIN = 5
BOARD_COLOR = (0, 128, 0)
TEXT_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (255, 200, 200)
FPS = 30

# Mapping for Vietnamese tile names
NUMBER_NAMES = {
    '1': 'Nhất',
    '2': 'Nhị',
    '3': 'Tam',
    '4': 'Tứ',
    '5': 'Ngũ',
    '6': 'Lục',
    '7': 'Thất',
    '8': 'Bát',
    '9': 'Cửu',
}

SUIT_NAMES = {
    'B': 'Sách',  # Bamboo
    'C': 'Văn',   # Dots
    'D': 'Vạn',   # Characters
}

def to_vietnamese(tile):
    """Convert an internal tile code like '1B' to a Vietnamese name."""
    if len(tile) != 2:
        return tile
    num, suit = tile[0], tile[1]
    return f"{NUMBER_NAMES.get(num, num)} {SUIT_NAMES.get(suit, suit)}"

class Player:
    """Game participant holding tiles.
    AI players discard randomly.
    """
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.hand = []

    def draw_tile(self, deck):
        if deck:
            self.hand.append(deck.pop())

    def discard_random(self):
        if not self.hand:
            return None
        idx = random.randrange(len(self.hand))
        return self.hand.pop(idx)

class MahjongGame:
    """Main game loop and rendering logic."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Mạt chược')
        self.font = pygame.font.SysFont(None, 24)
        self.clock = pygame.time.Clock()
        self.deck = self.create_tiles()
        self.players = [
            Player('Bạn', True),
            Player('Máy 1'),
            Player('Máy 2'),
            Player('Máy 3'),
        ]
        for _ in range(13):
            for p in self.players:
                p.draw_tile(self.deck)
        self.current = 0
        self.selected_idx = None
        self.running = True
        self.message = 'Chọn quân bài và nhấn SPACE để đánh'

    def create_tiles(self):
        suits = ['B', 'C', 'D']
        numbers = [str(i) for i in range(1, 10)]
        tiles = [n + s for s in suits for n in numbers]
        deck = []
        for t in tiles:
            deck.extend([t] * 4)
        random.shuffle(deck)
        return deck

    def run(self):
        """Main loop processing events and drawing each frame."""
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def handle_events(self):
        """Handle user input and AI turns."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.current_player().is_human:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.selected_idx = self.get_tile_index(event.pos)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if self.selected_idx is not None:
                        self.current_player().hand.pop(self.selected_idx)
                        self.next_turn()
                        self.selected_idx = None
            else:
                pygame.time.delay(500)
                self.current_player().discard_random()
                self.next_turn()

    def current_player(self):
        return self.players[self.current]

    def next_turn(self):
        self.current = (self.current + 1) % len(self.players)
        self.current_player().draw_tile(self.deck)

    def get_tile_index(self, pos):
        """Return index of clicked tile in the player hand."""
        hand = self.current_player().hand
        base_x = (WIDTH - (TILE_W + MARGIN) * len(hand)) // 2
        base_y = HEIGHT - TILE_H - MARGIN
        x, y = pos
        if not (base_y <= y <= base_y + TILE_H):
            return None
        idx = (x - base_x) // (TILE_W + MARGIN)
        if 0 <= idx < len(hand):
            tile_x = base_x + idx * (TILE_W + MARGIN)
            if tile_x <= x <= tile_x + TILE_W:
                return idx
        return None

    def draw(self):
        """Render all game elements."""
        self.screen.fill(BOARD_COLOR)
        self.draw_ai_players()
        self.draw_player_hand()
        msg = self.font.render(self.message, True, TEXT_COLOR)
        self.screen.blit(msg, (10, 10))

    def draw_ai_players(self):
        """Display AI player information."""
        for i, p in enumerate(self.players[1:], start=1):
            text = f"{p.name}: {len(p.hand)} quân"
            img = self.font.render(text, True, TEXT_COLOR)
            if i == 1:
                pos = (10, 50)
            elif i == 2:
                pos = (WIDTH - img.get_width() - 10, 50)
            else:
                pos = (10, 100)
            self.screen.blit(img, pos)

    def draw_player_hand(self):
        """Render the human player's hand."""
        hand = self.players[0].hand
        base_x = (WIDTH - (TILE_W + MARGIN) * len(hand)) // 2
        base_y = HEIGHT - TILE_H - MARGIN
        for i, tile in enumerate(hand):
            rect = pygame.Rect(base_x + i * (TILE_W + MARGIN), base_y, TILE_W, TILE_H)
            color = HIGHLIGHT_COLOR if i == self.selected_idx else (255, 255, 255)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, TEXT_COLOR, rect, 1)
            tile_text = to_vietnamese(tile)
            img = self.font.render(tile_text, True, TEXT_COLOR)
            img_rect = img.get_rect(center=rect.center)
            self.screen.blit(img, img_rect)

def main():
    game = MahjongGame()
    game.run()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
