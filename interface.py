import pygame
import sys
import os
import time
from move import Move
from board import Board
from engine import Engine


class Interface:
    def __init__(self, board: Board, engine: Engine):
        # --- Constants ---
        self.WINDOW_SIZE = 900
        self.SQUARE_SIZE = 800
        self.BOARD_SIZE = self.SQUARE_SIZE // 8
        self.FPS = 60

        self.WHITE = (230, 230, 230)
        self.BLACK = (20, 20, 20)
        self.CONTRAST = (80, 10, 140)

        self.running = True
        self.board = board
        self.engine = engine
        self.update_position()

        # --- Drag and Drop State ---
        self.selected_piece = None # Piece being dragged
        self.selected_sq_idx = None # Original square

        # --- Pygame init ---
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont('Lato', 18, bold = True)
        os.environ['SDL_VIDEO_WINDOW_POS'] = "50, 50"
        self.screen = pygame.display.set_mode(
            (self.WINDOW_SIZE, self.WINDOW_SIZE)
        )
        pygame.display.set_caption("Chess Engine Interface")
        self.clock = pygame.time.Clock()

        # --- Precompute board position ---
        self.board_x = (self.WINDOW_SIZE - self.SQUARE_SIZE) // 2
        self.board_y = (self.WINDOW_SIZE - self.SQUARE_SIZE) // 2

        # --- Load assets once ---
        self._load_piece_images()

        # --- Draw static board once ---
        self._create_board_surface()

    def update_position(self):
        """Synchronize local position with the Board object FEN."""
        self.position = self.board.fen.split()[0]

    # ------------------ Assets ------------------

    def _load_piece_images(self):
        self.piece_images = {
            'P': pygame.image.load('assets/wP.svg').convert_alpha(),
            'N': pygame.image.load('assets/wN.svg').convert_alpha(),
            'B': pygame.image.load('assets/wB.svg').convert_alpha(),
            'R': pygame.image.load('assets/wR.svg').convert_alpha(),
            'Q': pygame.image.load('assets/wQ.svg').convert_alpha(),
            'K': pygame.image.load('assets/wK.svg').convert_alpha(),
            'p': pygame.image.load('assets/bP.svg').convert_alpha(),
            'n': pygame.image.load('assets/bN.svg').convert_alpha(),
            'b': pygame.image.load('assets/bB.svg').convert_alpha(),
            'r': pygame.image.load('assets/bR.svg').convert_alpha(),
            'q': pygame.image.load('assets/bQ.svg').convert_alpha(),
            'k': pygame.image.load('assets/bK.svg').convert_alpha(),
        }

        # Pre-scale images
        for key in self.piece_images:
            self.piece_images[key] = pygame.transform.smoothscale(
                self.piece_images[key],
                (self.BOARD_SIZE, self.BOARD_SIZE)
            )

    # ------------------ Graphical board ------------------

    def _create_board_surface(self):
        # Static background
        self.board_surface = pygame.Surface((self.WINDOW_SIZE, self.WINDOW_SIZE))
        self.board_surface.fill(self.BLACK)

        for row in range(8):
            for col in range(8):
                color = self.WHITE if (row + col) % 2 == 0 else self.CONTRAST
                rect = (
                    self.board_x + col * self.BOARD_SIZE,
                    self.board_y + row * self.BOARD_SIZE,
                    self.BOARD_SIZE,
                    self.BOARD_SIZE,
                )
                pygame.draw.rect(self.board_surface, color, rect)

                text_value = str(row * 8 + col)
                text_color = (50, 50, 50) 
                text_surf = self.font.render(text_value, True, text_color)
                
                text_rect = text_surf.get_rect(center = (
                    rect[0] + self.BOARD_SIZE // 2,
                    rect[1] + self.BOARD_SIZE // 2
                ))
                
                self.board_surface.blit(text_surf, text_rect)
        
    # ------------------ Logic & Events ------------------

    def get_square_under_mouse(self):
        """Maps pixel coordinates to board square index (0-63)."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        adj_x, adj_y = mouse_x - self.board_x, mouse_y - self.board_y
        
        if 0 <= adj_x < self.SQUARE_SIZE and 0 <= adj_y < self.SQUARE_SIZE:
            col = adj_x // self.BOARD_SIZE
            row = adj_y // self.BOARD_SIZE
            return row * 8 + col
        return None

    def _get_piece_at_square(self, sq_idx):
        """Parses the FEN string to find the piece at a specific square index."""
        rows = self.position.split('/')
        target_row, target_col = divmod(sq_idx, 8)
        
        row_str = rows[target_row]
        curr_col = 0
        for char in row_str:
            if char.isdigit():
                curr_col += int(char)
                if curr_col > target_col: return None
            else:
                if curr_col == target_col: return char
                curr_col += 1
        return None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                sq = self.get_square_under_mouse()
                if sq is not None:
                    piece = self._get_piece_at_square(sq)
                    if piece:
                        self.selected_piece = piece
                        self.selected_sq_idx = sq

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.selected_piece is not None:
                    dest_sq = self.get_square_under_mouse()
                    if dest_sq is not None and dest_sq != self.selected_sq_idx:
                        
                        # --- Check for Promotion ---
                        promotion_piece = None
                        is_pawn = self.selected_piece.upper() == 'P'
                        promotion_row = 0 if self.selected_piece == 'P' else 7
                        
                        if is_pawn and (dest_sq // 8) == promotion_row:
                            promotion_piece = self.get_promotion_choice()
                        
                        # Passa il pezzo scelto al metodo move
                        self.move(self.selected_sq_idx, dest_sq, promotion_piece)
                    
                    self.selected_piece = None
                    self.selected_sq_idx = None

    def get_promotion_choice(self):
        """Displays a selection overlay and returns the integer ID of the chosen piece."""
        # Use characters to identify assets, then map to integer IDs
        chars = ['Q', 'R', 'B', 'N'] if self.selected_piece == 'P' else ['q', 'r', 'b', 'n']
        
        # Overlay dimensions
        panel_w = self.BOARD_SIZE * 4
        panel_h = self.BOARD_SIZE
        panel_x = (self.WINDOW_SIZE - panel_w) // 2
        panel_y = (self.WINDOW_SIZE - panel_h) // 2
        
        while True:
            # 1. Background & Border
            pygame.draw.rect(self.screen, (30, 30, 30), (panel_x - 4, panel_y - 4, panel_w + 8, panel_h + 8))
            pygame.draw.rect(self.screen, self.WHITE, (panel_x, panel_y, panel_w, panel_h))
            
            # 2. Render piece images using characters
            for i, char in enumerate(chars):
                self.screen.blit(self.piece_images[char], (panel_x + i * self.BOARD_SIZE, panel_y))
            
            pygame.display.flip()

            # 3. Input Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    # Check if click is within the panel bounds
                    if panel_y <= my <= panel_y + panel_h:
                        if panel_x <= mx <= panel_x + panel_w:
                            idx = (mx - panel_x) // self.BOARD_SIZE
                            chosen_char = chars[min(idx, 3)]
                            # Return the integer ID from your piece_map (e.g., 5 + WHITE)
                            return self.board.piece_map[chosen_char]

    def move(self, from_sq, to_sq, promotion = None):
        """Attempts to move a piece from from_sq to to_sq."""
        print(f"Attempting move from {from_sq} to {to_sq}")
        move = Move(from_sq, to_sq, promotion)
        legal_moves = self.engine.search(0)
        if move in legal_moves:
            print("Move is legal, executing.")
            self.board.move_piece(move)
            self.update_position()
        else:
            print("Illegal move attempted.")

    # ------------------ Rendering ------------------

    def draw_pieces(self):
        """Renders pieces based on FEN, excluding the piece being dragged."""
        rows = self.position.split('/')

        for row_idx, row in enumerate(rows):
            col_idx = 0
            for char in row:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    self.screen.blit(
                        self.piece_images[char],
                        (
                            self.board_x + col_idx * self.BOARD_SIZE,
                            self.board_y + row_idx * self.BOARD_SIZE,
                        ),
                    )
                    col_idx += 1

    # ------------------ Main Loop ------------------

    def run(self, player_side):
        self.player_side = player_side  
        computer_side = 'b' if player_side == 'w' else 'w'
        print("-------------------------------------------------------------")
        self.engine.evaluate()

        while self.running:
            if self.board.active_color == player_side:
                # print("White to move")
                self.handle_events()
            if self.board.active_color == computer_side:
                # print("Black to move")
                start_time = time.time()
                print("-------------------------------------------------------------")
                self.engine.evaluate()
                engine_move = self.engine.engine_move()
                if engine_move:
                    self.board.move_piece(engine_move)
                    self.update_position()
                    end_time = time.time()
                    print(f"Engine move took {end_time - start_time:.5f} seconds")
                else:
                    print("Engine has no legal moves.")
                    self.running = False
                
                print("-------------------------------------------------------------")
                self.engine.evaluate()

            self.screen.blit(self.board_surface, (0, 0))
            self.draw_pieces()
            pygame.display.flip()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()
