import re

from win32 import win32gui
from win32.lib import win32con
from window_manager.shared import Boundary

WINDOW_STATES = {
    'UNKNOWN'  : 1,
    'MAXIMIZED': 2,
    'MINIMIZED': 3,
    'NORMAL'   : 4
}

WINDOW_STATES_CONSTANTS = {
    WINDOW_STATES['UNKNOWN']  : -1,
    WINDOW_STATES['MAXIMIZED']: win32con.SW_SHOWMAXIMIZED,
    WINDOW_STATES['MINIMIZED']: win32con.SW_SHOWMINIMIZED,
    WINDOW_STATES['NORMAL']   : win32con.SW_SHOWNORMAL,
}

WINDOW_STATE_TRANSITIONS = {
    'UNKNOWN'    : -1,
    'MINIMIZE'   : win32con.SW_MINIMIZE,
    'RESTORE'    : win32con.SW_RESTORE,
    'MAXIMIZE'   : win32con.SW_MAXIMIZE,
    'SHOW_NORMAL': win32con.SW_SHOWNORMAL,
}


class Window:
    def __init__(self, handle):
        self.__hwnd = handle
        self.__state = WINDOW_STATES['UNKNOWN']
        self.__original_window_style = self.__get_style_long()

    def __update_title(self):
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowtexta
        self.__title = win32gui.GetWindowText(self.__hwnd)
        return self.__title

    def __update_boundary(self):
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowrect
        boundary = win32gui.GetWindowRect(self.__hwnd)
        self.__window_boundary = Boundary(*boundary)
        return self.__window_boundary

    def __update_window_state(self):
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowplacement
        window_placement = win32gui.GetWindowPlacement(self.__hwnd)
        window_state = window_placement[1]

        state_normal = WINDOW_STATES['NORMAL']
        state_minimized = WINDOW_STATES['MINIMIZED']
        state_maximized = WINDOW_STATES['MAXIMIZED']
        state_unknown = WINDOW_STATES['UNKNOWN']

        if window_state == WINDOW_STATES_CONSTANTS[state_normal]:
            self.__state = state_normal
        elif window_state == WINDOW_STATES_CONSTANTS[state_minimized]:
            self.__state = state_minimized
        elif window_state == WINDOW_STATES_CONSTANTS[state_maximized]:
            self.__state = state_maximized
        else:
            self.__state = state_unknown

        return self.__state

    def __get_client_rect(self):
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclientrect
        return win32gui.GetClientRect(self.__hwnd)

    def __get_client_boundary(self):
        # Get the top-left point of window's client area in screen coordinates.
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-clienttoscreen
        return win32gui.ClientToScreen(self.__hwnd, (0, 0))

    def __get_border_size(self):
        boundary_with_border = self.__update_boundary()
        boundary_without_border = self.__get_client_boundary()
        horizontal_border = boundary_without_border[0] - boundary_with_border.__left
        vertical_border = boundary_without_border[1] - boundary_with_border.__top

        return horizontal_border, vertical_border

    def __show_window(self, transition: int):
        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow
        win32gui.ShowWindow(self.__hwnd, transition)

    def window_maximize(self):
        self.__show_window(WINDOW_STATE_TRANSITIONS['MAXIMIZE'])

    def window_minimize(self):
        self.__show_window(WINDOW_STATE_TRANSITIONS['MINIMIZE'])

    def window_normalize(self):
        self.__update_window_state()
        minimized = self.__state == WINDOW_STATES['MINIMIZED']
        transition = WINDOW_STATE_TRANSITIONS['RESTORE'] if minimized else \
            WINDOW_STATE_TRANSITIONS['SHOW_NORMAL']
        self.__show_window(transition)

        # TODO: Somehow redraw/update because some widgets are not updated?
        # win32gui.UpdateWindow(self.hwnd)
        # win32gui.RedrawWindow(self.hwnd, None, None, win32con.RDW_UPDATENOW)

    def set_window_position(self, boundary: Boundary, redraw: bool = True):
        x = boundary.left
        y = boundary.top
        w = boundary.width
        h = boundary.height

        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-movewindow
        win32gui.MoveWindow(self.__hwnd, x, y, w, h, redraw)

    def window_style_hide_borders(self):
        """Make window borderless."""

        # Use bit mask to remove unwanted styles from the 64bit flag.
        window_style = self.__get_style_long()
        window_style &= ~(
                    win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZEBOX |
                    win32con.WS_MAXIMIZEBOX | win32con.WS_SYSMENU)
        self.__set_style_long(window_style)

    def window_style_show_original(self):
        self.__set_style_long(self.__original_window_style)

    def __get_style_long(self):
        """Get window style WinAPI flags."""

        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowlonga
        return win32gui.GetWindowLong(self.__hwnd, win32con.GWL_STYLE)

    def __set_style_long(self, style_long):
        """Set window style using WinAPI flags."""

        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowlonga
        win32gui.SetWindowLong(self.__hwnd, win32con.GWL_STYLE, style_long)

    @property
    def title(self):
        return self.__update_title()

    @property
    def client_boundary(self) -> Boundary:
        _, _, client_width, client_height = self.__get_client_rect()
        client_actual_x, client_actual_y = self.__get_client_boundary()
        return Boundary(client_actual_x
                        , client_actual_y
                        , client_actual_x + client_width
                        , client_actual_y + client_height)

    @property
    def boundary(self):
        return self.__update_boundary()

    @boundary.setter
    def boundary(self, boundary : Boundary):
        self.__window_boundary = boundary
        self.set_window_position(self.__window_boundary)

    @property
    def window_state(self):
        return self.__update_window_state()

    @property
    def handle(self):
        return self.__hwnd


