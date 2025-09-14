"""
Public Goods Game implementation
Based on the logic from src/pg_agent.py
"""

import json
import uuid
import random
import os
from datetime import datetime
from games import BaseGameEngine
from src.pg_agent import Agent, gpt_discourse

class PublicGoodsGame(BaseGameEngine):
    """Public Goods Game engine implementation"""
    
    def __init__(self, game, db):
        super().__init__(game, db)
        self.tokens_per_round = self.config.get('tokens_per_round', 5)
        self.keep_value = self.config.get('keep_value', 0.20)
        self.invest_value = self.config.get('invest_value', 0.10)
        self.social_value = self.config.get('social_value', 0.10)
        self.max_rounds = self.config.get('rounds', 15)
        self.dev_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
    
    def process_move(self, player_id, move_data):
        """Process a player's investment decision"""
        # Import here to avoid circular imports
        from app import Game, Player, Round, PlayerMove
        
        # Validate player
        player = Player.query.filter_by(id=player_id, game_id=self.game.id).first()
        if not player:
            return {'error': 'Player not found'}
        
        # Get or create current round
        current_round = Round.query.filter_by(
            game_id=self.game.id, 
            round_number=self.game.current_round
        ).first()
        
        if not current_round:
            current_round = Round(
                id=str(uuid.uuid4()),
                game_id=self.game.id,
                round_number=self.game.current_round
            )
            self.db.session.add(current_round)
        
        # Parse move data
        if isinstance(move_data, dict):
            tokens_invested = move_data.get('tokens', 0)
        else:
            tokens_invested = int(move_data)
        
        # Validate investment
        if tokens_invested < 0 or tokens_invested > self.tokens_per_round:
            return {'error': f'Invalid investment. Must be between 0 and {self.tokens_per_round}'}
        
        # Check if player already made a move this round
        existing_move = PlayerMove.query.filter_by(
            round_id=current_round.id,
            player_id=player_id
        ).first()
        
        if existing_move:
            return {'error': 'Player has already made a move this round'}
        
        # Create player move
        move = PlayerMove(
            id=str(uuid.uuid4()),
            round_id=current_round.id,
            player_id=player_id,
            move_data=json.dumps({
                'tokens_invested': tokens_invested,
                'tokens_kept': self.tokens_per_round - tokens_invested
            })
        )
        self.db.session.add(move)
        self.db.session.commit()
        
        # Check if round is complete
        if self.is_round_complete(current_round.id):
            self.calculate_round_results(current_round.id)
            
            # Check if game is complete
            if self.game.current_round >= self.max_rounds - 1:
                self.finalize_game()
                return {'status': 'game_complete', 'round_complete': True}
            else:
                self.advance_round()
                return {'status': 'round_complete', 'next_round': self.game.current_round}
        
        return {'status': 'move_accepted', 'waiting_for_others': True}
    
    def calculate_round_results(self, round_id):
        """Calculate earnings for all players in the round"""
        # Import here to avoid circular imports
        from app import PlayerMove, Player
        
        # Get all moves for this round
        moves = PlayerMove.query.filter_by(round_id=round_id).all()
        
        # Calculate total investment
        total_invested = 0
        move_data_list = []
        
        for move in moves:
            move_info = move.get_move_data()
            tokens_invested = move_info['tokens_invested']
            total_invested += tokens_invested
            move_data_list.append({
                'move': move,
                'player_id': move.player_id,
                'tokens_invested': tokens_invested,
                'tokens_kept': move_info['tokens_kept']
            })
        
        # Calculate earnings for each player
        for move_info in move_data_list:
            tokens_kept = move_info['tokens_kept']
            tokens_invested = move_info['tokens_invested']
            
            # Earnings calculation based on Public Goods Game rules
            earnings_from_kept = tokens_kept * self.keep_value
            earnings_from_own_investment = tokens_invested * self.invest_value
            earnings_from_others = total_invested * self.social_value
            
            total_earnings = earnings_from_kept + earnings_from_own_investment + earnings_from_others
            
            # Update move with earnings
            move_info['move'].earnings = total_earnings
            
            # Update player's total earnings
            player = Player.query.filter_by(id=move_info['player_id']).first()
            if player:
                player.total_earnings += total_earnings
        
        # Mark round as completed
        from app import Round
        round_obj = Round.query.filter_by(id=round_id).first()
        if round_obj:
            round_obj.completed_at = datetime.utcnow()
            round_obj.set_round_data({
                'total_invested': total_invested,
                'average_investment': total_invested / len(moves) if moves else 0
            })
        
        self.db.session.commit()
    
    def is_round_complete(self, round_id):
        """Check if all players have made their moves"""
        # Import here to avoid circular imports
        from app import PlayerMove, Player
        
        # Get total players in the game
        total_players = Player.query.filter_by(game_id=self.game.id).count()
        
        # Get moves for this round
        moves_count = PlayerMove.query.filter_by(round_id=round_id).count()
        
        return moves_count >= total_players
    
    def advance_round(self):
        """Move to the next round"""
        self.game.current_round += 1
        self.db.session.commit()
    
    def finalize_game(self):
        """Complete the game and calculate final results"""
        # Import here to avoid circular imports
        from app import GameResult, Player, PlayerMove, Round
        
        self.game.status = 'completed'
        self.game.completed_at = datetime.utcnow()
        
        # Calculate final results for each player
        players = Player.query.filter_by(game_id=self.game.id).all()
        
        # Sort players by total earnings for ranking
        players_sorted = sorted(players, key=lambda p: p.total_earnings, reverse=True)
        
        for rank, player in enumerate(players_sorted, 1):
            # Calculate additional statistics
            player_moves = PlayerMove.query.join(Round).filter(
                Round.game_id == self.game.id,
                PlayerMove.player_id == player.id
            ).all()
            
            total_investment = sum(
                move.get_move_data()['tokens_invested'] for move in player_moves
            )
            avg_investment = total_investment / len(player_moves) if player_moves else 0
            cooperation_rate = (total_investment / (self.max_rounds * self.tokens_per_round)) * 100
            
            # Create final result record
            result = GameResult(
                id=str(uuid.uuid4()),
                game_id=self.game.id,
                player_id=player.id,
                final_earnings=player.total_earnings,
                total_investment=total_investment,
                avg_investment_per_round=avg_investment,
                cooperation_rate=cooperation_rate,
                performance_rank=rank
            )
            self.db.session.add(result)
        
        self.db.session.commit()
    
    def generate_ai_move(self, player, round_number, game_history):
        """Generate AI player move using the original agent logic or dev mode"""
        if self.dev_mode:
            # In development mode, use random numbers
            return random.randint(0, self.tokens_per_round)
        
        # Use the original agent logic from src/pg_agent.py
        try:
            agent = Agent(
                model='gpt-4o-2024-08-06',
                game_id=self.game.id,
                user_id=player.id
            )
            
            # Build investment prompt using the existing logic
            message = agent.build_investment_prompt(round_number)
            
            # Get response from AI
            response = agent.ask(message)
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*?"tokens".*?:\s*(\d+).*?\}', response)
            if json_match:
                tokens = int(json_match.group(1))
                return max(0, min(tokens, self.tokens_per_round))
            else:
                # Fallback to random if parsing fails
                return random.randint(0, self.tokens_per_round)
                
        except Exception as e:
            print(f"Error generating AI move: {e}")
            # Fallback to random move
            return random.randint(0, self.tokens_per_round)
    
    def process_ai_moves(self, round_id):
        """Process moves for all AI players in the current round"""
        # Import here to avoid circular imports
        from app import Player, Round, PlayerMove
        
        # Get AI players who haven't moved yet
        round_obj = Round.query.filter_by(id=round_id).first()
        if not round_obj:
            return
        
        ai_players = Player.query.filter_by(game_id=self.game.id).all()  # All players are AI now
        
        for player in ai_players:
            # Check if AI player already made a move
            existing_move = PlayerMove.query.filter_by(
                round_id=round_id,
                player_id=player.id
            ).first()
            
            if not existing_move:
                # Generate AI move
                ai_investment = self.generate_ai_move(player, self.game.current_round, [])
                
                # Create AI move
                move = PlayerMove(
                    id=str(uuid.uuid4()),
                    round_id=round_id,
                    player_id=player.id,
                    move_data=json.dumps({
                        'tokens_invested': ai_investment,
                        'tokens_kept': self.tokens_per_round - ai_investment
                    })
                )
                self.db.session.add(move)
        
        self.db.session.commit()
    
    def run_full_game(self):
        """Run a complete game with all AI players"""
        # Import here to avoid circular imports
        from app import Player, Round, PlayerMove, GameResult
        
        # Get all players (all are AI)
        players = Player.query.filter_by(game_id=self.game.id).all()
        if len(players) != 4:
            return {'error': 'Game requires exactly 4 AI players'}
        
        game_results = []
        
        # Run all rounds
        for round_num in range(self.max_rounds):
            self.game.current_round = round_num
            
            # Create round
            current_round = Round(
                id=str(uuid.uuid4()),
                game_id=self.game.id,
                round_number=round_num
            )
            self.db.session.add(current_round)
            self.db.session.commit()
            
            # Generate moves for all AI players
            round_moves = []
            for player in players:
                ai_investment = self.generate_ai_move(player, round_num, game_results)
                
                move = PlayerMove(
                    id=str(uuid.uuid4()),
                    round_id=current_round.id,
                    player_id=player.id,
                    move_data=json.dumps({
                        'tokens_invested': ai_investment,
                        'tokens_kept': self.tokens_per_round - ai_investment
                    })
                )
                self.db.session.add(move)
                round_moves.append({
                    'player_id': player.id,
                    'player_name': player.name,
                    'tokens_invested': ai_investment,
                    'tokens_kept': self.tokens_per_round - ai_investment
                })
            
            self.db.session.commit()
            
            # Calculate round results
            self.calculate_round_results(current_round.id)
            
            # Store round results for history
            total_invested = sum(move['tokens_invested'] for move in round_moves)
            round_result = {
                'round_number': round_num,
                'moves': round_moves,
                'total_invested': total_invested,
                'average_investment': total_invested / len(players)
            }
            game_results.append(round_result)
        
        # Finalize game
        self.game.status = 'completed'
        self.game.completed_at = datetime.utcnow()
        self.finalize_game()
        
        # Get final results
        final_results = []
        updated_players = Player.query.filter_by(game_id=self.game.id).all()
        for player in updated_players:
            final_results.append({
                'player_id': player.id,
                'player_name': player.name,
                'ai_model': player.ai_model,
                'total_earnings': player.total_earnings,
                'position': player.position
            })
        
        return {
            'game_id': self.game.id,
            'total_rounds': self.max_rounds,
            'game_history': game_results,
            'final_results': final_results
        }