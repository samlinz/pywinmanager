class Boundary:
    """Represents arbitrary 2d boundary."""

    def __init__(self, left, top, right, bottom):
        self.__left = left
        self.__top = top
        self.__right = right
        self.__bottom = bottom

    @property
    def tuple(self): return (self.__left, self.__top, self.__right, self.__bottom)

    @property
    def left(self):
        return self.__left

    @property
    def top(self):
        return self.__top

    @property
    def width(self):
        return self.__right - self.__left

    @property
    def height(self):
        return self.__bottom - self.__top