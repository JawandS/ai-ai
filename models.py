"""
Database models for the experimental economics platform
"""

from datetime import datetime
import json

def init_models(db):
    """Initialize models with the database instance"""
    
    class Game(db.Model):
        """Main game table storing game instances"""
        __tablename__ = 'games'
        
        id = db.Column(db.String(36), primary_key=True)
        game_type = db.Column(db.String(50), nullable=False)
        status = db.Column(db.String(20), default='waiting')  # waiting, active, completed, cancelled
        current_round = db.Column(db.Integer, default=0)
        max_rounds = db.Column(db.Integer, default=15)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        started_at = db.Column(db.DateTime)
        completed_at = db.Column(db.DateTime)
        config = db.Column(db.Text)  # JSON string for game-specific configuration
        
        # Relationships
        players = db.relationship('Player', backref='game', lazy=True, cascade='all, delete-orphan')
        rounds = db.relationship('Round', backref='game', lazy=True, cascade='all, delete-orphan')
        results = db.relationship('GameResult', backref='game', lazy=True, cascade='all, delete-orphan')
        
        def get_config(self):
            """Parse config JSON into dictionary"""
            if self.config:
                return json.loads(self.config)
            return {}
        
        def set_config(self, config_dict):
            """Set config from dictionary"""
            self.config = json.dumps(config_dict)

    class Player(db.Model):
        """AI players in games"""
        __tablename__ = 'players'
        
        id = db.Column(db.String(36), primary_key=True)
        game_id = db.Column(db.String(36), db.ForeignKey('games.id'), nullable=False)
        name = db.Column(db.String(100), nullable=False)
        ai_model = db.Column(db.String(50), nullable=False)  # Required AI model name
        position = db.Column(db.Integer)  # Player position in game (0-3 for 4-player games)
        total_earnings = db.Column(db.Float, default=0.0)
        joined_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relationships
        moves = db.relationship('PlayerMove', backref='player', lazy=True, cascade='all, delete-orphan')

    class Round(db.Model):
        """Individual rounds within games"""
        __tablename__ = 'rounds'
        
        id = db.Column(db.String(36), primary_key=True)
        game_id = db.Column(db.String(36), db.ForeignKey('games.id'), nullable=False)
        round_number = db.Column(db.Integer, nullable=False)
        started_at = db.Column(db.DateTime, default=datetime.utcnow)
        completed_at = db.Column(db.DateTime)
        round_data = db.Column(db.Text)  # JSON string for round-specific data
        
        # Relationships
        moves = db.relationship('PlayerMove', backref='round', lazy=True, cascade='all, delete-orphan')
        
        def get_round_data(self):
            """Parse round data JSON into dictionary"""
            if self.round_data:
                return json.loads(self.round_data)
            return {}
        
        def set_round_data(self, data_dict):
            """Set round data from dictionary"""
            self.round_data = json.dumps(data_dict)

    class PlayerMove(db.Model):
        """Individual player moves/decisions within rounds"""
        __tablename__ = 'player_moves'
        
        id = db.Column(db.String(36), primary_key=True)
        round_id = db.Column(db.String(36), db.ForeignKey('rounds.id'), nullable=False)
        player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
        move_data = db.Column(db.Text, nullable=False)  # JSON string for move details
        earnings = db.Column(db.Float)
        submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        def get_move_data(self):
            """Parse move data JSON into dictionary"""
            if self.move_data:
                return json.loads(self.move_data)
            return {}
        
        def set_move_data(self, data_dict):
            """Set move data from dictionary"""
            self.move_data = json.dumps(data_dict)

    class GameResult(db.Model):
        """Final results and statistics for completed games"""
        __tablename__ = 'game_results'
        
        id = db.Column(db.String(36), primary_key=True)
        game_id = db.Column(db.String(36), db.ForeignKey('games.id'), nullable=False)
        player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
        final_earnings = db.Column(db.Float, nullable=False)
        total_investment = db.Column(db.Float)
        avg_investment_per_round = db.Column(db.Float)
        cooperation_rate = db.Column(db.Float)  # Percentage of tokens invested
        performance_rank = db.Column(db.Integer)
        additional_stats = db.Column(db.Text)  # JSON for game-specific statistics
        
        # Relationships
        player = db.relationship('Player', backref='result')
        
        def get_additional_stats(self):
            """Parse additional stats JSON into dictionary"""
            if self.additional_stats:
                return json.loads(self.additional_stats)
            return {}
        
        def set_additional_stats(self, stats_dict):
            """Set additional stats from dictionary"""
            self.additional_stats = json.dumps(stats_dict)
    
    return Game, Player, Round, PlayerMove, GameResult