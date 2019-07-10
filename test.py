import time

from monitor import get_monitors, get_monitor_from_window

from window import *

from win32 import win32gui

filters = [RegexWindowFilter('.*notepad.*')]
window = get_windows(filters)[0]

monitors = get_monitors()

window.window_normalize()

monitor = get_monitor_from_window(window, monitors)

# width = monitor.boundary.width // 2
# x = monitor.boundary.left + width
# y = 0
# height = monitor.boundary.height
# window.set_window_position(Boundary(x, y, width, height))

#window.window_style_hide_borders()
#window.window_maximize()

time.sleep(5)

#window.window_style_show_original()

print('jee')