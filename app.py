import curses
import random

def collapse_tiles(l):
    """Collapses list of 4 tiles in 2048-style"""
    l= [val for val in l if val]
    output= []
    while len(l) >= 2:
        if l[0] == l[1]:
            output.append(l[0]*2)
            l= l[2:]
        else:
            output.append(l[0])
            l= l[1:]
    if len(l):
        output.append(l[0])
    while len(output) < 4:
        output.append(0)
    return output

class Cursor(object):

    def __init__(self, y, x):
        self.x= x
        self.y= y
        self.text= ' '

    def move_left(self, x=1):
        self.x-= x

    def move_right(self, x=1):
        self.x+= x

    def move_up(self, y=1):
        self.y-= y

    def move_down(self, y=1):
        self.y+= y

class Grid(object):

    def __init__(self, scr, x=1, y=1, rows=4, cols=4, width=3, height=2):
        self.x= x
        self.y= y
        self.rows= rows
        self.cols= cols
        self.width= width
        self.height= height
        self.parent= scr
        self.won= False
        self.window= scr.subwin(rows*height, cols*width, y, x)
        self.drawgrid()
        self.cells= [[0 for _ in range(cols)] for _2 in range(rows)]
        self.create_cells()

    def drawgrid(self):
        self.window.border()

    def create_cells(self):
        for i in xrange(len(self.cells)):
            for j in xrange(len(self.cells[i])):
                self.cells[i][j]= Cell(self.window, self.height, self.width, 
                        self.y+i*self.height, self.x+j*self.width)

    def __iter__(self):
        for i in xrange(len(self.cells)):
            for j in xrange(len(self.cells[i])):
                yield self.cells[i][j]

    def set_values(self, values):
        for cell, value in zip(self, values):
            cell.value= value

    def refresh_all(self):
        for cell in self:
            cell.refresh()

    def nextMove(self, key):
        state= self.getState()
        if key == curses.KEY_LEFT:
            self.leftMove()
        elif key == curses.KEY_RIGHT:
            self.rightMove()
        elif key == curses.KEY_UP:
            self.upMove()
        elif key == curses.KEY_DOWN:
            self.downMove()
        self.refresh_all()
        if self.isWinner() and not self.won:
            self.won= True
            self.winRoutine()
        if self.illegalMove(state):
            return
        if not self.insertRandom():
            self.loseRoutine()
        self.refresh_all()

    def getState(self):
        """Returns list representation of all values"""
        return [self.getRowValues(i) for i in range(len(self.cells))]

    def illegalMove(self, previous_state):
        """Returns previous_state == current state"""
        return previous_state == self.getState()

    def getRow(self, row):
        return self.cells[row]

    def getRowValues(self, row):
        return [cell.value for cell in self.getRow(row)]

    def setRowValues(self, row, values):
        for val, cel in zip(values, self.getRow(row)):
            cel.value= val

    def getCol(self, col):
        return [self.cells[i][col] for i in xrange(len(self.cells))]

    def getColValues(self, col):
        return [cell.value for cell in self.getCol(col)]

    def setColValues(self, col, values):
        for val, cel in zip(values, self.getCol(col)):
            cel.value= val

    def rightMove(self):
        for i in range(len(self.cells)):
            row= self.getRowValues(i)[::-1]
            output= collapse_tiles(row)
            self.setRowValues(i, output[::-1])

    def leftMove(self):
        for i in range(len(self.cells)):
            row= self.getRowValues(i)
            output= collapse_tiles(row)
            self.setRowValues(i, output)

    def upMove(self):
        for i in range(len(self.cells[0])):
            col= self.getColValues(i)
            output= collapse_tiles(col)
            self.setColValues(i, output)

    def downMove(self):
        for i in range(len(self.cells[0])):
            col= self.getColValues(i)[::-1]
            output= collapse_tiles(col)
            self.setColValues(i, output[::-1])

    def isWinner(self):
        return False

    def insertRandom(self):
        available= [(x/4, x%4) for x, cell in enumerate(self) if not cell.value]
        if not available:
            return False
        row, col= random.choice(available)
        self.cells[row][col].value= random.choice([2, 4])
        return True

class Cell(object):

    def __init__(self, window, height, width, y, x):
        self.parent= window
        self.height= height
        self.width= width
        self.y= y
        self.x= x
        self.window= window.subwin(height, width, y, x)
        self.window.attron(curses.A_BOLD)
        self.window.refresh()
        self.value= 0

    def refresh(self):
        self.window.erase()
        prval= str(self.value if self.value else ' ')
        if prval == ' ':
            self.window.border('|', '|', '-', '-', ' ', ' ', ' ', ' ')
        else:
            self.window.border()
        self.window.addstr(self.height/2,self.width/2-len(prval)/2,prval)
        self.window.refresh()

    @staticmethod
    def compute_color(power2):
        i= 20
        while power2:
            power2>>= 1
            i+= 1
        return i

def main(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    grid= Grid(stdscr, width=6, height=3)
    grid.window.refresh() 
    grid.insertRandom()
    grid.insertRandom()
    grid.refresh_all()
    while True:
        press= stdscr.getch()
        if press == ord('q'):
            break
        else:
            grid.nextMove(press)

if __name__ == '__main__':
    curses.wrapper(main)
