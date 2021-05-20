import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import askyesno
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib as mpl
import os
import sys
from spec2cie import (spectrum_container, plot_container)

#-----------------------------------------------------------------------------
# Initialize the main window
#-----------------------------------------------------------------------------

main_window = tk.Tk()
main_window.title("Spectrum to CIE 1931")
#main_window.geometry("1024x700")
#main_window.minsize(160, 90)


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
    minsize = 540,
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
spectrum_count = 0          # How many spectra are stored in the container
spectrum_CIEx = []          # List the x CIE color coordinate for each spectrum
spectrum_CIEy = []          # List the y CIE color coordinate for each spectrum
spectrum_CIE_dict = {}      # Dictionary to associate each plotted point to its spectrum

#-----------------------------------------------------------------------------
# Global flags
#-----------------------------------------------------------------------------

confirm_exit = False                # Confirm wheter the user wants to close the program
                                    # This will be set to True when a file is imported and to False when a file is saved

show_gridlines = tk.BooleanVar()    # Display the grid lines on the Chromaticity Diagram (Default: False)
show_gridlines.set(False)
show_axis = tk.BooleanVar()         # Display the axis (x and y) and the bounding box on the diagram (Default: True)
show_axis.set(True)
show_labels = tk.BooleanVar()       # Display the numbering on each point of the graph (Default: True)
show_labels.set(True)

#-----------------------------------------------------------------------------
# Callback functions
#-----------------------------------------------------------------------------

# --- Update the window when new files are successfully loaded ---#

def update_spectrum_window(event):
    global spectrum_count, spectrum_CIEx, spectrum_CIEy, spectrum_CIE_dict, spectrum_box, canvas, confirm_exit

    count_start = spectrum_count

    # Populate the lists of the CIE xy color coordinates
    for spectrum in spectrum_box[spectrum_count:]:
        spectrum_CIEx.append(spectrum.x)
        spectrum_CIEy.append(spectrum.y)
    
    # Add the the color coordinates to the treeview and the diagram
    first_loop = True
    for i in range(spectrum_count, len(spectrum_box)):
        
        # Set the background colors for the odd and even rows
        if spectrum_count % 2 == 1:
            format_tag = ("odd",)
        else:
            format_tag = ("even",)

        spectrum_count += 1

        # Append the data to the treeview
        CIE_point = tree_spectrum.insert(
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
        
        # Update the dictionary that holds which item corresponds to which spectrum in the container
        spectrum_CIE_dict.update({CIE_point: spectrum_box[i]})
        
        # Stores the ID of first imported item, so it can be highlighted on the treeview
        if first_loop:
            first_item = CIE_point
            first_loop = False

    # Change the selection to the first imported item, if no more than 1 item is already selected
    if len(tree_spectrum.selection()) <= 1:
        tree_spectrum.selection_set(first_item)
    
    # Change the focus to the first imported item
    tree_spectrum.focus(first_item)

    # Plot the point to the spectra
    plot.plot_cie(spectrum_CIEx[count_start:spectrum_count], spectrum_CIEy[count_start:spectrum_count])
    canvas.draw()

    # Turn on exit confirmation
    confirm_exit = True

# Bind the update function to the "Files Imported" event
main_window.bind("<<FilesImported>>", update_spectrum_window)


#--- Saving the CIE diagram ---#

def save_diagram():
    toolbar.save_figure()

def disable_exit_confirmation(*event):
    global confirm_exit
    confirm_exit = False

main_window.bind("<<FigureSaved>>", disable_exit_confirmation)


# --- Updating the color information frame
def update_color_info(event):
    """ Updates automatically the color information frame when the user select a single spectrum.
    """
    global cell_spectrum_title, cell_x_value_text, cell_y_value_text, cell_z_value_text

    selected = tree_spectrum.selection()
    if len(selected) != 1:
        return False
    """NOTE
    I am doing the logic based on the selected items, instead of the focused item
    because of two reasons:
      1. It's more obvious to the user which item is active, because the focus is shown more subtly
      2. In order for the focus to work, the user would need to click on the Treeview.
         I want the information to update automatically to the latest imported spectrum, and that
         wouldn't happen if it was based on focus (item focus cannot change unless the Treeview is
         also focused).
    
    I am checking if exactly one item is selected so the frame does not keep updating while the user
    is doing a multiple selection with Ctrl held and clicking. That would be annoying and potentially
    also slow down the selection.
    """

    point = selected[0]
    spectrum = spectrum_CIE_dict[point]

    # Display the spectrum's title
    cell_spectrum_title["text"] = tree_spectrum.item(point, option="text")

    # Get CIE coordinates from the Treeview and display them on the color info frame
    CIE = tree_spectrum.item(point, option="values")
    cell_x_value_text.set(CIE[0])
    cell_y_value_text.set(CIE[1])
    cell_z_value_text.set(CIE[2])

    # Get the RGB color from the spectrum and display the color
    color_RGB = [int(255 * color) for color in spectrum.RGB]    # Integer list [Red, Green, Blue] on the 0..255 range

    color_hex = hex((color_RGB[0] << 16) | (color_RGB[1] << 8) | (color_RGB[2]))    # Convert the color values to hexadecimal
    color_hex = color_hex.replace("0x", "", 1)  # Remove the "0x" from the beginning
    color_hex = color_hex.rjust(6, "0")         # Ensure that the string is 6 characters long (fill with leading "0", if needed)
    color_hex = "#" + color_hex                 # Add a "#" to the beginning
    cell_color_display["bg"] = color_hex        # Display the color

# Bind the function to the Treeview Select event
main_window.bind("<<TreeviewSelect>>", update_color_info)


#--- Exiting the program ---#

# As the user if they want to close the program, when there are still stuff to save
def clean_exit(*event):
    if confirm_exit:
        confirmation = askyesno(
            master = main_window,
            title = "Confirm exit",
            message = "Unsaved data will be lost. Continue?",
            default = "no",
        )
        if confirmation:
            sys.exit()
    else:
        sys.exit()

# Exit the program properly when closing the window or pressing Alt+F4
main_window.bind("<Alt-F4>", clean_exit)
main_window.protocol("WM_DELETE_WINDOW", clean_exit)
"""NOTE
Those bindings are necessary because Matplotlib does not automatically close
the plots when the window is closed. That would cause the program to hang on
the shell.
"""

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
    label = "Import spectra...",
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
    label = "Save diagram...",
    accelerator = "Ctrl+S",
    command = save_diagram,
)

