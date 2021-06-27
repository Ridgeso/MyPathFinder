import argparse

parser = argparse.ArgumentParser(description="Type of the path finding algorithm.")
parser.add_argument("-c", help="Use cython version to compile", action="store_true")
args = parser.parse_args()

if args.c:
    from astarc import *
else:
    from astar import *

from tkinter import Button, Label, Scale, Tk, Canvas
from tkinter.constants import HORIZONTAL

colors = {"path": "green", "been": "red", "wall": "black", "none": "white", "start": "blue", "end": "purple"}

def fill_grid():
    color = colors["wall"]
    canvas.create_rectangle(0, 0, win_size+shift, win_size+shift, fill=colors["none"])
    for i in range(N+1):
        x = i*size
        canvas.create_line(0, x+shift, win_size+shift, x+shift, fill=color)
        canvas.create_line(x+shift, 0, x+shift, win_size+shift, fill=color)


def draw_path(pos, if_path):
    canvas.create_rectangle(
        pos.x*size+shift, pos.y*size+shift,
        pos.x*size+shift+size, pos.y*size+shift+size,
        fill=colors["been"]
    )
    if if_path:
        path = create_path(pos)
        for p in path:
            x, y = p.x*size, p.y*size
            canvas.create_rectangle(
                shift+x, shift+y,
                shift+x+size, shift+y+size,
                fill=colors["path"]
            )


def pathfinder():
        if openset:
            pos = openset.rem_fir()

            if speed.get():
                draw_path(pos, False)

            state = a_star(plane, openset, been, pos, end)
            if state is not None:
                draw_path(pos, True)
                return

            root.after(speed.get(), pathfinder)
        else:
            finished.config(text="Path Not Found")


def start_finding():
    if start is not None and end is not None:
        start_btn.config(text="Stop")
        
        start_time = perf_counter()
        openset.heappush(start)
        pathfinder()
        end_time = perf_counter()

        finished.config(text=f"Finished in {round((end_time-start_time)*1000, 1)} ms")

        start_btn.config(text="Start")

def draw_walls(event):
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        temp = plane[x][y]
        if temp == start or temp == end:
            return
        temp.wall = True
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=colors["wall"]
        )


def del_walls(event):
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        temp = plane[x][y]
        if temp == start or temp == end:
            return
        temp.wall = False
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=colors["none"]
        )


def make_start(event):
    global start
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        if start is None:
            start = plane[x][y]
            color = colors["start"]
        else:
            if plane[x][y] == start:
                start = None
                color = colors["none"]
            else:
                return
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=color
        )


def make_end(event):
    global end
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        if end is None:
            end = plane[x][y]
            color = colors["end"]
        else:
            if plane[x][y] == end:
                end = None
                color = colors["none"]
            else:
                return
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=color
        )


def try_reset():
    if start_btn["text"] == "Start":
        init()
        fill_grid()
        finished.config(text="Set Start and End point to start")

def init():
    global N, plane, win_size, shift, size
    global start, end, run
    global openset, been

    N = 50
    plane = [[Grid(i, j, False, 0) for j in range(N)] for i in range(N)]
    shift = 2
    win_size = 500
    size = win_size//N
    
    start = None
    end = None
    run = False

    openset = Heap(N)
    been = set()


if __name__ == "__main__":
    init()

    root = Tk()
    root.title("Path Finder")
    root.geometry(f"{win_size+50}x{win_size+150}")

    canvas = Canvas(root, width=win_size+shift, height=win_size+shift, bg="white")

    canvas.bind_all("<Motion>", lambda event: canvas.focus_set())
    canvas.bind("<B1-Motion>", draw_walls)
    canvas.bind("<B3-Motion>", del_walls)
    canvas.bind("<s><Button-1>", make_start)
    canvas.bind("<e><Button-1>", make_end)
    
    fill_grid()

    start_btn = Button(root, text="Start", command=start_finding)
    reset_btn = Button(root, text="Reset", command=try_reset)
    speed = Scale(root, from_=0, to=40, orient=HORIZONTAL)

    finished = Label(root, text="Set Start and End point to start")

    canvas.pack()
    start_btn.pack()
    reset_btn.pack()
    speed.pack()
    finished.pack()

    root.mainloop()
