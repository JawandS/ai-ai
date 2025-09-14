# AI Economics Platform

A simplified platform for running experimental economics games exclusively between AI agents.

## Features

- 🤖 **AI-Only Games**: Designed specifically for AI agent vs AI agent experiments
- � **Public Goods Game**: Classic cooperation experiment implementation
- � **Comprehensive Analytics**: Detailed results and statistics for each game
- 🔧 **Development Mode**: Test games with simulated responses without API calls
- 🚀 **Easy Automation**: Command-line tools for running multiple games
- 📈 **REST API**: Simple API for programmatic game execution

## Currently Supported Games

### Public Goods Game
- **Players**: 4 AI agents
- **Rounds**: 15
- **Duration**: Instant (automated)
- **Concept**: Study cooperation and free-riding behavior between AI models

AI agents receive tokens each round and decide how many to keep (earning $0.20 each) versus invest in a common pool (earning $0.10 each, plus $0.10 for each token invested by others).

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key (optional if using DEV_MODE)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd ai-ai
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure environment**:
   Edit `.env` file with your settings:
   ```env
   OPENAI_API_KEY=your-api-key-here
   DEV_MODE=true  # Use random responses instead of AI
   SECRET_KEY=your-secret-key
   ```

3. **Run the platform**:
   ```bash
   source venv/bin/activate  # If not already activated
   python app.py
   ```

4. **Access the platform**:
   - Open http://localhost:5000 for the admin dashboard
   - Create and monitor AI games through the web interface
   - Use the command-line tool for automated experiments

## Usage

### Web Interface
The platform provides a clean web interface for managing AI games:

- **Dashboard**: Monitor active and completed games
- **Create Games**: Configure AI players and game settings
- **Game Details**: View detailed results and round-by-round data
- **Export Results**: Download game data in JSON format

### Command Line Interface
For automated experiments and batch processing:

```bash
# Run a single game with default settings
python run_ai_game.py

# Run with specific AI models
python run_ai_game.py --models gpt-4o gpt-4o-mini gpt-3.5-turbo gpt-4o

# Run multiple games
python run_ai_game.py --rounds 5

# Custom API endpoint
python run_ai_game.py --url http://your-server:5000
```

### API Endpoints

- `GET /` - Admin dashboard homepage
- `GET /admin` - Games dashboard with statistics
- `GET /games/create` - Game creation interface  
- `GET /games/<game_id>` - View specific game details
- `POST /api/games/run` - Run complete AI game programmatically
- `GET /api/games/<game_id>/status` - Get game status via API

## Project Structure

```
├── app.py                 # Main Flask application with admin routes
├── models.py             # Database models (AI players only)
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
├── run_ai_game.py       # Command-line game runner
├── .env                 # Environment configuration
├── src/
│   └── pg_agent.py      # AI agent logic and OpenAI integration
├── games/
│   ├── __init__.py      # Base game engine
│   └── public_goods.py  # Public Goods Game implementation
└── templates/
    ├── base.html        # Base template with navigation
    ├── index.html       # Admin homepage
    ├── admin_dashboard.html # Games monitoring dashboard
    ├── create_game.html     # Game creation interface
    └── game_details.html    # Game results viewer
```

## Development Mode

Set `DEV_MODE=true` in your `.env` file to:
- Use random number generation instead of OpenAI API calls
- Faster testing and development
- No API costs during development
- Simulate AI agent behavior

## Game Architecture

The platform uses a modular architecture for easy extensibility:

### Base Game Engine
All games inherit from `BaseGameEngine` which provides:
- Move processing framework
- Round management
- Result calculation interface
- Database integration

### Adding New Games

1. Create a new game engine in `games/your_game.py`
2. Inherit from `BaseGameEngine`
3. Implement required methods:
   - `process_move()`
   - `calculate_round_results()`
   - `is_round_complete()`
   - `advance_round()`
   - `finalize_game()`

4. Add routes in `app.py`
5. Create templates for the game interface

## API Endpoints

### Game Management
- `POST /api/games` - Create new game
- `POST /api/games/{id}/join` - Join game
- `GET /api/games/{id}/status` - Get game status
- `POST /api/games/{id}/move` - Submit player move

### WebSocket Events
- `join_game_room` - Join game for real-time updates
- `game_update` - Broadcast game state changes
- `game_state_update` - Receive live updates

## Database Schema

### Core Tables
- **games**: Game instances and configuration
- **players**: Human and AI participants
- **rounds**: Individual game rounds
- **player_moves**: Player decisions within rounds
- **game_results**: Final statistics and rankings

All models support JSON configuration fields for game-specific data.

## AI Integration

The platform integrates with the original `src/pg_agent.py` logic:
- Uses OpenAI's GPT models for AI decision-making
- Maintains conversation history and context
- Supports different AI models and configurations
- Fallback to random decisions if AI fails

## Configuration Options

### Environment Variables
```env
# Required
OPENAI_API_KEY=your-api-key

# Optional
DEV_MODE=true|false
SECRET_KEY=flask-secret-key
DATABASE_URL=sqlite:///economics_platform.db
DEFAULT_GAME_ROUNDS=15
DEFAULT_TOKENS_PER_ROUND=5
```

## Future Extensions

The platform is designed to easily support additional games:

- **Ultimatum Game**: Bargaining and fairness
- **Dictator Game**: Altruistic behavior
- **Trust Game**: Trust and reciprocity
- **Auction Games**: Bidding strategies
- **Market Games**: Trading and price discovery

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your game following the base engine pattern
4. Add tests and documentation
5. Submit a pull request

## License

This project is designed for educational and research purposes in experimental economics.

## Support

For questions or issues:
- Check the admin dashboard for system status
- Review game logs in the database
- Enable DEV_MODE for testing without API costs