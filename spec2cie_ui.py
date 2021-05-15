import tkinter as tk
import tkinter.ttk as ttk
from tkinter.font import Font
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.pyplot import close as plot_close
from sys import exit as sys_exit
from spec2cie import (spectrum_container, plot_container)

#-----------------------------------------------------------------------------
# Initialize the main window
#-----------------------------------------------------------------------------

main_window = tk.Tk()
main_window.title("Spectrum to CIE 1931")
#main_window.geometry("1024x700")
#main_window.minsize(160, 90)

# Exit the program properly when closing the window or pressing Alt+F4
main_window.bind("<Alt-F4>", lambda event: plot_close("all"))
main_window.protocol("WM_DELETE_WINDOW", sys_exit)
"""NOTE
This is necessary because Matplotlib does not automatically close the plots
when the window is closed. That would cause the program to hang on the shell.
"""

# Left column - Color and spectrum tables
main_window.columnconfigure(
    0,
    weight = 1,
    minsize = 300
)

# Right column - CIE Chromaticity Diagram
main_window.columnconfigure(
    1,
    weight = 1,
    minsize = 480,
)

# Top row - Toolbar
main_window.rowconfigure(
    0,
    weight = 0,
)

# Next two rows (left column) - Tables
main_window.rowconfigure(
    1,
    weight = 1,
)
main_window.rowconfigure(
    2,
    weight = 1,
)

#-----------------------------------------------------------------------------
# Initialise the spectrum container
#-----------------------------------------------------------------------------

spectrum_box = spectrum_container(tk_window=main_window)
spectrum_count = 0
spectrum_CIEx = []
spectrum_CIEy = []

#-----------------------------------------------------------------------------
# Menu bar
#-----------------------------------------------------------------------------

# Disable detachable menus
main_window.option_add("*tearOff", tk.FALSE)

# Create menu bar on the main window
menubar = tk.Menu(main_window)
main_window["menu"] = menubar

# Create top level menus
menu_file = tk.Menu(menubar)
menu_edit = tk.Menu(menubar)
menu_help = tk.Menu(menubar)
menubar.add_cascade(menu=menu_file, label="File")
menubar.add_cascade(menu=menu_edit, label="Edit")
menubar.add_cascade(menu=menu_help, label="Help")

# Add File commands
menu_file.add_command(
    label = "Add spectra to diagram...",
    command = spectrum_box.import_files,
    accelerator = "Ctrl+O",
)
menu_file.add_command(
    label = "New diagram",
    accelerator = "Ctrl+N",
    # command = ,
)

menu_file.add_separator()

menu_file.add_command(
    label = "Save figure...",
    accelerator = "Ctrl+S",
    # command = ,
)

menu_file.add_command(
    label = "Save coordinates to text...",
    accelerator = "Ctrl+T",
    # command = ,
)

menu_file.add_separator()

menu_file.add_command(
    label = "Close",
    accelerator = "Alt+F4",
    command = sys_exit,
)

# Add Edit commands
show_gridlines = tk.BooleanVar()
show_gridlines.set(True)
menu_edit.add_checkbutton(
    label = "Show grid lines",
    variable = show_gridlines,
    onvalue = True,
    offvalue = False,
    accelerator = "F2",
    #command = ,
)

show_axis = tk.BooleanVar()
show_axis.set(True)
menu_edit.add_checkbutton(
    label = "Show axis",
    variable = show_axis,
    onvalue = True,
    offvalue = False,
    accelerator = "F3",
    #command = ,
)

show_locus = tk.BooleanVar()
show_locus.set(True)
menu_edit.add_checkbutton(
    label = "Show spectral locus",
    variable = show_locus,
    onvalue = True,
    offvalue = False,
    accelerator = "F4",
    #command = ,
)

menu_edit.add_separator()

menu_edit.add_command(
    label = "Delete selected spectra",
    accelerator = "Del",
    #command = ,
)
menu_edit.add_command(
    label = "Delete all spectra",
    #command = ,
)

# Add Help commands
menu_help.add_command(
    label = "Help",
    accelerator = "F1",
    # command = ,
)

menu_help.add_separator()

menu_help.add_command(
    label = "About",
    # command = ,
)

#-----------------------------------------------------------------------------
# Button to load spectrum files
#-----------------------------------------------------------------------------

button_open_files = tk.Button(
    master = main_window,
    text = "Open files",
    command = spectrum_box.import_files
)
button_open_files.grid(
    column = 0,
    row = 0,
    sticky = "snw",
)


#-----------------------------------------------------------------------------
# Treeview to show the spectrum color data
#-----------------------------------------------------------------------------

style = ttk.Style()
style.theme_use("alt")  # Styles: "clam", "alt", "default", "classic"

# Fix for not being able to apply tags to a Treeview - https://stackoverflow.com/a/67141755
if main_window.getvar('tk_patchLevel')=='8.6.9': #and OS_Name=='nt':
    def fixed_map(option):
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.
        #
        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        return [elm for elm in style.map('Treeview', query_opt=option) if elm[:2] != ('!disabled', '!selected')]
    style.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))

# Frame to hold the treeview and its scrollbar
frame_tree_spectrum = ttk.Frame(
    master = main_window
)

