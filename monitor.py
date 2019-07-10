from win32 import win32api
from window_manager.window import Window

from window_manager.shared import Boundary


class Monitor:
    """Represents display monitor and its attributes such as name and position."""

    def __init__(self, monitor_index: int, handle) -> None:
        super().__init__()

        self.index = monitor_index
        self.handle = handle

        self.__boundary = None
        self.__update()

    def __update(self):
        """Refresh monitor attributes."""

        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmonitorinfoa
        monitor_info = win32api.GetMonitorInfo(self.handle)

        # Get device name.
        self.__device = monitor_info['Device']

        # Get monitor coordinates.
        start_x, start_y, end_x, end_y = monitor_info['Monitor']

        # Calculate boundary object.
        self.__boundary = Boundary(start_x, start_y, end_x - start_x, end_y - start_y)

        pass

    @property
    def name(self): return self.__device

    @property
    def boundary(self): return self.__boundary

    @property
    def x(self): return self.__boundary.left

    @property
    def y(self): return self.__boundary.top

    @property
    def w(self): return self.__boundary.width

    @property
    def h(self): return self.__boundary.height


def get_monitors():
    """Get all enabled display monitors."""

    # Enumerate all display monitors and get their handles.
    win_monitors = win32api.EnumDisplayMonitors()
    monitors = []

    for index, monitor in enumerate(win_monitors):
        monitor_handle = monitor[0]
        # Create new monitor object using the handle.
        monitors.append(Monitor(index, monitor_handle))

    return monitors


def get_monitor_from_window(window : Window, monitors : [Monitor]) -> Window:
    monitor_handle = win32api.MonitorFromWindow(window.handle)

    for monitor in monitors:
        if monitor.handle == monitor_handle:
            return monitor

    return None