class WindowFilter:
    def filter(self, window: Window) -> bool:
        raise NotImplementedError()


class RegexWindowFilter(WindowFilter):
    def __init__(self, regex: str, flags: int = re.IGNORECASE) -> None:
        super().__init__()
        self.regex = regex
        self.flags = flags

    def filter(self, window: Window) -> bool:
        return re.match(self.regex, window.title, self.flags) != None


def get_windows(filters: [WindowFilter] = None):
    """Enumerate all windows, filter them according to provided filters and create Window
    objects."""

    if filters is None: filters = []

    # List of windows.
    windows = []  # type: [Window]

    def found_window(hwnd, extra):
        window = Window(hwnd)

        # Run through filters and return if some filter does not match.
        for filter in filters:
            if not filter.filter(window): return

        windows.append(window)

    win32gui.EnumWindows(found_window, None)

    return windows

class WindowHolder:
    MODES = {
        'FREE' : 1,
        'TILED' : 2
    }

    def __init__(self, window : Window, mode : MODES) -> None:
        super().__init__()

        if not isinstance(window, Window):
            raise ValueError('Invalid window')

        if mode not in WindowHolder.MODES.values():
            raise ValueError(f'Invalid mode {mode}')

        self.__mode = mode
        self.__window = window

    @property
    def mode(self):
        return self.__mode

    @property
    def window(self):
        return self.__window

    def set_boundary(self, boundary : Boundary):
        self.__window.boundary = boundary

class WindowContainerConfiguration:
    SPLIT_LAYOUT_MODES = {
        'HORIZONTAL': 1,
        'VERTICAL' : 2
    }

    LAYOUTS = {
        'SPLIT': 1,
        'STACKED': 2,
        'TABBED' : 3
    }

    # Default configuration.
    DEFAULT_LAYOUT = LAYOUTS['SPLIT']
    DEFAULT_SPLIT_MODE = SPLIT_LAYOUT_MODES['HORIZONTAL']

    def __init__(self
                 , layout : int
                 , split_layout_mode : int):
        super().__init__()

        if layout not in WindowContainerConfiguration.LAYOUTS.values():
            raise ValueError('Invalid layout')

        if split_layout_mode not in WindowContainerConfiguration.SPLIT_LAYOUT_MODES.values():
            raise ValueError('Invalid orientation')

        self.__layout = layout
        self.__split_layout_mode = split_layout_mode

    @property
    def layout(self):
        return self.__layout

    @property
    def split_layout_mode(self):
        return self.__split_layout_mode

