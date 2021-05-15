import tkinter as tk
import tkinter.ttk as ttk

main_window = tk.Tk()

frame = tk.LabelFrame(
    master = main_window,
    text = "Teste",
)

label = tk.Label(
    master = frame,
    text = "Bom dia!"
)

label.pack()
frame.pack(expand=True, fill=tk.BOTH)

main_window.mainloop()