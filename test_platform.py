#!/usr/bin/env python3
"""
Test script for the Experimental Economics Platform
Tests basic functionality and database setup
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the application
from app import app, db, Game, Player, Round, PlayerMove

class TestPlatform(unittest.TestCase):
    """Test basic platform functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary database
        self.db_fd, app.config['DATABASE_URI'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up test environment"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE_URI'])
    
    def test_homepage(self):
        """Test that homepage loads"""
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Experimental Economics Platform', rv.data)
    
    def test_games_page(self):
        """Test that games page loads"""
        rv = self.app.get('/games')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Available Games', rv.data)
    
    def test_admin_page(self):
        """Test that admin page loads"""
        rv = self.app.get('/admin')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Admin Dashboard', rv.data)
    
    def test_public_goods_lobby(self):
        """Test Public Goods Game lobby"""
        rv = self.app.get('/game/public-goods')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Public Goods Game', rv.data)
    
    def test_create_game_api(self):
        """Test game creation API"""
        with app.app_context():
            rv = self.app.post('/api/games', 
                             json={'game_type': 'public-goods'},
                             content_type='application/json')
            self.assertEqual(rv.status_code, 200)
            
            data = rv.get_json()
            self.assertIn('game_id', data)
            self.assertEqual(data['status'], 'created')
            
            # Verify game was created in database
            game = Game.query.filter_by(id=data['game_id']).first()
            self.assertIsNotNone(game)
            self.assertEqual(game.game_type, 'public-goods')
    
    def test_join_game_api(self):
        """Test joining a game"""
        with app.app_context():
            # First create a game
            rv = self.app.post('/api/games', 
                             json={'game_type': 'public-goods'},
                             content_type='application/json')
            game_data = rv.get_json()
            game_id = game_data['game_id']
            
            # Then join the game
            rv = self.app.post(f'/api/games/{game_id}/join',
                             json={'player_name': 'Test Player'},
                             content_type='application/json')
            self.assertEqual(rv.status_code, 200)
            
            data = rv.get_json()
            self.assertIn('player_id', data)
            self.assertEqual(data['players_count'], 1)
            
            # Verify player was created
            player = Player.query.filter_by(id=data['player_id']).first()
            self.assertIsNotNone(player)
            self.assertEqual(player.name, 'Test Player')
    
    def test_game_status_api(self):
        """Test game status API"""
        with app.app_context():
            # Create a game and add a player
            rv = self.app.post('/api/games', 
                             json={'game_type': 'public-goods'},
                             content_type='application/json')
            game_id = rv.get_json()['game_id']
            
            self.app.post(f'/api/games/{game_id}/join',
                         json={'player_name': 'Test Player'},
                         content_type='application/json')
            
            # Check game status
            rv = self.app.get(f'/api/games/{game_id}/status')
            self.assertEqual(rv.status_code, 200)
            
            data = rv.get_json()
            self.assertEqual(data['game_id'], game_id)
            self.assertEqual(len(data['players']), 1)
            self.assertEqual(data['players'][0]['name'], 'Test Player')
    
    def test_database_models(self):
        """Test that database models work correctly"""
        with app.app_context():
            # Create a game
            game = Game(
                id='test-game-123',
                game_type='public-goods',
                status='waiting'
            )
            db.session.add(game)
            
            # Create a player
            player = Player(
                id='test-player-123',
                game_id='test-game-123',
                name='Test Player',
                is_ai=False
            )
            db.session.add(player)
            
            # Create a round
            round_obj = Round(
                id='test-round-123',
                game_id='test-game-123',
                round_number=1
            )
            db.session.add(round_obj)
            
            # Create a move
            move = PlayerMove(
                id='test-move-123',
                round_id='test-round-123',
                player_id='test-player-123',
                move_data='{"tokens_invested": 3}'
            )
            db.session.add(move)
            
            db.session.commit()
            
            # Test relationships
            game_from_db = Game.query.filter_by(id='test-game-123').first()
            self.assertEqual(len(game_from_db.players), 1)
            self.assertEqual(len(game_from_db.rounds), 1)
            
            player_from_db = Player.query.filter_by(id='test-player-123').first()
            self.assertEqual(player_from_db.game.id, 'test-game-123')
            
            move_from_db = PlayerMove.query.filter_by(id='test-move-123').first()
            move_data = move_from_db.get_move_data()
            self.assertEqual(move_data['tokens_invested'], 3)

def run_basic_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic platform tests...")
    
    # Test imports
    try:
        from app import app, db, Game, Player, Round, PlayerMove
        from games.public_goods import PublicGoodsGame
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test database creation
    try:
        with app.app_context():
            db.create_all()
        print("✅ Database creation successful")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False
    
    # Test environment variables
    dev_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
    print(f"✅ DEV_MODE: {dev_mode}")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✅ OpenAI API key found")
    else:
        print("⚠️  OpenAI API key not found (OK if DEV_MODE=true)")
    
    print("🎉 Basic tests completed successfully!")
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--basic':
        run_basic_tests()
    else:
        # Run full unit tests
        unittest.main()