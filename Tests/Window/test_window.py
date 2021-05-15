import tkinter as tk

window = tk.Tk()

frame_left = tk.Frame(
    master = window,
)
frame_right = tk.Frame(
    master = window,
)


obj_left_top = tk.Label(
    master = frame_left,
    background = "grey",
)
obj_left_bottom = tk.Label(
    master = frame_left,
    background = "black",
)
obj_right_top = tk.Label(
    master = frame_right,
    background = "red",
)
obj_right_middle = tk.Label(
    master = frame_right,
    background = "green",
)
obj_right_bottom = tk.Label(
    master = frame_right,
    background = "blue",
)


frame_left.grid(
    row = 0,
    column = 0,
    sticky="nsew",
)
frame_right.grid(
    row = 0,
    column = 1,
    sticky="nsew",
)

window.columnconfigure(
    0,
    weight = 1,
    minsize = 640,
)
window.rowconfigure(
    0,
    weight = 1,
    minsize = 640,
)


obj_left_top.grid(
    row=0,
    column=0,
    sticky="nsew",
)
obj_left_bottom.grid(
    row=1,
    column=0,
    sticky="nsew",
)
obj_right_top.grid(
    row=0,
    column=1,
    sticky="nsew",
)
obj_right_middle.grid(
    row=1,
    column=1,
    sticky="nsew",
)
obj_right_bottom.grid(
    row=2,
    column=1,
    sticky="nsew",
)

frame_left.rowconfigure(
    0,
    weight = 1,
    minsize = 20,
)
frame_left.rowconfigure(
    1,
    weight = 1,
    minsize = 640,
)
frame_left.columnconfigure(
    0,
    weight = 1,
    minsize = 640,
)

window.mainloop()