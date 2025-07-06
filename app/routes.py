from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main page with node addresses for voting."""
    local_url = request.host_url.rstrip('/')

    if current_app.node.peers:
        peer_url = current_app.node.peers[0]
    else:
        peer_url = local_url

    other_id = 'B' if current_app.node.node_id == 'A' else 'A'
    nodes = [
        {"id": current_app.node.node_id, "url": local_url},
        {"id": other_id, "url": peer_url},
    ]

    return render_template(
        'index.html',
        value=current_app.node.value,
        nodes=nodes,
        counts=current_app.node.counts,
    )

@main_bp.route('/vote', methods=['POST'])
def vote():
    current_app.node.record_vote()
    return redirect(url_for('main.index'))

@main_bp.route('/update', methods=['POST'])
def update():
    data = request.get_json() or {}
    counts = data.get('counts')
    if isinstance(counts, dict):
        current_app.node.merge_counts(counts)
    return jsonify({'status': 'ok'})
