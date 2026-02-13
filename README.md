# Agentic Tic-Tac-Toe 🎮

> **Disclaimer:** I built this project for my kid to learn programming and have fun playing against AI. If you're here expecting enterprise-grade software, well... you clicked the wrong repo. Enjoy the game!

**Pit your wits against AI agents powered by cutting-edge LLMs.** Watch them think, strategize, and occasionally... make questionable life choices.

Think of it as chess for people with short attention spans, but the AI opponent is actually trying to beat you (not just randomly placing pieces like your coworker's "strategy").

## What Is This?

A Tic-Tac-Toe game where:
- **You play as X** (the noble underdog)
- **AI plays as O** (the silicon-based overlord)
- **Multiple AI models** to choose from (Gemini, GPT, Claude, Sarvam, and more)
- **Score tracking** to prove you're smarter than a machine (until you aren't)

## Quick Start

### Prerequisites

- Python 3.12+ (because we're living in the future)
- API keys for whatever AI models you want to use

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic_tic_tac_toe

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the `src/` directory with your API keys:

```env
# Required for Ollama models
OLLAMA_API_KEY=your_ollama_api_key_here

# Optional (for nerds who like tracing)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

## How to Play

### Launch the Game

```bash
python -m src.tic_tac_toe.tic_tac_toe_human
```

A window will appear. You're now staring at your opponent.

### The UI Guide

The interface is split into two panels:

#### 🎛️ Admin Panel (Left Side)

**Model Selection** - Your choice of opponent:
- ○ zai - For when you're feeling adventurous
- ○ nvidia - Because GPU companies need AI too
- ○ mistral - European sophistication
- ● gemini - Google's finest (default)
- ○ openai - The classic choice
- ○ sarvam - Made in India 🇮🇳
- ○ minimax - Small name, big brain

Click any radio button to select your opponent. Do this **before** the game starts, or after it ends (not during - the AI gets confused when you change opponents mid-game).

**Score Display** - Track your dominance:
```
Score:
AI: 0
Human: 0
```
Every win updates the score. Draws don't count (life is unfair, deal with it).

#### 🎮 Game Board (Right Side)

A classic 3×3 grid. You know how this works:
1. Click any empty cell to place your **X**
2. Wait for the AI to place its **O**
3. Repeat until someone wins or you're both too mediocre to win

**Status messages:**
- `"Your turn (X) - Click a cell"` - Your move! Don't overthink it.
- `"AI thinking..."` - Pray it makes a mistake.
- `"WINNER gemini"` - You lost. Blame the model.
- `"WINNER human"` - Victory! Tell everyone.
- `"DRAW"` - You're equally matched (or equally bad).

**After the game ends:**
- **Restart** - Play again with the same or different model
- **Close** - Rage quit (we won't judge)

## Game Modes

### Human vs AI (You vs The Machine)

```bash
python -m src.tic_tac_toe.tic_tac_toe_human
```

- **You (X)**: Click cells to make moves
- **AI (O)**: Uses whichever model you selected from the Admin panel

### AI vs AI (Battle of the Bots)

```bash
python -m src.tic_tac_toe.tic_tac_toe_sarvam
```

Watch two AIs compete. No UI needed - just console output. It's like watching paint dry, but smarter.

Default matchup:
- **Player One (O)**: Ollama's `minimax-m2.5:cloud`
- **Player Two (X)**: Sarvam's `sarvam-m`

## Tips & Tricks

1. **Start Easy**: Try `minimax` first. It's in the name.
2. **Go Hard**: Switch to `openai` or `gemini` or `zai` if you're feeling confident (or masochistic).
3. **Mix It Up**: Play different models to see which one makes the dumbest moves.
4. **Check the Score**: After 10 games, you'll know if you're smarter than AI (spoiler: probably not).
5. **Rage Quit**: Use the Close button. It's therapeutic.

## How It Works (For the Curious)

Under the hood, this isn't your grandma's Tic-Tac-Toe:

- **LangGraph** orchestrates the game as a state machine (fancy words for "it knows whose turn it is")
- **Each AI model** gets the same prompt but responds differently (personality test, but for code)
- **Token tracking** shows how many tokens each model used (e.g., "Gemini used 2,648 tokens vs Sarvam's 11,070" - efficiency matters!)
- **Langfuse tracing** (optional) lets you spy on exactly what the AI was thinking

## Troubleshooting

### "The AI picked an already-filled cell!"

Sometimes LLMs hallucinate. We've all been there. The game will retry up to 3 times before giving up on you.

### "I can't select a different model!"

Model selection is locked during gameplay. Wait for the game to end, click **Restart**, then choose a new model.

### "The window closed but Python is still running!"

Force quit with Ctrl+C. Sometimes even AI has existential crises.

### "ImportError: No module named 'src'"

You're in the wrong directory. Run from the project root:
```bash
cd agentic_tic_tac_toe  # or whatever you named it
python -m src.tic_tac_toe.tic_tac_toe_human
```

## Fun Facts

- The AI doesn't actually "see" the board - it gets a text representation like `[['.', '.', '.'], ['.', 'X', '.'], ...]` and has to figure out what that means
- Some models will occasionally try to play outside the 3×3 grid (ambition vs reality)
- The human always plays as X because we're generous like that
- No, the AI can't cheat. It follows the same rules as you. Probably.

## Project Structure (For Modders)

```
agentic_tic_tac_toe/
├── src/
│   ├── llms/
│   │   └── llm_options.py      # Where the AI models live
│   ├── prompts/
│   │   ├── system_prompt.txt   # "You are a Tic-Tac-Toe master..."
│   │   └── player_template.txt # "Here's the board, make a move"
│   ├── tic_tac_toe/
│   │   ├── core_functions.py   # Win checking, move validation
│   │   ├── tic_tac_toe_sarvam.py # AI vs AI
│   │   └── tic_tac_toe_human.py  # You vs AI
│   └── game_console/
│       └── pygame_ui.py        # The pretty interface
├── .env                       # Your API keys (don't share!)
└── requirements.txt           # Dependencies
```

Want to add a new model? Edit `src/llms/llm_options.py`. Want to make the AI dumber? Edit `src/prompts/system_prompt.txt`. We won't stop you.

## Credits & Acknowledgments

**Main Game Logic:** Built by me (for my kid - you're welcome!)

**Pygame UI & Test Cases:** Developed with assistance from [Claude Code](https://claude.com/claude-code), Anthropic's AI coding assistant. Because building UIs from scratch is painful, and sometimes you need an AI to help you build an AI game.

---

## License

[Your License Here]

---

**Made with ☕ and frustration at LLMs making questionable moves.**
