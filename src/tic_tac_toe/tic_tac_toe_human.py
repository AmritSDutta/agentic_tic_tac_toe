import warnings
warnings.simplefilter("ignore", UserWarning)
import asyncio
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game_console import PygameGame
from src.tic_tac_toe.core_functions import valid_move, check_winner, parse_coord, get_token_used

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from src.llms.llm_options import get_llm, get_llm_options
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing_extensions import TypedDict

score: dict[str, int] = {
    'AI': 0,
    'Human': 0,
}

load_dotenv()
player_one_model_name = None  # Will be set from dropdown selection
player_two_model = 'human'
os.environ["LANGSMITH_TRACING_V2"] = 'false'


def load_prompt(filename: str) -> str:
    """Load a prompt from the prompts directory."""
    # From src/tic_tac_toe/file.py, go up to src/, then into prompts/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, 'prompts', filename)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


SYSTEM_PROMPT = load_prompt('system_prompt.txt')
PLAYER_TEMPLATE = load_prompt('player_template.txt')

# Initialize pygame game instance
pygame_game = PygameGame()
restart_game_event = threading.Event()
continue_running = True


class Context(TypedDict):
    game_id: str


# Use dataclass for state with default values
@dataclass
class State:
    moves: tuple[int, int] = None
    game_status: str = None
    board: list[list[str]] = field(default_factory=lambda: [['.' for _ in range(3)] for _ in range(3)])
    last_player: str = None
    player_one_token: int = 0
    player_two_token: int = 0
    invalid_move_count: int = 0  # Track consecutive invalid moves

    def print_box(self):
        for row in self.board:
            line = " ".join("   " if c == "." else f" {c} " for c in row)
            print(f"|{line}|")

    def valid(self, i, j):
        return 0 <= i < 3 and 0 <= j < 3 and self.board[i][j] == '.'


async def coordinator_node(state: State):
    if state.last_player is None:
        return Command(
            update={"board": state.board, "invalid_move_count": 0},
            goto="player_one_node"  # Route directly here as game begis
        )

    i, j = state.moves
    symbol = state.last_player
    # Validate move
    if not valid_move(state.board, i, j):
        # Increment invalid move counter
        new_count = state.invalid_move_count + 1
        print(f"[DEBUG] Invalid move ({i}, {j}) by {symbol}. Attempt {new_count}/3")

        if new_count >= 3:
            # After 3 failed attempts, end the game
            return Command(
                update={"game_status": f"Invalid move ({i}, {j}) by {symbol} after 3 attempts"},
                goto=END
            )
        else:
            # Retry - send back to same player for another attempt
            retry_player = "player_one_node" if symbol == 'O' else "player_two_node"
            return Command(
                update={"invalid_move_count": new_count},
                goto=retry_player
            )

    # Valid move - reset invalid move counter
    state.board[i][j] = symbol  # Apply move
    state.print_box()

    # Check win conditions first
    result = check_winner(state.board)

    # Update pygame display with new board state
    game_status = None
    if result == 'DRAW':
        game_status = f"DRAW"
    elif result in ('X', 'O'):
        winner = player_two_model if result == 'X' else player_one_model_name
        game_status = f"WINNER {winner}"
        # Update score - convert to 'AI' or 'Human'
        if winner == 'human':
            pygame_game.update_score('Human')
        else:
            pygame_game.update_score('AI')
        # Re-enable model selection when game ends
        pygame_game.set_model_selection_enabled(True)
    pygame_game.update_board(state.board, state.last_player, game_status)

    if result == 'DRAW':
        print(f'{result}:\n{state.board}')
        return Command(
            update={"game_status": f"DRAW."},
            goto=END
        )
    if result in ('X', 'O'):
        winner = player_two_model if result == 'X' else player_one_model_name
        print(state.board)
        return Command(
            update={"game_status": f"WINNER {winner}"},
            goto=END
        )

    # Determine next player
    next_player = "player_two_node" if state.last_player == 'O' else "player_one_node"
    return Command(
        update={"board": state.board, "invalid_move_count": 0},  # Reset counter on valid move
        goto=next_player  # All routing logic HERE
    )


def get_human_move(state):
    """
    Get human move through pygame UI by waiting for user to click a cell.
    This is a synchronous blocking call that waits for the pygame thread.

    Returns:
        tuple[int, int]: (row, col) coordinates of the selected cell
    """
    return pygame_game.wait_for_human_move()


