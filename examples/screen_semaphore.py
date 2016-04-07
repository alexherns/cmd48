import curses
import subprocess
import threading

screen_write_sema = threading.BoundedSemaphore(value = 1)
SCREEN_H, SCREEN_W = 0, 0

"""
PURPOSE:
    -- a screen-writing semaphore. Lock this semaphore while the program is
    re-dawing the screen, and then unlock when finished. Ensures that only a
    single thread is writing to the screen at a time
"""

def redraw_scr(window):
    screen_write_sema.acquire()
    height, width = get_win_size()
    if is_term_resized(height, width):
        curses.resizeterm(height, width)
        window.erase()
        window.box()
        window.addstr(2, 2, "{0} - {1}".format(height, width))
    screen_write_sema.release()

def get_win_size():
    out, err = subprocess.Popen('stty size', shell=True,
            stdout=subprocess.PIPE).communicate()
    if err != None:
        raise OSError
    else:
        height, width = map(int, out.strip().split(' '))
        return height, width

def is_term_resized(height, width):
    global SCREEN_H, SCREEN_W
    if (height != SCREEN_H) or (width != SCREEN_W):
        SCREEN_H = height
        SCREEN_W = width
        return True
    return False

def main(stdscr):
    """Mainloop for program"""
    curses.curs_set(0)
    curses.use_default_colors()
    window = curses.initscr()
    redraw_scr(window)
    while True:
        press = window.getch()
        redraw_scr(window)
        if press == ord('q'):
            break
        elif press == ord('m'):
            pass

if __name__ == '__main__':
    curses.wrapper(main)
