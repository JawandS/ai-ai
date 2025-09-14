"""
Experimental Economics Platform
A modular web application for running experimental economics games.
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///economics_platform.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize models
from models import init_models
Game, Player, Round, PlayerMove, GameResult = init_models(db)

# Import game engines after models are initialized
from games.public_goods import PublicGoodsGame

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/games')
def games_list():
    """List of available games"""
    available_games = [
        {
            'id': 'public-goods',
            'name': 'Public Goods Game',
            'description': 'Classic experimental economics game studying cooperation and free-riding behavior',
            'min_players': 4,
            'max_players': 4,
            'estimated_time': '15 minutes'
        }
    ]
    return render_template('games_list.html', games=available_games)

@app.route('/game/<game_type>')
def game_lobby(game_type):
    """Game lobby page"""
    if game_type not in ['public-goods']:
        return "Game type not found", 404
    
    return render_template('game_lobby.html', game_type=game_type)

@app.route('/game/<game_type>/play/<game_id>')
def game_interface(game_type, game_id):
    """Main game playing interface"""
    game = Game.query.filter_by(id=game_id).first()
    if not game:
        return "Game not found", 404
    
    return render_template('game_interface.html', game=game, game_type=game_type)

@app.route('/api/games', methods=['POST'])
def create_game():
    """API endpoint to create a new game"""
    data = request.json
    game_type = data.get('game_type')
    
    if game_type == 'public-goods':
        game = Game(
            id=str(uuid.uuid4()),
            game_type=game_type,
            status='waiting',
            created_at=datetime.utcnow(),
            config={
                'rounds': 15,
                'tokens_per_round': 5,
                'keep_value': 0.20,
                'invest_value': 0.10,
                'social_value': 0.10
            }
        )
        db.session.add(game)
        db.session.commit()
        
        return jsonify({'game_id': game.id, 'status': 'created'})
    
    return jsonify({'error': 'Invalid game type'}), 400

@app.route('/api/games/<game_id>/join', methods=['POST'])
def join_game(game_id):
    """API endpoint to join a game"""
    game = Game.query.filter_by(id=game_id).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    data = request.json
    player_name = data.get('player_name', f'Player_{uuid.uuid4().hex[:8]}')
    
    # Check if game is full
    current_players = Player.query.filter_by(game_id=game_id).count()
    if current_players >= 4:  # Max players for public goods game
        return jsonify({'error': 'Game is full'}), 400
    
    player = Player(
        id=str(uuid.uuid4()),
        game_id=game_id,
        name=player_name,
        is_ai=data.get('is_ai', False),
        joined_at=datetime.utcnow()
    )
    db.session.add(player)
    
    # Start game if we have enough players
    if current_players + 1 >= 4:
        game.status = 'active'
        game.started_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'player_id': player.id,
        'game_status': game.status,
        'players_count': current_players + 1
    })

@app.route('/api/games/<game_id>/move', methods=['POST'])
def make_move(game_id):
    """API endpoint to make a move in the game"""
    game = Game.query.filter_by(id=game_id).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    data = request.json
    player_id = data.get('player_id')
    move = data.get('move')  # For public goods, this is tokens invested
    
    # Validate player
    player = Player.query.filter_by(id=player_id, game_id=game_id).first()
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Create game engine instance
    if game.game_type == 'public-goods':
        game_engine = PublicGoodsGame(game, db)
        result = game_engine.process_move(player_id, move)
        return jsonify(result)
    
    return jsonify({'error': 'Invalid game type'}), 400

@app.route('/api/games/<game_id>/status')
def game_status(game_id):
    """API endpoint to get current game status"""
    game = Game.query.filter_by(id=game_id).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    players = Player.query.filter_by(game_id=game_id).all()
    rounds = Round.query.filter_by(game_id=game_id).order_by(Round.round_number.desc()).all()
    
    return jsonify({
        'game_id': game.id,
        'status': game.status,
        'current_round': game.current_round,
        'players': [{'id': p.id, 'name': p.name, 'is_ai': p.is_ai} for p in players],
        'rounds': [{'round': r.round_number, 'completed': r.completed_at is not None} for r in rounds]
    })

@app.route('/admin')
def admin_dashboard():
    """Administrative dashboard"""
    games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template('admin_dashboard.html', games=games)

# WebSocket events for real-time updates
@socketio.on('join_game_room')
def on_join(data):
    """Handle player joining a game room"""
    game_id = data['game_id']
    join_room(game_id)
    emit('status', {'msg': f'Player joined game {game_id}'}, room=game_id)

@socketio.on('leave_game_room')
def on_leave(data):
    """Handle player leaving a game room"""
    game_id = data['game_id']
    leave_room(game_id)
    emit('status', {'msg': f'Player left game {game_id}'}, room=game_id)

@socketio.on('game_update')
def handle_game_update(data):
    """Broadcast game updates to all players in the room"""
    game_id = data['game_id']
    emit('game_state_update', data, room=game_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Run in development mode
    debug_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=5000)