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

    def start(self):
        """Initialize pygame - this must be called from main thread."""
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((600, 700))
        pygame.display.set_caption("Tic-Tac-Toe: You are X")
        self.clock = pygame.time.Clock()
        self.running = True

    def run_event_loop(self, stop_event=None):
        """Run the pygame event loop - this blocks and should be in main thread."""
        font = pygame.font.Font(None, 120)
        status_font = pygame.font.Font(None, 48)

        while self.running:
            # Check if game is complete
            if stop_event and stop_event.is_set():
                time.sleep(3)  # Show final result for 3 seconds
                self.running = False
                break

            # Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.shutdown_event.set()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    x, y = pygame.mouse.get_pos()
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
                status_text = game_status
            elif human_turn:
                status_text = "Your turn (X) - Click a cell"
            elif current_player == 'O':
                status_text = "Your turn (X) - Click a cell"
            else:
                status_text = "AI thinking..."

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

    def shutdown(self):
        """Clean shutdown."""
        self.running = False
        self.shutdown_event.set()
        pygame.quit()
