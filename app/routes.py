from flask import Blueprint, current_app, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main page with local node buttons."""
    nodes = [
        {"id": "A"},
        {"id": "B"},
    ]

    return render_template(
        'index.html',
        value=current_app.node.value,
        nodes=nodes,
        counts=current_app.node.counts,
    )

@main_bp.route('/vote/<node_id>', methods=['POST'])
def vote(node_id):
    current_app.node.record_vote(node_id.upper())
    return redirect(url_for('main.index'))


@main_bp.route('/slow_vote/<node_id>', methods=['POST'])
def slow_vote(node_id):
    """Record a vote with an artificial delay to demonstrate latency."""
    current_app.node.record_vote_with_latency(node_id.upper(), 2)
    return redirect(url_for('main.index'))
