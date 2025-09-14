"""
Game engine package initialization
"""

from abc import ABC, abstractmethod
import uuid
from datetime import datetime

class BaseGameEngine(ABC):
    """Abstract base class for all game engines"""
    
    def __init__(self, game, db):
        self.game = game
        self.db = db
        self.config = game.get_config()
    
    @abstractmethod
    def process_move(self, player_id, move_data):
        """Process a player's move and return result"""
        pass
    
    @abstractmethod
    def calculate_round_results(self, round_moves):
        """Calculate results for all players in a round"""
        pass
    
    @abstractmethod
    def is_round_complete(self, round_id):
        """Check if all players have made their moves for the round"""
        pass
    
    @abstractmethod
    def advance_round(self):
        """Move the game to the next round"""
        pass
    
    @abstractmethod
    def finalize_game(self):
        """Complete the game and calculate final results"""
        pass