from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    nodes = [request.host_url.rstrip('/')]
    nodes.extend(current_app.node.peers)
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
