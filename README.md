# Mahjong

A minimal four-player Mahjong game built with `pygame`. Tiles are displayed using Vietnamese names such as "Nhất Sách". The human player competes against three computer-controlled opponents.

## Requirements

- Python 3.8+
- `pygame`

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Running the Game

Launch the game with:

```bash
python mahjong_game.py
```

Click on a tile in your hand and press the space bar to discard. The AI players will automatically draw and discard tiles on their turns. The game continues until the tile deck is empty.

Trong giao diện, các quân bài được hiển thị bằng tiếng Việt, ví dụ "Nhất Sách".

## Web Version

Open `web/index.html` in a browser to play the game directly in your browser. The interface and tile names are displayed in Vietnamese. Gameplay is the same: click a tile to select it and press **Đánh** to discard. AI opponents will automatically take their turns.

## Testing and Linting

Run the automated tests with:

```bash
pytest
```

Check code style using flake8:

```bash
flake8 mahjong_game.py
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
