from board import Board, TYPE_MASK, COLOR_MASK, WHITE, BLACK


class Evaluator:
    def __init__(self):
        # Piece values in centipawns
        self.VALUES = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}

    def evaluate(self, board: Board) -> int:
        # Basic evaluation
        NUMBER_OF_PIECES = len([piece for piece in board.board_pieces if piece != 0])

        material_score = self.material_evaluation(board)
        pawn_structure_score = self.pawn_structure_evaluation(board, NUMBER_OF_PIECES)
        king_position_score = self.king_position_evaluation(board, NUMBER_OF_PIECES)
        pieces_combination_score = self.pieces_combination_evaluation(board)

        total_score = material_score + pawn_structure_score + king_position_score + pieces_combination_score

        print(f"Material Score: \t{material_score}")
        print(f"Pawn Structure Score: \t{pawn_structure_score}")
        print(f"King Position Score: \t{king_position_score}")
        print(f"Pieces Comb. Score: \t{pieces_combination_score}")
        print(f"Total Evaluation: \t{total_score}")
        return total_score

    def material_evaluation(self, board: Board) -> int:
        score = 0
        piece_values = {
            1: 100,  # Pawn
            2: 320,  # Knight
            3: 330,  # Bishop
            4: 500,  # Rook
            5: 900,  # Queen
            6: 0     # King
        }

        for piece in board.board_pieces:
            if piece == 0:
                continue
            piece_type = piece & TYPE_MASK
            piece_color = piece & COLOR_MASK
            value = piece_values[piece_type]
            if piece_color == WHITE:
                score += value
            else:
                score -= value

        return score

    def pawn_structure_evaluation(self, board: Board, number_of_pieces: int) -> int:
        score = 0
        doubled_pawn_penalty = 30
        isolated_pawn_penalty = 20
        passed_pawn_bonus = 30
        pawn_controlling_center_bonus = 50
        pawn_positions = {WHITE: [], BLACK: []}

        for index, piece in enumerate(board.board_pieces):
            if piece == 0:
                continue
            piece_type = piece & TYPE_MASK
            piece_color = piece & COLOR_MASK
            if piece_type == 1:  # Pawn
                pawn_positions[piece_color].append(index)

        # Doubled pawns
        for color in [WHITE, BLACK]:
            file_counts = [0] * 8
            for pos in pawn_positions[color]:
                file = pos % 8
                file_counts[file] += 1

            for count in file_counts:
                if count > 1:
                    if color == WHITE:
                        score -= (count - 1) * doubled_pawn_penalty
                    else:
                        score += (count - 1) * doubled_pawn_penalty

        # Isolated pawns
        for color in [WHITE, BLACK]:
            files_with_pawns = set()
            for pos in pawn_positions[color]:
                file = pos % 8
                if file in [0, 7]:
                    continue
                files_with_pawns.add(file)

            for file in files_with_pawns:
                if (file - 1 not in files_with_pawns) and (file + 1 not in files_with_pawns):
                    if color == WHITE:
                        score -= isolated_pawn_penalty
                    else:
                        score += isolated_pawn_penalty

        # Passed pawns
        for color in [WHITE, BLACK]:
            for pos in pawn_positions[color]:
                file = pos % 8
                rank = pos // 8
                is_passed = True

                for opp_pos in pawn_positions[BLACK if color == WHITE else WHITE]:
                    opp_file = opp_pos % 8
                    opp_rank = opp_pos // 8
                    if abs(opp_file - file) <= 1:
                        if (color == WHITE and opp_rank > rank) or (color == BLACK and opp_rank < rank):
                            is_passed = False
                            break

                if is_passed:
                    if color == WHITE:
                        score += passed_pawn_bonus
                    else:
                        score -= passed_pawn_bonus

        # Pawns controlling center
        center_squares = [27, 28, 35, 36]  # e4, d4, e5, d5
        for color in [WHITE, BLACK]:
            for pos in pawn_positions[color]:
                if pos in center_squares:
                    if color == WHITE:
                        score += pawn_controlling_center_bonus
                    else:
                        score -= pawn_controlling_center_bonus

            for pos in center_squares:
                file = pos % 8
                rank = pos // 8
                adjacent_files = [file - 1, file + 1]
                for adj_file in adjacent_files:
                    if 0 <= adj_file <= 7:
                        adj_pos = rank * 8 + adj_file
                        if adj_pos in pawn_positions[color]:
                            if color == WHITE:
                                score += pawn_controlling_center_bonus // 2
                            else:
                                score -= pawn_controlling_center_bonus // 2

        return score * int(round(32 / number_of_pieces))
    
    def king_position_evaluation(self, board: Board, number_of_pieces: int) -> int:
        king_safety_score = 0
        king_safety_bonus = 50 * int(round((number_of_pieces - 2) / (32 - 2)))
        king_safety_penalty = 50 * int(round((number_of_pieces - 2) / (32 - 2)))

        king_positions = {WHITE: - 1, BLACK: - 1}
        for index, piece in enumerate(board.board_pieces):
            if piece == 0:
                continue
            piece_type = piece & TYPE_MASK
            piece_color = piece & COLOR_MASK
            if piece_type == 6:  # King
                king_positions[piece_color] = index

        for color in [WHITE, BLACK]:
            king_index = king_positions[color]
            if king_index == -1:
                continue

            rank = king_index // 8
            file = king_index % 8

            # Simple heuristic: kings on back rank and flank files are safer
            if (color == WHITE and rank == 7) or (color == BLACK and rank == 0):
                if color == WHITE:
                    king_safety_score += king_safety_bonus
                else:
                    king_safety_score -= king_safety_bonus
            else:
                if color == WHITE:
                    king_safety_score -= king_safety_bonus
                else:
                    king_safety_score += king_safety_bonus
            
            if file in [3, 4, 5]:  # Central files
                if color == WHITE:
                    king_safety_score -= king_safety_penalty
                else:
                    king_safety_score += king_safety_penalty

            # King safety
            directions = [-9, -8, -7, -1, 1, 7, 8, 9]
            for direction in directions:
                target_index = king_index + direction
                if 0 <= target_index < 64:
                    target_piece = board.board_pieces[target_index]
                    if (target_piece != 0 and (target_piece & COLOR_MASK) != color) or board.is_square_attacked(target_index, color):
                        if color == WHITE:
                            king_safety_score -= king_safety_penalty
                        else:
                            king_safety_score += king_safety_penalty

        return king_safety_score

    def pieces_combination_evaluation(self, board: Board) -> int:
        score = 0
        bishop_pair_bonus = 40

        white_bishops = [i for i, p in enumerate(board.board_pieces) if p != 0 and (p & TYPE_MASK) == 3 and (p & COLOR_MASK) == WHITE]
        black_bishops = [i for i, p in enumerate(board.board_pieces) if p != 0 and (p & TYPE_MASK) == 3 and (p & COLOR_MASK) == BLACK]

        # Bishop pair bonus
        if len(white_bishops) >= 2:
            score += bishop_pair_bonus
        if len(black_bishops) >= 2:
            score -= bishop_pair_bonus

        return score