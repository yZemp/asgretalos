class Move(tuple):
    def __new__(cls, from_square, to_square, promotion = None):
        if promotion is not None:
            return super().__new__(cls, (from_square, to_square, promotion))
        else:
            return super().__new__(cls, (from_square, to_square))