# Create a treeview
tree_spectrum = ttk.Treeview(
    master = frame_tree_spectrum,
    columns = ("CIE x", "CIE y", "CIE z"),
    #height = 30
)

# Scrollbar for the treeview
scroll_tree_spectrum = ttk.Scrollbar(
    master = frame_tree_spectrum,
    orient = tk.VERTICAL,
    command = tree_spectrum.yview
)
tree_spectrum["yscrollcommand"] = scroll_tree_spectrum.set

# The titles of each column
tree_spectrum.heading("#0", text="Spectrum")
tree_spectrum.heading("#1", text="CIE x")
tree_spectrum.heading("#2", text="CIE y")
tree_spectrum.heading("#3", text="CIE z")

# The aligment of the text in the cells
# Leftmost column has the text aligned to the left, while all others columns have centered text
tree_spectrum.column("#0", anchor=tk.W, minwidth=100, width=100, stretch=True)
tree_spectrum.column("#1", anchor=tk.CENTER, minwidth=50, width=50, stretch=True)
tree_spectrum.column("#2", anchor=tk.CENTER, minwidth=50, width=50, stretch=True)
tree_spectrum.column("#3", anchor=tk.CENTER, minwidth=50, width=50, stretch=True)

# The background colors for odd and even rows (to make rows alternate colors)
tree_spectrum.tag_configure(
    "odd",
    background = "gray92",
    foreground = "black",
)
tree_spectrum.tag_configure(
    "even",
    background = "white",
    foreground = "black"
)

# Update the window when new files are successfully loaded
def update_spectrum_window(event):
    global spectrum_count, spectrum_CIEx, spectrum_CIEy, spectrum_box, canvas

    count_start = spectrum_count

    # Populate the lists of the CIE xy color coordinates
    for spectrum in spectrum_box[spectrum_count:]:
        spectrum_CIEx.append(spectrum.x)
        spectrum_CIEy.append(spectrum.y)
    
    # Add the the color coordinates to the treeview and the diagram
    for i in range(spectrum_count, len(spectrum_box)):
        
        # Set the background colors for the odd and even rows
        if spectrum_count % 2 == 1:
            format_tag = ("odd",)
        else:
            format_tag = ("even",)

        spectrum_count += 1

        # Append the data to the treeview
        last_item = tree_spectrum.insert(
            parent = "",
            index = tk.END,
            text = f"{spectrum_count:>2}. {spectrum_box[i].file_name}",
            values = (f"{spectrum_CIEx[i]:.3f}", f"{spectrum_CIEy[i]:.3f}", f"{1.0 - spectrum_CIEx[i] - spectrum_CIEy[i]:.3f}"),
            tags = format_tag
        )
        """NOTE:
        On the first column, if the spectrum count is a single digit, then it gets a white space added to its left.
        This way the labels look better, because all the periods after the count get aligned vertically (on counts up to 99).
        If the count goes to the 3 digits, the periods just get misaligned. I doubt that anyone is going to add 100+ files,
        and even if they do the misalignment will be hardly a problem on longer labels.

        On a related note, for the Treeview the coordinates values get rounded to 3 decimals. This is the precision normally
        seen on literature, and 3 decimals on each coordinate (x,y) already covers one million different colors. Any more
        decimals would hardly produce any difference on the perceived color, plus it likely is beyond the experimental error.

        The plotting still uses the maximum precision provided by Python.
        """

    # Change the selection to the last item, if no more than 1 item is already selected
    if len(tree_spectrum.selection()) <= 1:
        tree_spectrum.selection_set(last_item)
    
    # Change the focus to the last item
    tree_spectrum.focus(last_item)

    # Plot the point to the spectra
    plot.plot_cie(spectrum_CIEx[count_start:spectrum_count], spectrum_CIEy[count_start:spectrum_count])
    canvas.draw()

# Bind the update function to the "Files Imported" event
main_window.bind("<<FilesImported>>", update_spectrum_window)

scroll_tree_spectrum.pack(
    side = tk.RIGHT,
    fill = tk.Y
)
tree_spectrum.pack(side = tk.RIGHT,
    expand = True,
    fill = tk.BOTH,
)

frame_tree_spectrum.grid(
    column = 0,
    row = 2,
    sticky = "nsew",
    padx = 3,
    pady = 3,
)

#-----------------------------------------------------------------------------------------------------------------

frame_cie = tk.Frame(
    master = main_window,
    borderwidth = 2,
    relief = tk.SUNKEN,
)
plot = plot_container()
canvas = FigureCanvasTkAgg(plot.fig_CIE, master = frame_cie)
canvas.get_tk_widget().pack(
    expand = True,
    fill = tk.BOTH,
)


frame_cie.grid(
    column = 1,
    row = 1,
    rowspan = 2,
    sticky = "nsew",
    padx = 3,
    pady = 3,
)

canvas.draw()

toolbar = NavigationToolbar2Tk(canvas, main_window, pack_toolbar=False)
toolbar.update()
toolbar.grid(
    column = 1,
    row = 0,
    sticky = "w",
)
#-----------------------------------------------------------------------------------------------------------------

main_window.mainloop()