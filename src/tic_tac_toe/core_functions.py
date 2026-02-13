from langchain_core.messages import AIMessage


def parse_coord(s: str) -> tuple[int, int] | None:
    import re
    m = re.search(r"(-?\d+)\s*[, ]\s*(-?\d+)", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def valid_move(board, i, j):
    return 0 <= i < 3 and 0 <= j < 3 and board[i][j] == '.'


def check_winner(b):
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


def get_token_used(response: AIMessage):
    return response.usage_metadata['total_tokens']
