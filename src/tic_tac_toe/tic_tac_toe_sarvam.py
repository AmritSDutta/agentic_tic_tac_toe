import asyncio
import os
import re
from dataclasses import dataclass, field

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langfuse import get_client
from langfuse import observe
from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from sarvam.chat.model import SarvamChat
from typing_extensions import TypedDict

load_dotenv()

player_one_model = 'minimax-m2.5:cloud'
player_two_model = 'sarvam-m'
os.environ["LANGSMITH_TRACING_V2"] = 'true'
os.environ["LANGSMITH_PROJECT"] = f"[{player_one_model}]_vs_[{player_two_model}]"

# Verify connection
langfuse = get_client()
langfuse_handler = CallbackHandler()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

SYSTEM_PROMPT = """
You are an autonomous Tic-Tac-Toe agent.
GENERAL RULES:
1. You play exactly one move per turn.
2. A move must target a cell that currently contains '.' (empty).
3. Choose the strongest legal move for {{SYMBOL}} only.
4. Never choose a filled cell.
5. Never describe reasoning, analysis, or commentary.


OBJECTIVE:
Maximize your chance of winning and minimize opponent advantage.

WIN-MAXIMIZATION STRATEGY (APPLY IN ORDER):
1. Immediate Win: play any move that wins instantly.
2. Block Opponent: if opponent can win next turn, block that move.
3. Center: take (1,1) if empty.
4. Corners: take any available corner.
5. Best Available: choose the most advantageous remaining empty cell.

RULES:
- You must pick exactly one empty cell.
- Never select a filled square.
- No explanations.

OUTPUT FORMAT (STRICT):
Return only:

    row,col

No other text, punctuation, or formatting.
"""

PLAYER_TEMPLATE = """
make your move.

YOUR SYMBOL: {{SYMBOL}}
BOARD STATE:
{{BOARD}}

OUTPUT FORMAT (STRICT):
Return only:

    row,col

No other text, punctuation, or formatting.
"""


def _parse_coord(s: str) -> tuple[int, int] | None:
    m = re.search(r"(-?\d+)\s*[, ]\s*(-?\d+)", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _valid_move(board, i, j):
    return 0 <= i < 3 and 0 <= j < 3 and board[i][j] == '.'


def _check_winner(b):
    lines = ([(r, c) for c in range(3)] for r in range(3))  # rows generator
    wins = []
    for r in range(3):
        if b[r][0] == b[r][1] == b[r][2] != '.':
            return b[r][0]
    for c in range(3):
        if b[0][c] == b[1][c] == b[2][c] != '.':
            return b[0][c]
    if b[0][0] == b[1][1] == b[2][2] != '.':
        return b[0][0]
    if b[0][2] == b[1][1] == b[2][0] != '.':
        return b[0][2]
    if all(cell != '.' for row in b for cell in row):
        return 'DRAW'
    return None


player_one_agent = ChatOllama(
    model=player_one_model,
    base_url="https://ollama.com",  # Cloud endpoint
    client_kwargs={
        "headers": {"Authorization": "Bearer " + os.getenv("OLLAMA_API_KEY")},
        "timeout": 60.0  # Timeout in seconds
    }
)

player_two_agent = SarvamChat(
    model=player_two_model,
    reasoning_effort="low",
    temperature=0.1,
    max_retry=3,
    wiki_grounding=False,
    top_p=0.9
)


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

    def print_box(self):
        for row in self.board:
            line = " ".join("   " if c == "." else f" {c} " for c in row)
            print(f"|{line}|")

    def valid(self, i, j):
        return 0 <= i < 3 and 0 <= j < 3 and self.board[i][j] == '.'


@observe(name="coordinator_node")
async def coordinator_node(state: State):
    if state.last_player is None:
        return Command(
            update={"board": state.board},
            goto="player_one_node"  # Route directly here as game begis
        )

    i, j = state.moves
    symbol = state.last_player
    # Validate move
    if not _valid_move(state.board, i, j):
        return Command(
            update={"game_status": f"Invalid move {(i, j)} by {symbol}"},
            goto=END
        )

    state.board[i][j] = symbol  # Apply move
    state.print_box()

    result = _check_winner(state.board)  # Check win conditions
    if result == 'DRAW':
        return Command(
            update={"game_status": f"DRAW. Board: {state.board}"},
            goto=END
        )
    if result in ('X', 'O'):
        winner = player_two_model if result == 'X' else player_one_model
        return Command(
            update={"game_status": f"WINNER {winner}. Final: {state.board}"},
            goto=END
        )

    # Determine next player
    next_player = "player_two_node" if state.last_player == 'O' else "player_one_node"
    return Command(
        update={"board": state.board},
        goto=next_player  # All routing logic HERE
    )


def get_token_used(response: AIMessage):
    return response.usage_metadata['total_tokens']


@observe(name=player_one_model, as_type='agent')
async def player_one_node(state: State):
    print(f'{player_one_model} move:')

    prompt = (PLAYER_TEMPLATE
              .replace("{{SYMBOL}}", "O")
              .replace("{{BOARD}}", str(state.board)))
    prompt = SYSTEM_PROMPT + '\n' + prompt
    response: AIMessage = await player_one_agent.ainvoke(prompt)

    coord = _parse_coord(response.content)
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


@observe(name=player_two_model, as_type='agent')
async def player_two_node(state: State):
    print(f'{player_two_model} move:')
    prompt = (PLAYER_TEMPLATE
              .replace("{{SYMBOL}}", "X")
              .replace("{{BOARD}}", str(state.board)))
    prompt = SYSTEM_PROMPT + '\n' + prompt
    # Manually create a span for the LLM call
    response: AIMessage = await player_two_agent.ainvoke(prompt)
    coord = _parse_coord(response.content)
    if coord is None:
        raise ValueError(f"unparsable move: {coord}")

    p2_token_used_till_now = state.player_two_token + get_token_used(response)
    return Command(update={"board": state.board,
                           'last_player': "X",
                           'moves': coord,
                           'player_two_token': p2_token_used_till_now},
                   goto='coordinator_node')


# Build graph
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


# ============ ASYNC EXECUTION ============
async def run_game_async():
    """Execute graph asynchronously"""
    import uuid
    my_trace_id = str(uuid.uuid4())
    result = await graph.ainvoke(
        State(),
        config={
            "callbacks": [langfuse_handler],
            "configurable": {"game_id": my_trace_id},
            "run_id": my_trace_id,
            "run_name": f"[{player_one_model}]_vs_[{player_two_model}]",
        }
    )
    print('*' * 20)
    print(
        f"Final result: {result['game_status']} , "
        f"\n{player_one_model} tokens: {result['player_one_token']}, "
        f"\n{player_two_model} tokens: {result['player_two_token']}"
    )
    print('* ' * 20)
    get_client().shutdown()


# ============ RUN ============
if __name__ == "__main__":
    asyncio.run(run_game_async())
