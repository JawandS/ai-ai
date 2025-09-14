"""
AI Economics Platform
A simplified platform for running experimental economics games between AI agents.
"""

from flask import Flask, request, jsonify, render_template
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

# Initialize models
from models import init_models
Game, Player, Round, PlayerMove, GameResult = init_models(db)

# Import game engines after models are initialized
from games.public_goods import PublicGoodsGame

@app.route('/')
def index():
    """Admin dashboard homepage"""
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    """Administrative dashboard for managing AI games"""
    games = Game.query.order_by(Game.created_at.desc()).limit(20).all()
    
    # Add some summary statistics
    total_games = Game.query.count()
    active_games = Game.query.filter_by(status='active').count()
    completed_games = Game.query.filter_by(status='completed').count()
    
    stats = {
        'total_games': total_games,
        'active_games': active_games,
        'completed_games': completed_games
    }
    
    return render_template('admin_dashboard.html', games=games, stats=stats)

@app.route('/games/create')
def create_game_page():
    """Page for creating new AI games"""
    return render_template('create_game.html')

@app.route('/games/<game_id>')
def game_details(game_id):
    """View details of a specific game"""
    game = Game.query.filter_by(id=game_id).first()
    if not game:
        return "Game not found", 404
    
    players = Player.query.filter_by(game_id=game_id).all()
    rounds = Round.query.filter_by(game_id=game_id).order_by(Round.round_number).all()
    
    return render_template('game_details.html', game=game, players=players, rounds=rounds)

@app.route('/api/status')
def api_status():
    """Simple status page"""
    return jsonify({
        'status': 'AI Economics Platform',
        'available_games': ['public-goods'],
        'endpoints': [
            'POST /api/games - Create a new game',
            'GET /api/games/<game_id>/status - Get game status',
            'POST /api/games/<game_id>/move - Make a move',
            'POST /api/games/run - Run complete game with AI agents'
        ]
    })

@app.route('/api/games', methods=['POST'])
def create_game():
    """API endpoint to create a new game with AI agents"""
    data = request.json
    game_type = data.get('game_type', 'public-goods')
    
    if game_type == 'public-goods':
        game = Game(
            id=str(uuid.uuid4()),
            game_type=game_type,
            status='active',
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            max_rounds=15
        )
        game.set_config({
            'rounds': 15,
            'tokens_per_round': 5,
            'keep_value': 0.20,
            'invest_value': 0.10,
            'social_value': 0.10
        })
        db.session.add(game)
        db.session.commit()
        
        return jsonify({'game_id': game.id, 'status': 'created'})
    
    return jsonify({'error': 'Invalid game type'}), 400

@app.route('/api/games/<game_id>/add_ai_player', methods=['POST'])
def add_ai_player(game_id):
    """API endpoint to add an AI player to a game"""
    game = Game.query.filter_by(id=game_id).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    data = request.json
    ai_model = data.get('ai_model', 'gpt-4o-mini')
    player_name = data.get('player_name', f'AI_{uuid.uuid4().hex[:8]}')
    
    # Check if game is full
    current_players = Player.query.filter_by(game_id=game_id).count()
    if current_players >= 4:  # Max players for public goods game
        return jsonify({'error': 'Game is full'}), 400
    
    player = Player(
        id=str(uuid.uuid4()),
        game_id=game_id,
        name=player_name,
        ai_model=ai_model,
        position=current_players,
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
        'players': [{'id': p.id, 'name': p.name, 'ai_model': p.ai_model} for p in players],
        'rounds': [{'round': r.round_number, 'completed': r.completed_at is not None} for r in rounds]
    })

@app.route('/api/games/run', methods=['POST'])
def run_ai_game():
    """Run a complete game with AI agents"""
    data = request.json
    game_type = data.get('game_type', 'public-goods')
    ai_models = data.get('ai_models', ['gpt-4o-mini'] * 4)
    
    if len(ai_models) != 4:
        return jsonify({'error': 'Exactly 4 AI models required for public goods game'}), 400
    
    # Create game
    game = Game(
        id=str(uuid.uuid4()),
        game_type=game_type,
        status='active',
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        config={
            'rounds': 15,
            'tokens_per_round': 5,
            'keep_value': 0.20,
            'invest_value': 0.10,
            'social_value': 0.10
        }
    )
    db.session.add(game)
    
    # Add AI players
    for i, ai_model in enumerate(ai_models):
        player = Player(
            id=str(uuid.uuid4()),
            game_id=game.id,
            name=f'AI_Player_{i+1}',
            ai_model=ai_model,
            position=i,
            joined_at=datetime.utcnow()
        )
        db.session.add(player)
    
    db.session.commit()
    
    # Run the game
    if game_type == 'public-goods':
        game_engine = PublicGoodsGame(game, db)
        result = game_engine.run_full_game()
        return jsonify({
            'game_id': game.id,
            'status': 'completed',
            'results': result
        })
    
    return jsonify({'error': 'Invalid game type'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Run in development mode
    debug_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)