from flask import Blueprint, render_template, redirect, url_for
from .manager import ManagerGame

main_bp = Blueprint('main', __name__)

GAME = ManagerGame()

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/team')
def team():
    return render_template('team.html', team=GAME.user_team, history=GAME.history)

@main_bp.route('/match')
def match():
    GAME.play_match()
    return redirect(url_for('main.team'))
