from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', resources=current_app.node.resources)

@main_bp.route('/increment/<name>', methods=['POST'])
def increment(name):
    current_app.node.increment(name)
    return redirect(url_for('main.index'))

@main_bp.route('/add', methods=['POST'])
def add_resource():
    name = request.form.get('name', '').strip()
    if name:
        current_app.node.add_resource(name)
    return redirect(url_for('main.index'))

@main_bp.route('/update', methods=['POST'])
def update():
    data = request.get_json() or {}
    resources = data.get('resources')
    if isinstance(resources, dict):
        current_app.node.set_resources(resources)
    return jsonify({'status': 'ok'})
