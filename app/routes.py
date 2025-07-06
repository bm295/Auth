from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    nodes = [request.host_url.rstrip('/')]
    nodes.extend(current_app.node.peers)
    return render_template('index.html', value=current_app.node.value, nodes=nodes)

@main_bp.route('/increment', methods=['POST'])
def increment():
    current_app.node.increment()
    return redirect(url_for('main.index'))

@main_bp.route('/update', methods=['POST'])
def update():
    data = request.get_json() or {}
    value = data.get('value')
    if isinstance(value, int):
        current_app.node.set_value(value)
    return jsonify({'status': 'ok'})
