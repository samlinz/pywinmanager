import time

from window import *
from monitor import *

from win32 import win32gui

filters = [RegexWindowFilter('.*notepad.*')]
windows = get_windows(filters)

monitors = get_monitors()

monitor = monitors[0]

# width = monitor.boundary.width // 2
# x = monitor.boundary.left + width
# y = 0
# height = monitor.boundary.height
# window.set_window_position(Boundary(x, y, width, height))

#window.window_style_hide_borders()
#window.window_maximize()


configuration = WindowContainerConfiguration(WindowContainerConfiguration.LAYOUTS['SPLIT']
                                             , WindowContainerConfiguration.SPLIT_LAYOUT_MODES['HORIZONTAL'])

windows = list(map(lambda window: WindowHolder(window, WindowHolder.MODES['TILED']), windows))
container1 = WindowContainer(configuration, monitor.boundary, windows[:-1])
container2 = WindowContainer(configuration, monitor.boundary, windows[-1:])

configuration2 = WindowContainerConfiguration(WindowContainerConfiguration.LAYOUTS['SPLIT']
                                             , WindowContainerConfiguration.SPLIT_LAYOUT_MODES['VERTICAL'])

container = WindowContainer(configuration2, monitor.boundary, containers=[container1, container2])

#window.window_style_show_original()

print('jee')