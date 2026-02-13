import pygame
import threading
import time
from typing import Optional


class PygameGame:
    """Pygame-based UI for human vs AI Tic-Tac-Toe game.

    This class runs pygame in the main thread and coordinates with async game logic
    running in a background thread via threading events.
    """

    def __init__(self):
        self.board = [['.' for _ in range(3)] for _ in range(3)]
        self.current_player = None  # Who last played
        self.running = False
        self.lock = threading.Lock()
        self.game_over = False
        self.game_status = ""
        self.screen = None
        self.clock = None
        self.human_turn = False  # Flag indicating if waiting for human input
        self.move_ready = threading.Event()
        self.human_move = None
        self.shutdown_event = threading.Event()
        self.restart_event = threading.Event()

        # Layout constants
        self.SIDEBAR_WIDTH = 250
        self.GAME_START_X = 250
        self.GAME_WIDTH = 600
        self.GAME_START_Y = 100

        # Button regions: (x, y, width, height)
        self.restart_btn = (325, 720, 140, 50)
        self.close_btn = (485, 720, 140, 50)

        # Model selection dropdown
        self.model_options = None  # List of available models
        self.selected_model_index = 0  # Currently selected model index
        self.dropdown_open = False  # Is dropdown menu expanded
        self.dropdown_rect = (20, 20, 200, 40)  # x, y, width, height
        self.dropdown_items_rect = []  # Calculated dynamically when opened
        self.model_lock = threading.Lock()  # Lock for model selection state

        # Radio button for model selection
        self.radio_buttons = []  # List of (label, rect) tuples
        self.radio_button_start_y = 80  # First radio button y position
        self.radio_button_spacing = 40  # Space between radio buttons

        # Score tracking
        self.score = {'AI': 0, 'Human': 0}

    def start(self):
        """Initialize pygame - this must be called from main thread."""
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((850, 800))  # 250 sidebar + 600 game
        pygame.display.set_caption("Tic-Tac-Toe: You (X) vs AI (O)")
        self.clock = pygame.time.Clock()
        self.running = True
        self.model_selection_enabled = True  # Start enabled

    def set_model_options(self, models: list[str], default: str = None):
        """Set available models for dropdown selection."""
        with self.model_lock:
            self.model_options = models
            if default and default in models:
                self.selected_model_index = models.index(default)
            else:
                self.selected_model_index = 0

    def get_selected_model(self) -> str:
        """Get the currently selected model name."""
        with self.model_lock:
            if self.model_options:
                return self.model_options[self.selected_model_index]
            return "gemini"  # Fallback default

    def set_model_selection_enabled(self, enabled: bool):
        """Enable or disable model selection dropdown."""
        print(f"[DEBUG] set_model_selection_enabled({enabled}) called")
        with self.model_lock:
            self.model_selection_enabled = enabled
            if not enabled:
                self.dropdown_open = False  # Close dropdown when disabled
        print(f"[DEBUG] model_selection_enabled is now: {self.model_selection_enabled}")

    def update_score(self, winner: str):
        """Update score when a game completes.

        Args:
            winner: 'AI', 'Human', or 'DRAW'
        """
        with self.model_lock:
            if winner == 'AI':
                self.score['AI'] += 1
            elif winner == 'Human':
                self.score['Human'] += 1
            # DRAW doesn't increment either score

    def get_score(self) -> dict[str, int]:
        """Get current score."""
        with self.model_lock:
            return self.score.copy()

    def reset_score(self):
        """Reset score to zero."""
        with self.model_lock:
            self.score = {'AI': 0, 'Human': 0}

    def run_event_loop(self, stop_event=None):
        """Run the pygame event loop - this blocks and should be in main thread."""
        font = pygame.font.Font(None, 120)
        status_font = pygame.font.Font(None, 48)

        while self.running:
            # Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.shutdown_event.set()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    click_handled = False

                    # Check radio button clicks first (if enabled)
                    if self.model_selection_enabled and self.model_options is not None:
                        for i, (model_name, rect) in enumerate(self.radio_buttons):
                            if (rect[0] <= x <= rect[0] + rect[2] and
                                rect[1] <= y <= rect[1] + rect[3]):
                                with self.model_lock:
                                    self.selected_model_index = i
                                print(f"[DEBUG] Radio button clicked: {model_name} (index {i})")
                                click_handled = True
                                break  # Don't check other radio buttons

                    # Only check buttons if radio button wasn't clicked
                    if not click_handled and self.game_over:
                        # Check button clicks
                        # Restart button
                        if (self.restart_btn[0] <= x <= self.restart_btn[0] + self.restart_btn[2] and
                            self.restart_btn[1] <= y <= self.restart_btn[1] + self.restart_btn[3]):
                            print(f"[DEBUG] Restart button clicked! Selected model: {self.get_selected_model()}")
                            self.restart_event.set()
                        # Close button
                        elif (self.close_btn[0] <= x <= self.close_btn[0] + self.close_btn[2] and
                              self.close_btn[1] <= y <= self.close_btn[1] + self.close_btn[3]):
                            self.restart_event.clear()  # Clear restart to avoid confusion
                            self.running = False
                            self.shutdown_event.set()
                            return
                    else:
                        # Game in progress - check for board clicks
                        col = (x - self.GAME_START_X) // 200
                        row = (y - self.GAME_START_Y) // 200

                        if 0 <= row < 3 and 0 <= col < 3:
                            # Quick check without lock - is cell empty and is it human's turn?
                            with self.lock:
                                cell_empty = self.board[row][col] == '.'
                                is_human_turn = self.human_turn

                            if cell_empty and is_human_turn:
                                # Valid move - record it
                                with self.lock:
                                    self.board[row][col] = 'X'
                                    self.human_move = (row, col)
                                    self.human_turn = False
                                self.move_ready.set()

            # Draw everything
            self.screen.fill((240, 240, 240))

            # Draw Admin Sidebar
            self._draw_sidebar()

            # Draw grid lines (with offset for sidebar)
            for i in range(1, 3):
                x_pos = self.GAME_START_X + i * 200
                pygame.draw.line(self.screen, (0, 0, 0), (x_pos, self.GAME_START_Y), (x_pos, self.GAME_START_Y + 600), 3)
                y_pos = self.GAME_START_Y + i * 200
                pygame.draw.line(self.screen, (0, 0, 0), (self.GAME_START_X, y_pos), (self.GAME_START_X + self.GAME_WIDTH, y_pos), 3)

            # Draw symbols
            with self.lock:
                board_copy = [row[:] for row in self.board]

            for row in range(3):
                for col in range(3):
                    if board_copy[row][col] != '.':
                        color = (200, 0, 0) if board_copy[row][col] == 'X' else (0, 0, 200)
                        text = font.render(board_copy[row][col], True, color)
                        rect = text.get_rect(center=(self.GAME_START_X + col * 200 + 100, self.GAME_START_Y + row * 200 + 100))
                        self.screen.blit(text, rect)

            # Draw status
            with self.lock:
                current_player = self.current_player
                game_over = self.game_over
                game_status = self.game_status
                human_turn = self.human_turn

            if game_over:
                # Draw status/result text first
                status_text = game_status
                status_surf = status_font.render(status_text, True, (0, 0, 0))
                self.screen.blit(status_surf, (self.GAME_START_X + 300 - status_surf.get_width() // 2, 30))

                # Draw buttons on top of everything
                btn_font = pygame.font.Font(None, 36)

                # Restart button (green)
                pygame.draw.rect(self.screen, (50, 150, 50), self.restart_btn, border_radius=10)
                restart_text = btn_font.render("Restart", True, (255, 255, 255))
                restart_rect = restart_text.get_rect(center=(
                    self.restart_btn[0] + self.restart_btn[2] // 2,
                    self.restart_btn[1] + self.restart_btn[3] // 2
                ))
                self.screen.blit(restart_text, restart_rect)

                # Close button (red)
                pygame.draw.rect(self.screen, (200, 50, 50), self.close_btn, border_radius=10)
                close_text = btn_font.render("Close", True, (255, 255, 255))
                close_rect = close_text.get_rect(center=(
                    self.close_btn[0] + self.close_btn[2] // 2,
                    self.close_btn[1] + self.close_btn[3] // 2
                ))
                self.screen.blit(close_text, close_rect)
            elif human_turn:
                status_text = "Your turn (X) - Click a cell"
            elif current_player == 'O':
                status_text = "Your turn (X) - Click a cell"
            else:
                status_text = "AI thinking..."

            if not game_over:
                status_surf = status_font.render(status_text, True, (0, 0, 0))
                self.screen.blit(status_surf, (self.GAME_START_X + 300 - status_surf.get_width() // 2, 50))

            pygame.display.flip()
            self.clock.tick(30)

    def _draw_sidebar(self):
        """Draw the Admin sidebar with model selection and score."""
        # Draw sidebar background
        sidebar_rect = (0, 0, self.SIDEBAR_WIDTH, 800)
        pygame.draw.rect(self.screen, (230, 230, 240), sidebar_rect)
        pygame.draw.line(self.screen, (100, 100, 100), (self.SIDEBAR_WIDTH, 0), (self.SIDEBAR_WIDTH, 800), 2)

        # Draw "Admin" header
        header_font = pygame.font.Font(None, 36)
        header_text = header_font.render("Admin", True, (0, 0, 100))
        self.screen.blit(header_text, (20, 20))

        # Draw "Select AI Model:" label
        label_font = pygame.font.Font(None, 28)
        model_label = label_font.render("Select AI Model:", True, (0, 0, 0))
        self.screen.blit(model_label, (20, 60))

        # Draw radio buttons for each model
        with self.model_lock:
            enabled = self.model_selection_enabled
            selected_idx = self.selected_model_index
            if self.model_options:
                options = self.model_options[:]
            else:
                options = []

        self.radio_buttons = []
        for i, model_name in enumerate(options):
            y_pos = self.radio_button_start_y + i * self.radio_button_spacing

            # Radio button circle
            radio_center = (40, y_pos + 10)
            radio_radius = 10
            pygame.draw.circle(self.screen, (255, 255, 255), radio_center, radio_radius)
            pygame.draw.circle(self.screen, (0, 0, 0), radio_center, radio_radius, 2)

            # Fill if selected
            if i == selected_idx:
                pygame.draw.circle(self.screen, (0, 0, 200), radio_center, radio_radius - 4)

            # Store radio button rect for click detection
            radio_rect = (20, y_pos, 200, 30)
            self.radio_buttons.append((model_name, radio_rect))

            # Draw model name
            model_text = label_font.render(model_name, True, (0, 0, 0) if enabled else (150, 150, 150))
            self.screen.blit(model_text, (60, y_pos))

        # Draw separator line
        separator_y = self.radio_button_start_y + len(options) * self.radio_button_spacing + 20
        pygame.draw.line(self.screen, (150, 150, 150), (20, separator_y), (230, separator_y), 2)

        # Draw "Score:" label
        score_label_y = separator_y + 20
        score_label = label_font.render("Score:", True, (0, 0, 100))
        self.screen.blit(score_label, (20, score_label_y))

        # Draw scores
        with self.model_lock:
            ai_score = self.score['AI']
            human_score = self.score['Human']

        score_font = pygame.font.Font(None, 32)
        ai_text = score_font.render(f"AI: {ai_score}", True, (200, 0, 0))
        human_text = score_font.render(f"Human: {human_score}", True, (0, 0, 200))
        self.screen.blit(ai_text, (30, score_label_y + 40))
        self.screen.blit(human_text, (30, score_label_y + 80))

    def wait_for_human_move(self) -> tuple[int, int]:
        """Block until human makes a move - called from async thread."""
        with self.lock:
            self.human_turn = True
            self.move_ready.clear()
            self.human_move = None

        # Wait for the move (release lock while waiting)
        self.move_ready.wait()

        with self.lock:
            move = self.human_move
            self.human_move = None

        return move

    def update_board(self, board, last_player, game_status=None):
        """Update the display with current board state - called from async thread."""
        with self.lock:
            self.board = [row[:] for row in board]
            self.current_player = last_player
            if game_status is not None:
                self.game_over = True
                self.game_status = game_status

    def reset_game(self):
        """Reset game state for a new game."""
        print(f"[DEBUG] reset_game() called")
        with self.lock:
            self.board = [['.' for _ in range(3)] for _ in range(3)]
            self.current_player = None
            self.game_over = False
            self.game_status = ""
            self.human_turn = False
            self.human_move = None
            self.restart_event.clear()

        # Re-enable model selection on restart
        print(f"[DEBUG] Model selection re-enabled")
        self.set_model_selection_enabled(True)

    def shutdown(self):
        """Clean shutdown."""
        self.running = False
        self.shutdown_event.set()
        pygame.quit()
