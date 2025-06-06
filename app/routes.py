from flask import Blueprint, render_template, redirect, url_for, request
from .game import Game

main_bp = Blueprint('main', __name__)

# Tạo một game toàn cục đơn giản
GAME = Game()


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/game')
def game():
    player = GAME.players[0]
    ai_info = GAME.history[-3:]
    return render_template(
        'game.html',
        hand=player.hand,
        history=ai_info,
        deck_remaining=len(GAME.deck),
    )


@main_bp.route('/draw')
def draw():
    GAME.user_draw()
    return redirect(url_for('main.game'))


@main_bp.route('/discard', methods=['POST'])
def discard():
    tile = request.form.get('tile')
    GAME.user_discard(tile)
    # sau khi người chơi bỏ, đến lượt 3 AI
    for _ in range(3):
        GAME.ai_move()
    return redirect(url_for('main.game'))
