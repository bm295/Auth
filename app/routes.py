from flask import Blueprint, current_app, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Display the demo selector."""
    return render_template('home.html')

@main_bp.route('/voting')
def voting():
    """Render the voting demo page with local node buttons."""
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


@main_bp.route('/client-server')
def client_server():
    """Placeholder page for the client-server model."""
    return render_template('client_server.html')

@main_bp.route('/vote/<node_id>', methods=['POST'])
def vote(node_id):
    current_app.node.record_vote(node_id.upper())
    return redirect(url_for('main.voting'))


@main_bp.route('/slow_vote/<node_id>', methods=['POST'])
def slow_vote(node_id):
    """Record a vote with an artificial delay to demonstrate latency."""
    current_app.node.record_vote_with_latency(node_id.upper(), 2)
    return redirect(url_for('main.voting'))
