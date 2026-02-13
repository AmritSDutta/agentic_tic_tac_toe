# Agentic Tic-Tac-Toe

An AI-powered Tic-Tac-Toe implementation using LangGraph for orchestration and Langfuse for observability. Two AI agents compete against each other, or play against a human opponent, with each agent using different LLM backends.

## Features

- **Multi-LLM Architecture**: Different LLM backends for each player (Ollama, Sarvam, etc.)
- **LangGraph Orchestration**: Game logic managed through LangGraph state machine
- **Observability**: Full tracing via Langfuse for token usage and performance metrics
- **Interactive UI**: Pygame-based graphical interface for human vs AI games
- **Modular Prompts**: Prompt templates stored separately for easy customization

## Quick Start

### Prerequisites

- Python 3.12+
- Ollama API key for cloud models
- Langfuse account credentials (optional, for tracing)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic_tic_tac_toe

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the `src/` directory:

```env
OLLAMA_API_KEY=your_ollama_api_key_here
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

## Running the Application

### AI vs AI Game

Two AI agents compete against each other:

```bash
python -m src.tic_tac_toe.tic_tac_toe_sarvam
```

Default configuration:
- **Player One (O)**: Ollama `minimax-m2.5:cloud` model
- **Player Two (X)**: Sarvam `sarvam-m` model

### Human vs AI Game

Play against an AI opponent with a graphical interface:

```bash
python -m src.tic_tac_toe.tic_tac_toe_human
```

- **Player One (O)**: AI agent (default: Gemini-3-flash-preview)
- **Player Two (X)**: Human (you!)

## Project Structure

```
agentic_tic_tac_toe/
├── src/
│   ├── llms/
│   │   └── llm_options.py      # LLM initialization and configuration
│   ├── prompts/
│   │   ├── system_prompt.txt   # AI agent system instructions
│   │   └── player_template.txt # Move request template
│   ├── tic_tac_toe/
│   │   ├── core_functions.py   # Game logic (move validation, win detection)
│   │   ├── tic_tac_toe_sarvam.py # AI vs AI game entry point
│   │   └── tic_tac_toe_human.py  # Human vs AI game entry point
│   └── game_console.py         # Pygame UI implementation
├── .env                         # Environment variables (not in repo)
├── CLAUDE.md                    # Project documentation
└── README.md                    # This file
```

## Architecture

### LangGraph State Machine

The game uses a three-node LangGraph state machine:

1. **coordinator_node**: Central game logic hub
   - Validates moves (coordinates and cell emptiness)
   - Applies moves to the board
   - Checks win/draw conditions
   - Routes to the next player or ends the game

2. **player_one_node**: AI agent (plays as 'O')
   - Constructs prompt with board state
   - Invokes LLM agent
   - Parses response for coordinates
   - Tracks token usage

3. **player_two_node**: AI agent or Human (plays as 'X')
   - Same flow as player_one_node for AI
   - In human mode, waits for pygame UI input

### State Management

The `State` dataclass maintains:
- `board`: 3x3 grid with '.' for empty cells
- `moves`: tuple[int, int] for the last move coordinates
- `last_player`: 'X' or 'O' indicating who just moved
- `game_status`: Final result string
- `player_one_token` / `player_two_token`: Cumulative token usage

### Prompt System

Prompts are stored externally in `src/prompts/`:
- `system_prompt.txt`: Instructions for AI agent behavior
- `player_template.txt`: Template for move requests with `{{SYMBOL}}` and `{{BOARD}}` placeholders

## Token Usage Tracking

Each game tracks token consumption per player:

```
Final result: WINNER minimax
minimax tokens: 2,648
sarvam tokens: 11,070
```

This enables comparison of efficiency between different LLM models.

## Customization

### Changing Models

Edit the model variables in the entry point files:

```python
# In tic_tac_toe_sarvam.py or tic_tac_toe_human.py
player_one_model = 'your-model-name'
player_two_model = 'another-model-name'
```

### Modifying AI Behavior

Edit the prompt templates in `src/prompts/`:
- `system_prompt.txt`: Change strategy instructions
- `player_template.txt`: Modify move request format

## Troubleshooting

### Module Import Errors

Always run as a module from the project root:
```bash
python -m src.tic_tac_toe.tic_tac_toe_sarvam
```

### FileNotFoundError for Prompts

Ensure the `src/prompts/` directory contains:
- `system_prompt.txt`
- `player_template.txt`

### Langfuse Authentication

Langfuse authentication failures are non-fatal. The game will run without tracing if credentials are invalid.

## License

[Your License Here]