# ============ ASYNC EXECUTION ============
async def run_single_game():
    """Execute a single game asynchronously with pygame UI"""
    import uuid

    # Get selected model from dropdown and create agent
    selected_model = pygame_game.get_selected_model()
    print(f"[DEBUG] Starting new game with model: {selected_model}")
    player_one_agent = get_llm(selected_model)

    # Update global for coordinator access
    global player_one_model_name
    player_one_model_name = selected_model

    # Set LANGSMITH project dynamically
    os.environ["LANGSMITH_PROJECT"] = f"[{player_one_model_name}]_vs_[{player_two_model}]"

    # Disable model selection during gameplay
    pygame_game.set_model_selection_enabled(False)

    # Define node functions that capture fresh agents via closure
    async def player_one_node(state: State):
        print(f'{player_one_model_name} move:')

        prompt = (PLAYER_TEMPLATE
                  .replace("{{SYMBOL}}", "O")
                  .replace("{{BOARD}}", str(state.board)))
        prompt = SYSTEM_PROMPT + '\n' + prompt
        response: AIMessage = await player_one_agent.ainvoke(prompt)

        coord = parse_coord(response.content)
        if coord is None:
            raise ValueError(f"unparsable move: {response}")
        p1_token_used_till_now = state.player_one_token + get_token_used(response)

        return Command(
            update={"board": state.board,
                    'last_player': "O",
                    'moves': coord,
                    'player_one_token': p1_token_used_till_now
                    },
            goto='coordinator_node'
        )

    async def player_two_node(state: State):
        print(f'{player_two_model} move:')

        # Run blocking human move in thread pool to avoid blocking event loop
        loop = asyncio.get_running_loop()
        coord = await loop.run_in_executor(None, lambda: get_human_move(state))

        if coord is None:
            raise ValueError(f"unparsable move: {coord}")

        p2_token_used_till_now = state.player_two_token + 0
        return Command(update={"board": state.board,
                               'last_player': "X",
                               'moves': coord,
                               'player_two_token': p2_token_used_till_now},
                       goto='coordinator_node')

    # Build fresh graph with new node functions for this game
    builder = (
        StateGraph(State, context_schema=Context)
        .add_node("coordinator_node", coordinator_node)
        .add_node("player_one_node", player_one_node)
        .add_node("player_two_node", player_two_node)
        .add_edge(START, "coordinator_node")
        .add_edge("player_one_node", "coordinator_node")
        .add_edge("player_two_node", "coordinator_node")
    )
    graph = builder.compile()

    # Run the game
    my_trace_id = str(uuid.uuid4())
    result = await graph.ainvoke(
        State(),
        config={
            "configurable": {"game_id": my_trace_id},
            "run_id": my_trace_id,
            "run_name": f"[{player_one_model_name}]_vs_[{player_two_model}]",
        }
    )
    print('*' * 20)
    print(
        f"Final result: {result['game_status']} , "
        f"\n{player_one_model_name} tokens: {result['player_one_token']}, "
        f"\n{player_two_model} tokens: {result['player_two_token']}"
    )
    print('*' * 20)


def run_async_in_thread():
    """Run the async game logic in a separate thread with restart support."""
    global continue_running

    while continue_running:
        try:
            # Use new_event_loop for each game to avoid closed loop error
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_single_game())
            loop.close()

            # Game complete - wait for user action (restart or close)
            if pygame_game.shutdown_event.is_set():
                break

            print(f"[DEBUG] Game ended. Waiting for restart event...")
            pygame_game.restart_event.wait()

            # Check if user wants to restart or close
            if pygame_game.restart_event.is_set() and continue_running:
                print(f"[DEBUG] Restart event detected! Resetting game...")
                pygame_game.reset_game()
                pygame_game.restart_event.clear()
            else:
                break

        except Exception as e:
            print(f"Game error: {e}")
            continue_running = False
            pygame_game.shutdown_event.set()
            break


# ============ RUN ============
if __name__ == "__main__":
    # Initialize pygame in main thread (required for Windows)
    pygame_game.start()

    # Initialize model selection dropdown
    available_models = get_llm_options()
    pygame_game.set_model_options(available_models, default="gemini")

    # Start the async game logic in a background thread
    game_thread = threading.Thread(target=run_async_in_thread, daemon=False)
    game_thread.start()

    # Run pygame event loop in main thread - handles UI and button clicks
    try:
        pygame_game.run_event_loop()
    finally:
        # Signal to stop game
        continue_running = False
        pygame_game.restart_event.set()
        # Wait for game thread to complete
        game_thread.join(timeout=5)
        # Clean shutdown
