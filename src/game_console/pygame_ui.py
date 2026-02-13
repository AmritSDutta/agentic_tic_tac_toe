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

        # Button regions: (x, y, width, height)
        self.restart_btn = (150, 720, 140, 50)
        self.close_btn = (310, 720, 140, 50)

    def start(self):
        """Initialize pygame - this must be called from main thread."""
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((600, 800))  # Extra space for buttons
        pygame.display.set_caption("Tic-Tac-Toe: You (X) vs AI (O)")
        self.clock = pygame.time.Clock()
        self.running = True

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

                    if self.game_over:
                        # Check button clicks
                        # Restart button
                        if (self.restart_btn[0] <= x <= self.restart_btn[0] + self.restart_btn[2] and
                            self.restart_btn[1] <= y <= self.restart_btn[1] + self.restart_btn[3]):
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
                        col = x // 200
                        row = (y - 100) // 200

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

            # Draw grid lines
            for i in range(1, 3):
                pygame.draw.line(self.screen, (0, 0, 0), (i * 200, 100), (i * 200, 700), 3)
                pygame.draw.line(self.screen, (0, 0, 0), (0, 100 + i * 200), (600, 100 + i * 200), 3)

            # Draw symbols
            with self.lock:
                board_copy = [row[:] for row in self.board]

            for row in range(3):
                for col in range(3):
                    if board_copy[row][col] != '.':
                        color = (200, 0, 0) if board_copy[row][col] == 'X' else (0, 0, 200)
                        text = font.render(board_copy[row][col], True, color)
                        rect = text.get_rect(center=(col * 200 + 100, row * 200 + 200))
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
                self.screen.blit(status_surf, (300 - status_surf.get_width() // 2, 30))

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
                self.screen.blit(status_surf, (300 - status_surf.get_width() // 2, 50))

            pygame.display.flip()
            self.clock.tick(30)

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
        with self.lock:
            self.board = [['.' for _ in range(3)] for _ in range(3)]
            self.current_player = None
            self.game_over = False
            self.game_status = ""
            self.human_turn = False
            self.human_move = None
            self.restart_event.clear()

    def shutdown(self):
        """Clean shutdown."""
        self.running = False
        self.shutdown_event.set()
        pygame.quit()
