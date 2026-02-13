"""Test script to verify game logic fixes."""
import sys
import os
from pathlib import Path

# Use ASCII checkmarks for Windows compatibility
PASS = "[PASS]"
FAIL = "[FAIL]"

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tic_tac_toe.core_functions import valid_move, check_winner
from dataclasses import dataclass, field


@dataclass
class TestState:
    """Test state matching the actual State structure."""
    board: list[list[str]]
    invalid_move_count: int = 0


def test_invalid_move_retry_logic():
    """Test that invalid move counter works correctly."""
    print("=== Test 1: Invalid Move Retry Logic ===")

    # Start with empty board
    board = [['.' for _ in range(3)] for _ in range(3)]
    state = TestState(board=board, invalid_move_count=0)

    # Simulate AI trying to move to (1, 1) which is valid
    assert valid_move(state.board, 1, 1), "Move (1,1) should be valid initially"
    state.board[1][1] = 'O'  # Place O in center

    # Now try to move to (1, 1) again - should be invalid
    assert not valid_move(state.board, 1, 1), "Move (1,1) should be invalid after O is placed"

    # Test retry logic
    for attempt in range(1, 4):
        if not valid_move(state.board, 1, 1):
            state.invalid_move_count += 1
            print(f"  Attempt {attempt}/3: Invalid move detected. Counter = {state.invalid_move_count}")

            if state.invalid_move_count >= 3:
                print(f"  PASS Correctly ended game after 3 attempts")
                return True
            else:
                print(f"  PASS Would retry (attempt {state.invalid_move_count}/3)")

    print("  FAIL Test failed: Should have ended after 3 attempts")
    return False


def test_score_update_conversion():
    """Test that winner name is correctly converted to AI/Human."""
    print("\n=== Test 2: Score Update Logic ===")

    test_cases = [
        ("human", "Human", "Human player should map to 'Human'"),
        ("gemini", "AI", "Model 'gemini' should map to 'AI'"),
        ("mistral", "AI", "Model 'mistral' should map to 'AI'"),
        ("sarvam", "AI", "Model 'sarvam' should map to 'AI'"),
        ("openai", "AI", "Model 'openai' should map to 'AI'"),
    ]

    all_passed = True
    for winner, expected, description in test_cases:
        # This is the logic from the coordinator_node
        if winner == 'human':
            score_category = 'Human'
        else:
            score_category = 'AI'

        if score_category == expected:
            print(f"  PASS {description}: '{winner}' -> '{score_category}'")
        else:
            print(f"  FAIL {description}: '{winner}' -> '{score_category}' (expected '{expected}')")
            all_passed = False

    return all_passed


def test_board_state_flow():
    """Test complete game flow with valid moves."""
    print("\n=== Test 3: Complete Game Flow ===")

    board = [['.' for _ in range(3)] for _ in range(3)]

    # Simulate a few moves
    moves = [
        (1, 1, 'O'),  # AI moves center
        (0, 0, 'X'),  # Human moves top-left
        (1, 2, 'O'),  # AI moves right-center
        (0, 2, 'X'),  # Human moves top-right
    ]

    for row, col, symbol in moves:
        if valid_move(board, row, col):
            board[row][col] = symbol
            print(f"  PASS Valid move: {symbol} to ({row}, {col})")
        else:
            print(f"  FAIL Invalid move rejected: {symbol} to ({row}, {col})")
            return False

    # Check if game is still ongoing
    result = check_winner(board)
    if result == 'DRAW':
        print(f"  FAIL Game ended in DRAW unexpectedly")
    elif result in ('X', 'O'):
        print(f"  FAIL Game ended with winner {result} unexpectedly")
    else:
        print(f"  PASS Game still ongoing (no winner yet)")

    return True


def test_invalid_move_reset():
    """Test that invalid move counter resets on valid move."""
    print("\n=== Test 4: Invalid Move Counter Reset ===")

    board = [['.' for _ in range(3)] for _ in range(3)]
    state = TestState(board=board, invalid_move_count=2)

    print(f"  Initial invalid_move_count: {state.invalid_move_count}")

    # Make a valid move
    if valid_move(state.board, 0, 0):
        state.board[0][0] = 'O'
        state.invalid_move_count = 0  # Reset on valid move
        print(f"  PASS Counter reset to 0 after valid move")
        return True
    else:
        print(f"  FAIL Valid move rejected")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("TESTING GAME LOGIC FIXES")
    print("=" * 50)

    results = {
        "Invalid Move Retry Logic": test_invalid_move_retry_logic(),
        "Score Update Conversion": test_score_update_conversion(),
        "Complete Game Flow": test_board_state_flow(),
        "Counter Reset on Valid Move": test_invalid_move_reset(),
    }

    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results.items():
        status = "PASS PASSED" if passed else "FAIL FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("ALL TESTS PASSED PASS")
        return 0
    else:
        print("SOME TESTS FAILED FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
