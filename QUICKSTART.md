# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Setup (One-time)
```bash
# Run the setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Edit `.env` file:
```env
# For development/testing
DEV_MODE=true

# For AI agents (optional if DEV_MODE=true)
OPENAI_API_KEY=your-key-here
```

### 3. Run the Platform
```bash
# Start the server
python app.py

# Open in browser
# http://localhost:5000
```

### 4. Test the Platform
```bash
# Run basic tests
python test_platform.py --basic

# Run full test suite
python test_platform.py
```

## 🎮 Playing the Public Goods Game

### As a Human Player:
1. Go to http://localhost:5000
2. Click "Start Playing" → "Public Goods Game"
3. Enter your name
4. Choose number of AI players (0-3)
5. Click "Create Game"
6. Make investment decisions each round

### Game Rules:
- **Start**: 5 tokens each round
- **Keep**: Earn $0.20 per token kept
- **Invest**: Earn $0.10 per token invested
- **Bonus**: Earn $0.10 per token invested by others
- **Strategy**: Balance personal gain vs. group benefit

### Example Round:
```
You have 5 tokens:
- Keep 2 tokens: $0.40 guaranteed
- Invest 3 tokens: $0.30 + group bonus
- If others invest 10 tokens total: +$1.00
- Your total: $0.40 + $0.30 + $1.00 = $1.70
```

## 🔧 Development Mode

Set `DEV_MODE=true` to:
- ✅ No OpenAI API calls needed
- ✅ AI players use random decisions
- ✅ Faster testing and development
- ✅ No API costs

## 📊 Admin Features

Visit `/admin` to:
- Monitor active games
- View completed game results
- Export data for analysis
- Check system status

## 🤖 AI vs Human Analysis

The platform enables research into:
- Cooperation patterns between AI and humans
- Learning and adaptation over time
- Strategy differences between AI models
- Group dynamics in mixed populations

## 🆘 Troubleshooting

### Common Issues:

**"Import flask could not be resolved"**
- Solution: `pip install -r requirements.txt`

**"Database not found"**
- Solution: Run `python -c "from app import app, db; app.app_context().push(); db.create_all()"`

**"Game not starting"**
- Check: DEV_MODE=true in .env file
- Check: All players have joined (4 total)

**"AI players not working"**
- Check: OPENAI_API_KEY in .env (if DEV_MODE=false)
- Check: Internet connection for API calls

### Reset Everything:
```bash
# Delete database and restart
rm economics_platform.db
python app.py
```

## 📈 Next Steps

1. **Analyze Results**: Use admin dashboard to view game outcomes
2. **Customize Games**: Modify `games/public_goods.py` for different rules
3. **Add New Games**: Create new game engines following the base pattern
4. **Scale Up**: Deploy to cloud for larger experiments

## 💡 Research Ideas

- **Cooperation Evolution**: How does cooperation change over rounds?
- **AI vs Human**: Do AI agents cooperate differently than humans?
- **Group Composition**: How does the AI/human ratio affect outcomes?
- **Strategy Learning**: Can you identify distinct strategies?
- **Information Effects**: How does showing past results affect decisions?

Ready to explore experimental economics? Start with the Public Goods Game and see how cooperation emerges!