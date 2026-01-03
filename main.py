from interface import Interface
from board import Board
from engine import Engine
STARTING_POSITION = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# STARTING_POSITION = "r1bqk2r/ppp2ppp/2n2n2/2bpp1B1/2B1P3/P2P1N2/1PP3PP/RN1QK2R w KQkq - 0 1"
# STARTING_POSITION = "rn1qk2r/pp2ppbp/2p2np1/3p4/2PPb1PN/4P3/PP2BP1P/RNBQK2R w KQkq - 0 1"
# STARTING_POSITION = "8/P7/8/8/8/8/8/k6K w - - 0 0" # Promotion test
DEFAULT_PLAYER_SIDE = 'w'


def main():
    FEN = input("Input FEN string (enter for default):\n")

    # Check if FEN is valid and use STARTING_POSITION if empty
    if not _is_valid_fen(FEN) and FEN != "":
        raise ValueError("Invalid FEN string provided.")
    else:
        if FEN == "":
            FEN = STARTING_POSITION

    PLAYER_SIDE = input("Choose side (w/b, enter for white):\n")
    if PLAYER_SIDE not in ['w', 'b', '']:
        raise ValueError("Invalid side choice. Must be 'w' (white) or 'b' (black).")
    else:
        if PLAYER_SIDE == '':
            PLAYER_SIDE = DEFAULT_PLAYER_SIDE

    start_game(FEN, PLAYER_SIDE)

def start_game(FEN, PLAYER_SIDE):
    board = Board(FEN)
    engine = Engine(board)
    interface = Interface(board, engine)

    print(f"Game started as {PLAYER_SIDE} with FEN: {FEN}")    
    interface.run(player_side = PLAYER_SIDE)



def _is_valid_fen(fen):
    parts = fen.split()
    if len(parts) != 6:
        return False

    board, turn, castling, en_passant, halfmove, fullmove = parts

    rows = board.split('/')
    if len(rows) != 8:
        return False

    for row in rows:
        count = 0
        for char in row:
            if char.isdigit():
                count += int(char)
            elif char.isalpha() and char in "prnbqkPRNBQK":
                count += 1
            else:
                return False
        if count != 8:
            return False

    if turn not in ['w', 'b']:
        return False

    if not all(c in "KQkq-" for c in castling):
        return False

    if en_passant != '-' and not (len(en_passant) == 2 and en_passant[0] in "abcdefgh" and en_passant[1] in "36"):
        return False

    if not halfmove.isdigit() or not fullmove.isdigit():
        return False

    return True



if __name__ == "__main__":
    main()