class WindowContainer:
    def __init__(self
            , configuration : WindowContainerConfiguration
            , boundary : Boundary
            , windows : [WindowHolder] = None
            , containers : [] = None):
        super().__init__()

        self.__windows = []
        self.__containers = []

        if windows is not None:
            for window in windows:
                if not isinstance(window, WindowHolder): raise ValueError('Provided window is not WindowHolder')
            self.__windows = windows

        if containers is not None:
            for container in containers:
                if not isinstance(container, WindowContainer):
                    raise ValueError('Invalid container')

            self.__containers = containers

        if len(self.__windows) > 0 and len(self.__containers) > 0:
            raise ValueError('Container cannot have both window and containers')

        self.__configuration = configuration # type: WindowContainerConfiguration
        self.__boundary = boundary # type: Boundary

        self.__convert_container_if_needed()
        self.__enforce_layout()

    def is_container(self):
        return len(self.__windows) == 0 and len(self.__containers) > 0

    def add_window(self, window : WindowHolder):
        if not isinstance(window, WindowHolder): raise ValueError(
            'Provided window is not WindowHolder')

        self.__windows.append(window)
        self.__convert_container_if_needed()

    def __enforce_layout(self):
        # Calculate children's positions inside this container.
        layout = self.__configuration.layout
        num_children = len(self.__containers) if len(self.__containers) > 0 else len(self.__windows)
        x, y, _, _ = self.__boundary.tuple
        width, height = self.__boundary.width, self.__boundary.height

        if layout == WindowContainerConfiguration.LAYOUTS['SPLIT']:
            orientation = self.__configuration.split_layout_mode

            orientation_horizontal = orientation == WindowContainerConfiguration.SPLIT_LAYOUT_MODES['HORIZONTAL']
            orientation_vertical = orientation == WindowContainerConfiguration.SPLIT_LAYOUT_MODES['VERTICAL']

            single_width = width // num_children if orientation_horizontal else width
            single_height = height // num_children if orientation_vertical else height

            if sum([orientation_horizontal, orientation_vertical]) != 1:
                raise ValueError(f'Invalid orientation {orientation}')

            children = self.__containers if len(self.__containers) > 0 else self.__windows

            # Set children's boundaries.
            for child_index, child in enumerate(children):
                child_x = child_index * single_width + x if orientation_horizontal else x
                child_y = child_index * single_height + y if orientation_vertical else y
                child_x2 = child_x + single_width
                child_y2 = child_y + single_height
                child_boundary = Boundary(child_x, child_y, child_x2, child_y2)
                child.set_boundary(child_boundary)

        else:
            raise NotImplementedError() # TODO: OTHER MODES

        # If this container contains multiple layouts, propagate call to them.
        for child_container in self.__containers:
            child_container.enforce_layout()

    def __convert_container_if_needed(self):
        window_count = len(self.__windows)
        container_count = len(self.__containers)

        if window_count == 0 and container_count == 1:
            # This container becomes a leaf node with only one window.
            self.__windows = [self.__containers[0].window]
            self.__containers = None
        elif window_count > 1 and container_count == 0:
            # Turn multiple windows into child containers.
            self.__containers = []
            for child_window in self.__windows:
                child_window_container = WindowContainer(self.__configuration
                                                         , child_window.window.boundary
                                                         , windows=[child_window])
                self.__containers.append(child_window_container)

            self.__windows = []
        else:
            return

    @property
    def window(self) -> WindowHolder:
        if len(self.__windows) != 1:
            raise ValueError('Container does not have a single window')

        return self.__windows[0]

    def set_boundary(self, boundary : Boundary):
        self.__boundary = boundary

    def enforce_layout(self):
        self.__enforce_layout()