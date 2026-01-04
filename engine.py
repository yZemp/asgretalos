from board import Board
from random import randint
from move import Move
from evaluator import Evaluator
from constants import WHITE, BLACK, TYPE_MASK, COLOR_MASK

class Engine:
    def __init__(self, board: Board):
        self.board = board
        self.evaluator = Evaluator()

    def engine_move(self):
        legal_moves = self.search(0)
        if not legal_moves:
            return None

        # Random move for now
        random_index = randint(0, len(legal_moves) - 1)
        move = legal_moves[random_index]
        print(f"Engine selected move: {move[0]} to {move[1]}")
        return move
    
    def evaluate(self) -> int:
        return self.evaluator.evaluate(self.board)

    def search(self, depth: int = 0):
        legal_moves = self.find_legal_moves()
        return legal_moves
        # Placeholder for search algorithm implementation

    def find_legal_moves(self) -> list:
        psuedo_legal_moves = []
        self.active = WHITE if self.board.active_color == 'w' else BLACK
        for i, piece in enumerate(self.board.board_pieces):
            if piece == 0: continue
            if (piece & COLOR_MASK) != self.active: continue
            piece_type = piece & TYPE_MASK
            # print(piece_type, piece)
            match piece_type:
                case 3: # Bishop
                    self._find_sliding_moves(i, [-9, -7, 7, 9], psuedo_legal_moves)
                case 4: # Rook
                    self._find_sliding_moves(i, [-8, -1, 1, 8], psuedo_legal_moves)
                case 5: # Queen
                    self._find_sliding_moves(i, [-9, -8, -7, -1, 1, 7, 8, 9], psuedo_legal_moves)
                case 1: # Pawn
                    self._find_pawn_moves(i, psuedo_legal_moves)
                case 2: # Knight
                    self._find_knight_moves(i, psuedo_legal_moves)
                case 6: # King
                    self._find_king_moves(i, psuedo_legal_moves)

        legal_moves = self.filter_legal_moves(psuedo_legal_moves)
        
        return legal_moves

    def filter_legal_moves(self, pseudo_legal_moves: list) -> list:
        real_legal_moves = []
        
        for move in pseudo_legal_moves:
            from_idx, to_idx, *promotion = move
            
            # 1. Save state for manual "unmake" later
            original_src_piece = self.board.board_pieces[from_idx]
            original_dest_piece = self.board.board_pieces[to_idx]
            
            # 2. Simulate move
            self.board.board_pieces[to_idx] = original_src_piece
            self.board.board_pieces[from_idx] = 0
            
            # 3. Verify king safety
            # Note: Must find king AFTER simulation if the king itself moved
            king_idx = self._find_king_position(self.active)
            
            if not self.board.is_square_attacked(king_idx, self.active):
                real_legal_moves.append(move)
                
            # 4. Unmake move (Restore state)
            self.board.board_pieces[from_idx] = original_src_piece
            self.board.board_pieces[to_idx] = original_dest_piece
            
        return real_legal_moves

    def _find_sliding_moves(self, index: int, directions: list, moves: list):
        friendly_color = self.board.board_pieces[index] & COLOR_MASK

        for direction in directions:
            current_index = index
            while True:
                # Calculate previous coordinates for wrapping check
                prev_col = current_index % 8
                
                current_index += direction
                
                # 1. Check for out-of-bounds
                if not (0 <= current_index < 64):
                    break
                
                # 2. Check for wrapping
                curr_row = current_index // 8
                curr_col = current_index % 8
                
                if abs(curr_col - prev_col) > 2: 
                    break

                target_piece = self.board.board_pieces[current_index]
                
                if target_piece == 0:
                    moves.append(Move(index, current_index))
                else:
                    # Add move only if capturing an enemy piece
                    if (target_piece & COLOR_MASK) != friendly_color:
                        moves.append(Move(index, current_index))
                    # Stop scanning (both friendly and enemy pieces)
                    break

    def _find_pawn_moves(self, index: int, moves: list):
        friendly_color = self.board.board_pieces[index] & COLOR_MASK
        direction = -8 if friendly_color == WHITE else 8
        start_row = 6 if friendly_color == WHITE else 1
        curr_col = index % 8
        promotion_row = 0 if friendly_color == WHITE else 7

        def add_move(src, dest):
            """Helper to handle promotion logic during move addition."""
            if (dest // 8) == promotion_row:
                # Add 4 moves for the 4 possible promotion pieces
                for piece_type in [5, 4, 3, 2]: # Queen, Rook, Bishop, Knight
                    moves.append(Move(src, dest, promotion = piece_type + friendly_color))
            else:
                moves.append(Move(src, dest))

        # 1. Single & Double step forward
        forward_index = index + direction
        if 0 <= forward_index < 64 and self.board.board_pieces[forward_index] == 0:
            add_move(index, forward_index)
            if (index // 8) == start_row:
                double_forward_index = index + 2 * direction
                if self.board.board_pieces[double_forward_index] == 0:
                    add_move(index, double_forward_index)

        # 2. Standard Captures
        for capture_offset in [-1, 1]:
            target_col = curr_col + capture_offset
            if 0 <= target_col <= 7: # Ensure we stay on the board horizontally
                capture_index = index + direction + capture_offset
                if 0 <= capture_index < 64:
                    target_piece = self.board.board_pieces[capture_index]
                    if target_piece != 0 and (target_piece & COLOR_MASK) != friendly_color:
                        add_move(index, capture_index)
                    
        # 3. En Passant
        if self.board.en_passant != '-':
            ep_file = ord(self.board.en_passant[0]) - ord('a')
            ep_rank = 8 - int(self.board.en_passant[1])
            ep_index = ep_rank * 8 + ep_file
            
            # En Passant is only possible if the target square is diagonally adjacent
            if abs(ep_file - curr_col) == 1 and (index // 8 + (direction // 8)) == ep_rank:
                moves.append(Move(index, ep_index))
            
    def _find_knight_moves(self, index: int, moves: list):
        knight_moves = [-17, -15, -10, -6, 6, 10, 15, 17]
        friendly_color = self.board.board_pieces[index] & COLOR_MASK

        for move in knight_moves:
            target_index = index + move
            if not (0 <= target_index < 64):
                continue
            
            # Check for wrapping
            row_diff = abs((target_index // 8) - (index // 8))
            col_diff = abs((target_index % 8) - (index % 8))
            if (row_diff, col_diff) not in [(2, 1), (1, 2)]:
                continue

            target_piece = self.board.board_pieces[target_index]
            if target_piece == 0 or (target_piece & COLOR_MASK) != friendly_color:
                moves.append(Move(index, target_index))

    def _find_king_moves(self, index: int, moves: list):
        directions = [-9, -8, -7, -1, 1, 7, 8, 9]
        friendly_color = self.board.board_pieces[index] & COLOR_MASK
        curr_col = index % 8

        for direction in directions:
            target_index = index + direction
            
            if 0 <= target_index < 64:

                # Check for wrapping
                target_col = target_index % 8
                if abs(target_col - curr_col) <= 1:
                    target_piece = self.board.board_pieces[target_index]
                    
                    if (target_piece & COLOR_MASK) != friendly_color:
                        moves.append(Move(index, target_index))
        
        # Castling
        if self.board.is_square_attacked(index, friendly_color):
            return # Cannot castle out of check
        
        if friendly_color == WHITE:
            if 'K' in self.board.castling_rights:
                if (self.board.board_pieces[61] == 0 and 
                    self.board.board_pieces[62] == 0 and
                    not self.board.is_square_attacked(61, friendly_color) and
                    not self.board.is_square_attacked(62, friendly_color)):
                    moves.append(Move(60, 62))
            if 'Q' in self.board.castling_rights:
                if (self.board.board_pieces[59] == 0 and 
                    self.board.board_pieces[58] == 0 and
                    self.board.board_pieces[57] == 0 and
                    not self.board.is_square_attacked(59, friendly_color) and
                    not self.board.is_square_attacked(58, friendly_color)):

                    moves.append(Move(60, 58))
            
        if friendly_color == BLACK:
            if 'k' in self.board.castling_rights:
                if (self.board.board_pieces[5] == 0 and 
                    self.board.board_pieces[6] == 0 and
                    not self.board.is_square_attacked(5, friendly_color) and
                    not self.board.is_square_attacked(6, friendly_color)):
                    moves.append(Move(4, 6))
            if 'q' in self.board.castling_rights:
                if (self.board.board_pieces[3] == 0 and 
                    self.board.board_pieces[2] == 0 and
                    self.board.board_pieces[1] == 0 and
                    not self.board.is_square_attacked(3, friendly_color) and
                    not self.board.is_square_attacked(2, friendly_color)):
                    moves.append(Move(4, 2))

    def _find_king_position(self, active_color: int) -> int:
        king_position = -1
        for i, piece in enumerate(self.board.board_pieces):
            if piece != 0 and (piece & TYPE_MASK) == 6 and (piece & COLOR_MASK) == active_color:
                king_position = i
                break
        if king_position == -1:
            raise ValueError("King not found on the board.")
        
        return king_position