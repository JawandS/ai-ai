#!/usr/bin/env python3
"""
Command-line script to run AI economics games
"""

import argparse
import requests
import json
import time
import sys
from typing import List

def run_ai_game(ai_models: List[str] = None, base_url: str = "http://localhost:5000"):
    """Run a complete AI game using the REST API"""
    if ai_models is None:
        ai_models = ["gpt-4o-mini"] * 4
    
    if len(ai_models) != 4:
        print("Error: Exactly 4 AI models required for public goods game")
        return None
    
    # Run the game
    response = requests.post(f"{base_url}/api/games/run", json={
        "game_type": "public-goods",
        "ai_models": ai_models
    })
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error running game: {response.text}")
        return None

def print_game_results(results):
    """Pretty print game results"""
    if not results:
        return
    
    print(f"\n🎮 Game Results (ID: {results['game_id']})")
    print("=" * 60)
    
    # Print final results
    print("\n📊 Final Results:")
    final_results = sorted(results['results']['final_results'], 
                          key=lambda x: x['total_earnings'], reverse=True)
    
    for i, player in enumerate(final_results, 1):
        print(f"{i}. {player['player_name']} ({player['ai_model']}): ${player['total_earnings']:.2f}")
    
    # Print round-by-round summary
    print("\n📈 Round Summary:")
    game_history = results['results']['game_history']
    
    print("Round | Total Invested | Avg Investment | Player Investments")
    print("-" * 65)
    
    for round_data in game_history:
        round_num = round_data['round_number'] + 1
        total_inv = round_data['total_invested']
        avg_inv = round_data['average_investment']
        
        investments = [str(move['tokens_invested']) for move in round_data['moves']]
        investments_str = " | ".join(investments)
        
        print(f"{round_num:5d} | {total_inv:14d} | {avg_inv:14.1f} | {investments_str}")

def main():
    parser = argparse.ArgumentParser(description="Run AI economics games")
    parser.add_argument("--models", nargs=4, default=["gpt-4o-mini"] * 4,
                       help="AI models for the 4 players (default: gpt-4o-mini for all)")
    parser.add_argument("--url", default="http://localhost:5000",
                       help="Base URL for the economics platform API")
    parser.add_argument("--rounds", type=int, default=1,
                       help="Number of games to run")
    
    args = parser.parse_args()
    
    print(f"🚀 Running {args.rounds} AI economics game(s)")
    print(f"🤖 AI Models: {', '.join(args.models)}")
    print(f"🌐 API URL: {args.url}")
    
    for game_num in range(args.rounds):
        if args.rounds > 1:
            print(f"\n--- Game {game_num + 1}/{args.rounds} ---")
        
        try:
            results = run_ai_game(args.models, args.url)
            if results:
                print_game_results(results)
            else:
                print("❌ Game failed to run")
                sys.exit(1)
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to {args.url}")
            print("Make sure the economics platform is running: python app.py")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            sys.exit(1)
        
        if game_num < args.rounds - 1:
            time.sleep(1)  # Brief pause between games

if __name__ == "__main__":
    main()