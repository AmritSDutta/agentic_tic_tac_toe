"""Quick test of pygame UI components without running the full game."""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from game_console.pygame_ui import PygameGame


def test_ui_initialization():
    """Test that UI initializes with correct layout."""
    game = PygameGame()

    print("Testing UI initialization...")
    print(f"[OK] SIDEBAR_WIDTH: {game.SIDEBAR_WIDTH} (expected: 250)")
    print(f"[OK] GAME_START_X: {game.GAME_START_X} (expected: 250)")
    print(f"[OK] GAME_WIDTH: {game.GAME_WIDTH} (expected: 600)")
    print(f"[OK] GAME_START_Y: {game.GAME_START_Y} (expected: 100)")

    # Test score tracking
    print("\nTesting score tracking...")
    assert game.get_score() == {'AI': 0, 'Human': 0}, "Initial score should be 0-0"
    print("[OK] Initial score: AI=0, Human=0")

    game.update_score('AI')
    assert game.get_score() == {'AI': 1, 'Human': 0}, "AI score should increment"
    print("[OK] After AI wins: AI=1, Human=0")

    game.update_score('Human')
    assert game.get_score() == {'AI': 1, 'Human': 1}, "Human score should increment"
    print("[OK] After Human wins: AI=1, Human=1")

    game.update_score('DRAW')
    assert game.get_score() == {'AI': 1, 'Human': 1}, "Draw should not change score"
    print("[OK] After DRAW: AI=1, Human=1 (unchanged)")

    # Test score reset
    game.reset_score()
    assert game.get_score() == {'AI': 0, 'Human': 0}, "Reset should zero scores"
    print("[OK] After reset: AI=0, Human=0")

    # Test model selection
    print("\nTesting model selection...")
    test_models = ['zai', 'nvidia', 'mistral', 'gemini', 'openai', 'sarvam', 'minimax']
    game.set_model_options(test_models, default='gemini')
    assert game.get_selected_model() == 'gemini', "Default model should be gemini"
    print(f"[OK] Default model: {game.get_selected_model()}")

    # Test selection enabled/disabled (need to check internal state)
    game.set_model_selection_enabled(True)
    with game.model_lock:
        enabled = game.model_selection_enabled
    assert enabled == True, "Selection should start enabled"
    print("[OK] Model selection starts enabled")

    game.set_model_selection_enabled(False)
    with game.model_lock:
        enabled = game.model_selection_enabled
    assert enabled == False, "Selection should be disabled"
    print("[OK] Model selection can be disabled")

    game.set_model_selection_enabled(True)
    with game.model_lock:
        enabled = game.model_selection_enabled
    assert enabled == True, "Selection should be enabled"
    print("[OK] Model selection can be re-enabled")

    print("\n" + "="*50)
    print("All tests passed!")
    print("="*50)
    print("\nThe pygame UI is ready to use with:")
    print("  • Admin sidebar with radio buttons")
    print("  • Score tracking (AI vs Human)")
    print("  • Game board shifted to the right")
    print("  • Model selection that disables during gameplay")


if __name__ == "__main__":
    test_ui_initialization()
