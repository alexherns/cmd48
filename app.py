#!/usr/bin/env python
import curses
import random
import logging
logging.basicConfig(filename='logging.txt', level=logging.DEBUG)

def collapse_tiles(tile_array):
    """Collapse list of 4 tiles in 2048-style"""
    tile_array = [val for val in tile_array if val]
    output = []
    while len(tile_array) >= 2:
        if tile_array[0] == tile_array[1]:
            output.append(tile_array[0]*2)
            tile_array = tile_array[2:]
        else:
            output.append(tile_array[0])
            tile_array = tile_array[1:]
    if len(tile_array):
        output.append(tile_array[0])
    while len(output) < 4:
        output.append(0)
    return output

def kwarg_mapper(obj, kwargs, check_arg, alternate):
    """Automates use of kwargs by handling cases when the check_arg not
    specified in kwargs, but you want to provide an alternate"""
    if check_arg in kwargs:
        setattr(obj, check_arg, kwargs[check_arg])
    else:
        setattr(obj, check_arg, alternate)

class Grid(object):
    """The Grid maintains the tiles and functions necessary for playing the
    game."""

    def __init__(self, scr, x=1, y=1, rows=4, cols=4, width=3, height=2):
        """Initialize a grid of cells"""
        self.x = x
        self.y = y
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height
        self.parent = scr
        self.won = False
        self.window = scr.subwin(rows*height, cols*width, y, x)
        self.window.border()
        self.cells = [[0 for _ in range(cols)] for __ in range(rows)]
        self.create_cells()

    def next_move(self, key):
        """Advance game one step, using key press"""
        state = self.get_state()
        if key == curses.KEY_LEFT:
            self.left_move()
        elif key == curses.KEY_RIGHT:
            self.right_move()
        elif key == curses.KEY_UP:
            self.up_move()
        elif key == curses.KEY_DOWN:
            self.down_move()
        self.refresh_all()
        if self.is_winner() and not self.won:
            self.won = True
            self.win_routine()
        if self.illegal_move(state):
            if self.is_loser():
                self.lose_routine()
                self.refresh_all()
                curses.beep()
                return
            else:
                curses.beep()
                return
        else:
            self.insert_random()
        self.refresh_all()

    def create_cells(self):
        """Initiliaze the cells of the game, one Cell object in each tile of
        the Grid"""
        for i in xrange(len(self.cells)):
            for j in xrange(len(self.cells[i])):
                self.cells[i][j] = Cell(self.window, self.height, self.width,
                                        self.y+i*self.height, self.x+j*self.width)

    def __iter__(self):
        """Iterate through each cell, row by row"""
        for i in xrange(len(self.cells)):
            for j in xrange(len(self.cells[i])):
                yield self.cells[i][j]

    def set_values(self, values):
        """Set the values of each cell using a list"""
        for cell, value in zip(self, values):
            cell.value = value

    def refresh_all(self):
        """Refresh all cells"""
        for cell in self:
            cell.refresh()

    def get_state(self):
        """Return list representation of all values"""
        return [self.get_row_values(i) for i in range(len(self.cells))]

    def illegal_move(self, previous_state):
        """Return previous_state == current state"""
        return previous_state == self.get_state()

    def get_row(self, row):
        """Return list of cells in row"""
        return self.cells[row]

    def get_row_values(self, row):
        """Return list of values of each cell in row"""
        return [cell.value for cell in self.get_row(row)]

    def set_row_values(self, row, values):
        """Set values of each cell in row using list"""
        for val, cel in zip(values, self.get_row(row)):
            cel.value = val

    def get_col(self, col):
        """Return list of cells in column"""
        return [self.cells[i][col] for i in xrange(len(self.cells))]

    def get_col_values(self, col):
        """Return list of values of each cell in column"""
        return [cell.value for cell in self.get_col(col)]

    def set_col_values(self, col, values):
        """Set values of each cell in column using list"""
        for val, cel in zip(values, self.get_col(col)):
            cel.value = val

    def right_move(self):
        """Shift cells right"""
        for i in range(len(self.cells)):
            row = self.get_row_values(i)[::-1]
            output = collapse_tiles(row)
            self.set_row_values(i, output[::-1])

    def left_move(self):
        """Shift cells left"""
        for i in range(len(self.cells)):
            row = self.get_row_values(i)
            output = collapse_tiles(row)
            self.set_row_values(i, output)

    def up_move(self):
        """Shift cells up"""
        for i in range(len(self.cells[0])):
            col = self.get_col_values(i)
            output = collapse_tiles(col)
            self.set_col_values(i, output)

    def down_move(self):
        """Shift cells down"""
        for i in range(len(self.cells[0])):
            col = self.get_col_values(i)[::-1]
            output = collapse_tiles(col)
            self.set_col_values(i, output[::-1])

    def is_winner(self):
        """Return 2048 in any cell"""
        for cell in self:
            if cell.value == 2048:
                return True

    def is_loser(self):
        """Return no possible moves"""
        #Check for non-full board
        if [cell for cell in self if not cell.value] != []:
            return False
        #Check for collapsible rows
        for i in range(len(self.cells)):
            if collapse_tiles(self.get_row_values(i))[-1] == 0:
                return False
        #Check for collapsible columns
        for j in range(len(self.cells[0])):
            if collapse_tiles(self.get_col_values(j))[-1] == 0:
                return False
        return True

    def win_routine(self):
        """Creates a win dialog box, and allows you to keep playing"""
        alert = Alert(self.window, 'YOU WIN!')
        alert.draw()
        alert.refresh()
        while True:
            key = alert.window.getch()
            if key == ord('q'):
                alert = None
                break

    def lose_routine(self):
        """Creates a lose dialog box, the game is not over"""
        alert = Alert(self.window, 'GAME OVER\nScore: {0}'.format(\
                str(self.tally_score())))
        alert.draw()
        alert.refresh()
        while True:
            key = alert.window.getch()
            if key == ord('q'):
                alert = None
                break

    def insert_random(self):
        """Insert 2 or 4 into any unoccupied cell.
        Return 'method was able to find unoccupied cell'"""
        available = [(x/4, x%4) for x, cell in enumerate(self) if not cell.value]
        if available == []:
            return False
        row, col = random.choice(available)
        self.cells[row][col].value = random.choice([2, 4])
        return True

    def tally_score(self):
        """Sums the score of each tile"""
        return sum(cell.value for cell in self)



