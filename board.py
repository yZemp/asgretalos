from constants import WHITE, BLACK, TYPE_MASK, COLOR_MASK
from move import Move

class Board:
    def __init__(self, fen):
        self.board_pieces = [0] * 64
        self.piece_map = {
            'p': 1 + BLACK, 'n': 2 + BLACK, 'b': 3 + BLACK, 'r': 4 + BLACK, 'q': 5 + BLACK, 'k': 6 + BLACK,
            'P': 1 + WHITE, 'N': 2 + WHITE, 'B': 3 + WHITE, 'R': 4 + WHITE, 'Q': 5 + WHITE, 'K': 6 + WHITE
        }
        self.load_fen(fen)

    def load_fen(self, fen):
        # Position
        fen_parts = fen.split()
        board_fen = fen_parts[0]
        rows = board_fen.split('/')
        for row_idx, row in enumerate(rows):
            col_idx = 0
            for char in row:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    self.board_pieces[row_idx * 8 + col_idx] = self.piece_map[char]
                    col_idx += 1

        # Other data
        self.active_color = fen_parts[1]
        self.castling_rights = fen_parts[2]
        self.en_passant = fen_parts[3]
        self.halfmove_clock = int(fen_parts[4])
        self.fullmove_number = int(fen_parts[5])

        # Save also the FEN itself
        self.fen = fen

    def move_piece(self, move):
        src, dest, *promotion = move
        piece = self.board_pieces[src]
        captured_piece = self.board_pieces[dest]
        piece_type = piece & TYPE_MASK

        self.pseudo_move(src, dest, piece, piece_type, promotion)

        # --- Castling Rights Logic ---
        
        # 1. King Move: Remove all rights for the active player
        if piece_type == 6: 
            if self.active_color == 'w':
                self.castling_rights = self.castling_rights.replace('K', '').replace('Q', '')
            else: # active_color == 'b'
                self.castling_rights = self.castling_rights.replace('k', '').replace('q', '')

        # 2. Rook Move: Remove specific side right
        if piece_type == 4:
            if self.active_color == 'w':
                if src == 56: self.castling_rights = self.castling_rights.replace('Q', '')
                if src == 63: self.castling_rights = self.castling_rights.replace('K', '')
            else: # active_color == 'b'
                if src == 0: self.castling_rights = self.castling_rights.replace('q', '')
                if src == 7: self.castling_rights = self.castling_rights.replace('k', '')

        # 3. Rook Capture: If a rook is captured, the opponent loses rights for that side
        if (captured_piece & TYPE_MASK) == 4:
            # If White captures a Black rook
            if self.active_color == 'w':
                if dest == 0: self.castling_rights = self.castling_rights.replace('q', '')
                if dest == 7: self.castling_rights = self.castling_rights.replace('k', '')
            # If Black captures a White rook
            else:
                if dest == 56: self.castling_rights = self.castling_rights.replace('Q', '')
                if dest == 63: self.castling_rights = self.castling_rights.replace('K', '')

        # Cleanup
        if not self.castling_rights or self.castling_rights == '':
            self.castling_rights = '-'

        # Move counters
        self.fullmove_number += 1 if self.active_color == 'w' else 0
        self.halfmove_clock += 1
        if piece & TYPE_MASK == 1: # Pawn move
            self.halfmove_clock = 0
        if self.board_pieces[dest] != 0: # Capture
            self.halfmove_clock = 0

        # En passant target square
        if (piece & TYPE_MASK) == 1 and abs(dest - src) == 16: # Double pawn move
            file = dest % 8
            # Convert array row (0-7) to FEN rank (8-1)
            # If white moved: dest is rank 4 (array row 4), EP target is rank 3 (array row 5)
            # If black moved: dest is rank 5 (array row 3), EP target is rank 6 (array row 2)
            
            if self.active_color == 'w':
                # White moved from rank 2 to 4 (row 6 to 4)
                # EP target is rank 3 (row 5)
                ep_rank = 3 
            else: # active_color == 'b'
                # Black moved from rank 7 to 5 (row 1 to 3)
                # EP target is rank 6 (row 2)
                ep_rank = 6

            self.en_passant = chr(ord('a') + file) + str(ep_rank)
        else:
            self.en_passant = '-'

        # Active color
        self.active_color = 'b' if self.active_color == 'w' else 'w'

        # Update FEN
        self.fen = self.generate_fen()
        print(f"Updated FEN: {self.fen}")

    def pseudo_move(self, src, dest, piece, piece_type, promotion):
        self.board_pieces[dest] = piece
        self.board_pieces[src] = 0

        # Pawn promotion
        if promotion:
            if piece_type != 1:
                raise ValueError("Promotion can only occur for pawns.")
            dest_rank = dest // 8
            if (self.active_color == 'w' and dest_rank != 0) or (self.active_color == 'b' and dest_rank != 7):
                raise ValueError("Pawn promotion must occur on the last rank.")

            self.board_pieces[dest] = promotion[0]

        # Castling move
        if piece_type == 6: # King
            # White Castling
            if src == 60:
                if dest == 62:  # Kingside (e1 -> g1)
                    self.board_pieces[61] = self.board_pieces[63]
                    self.board_pieces[63] = 0
                elif dest == 58:  # Queenside (e1 -> c1)
                    self.board_pieces[59] = self.board_pieces[56]
                    self.board_pieces[56] = 0
            # Black Castling
            elif src == 4:
                if dest == 6:  # Kingside (e8 -> g8)
                    self.board_pieces[5] = self.board_pieces[7]
                    self.board_pieces[7] = 0
                elif dest == 2:  # Queenside (e8 -> c8)
                    self.board_pieces[3] = self.board_pieces[0]
                    self.board_pieces[0] = 0
        
        # En Passant capture
        if piece_type == 1:  # Pawn
            if self.en_passant != '-':
                file = ord(self.en_passant[0]) - ord('a')
                rank = 8 - int(self.en_passant[1])
                en_passant_index = rank * 8 + file
                if dest == en_passant_index:
                    if self.active_color == 'w':
                        self.board_pieces[en_passant_index + 8] = 0  # Remove black pawn
                    else:
                        self.board_pieces[en_passant_index - 8] = 0  # Remove white pawn

    def generate_fen(self) -> str:
        fen_rows = []
        for row in range(8):
            fen_row = ""
            empty_count = 0
            for col in range(8):
                piece = self.board_pieces[row * 8 + col]
                if piece == 0:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    for symbol, value in self.piece_map.items():
                        if value == piece:
                            fen_row += symbol
                            break
            if empty_count > 0:
                fen_row += str(empty_count)
            fen_rows.append(fen_row)
        board_fen = '/'.join(fen_rows)
        fen = f"{board_fen} {self.active_color} {self.castling_rights} {self.en_passant} {self.halfmove_clock} {self.fullmove_number}"
        return fen
    
    def is_square_attacked(self, square: int, active_color: int) -> bool:
        enemy_color = BLACK if active_color == WHITE else WHITE

        # 1. Sliding pieces (Rook, Bishop, Queen)
        # Combined directions for optimization
        directions = [
            (-8, 'orthogonal'), (8, 'orthogonal'), (-1, 'orthogonal'), (1, 'orthogonal'), # Rook/Queen
            (-9, 'diagonal'), (-7, 'diagonal'), (7, 'diagonal'), (9, 'diagonal')         # Bishop/Queen
        ]

        for d, d_type in directions:
            current_index = square
            while True:
                prev_col = current_index % 8
                current_index += d

                if not (0 <= current_index < 64): break
                if abs((current_index % 8) - prev_col) > 1: break # Correct edge wrap check

                piece = self.board_pieces[current_index]
                if piece != 0:
                    if (piece & COLOR_MASK) == enemy_color:
                        t = piece & TYPE_MASK
                        if t == 5: return True # Queen
                        if d_type == 'orthogonal' and t == 4: return True # Rook
                        if d_type == 'diagonal' and t == 3: return True # Bishop
                    break # Blocked by any piece

        # 2. Knights
        knight_moves = [-17, -15, -10, -6, 6, 10, 15, 17]
        for m in knight_moves:
            target = square + m
            if 0 <= target < 64:
                # Verify L-shape (prevents horizontal wrapping)
                if abs((target % 8) - (square % 8)) <= 2 and \
                abs((target // 8) - (square // 8)) <= 2 and \
                abs((target % 8) - (square % 8)) + abs((target // 8) - (square // 8)) == 3:
                    piece = self.board_pieces[target]
                    if (piece & COLOR_MASK) == enemy_color and (piece & TYPE_MASK) == 2:
                        return True

        # 3. Pawns
        # Pawns attack from the perspective of the king
        pawn_offsets = [-7, -9] if active_color == WHITE else [7, 9]
        for offset in pawn_offsets:
            target = square + offset
            if 0 <= target < 64 and abs((target % 8) - (square % 8)) == 1:
                piece = self.board_pieces[target]
                if (piece & COLOR_MASK) == enemy_color and (piece & TYPE_MASK) == 1:
                    return True

        # 4. Enemy King (Kings cannot be adjacent)
        king_offsets = [-9, -8, -7, -1, 1, 7, 8, 9]
        for offset in king_offsets:
            target = square + offset
            if 0 <= target < 64 and abs((target % 8) - (square % 8)) <= 1:
                piece = self.board_pieces[target]
                if (piece & COLOR_MASK) == enemy_color and (piece & TYPE_MASK) == 6:
                    return True

        return False


    def get_color(piece_value):
        return piece_value & COLOR_MASK

    def get_type(piece_value):
        return piece_value & TYPE_MASK

    def is_color(piece_value, color):
        return (piece_value & COLOR_MASK) == color

    def __str__(self):
        result = []
        for row in range(8):
            result.append(' '.join(f"{self.board_pieces[row * 8 + col]:2}" for col in range(8)))
        result.append(f"Active color: {self.active_color}")
        result.append(f"Castling rights: {self.castling_rights}")
        result.append(f"En passant: {self.en_passant}")
        result.append(f"Halfmove clock: {self.halfmove_clock}")
        result.append(f"Fullmove number: {self.fullmove_number}")

        return '\n'.join(result)


# Example usage:
if __name__ == "__main__":
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    board_pieces = Board(fen)
    print(board_pieces)