menu_file.add_command(
    label = "Export coordinates...",
    accelerator = "Ctrl+E",
    # command = ,
)

menu_file.add_separator()

menu_file.add_command(
    label = "Close",
    accelerator = "Alt+F4",
    command = clean_exit,
)

# Add Edit commands
menu_edit.add_checkbutton(
    label = "Show grid lines",
    variable = show_gridlines,
    onvalue = True,
    offvalue = False,
    accelerator = "F2",
    #command = ,
)

menu_edit.add_checkbutton(
    label = "Show axis",
    variable = show_axis,
    onvalue = True,
    offvalue = False,
    accelerator = "F3",
    #command = ,
)

menu_edit.add_checkbutton(
    label = "Show labels",
    variable = show_labels,
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
# Color information frame
#-----------------------------------------------------------------------------

frame_color_info = tk.LabelFrame(
    master = main_window,
    text = "Color coordinate"
)

# Spectrum name

cell_spectrum_title = tk.Label(
    master = frame_color_info,
    text = "Please import spectra (Ctrl+O or File menu)",
    anchor = "w",
)

# Coordinates names

cell_x_name = tk.Label(
    master = frame_color_info,
    text = "CIE x =",
)
cell_y_name = tk.Label(
    master = frame_color_info,
    text = "CIE y =",
)
cell_z_name = tk.Label(
    master = frame_color_info,
    text = "CIE z =",
)

# Coordinates values (can be copied by the user)

cell_value_arguments = dict(
    master = frame_color_info,
    state = "readonly",
    readonlybackground = "#f8f8f8",
    foreground = "black",
)

cell_x_value_text = tk.StringVar()
cell_y_value_text = tk.StringVar()
cell_z_value_text = tk.StringVar()

cell_x_value = tk.Entry(textvariable=cell_x_value_text, **cell_value_arguments)
cell_y_value = tk.Entry(textvariable=cell_y_value_text, **cell_value_arguments)
cell_z_value = tk.Entry(textvariable=cell_z_value_text, **cell_value_arguments)

# Label to display the color itself

cell_color_display = tk.Label(
    master = frame_color_info,
    borderwidth = 1,
    relief = tk.SUNKEN,
)

# Adding the cells to the frame

cell_padding = 5

cell_spectrum_title.grid(
    column = 0,
    row = 0,
    columnspan = 3,
    sticky = "we",
    padx = cell_padding,
)

cell_x_name.grid(
    column = 0,
    row = 1,
    padx = cell_padding,
)
cell_y_name.grid(
    column = 0,
    row = 2,
    padx = cell_padding,
)
cell_z_name.grid(
    column = 0,
    row = 3,
    padx = cell_padding,
)
cell_x_value.grid(
    column = 1,
    row = 1,
)
cell_y_value.grid(
    column = 1,
    row = 2,
)
cell_z_value.grid(
    column = 1,
    row = 3,
)
cell_color_display.grid(
    column = 2,
    row = 1,
    rowspan = 3,
    sticky = "nsew",
    padx = cell_padding,
    ipady = cell_padding,
)

frame_color_info.columnconfigure(
    2,
    weight = 1,
)

# Add the frame to the main window
frame_color_info.grid(
    column = 0,
    row = 0,
    rowspan = 2,
    sticky = "nsew",
    padx = 3,
    pady = 3,
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

# Pack the scrollbar to the right side of the frame and make the bar fill the entire height
scroll_tree_spectrum.pack(
    side = tk.RIGHT,
    fill = tk.Y
)
# Pack the treeview to the frame and make the treeview to fill the remaining space on the frame
tree_spectrum.pack(side = tk.RIGHT,
    expand = True,
    fill = tk.BOTH,
)

# Add the treeview frame to the main window grid, and make it fill the available space
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

# Modify the save_figure() method of the  avigationToolbar2Tk class
"""NOTE
The only change I am making is to add en event generated when the figure is successfully saved.
That event is used to toggle off the exit confirmation after the figure is saved.
"""
class NavigationToolbar2Tk_modified(NavigationToolbar2Tk):
    def save_figure(self, *args):
        filetypes = self.canvas.get_supported_filetypes().copy()
        default_filetype = self.canvas.get_default_filetype()

        # Tk doesn't provide a way to choose a default filetype,
        # so we just have to put it first
        default_filetype_name = filetypes.pop(default_filetype)
        sorted_filetypes = ([(default_filetype, default_filetype_name)]
                            + sorted(filetypes.items()))
        tk_filetypes = [(name, '*.%s' % ext) for ext, name in sorted_filetypes]

        # adding a default extension seems to break the
        # asksaveasfilename dialog when you choose various save types
        # from the dropdown.  Passing in the empty string seems to
        # work - JDH!
        #defaultextension = self.canvas.get_default_filetype()
        defaultextension = ''
        initialdir = os.path.expanduser(mpl.rcParams['savefig.directory'])
        initialfile = self.canvas.get_default_filename()
        fname = tk.filedialog.asksaveasfilename(
            master=self.canvas.get_tk_widget().master,
            title='Save the figure',
            filetypes=tk_filetypes,
            defaultextension=defaultextension,
            initialdir=initialdir,
            initialfile=initialfile,
            )

        if fname in ["", ()]:
            return
        # Save dir for next time, unless empty str (i.e., use cwd).
        if initialdir != "":
            mpl.rcParams['savefig.directory'] = (
                os.path.dirname(str(fname)))
        try:
            # This method will handle the delegation to the correct type
            self.canvas.figure.savefig(fname)
            """ Change begin """
            self.window.event_generate("<<FigureSaved>>", when="tail")
            self.window.update()
            """ Change end """
        except Exception as e:
            tk.messagebox.showerror("Error saving file", str(e))

toolbar = NavigationToolbar2Tk_modified(canvas, main_window, pack_toolbar=False)
toolbar.update()
toolbar.grid(
    column = 1,
    row = 0,
    sticky = "w",
)

# toolbar.message.get()
#-----------------------------------------------------------------------------------------------------------------

main_window.mainloop()