class Cell(object):
    """A Cell represents a tile in the Grid."""

    def __init__(self, window, height, width, y, x):
        """Initialize a Cell object"""
        self.parent = window
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.window = window.subwin(height, width, y, x)
        self.window.attron(curses.A_BOLD)
        self.window.refresh()
        self.value = 0

    def refresh(self):
        """Refresh cell with new value"""
        self.window.erase()
        prval = str(self.value if self.value else ' ')
        if prval == ' ':
            self.window.border('|', '|', '-', '-', ' ', ' ', ' ', ' ')
        else:
            self.window.border()
        self.window.addstr(self.height/2, self.width/2-len(prval)/2, prval)
        self.window.refresh()

    @staticmethod
    def compute_color(power2):
        """[Deprecated] Return a color integer according to log2(self.value)"""
        i = 20
        while power2:
            power2 >>= 1
            i += 1
        return i



class Alert(object):
    """An Alert represents a window with simple dismissal functions"""

    def __init__(self, window, message, **kwargs):
        """Initialize an Alert. By default, center within the parent window"""
        self.parent = window
        self.message = message
        parheight, parwidth = self.parent.getmaxyx()
        self.width, self.height = Alert.message_dimensions(message, parwidth-2,
                                                           parheight-2)
        self.width += 2
        self.height += 2
        kwarg_mapper(self, kwargs, 'x', (parwidth-self.width)/2)
        kwarg_mapper(self, kwargs, 'y', (parheight-self.height)/2)

    def draw(self):
        """Draws window, border, and message for alert"""
        self.window = self.parent.subwin(self.height, self.width, self.y, self.x)
        self.window.border('#', '#', '#', '#', '#', '#', '#', '#')
        self.set_message()

    def set_message(self, message=None):
        """Adds strings to the message window, padding with spaces to cover
        background objects"""
        if not message:
            message = self.message
        line_num = 1
        for line in Alert.split_message(self.message, self.width):
            line = line + (self.width-2-len(line))*' '
            self.window.addstr(line_num, 1, line)
            line_num += 1

    @staticmethod
    def split_message(message, max_w):
        """Splits the message into lines according to a rigid width and
        potential linebreaks in the message itself"""
        output = []
        for line in message.splitlines():
            while line:
                output.append(line[:max_w])
                line = line[max_w:]
        return output

    @staticmethod
    def message_dimensions(message, max_w, max_h):
        """Returns the dimensions of a message, according to a rigid width and
        potential linebreaks in the message itself"""
        width, height = 0, 0
        for line in Alert.split_message(message, max_w):
            width = max(width, len(line[:max_w]))
            height += 1
        return width, height


    def refresh(self):
        """Refreshes window"""
        self.window.refresh()



def main(stdscr):
    """Mainloop for program"""
    curses.curs_set(0)
    curses.use_default_colors()
    curses.resizeterm(30, 100)
    grid = Grid(stdscr, width=6, height=3)
    grid.window.refresh()
    grid.insert_random()
    grid.insert_random()
    grid.refresh_all()
    while True:
        press = stdscr.getch()
        if press == ord('q'):
            break
        elif press == ord('m'):
            pass
            #menuloop(grid, stdscr)
        else:
            grid.next_move(press)

if __name__ == '__main__':
    curses.wrapper(main)
