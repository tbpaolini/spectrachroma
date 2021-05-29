import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import (askyesno, showerror)
from tkinter.filedialog import asksaveasfilename
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib as mpl
import xlsxwriter as excel
import os, sys, gc, re
from spec2cie import (spectrum_container, plot_container)

#-----------------------------------------------------------------------------
# Initialize the main window
#-----------------------------------------------------------------------------

main_window = tk.Tk()
main_window.title("SpectraChroma")
#main_window.geometry("1024x700")
main_window.minsize(840, 590)
#main_window.iconbitmap("icon.ico")
main_window.iconphoto(True, tk.PhotoImage(file="lib\icon.png"))


# Left column - Color and spectrum tables
main_window.columnconfigure(
    0,
    weight = 1,
    minsize = 300
)

# Right column - CIE Chromaticity Diagram
main_window.columnconfigure(
    1,
    weight = 2,
    minsize = 540,
)

# Top row - Toolbar
main_window.rowconfigure(
    0,
    weight = 0,
)

# Next two rows (left column) - Tables
main_window.rowconfigure(
    # Color information table
    1,
    weight = 2,
)
main_window.rowconfigure(
    # Treeview table
    2,
    weight = 1,
)

#-----------------------------------------------------------------------------
# Initialise the containers
#-----------------------------------------------------------------------------

# Spectrum container
spectrum_box = spectrum_container(tk_window=main_window)
spectrum_count = 0          # How many spectra are stored in the container
spectrum_CIEx = []          # List the x CIE color coordinate for each spectrum
spectrum_CIEy = []          # List the y CIE color coordinate for each spectrum
spectrum_CIE_dict = {}      # Dictionary to associate each plotted point to its spectrum

# Container for the Chromaticity Diagram and the Spectral Distribution
plot = plot_container()
current_sd = None           # Which Spectral Distribution is being shown
previous_sd = None          # Which Spectral Distribution was shown last (so it can be hidden when a new one is shown)

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

#--- Import spectra ---#

def import_spectra(*event):
    spectrum_box.import_files()

main_window.bind("<Control-o>", import_spectra)     # Bind to the Ctrl+O shortcut


# --- Update the window when new files are successfully loaded ---#

def update_spectrum_window(event):
    global spectrum_count, spectrum_CIEx, spectrum_CIEy, spectrum_CIE_dict, spectrum_box, canvas_CIE, confirm_exit

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
    canvas_CIE.draw()

    # Create the spectral distribution for each new spectrum
    plot.plot_sd(spectrum_box[count_start:spectrum_count])

    # Turn on exit confirmation
    confirm_exit = True

    # Enable menu options
    menu_file.entryconfigure(4, state=tk.NORMAL)    # File > Save spectral distribution
    menu_file.entryconfigure(5, state=tk.NORMAL)    # File > Export coordinates
    menu_edit.entryconfigure(4, state=tk.NORMAL)    # Edit > Select all spectra
    menu_edit.entryconfigure(5, state=tk.NORMAL)    # Edit > Delete selected spectra
    menu_edit.entryconfigure(6, state=tk.NORMAL)    # Edit > Delete all spectra

# Bind the update function to the "Files Imported" event
main_window.bind("<<FilesImported>>", update_spectrum_window)


#--- Saving the CIE diagram ---#

def save_diagram(*event):
    toolbar.save_figure()

def disable_exit_confirmation(*event):
    global confirm_exit
    confirm_exit = False

main_window.bind("<<FigureSaved>>", disable_exit_confirmation)  # Turn off exit confirmation when the diagram is saved
main_window.bind("<Control-s>", save_diagram)                   # Bind diagram saving to the Ctrl+S shortcut

#--- Convert RGB color to hexadecimal (HTML representation)---#

def rgb_to_hex(color_RGB):
    """Takes a sequence of 3 elements (each one a integer from 0 to 255), representing a RGB color.
    Returns the HTML representation of the color (hexadecimal): #RRGGBB
    """

    color_hex = hex((color_RGB[0] << 16) | (color_RGB[1] << 8) | (color_RGB[2]))    # Convert the color values to hexadecimal
    color_hex = color_hex.replace("0x", "", 1)  # Remove the "0x" from the beginning
    color_hex = color_hex.rjust(6, "0")         # Ensure that the string is 6 characters long (fill with leading "0", if needed)
    color_hex = "#" + color_hex                 # Add a "#" to the beginning

    return color_hex


#--- Exporting the coordinates to a text file ---#

def export_coordinates(*event):

    if menu_file.entrycget(5, "state") == tk.DISABLED:
        return False    # Exit the funtion when there is no data to be exported
    
    save_path = asksaveasfilename(
        parent =  main_window,
        title = "Exporting CIE color coordinates",
        defaultextension = "",
        filetypes = (("Microsoft Excel spreadsheet (*.xlsx)", "*.xlsx"), ("Text file (*.txt)", "*.txt")),
    )
    
    if save_path == "":
        return False

    if save_path.endswith(".xlsx"):     # File is being saved as Microsoft Excel spreadsheet
        
        workbook = excel.Workbook(save_path)            # Create the workbook (a colection of spreadsheets)
        worksheet = workbook.add_worksheet("CIE 1931")  # Create a spreadsheet on the workbook

        # Format the first row to bold
        bold = workbook.add_format({'bold': True})
        worksheet.set_row(0, None, bold)

        # Write the title headers on the first row
        worksheet.write(0, 0, "Spectrum")   # Column A
        worksheet.write(0, 1, "CIE x")      # Column B
        worksheet.write(0, 2, "CIE y")      # Column C
        worksheet.write(0, 3, "CIE z")      # Column D
        worksheet.write(0, 4, "RGB color")  # Column E

        # Loop through all spectra and write their color coordinates to the spreadsheet
        for row, spectrum in enumerate(spectrum_CIE_dict.values(), 1):

            # Get the RGB color and use it as the background of its own cell
            color_RGB = tuple(int(255 * color) for color in spectrum.RGB)
            color_hex = rgb_to_hex(color_RGB)
            background = workbook.add_format({"bg_color" : color_hex})

            # Write each cell of the row
            worksheet.write(row, 0, spectrum.file_name)             # Spectrum
            worksheet.write(row, 1, spectrum.x)                     # CIE x
            worksheet.write(row, 2, spectrum.y)                     # CIE y
            worksheet.write(row, 3, 1.0 - spectrum.x - spectrum.y)  # CIE z
            worksheet.write(row, 4, str(color_RGB), background)     # RGB color

        # Enlarge the columns A (Spectrum) and E (RBG color), so their contents are better displayed
        worksheet.set_column(0, 0, 30)          # 30 numeric characters wide
        worksheet.set_column_pixels(4, 4, 95)   # 95 pixels wide
        """NOTE
        It is not possible to do an "auto fit" column through code, only when viewing the file on Excel.
        The correlation between the width of the column and the number of characters is now trivial,
        it depends on the screen resolution and the default font (which can have variable character width).
        More info: https://docs.microsoft.com/en-US/office/troubleshoot/excel/determine-column-widths
                   https://xlsxwriter.readthedocs.io/worksheet.html#set_column
        
        That width is based on numeric characters, however the file names usually use mostly letters.
        It is perhaps not possibly the reliably calculate the maximum width of the text in Column A.
        So I instead just set it to a reasonable value so most of the text can be shown.
        """

        try:
            workbook.close()    # Finish writing to the workbook and save the file
        except excel.exceptions.FileCreateError:
            # Display a error if the file was already in use
            showerror(
                master = main_window,
                title = "Save error",
                message = f"Could not save to {save_path}\nThe file is already in use by another program."
            )
            del worksheet
            del workbook
    
    else:   # File is being saved as plain text

        try:
            with open(save_path, "w") as file:

                # Write the header titles
                file.write(f"{'Spectrum':<20}\tCIE x\tCIE y\tCIE z\tRGB color\n")
                
                # Loop through each spectrum and write its color coordinates to a new line
                for spectrum in spectrum_CIE_dict.values():
                    color_RGB = tuple(int(255 * color) for color in spectrum.RGB)
                    line = f"{spectrum.file_name:<20}\t{spectrum.x:.3f}\t{spectrum.y:.3f}\t{1.0 - spectrum.x - spectrum.y:.3f}\t{color_RGB}\n"
                    file.write(line)
        
        except PermissionError:
            # Display a error if the file was already in use
            showerror(
                master = main_window,
                title = "Save error",
                message = f"Could not save to {save_path}\nThe file is already in use by another program."
            )

main_window.bind("<Control-e>", export_coordinates)


#--- Exporting the Spectral Distribution ---#

def save_sd(*event):
    if current_sd:
        plot.save_sd(current_sd)

# Bind the function to the Ctrl+D shortcut
main_window.bind("<Control-d>", save_sd)

# --- Updating the color information frame
def update_color_info(event):
    """ Updates automatically the color information frame when the user select a single spectrum.
    """
    global cell_spectrum_title, cell_x_value_text, cell_y_value_text, cell_z_value_text, canvas_sd, \
        current_sd, previous_sd

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
    color_hex = rgb_to_hex(color_RGB)                           # Convert the color to the hexadecimal format: #RRGGBB
    cell_color_display["bg"] = color_hex                        # Display the color

    # Update the Spectral Distribution
    previous_sd = current_sd            # Store the previous Spectral Distribution
    current_sd = plot.ax_sd[spectrum]   # Get the current distribution
    if previous_sd:
        previous_sd.set_visible(False)  # Switch off the previous distribution
    current_sd.set_visible(True)        # Switch on the current distribution
    canvas_sd.draw()                    # Update the canvas so the distribution is show

# Bind the function to the Treeview Select event
main_window.bind("<<TreeviewSelect>>", update_color_info)


#--- Clear the values of color info frame ---#

def reset_color_info(*event):
    """Remove the values from the color info frame.
    This function will be called when no items on the Treeview are selected.
    """
    global previous_sd, current_sd
    
    cell_spectrum_title["text"] = "Please select or add a spectrum to display its color coordinate"
    cell_x_value_text.set("")
    cell_y_value_text.set("")
    cell_z_value_text.set("")
    cell_color_display["bg"] = "#f0f0f0"

    if current_sd:
        current_sd.set_visible(False)
    canvas_sd.draw()
    current_sd = None
    previous_sd = None


#--- Toggle grid lines on the Chromaticity Diagram ---#

def toggle_gridlines(*event, reset=False):
    """Switch on/off the gridlines on the Chromaticity Diagram
    """
    
    if len(event) > 0:
        shortcut = True
    else:
        shortcut = False
    """NOTE
    If the "event" argument was sent to the function, then that means that
    the function was activated by its shortcut key rather than chosen on
    the menu.
    So len(event) will always be 0 when the function is activated by the
    menu, and will be 1 when activated by the shortcut.
    This is important because the option flag is switched automatically
    when actiavted through the menu, but in the case of a shortcut being used
    I need to switch through my code.
    """
    
    # Toggle the variable if the shortcut key was used
    if shortcut:
        old_value = show_gridlines.get()
        show_gridlines.set(not old_value)
    elif reset:
        show_gridlines.set(False)
    
    # Display or remove the grid lines
    if show_gridlines.get():    # Grid lines are enabled
        plot.ax_CIE.grid(alpha = 0.3)
        canvas_CIE.draw()
    
    else:                       # Grid lines are disabled
        plot.ax_CIE.grid(False)
        canvas_CIE.draw()

# Bind the function to the F2 shortcut
main_window.bind("<F2>", toggle_gridlines)


#--- Toggle grid lines on the Chromaticity Diagram ---#

def toggle_axis(*event, reset=False):
    """Switch on/off the axes on the Chromaticity Diagram
    """
    
    # Verify if the shortcut key was used
    if len(event) > 0:
        shortcut = True
    else:
        shortcut = False
    
    # Toggle the variable if the shortcut key was used
    if shortcut:
        old_value = show_axis.get()
        show_axis.set(not old_value)
    elif reset:
        show_axis.set(True)
    
    # Display or remove the grid lines
    if show_axis.get():                     # Axes are enabled
        plot.ax_CIE.axis("on")              # Display axes
        plot.title_CIE.set_visible(True)    # Display title
        canvas_CIE.draw()
    
    else:                                   # Axes are disabled
        plot.ax_CIE.axis("off")             # Hide axes
        plot.title_CIE.set_visible(False)   # Hide title
        canvas_CIE.draw()

# Bind the function to the F3 shortcut
main_window.bind("<F3>", toggle_axis)


#--- Toggle grid lines on the Chromaticity Diagram ---#

def toggle_labels(*event, reset=False):
    """Switch on/off the data labels on the Chromaticity Diagram
    """
    
    # Verify if the shortcut key was used
    if len(event) > 0:
        shortcut = True
    else:
        shortcut = False
    
    # Toggle the variable if the shortcut key was used
    if shortcut:
        old_value = show_labels.get()
        show_labels.set(not old_value)
    elif reset:
        show_labels.set(True)
    
    # Display or remove the grid lines
    if show_labels.get():                     # Axes are enabled
        plot.show_labels_cie(True)              # Display axes
        canvas_CIE.draw()
    
    else:                                   # Axes are disabled
        plot.show_labels_cie(False)             # Hide axes
        canvas_CIE.draw()

# Bind the function to the F4 shortcut
main_window.bind("<F4>", toggle_labels)


#--- Deleting points from the diagram ---#

def delete_selected(*event, do_confirmation=True):
    """Remove from the diagram the points selected on the Treeview
    """
    
    # Get the current selection from the Treeview
    selected_items = tree_spectrum.selection()
    selected_amount = len(selected_items)

    if selected_amount == 0:
        return False
    
    # Whether the user is pressing the Shift key (True or False)
    if len(event) > 0:
        shift_key = bool(event[0].state & 0x0001)
    else:
        shift_key = False
    """NOTE
    The .state attribute returns a mask that tells which modifiers keys are active.
    The hexadecimal mask 0x0001 corresponds to the Shift key, so I am performing
    the bitwise AND to the state mask in order to check if the Shift key is active.
    
    The following page has a table of modifier key masks:
    https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html
    
    The "event" argument isn't passed when the function is called through the
    menu, only when the Delete key is pressed. So the items are only deleted
    without confirmation if the user press Shift+Del
    This behaviour is desired, since I always want a confirmation when deleting
    through the menu.
    """
    
    def do_deletion():
        global confirm_exit, spectrum_count, spectrum_CIEx, spectrum_CIEy, spectrum_CIE_dict

        # Delete the selected data from the containers
        for item in selected_items:
            spectrum = spectrum_CIE_dict[item]  # Spectrum handler
            
            # Remove spectrum from its container
            spectrum_box.id.remove(spectrum)
            
            # Remove the spectral distribution from its container
            plot.ax_sd[spectrum].cla()      # Clear axis
            plot.ax_sd[spectrum].remove()   # Delete axis
            del plot.ax_sd[spectrum]        # Delete its entry on the axis dictionary
            
            # Remove spectrum from the CIE coordinates dictionary
            del spectrum_CIE_dict[item]
        
        # Rebuild the lists of CIEx and CIEy coordinates
        """NOTE
        I am aware that those lists might be a little redundant with the spectrum_CIE_dict[], maybe
        it would be easier to just associate each spectrum to its coordinates. However when I started
        developing this program an ordered list just seemed to make more sense, and later it got clear
        that a dictionary would be necessary.

        Now I do not want to completely remove the lists, because that could break the file importing logic.
        And also because reading the data from an ordered list is still faster than reading from an
        unordered dictionary. So at the very least the file importing is more efficient, when speed is
        concerned :-)

        Just clearing and rebuilding the list from scratch should do the trick to keep data consistecy.
        """
        spectrum_CIEx.clear()
        spectrum_CIEy.clear()
        CIE_coordinate = spectrum_box.get_xy()
        spectrum_CIEx.extend(CIE_coordinate["x"])
        spectrum_CIEy.extend(CIE_coordinate["y"])
        spectrum_count = len(spectrum_CIEx)

        # Plot the remaining points to the Chromaticity Diagram
        """NOTE
        Similarly to above, just rebuilding the diagram's points is easier than removing only specific points and
        renumbering them.

        I am assuming that people will not import hundreds of spectra, which would make my approach ineficient.
        But realistically speaking, there's no need to import that big amount. Usually what I saw was 4 or 5 at
        most, but even with a few dozens spectra this program still run fast.
        """
        plot.flush_cie()                                    # Clear the diagram's points
        if spectrum_count > 0:
            plot.plot_cie(spectrum_CIEx, spectrum_CIEy)     # Plot the points of the remaining spectra
            confirm_exit = True                             # Turn on exit confirmation because the diagram has changed
        else:
            confirm_exit = False                            # Turn off exit confirmation because there are no remaining spectra
            menu_file.entryconfigure(4, state=tk.DISABLED)  # Disable menu option: File > Save spectral distribution
            menu_file.entryconfigure(5, state=tk.DISABLED)  # Disable menu option: File > Export coordinates
            menu_edit.entryconfigure(4, state=tk.DISABLED)  # Disable menu option: Edit > Select all spectra
            menu_edit.entryconfigure(5, state=tk.DISABLED)  # Disable menu option: Edit > Remove selected spectra
            menu_edit.entryconfigure(6, state=tk.DISABLED)  # Disable menu option: Edit > Remove all spectra
        
        canvas_CIE.draw()                                   # Update the diagram's canvas

        # Delete the selected items from the Treeview
        tree_spectrum.delete(*selected_items)

        # Change the selection to the first item on the Treeview
        if spectrum_count > 0:
            first_item = tree_spectrum.get_children()[0]
            tree_spectrum.selection_set(first_item)
            tree_spectrum.focus(first_item)
        
        # Run the garbage collector to free the memory that was being used by the removed spectra
        gc.collect()
    
    # Delete without confirmation if Shift is being held
    if shift_key:
        do_deletion()
    
    # Ask whether the user wants to delete the points
    else:
        # Confirmation message, based on if one or more items are selected
        if selected_amount == 1:
            item_name = spectrum_CIE_dict[selected_items[0]].file_name    # Name of the corresponding spectrum file
            confirmation_message = f"{item_name} will be removed from the list and diagram. Continue?"
        else:
            confirmation_message = f"{selected_amount} items will be removed from the list and diagram. Continue?"
        
        # Display the confirmation dialog
        if do_confirmation:
            confirmation = askyesno(
                master = main_window,
                title = "Confirm removal",
                message = confirmation_message,
                default = "no",
            )
        else:
            confirmation = True

        if confirmation:
            # Delete items if the user chose "yes"
            do_deletion()
        else:
            # Exit the function if the user chose "no"
            return False
    
    # Reset the color info frame
    reset_color_info()
    
    # Renumber and recolor the background of the Treeview's rows
    # (so they still keep the alternate colors while being numbered sequentially from 1)
    
    remaining_rows = tree_spectrum.get_children()   # Get the rows present on the Treeview

    for number,row in enumerate(remaining_rows):    # Enumerate the rows and loop through then
        
        if number % 2 == 1:         # Odd rows
            format_tag = ("odd",)
        else:                       # Even rows
            format_tag = ("even",)
        
        old_text = tree_spectrum.item(row, option = "text")
        new_text = f"{(number + 1):>2}{old_text.lstrip().lstrip('0123456789')}"
        """NOTE
        The first lstrip() only removes the spaces to the left,
        while the next lstrip() removes the digits to the left.
        """

        # Apply the format tag and new text
        tree_spectrum.item(row, tags = format_tag, text = new_text)  # Apply the corresponding format tag

# Bind the function to the Delete key
main_window.bind("<Delete>", delete_selected)


#--- Select all spectra ---#

def select_all(*event):
    all_items = tree_spectrum.get_children()
    tree_spectrum.selection_set(all_items)

# Bind the function to the Ctrl+A shortcut
main_window.bind("<Control-a>", select_all)


#--- Deleta all spectra ---#

def delete_all():
    select_all()
    delete_selected()


#--- New diagram ---#

def new_diagram(*event):
    # Delete all items (no confirmation, if the user has already saved the diagram)
    select_all()
    delete_selected(do_confirmation=confirm_exit)

    # Reset the diagram options
    toggle_gridlines(reset=True)
    toggle_axis(reset=True)
    toggle_labels(reset=True)

    # Reset to the original view
    toolbar.home()

main_window.bind("<Control-n>", new_diagram)

#--- Exiting the program ---#

# As the user if they want to close the program, when there are still stuff to save
def clean_exit(*event):
    global main_window
    if confirm_exit:
        confirmation = askyesno(
            master = main_window,
            title = "Confirm exit",
            message = "Unsaved diagram will be lost. Continue?",
            default = "no",
        )
        if confirmation:
            main_window.destroy()
            sys.exit()
    else:
        main_window.destroy()
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
# "Help" and "About" windows
#-----------------------------------------------------------------------------

class new_window():
    """Create the "Help" and the "About" windows, that are opened from the Help menu.
    That is done by calling the .help() or the .about() methods.
    """
    def __init__(self, parent_window):
        self.parent_window = parent_window  # Associate the new window to the main window
        self.open_windows = {}              # Store the open windows so any duplicates can be closed
    
    def __create_window(self, text_file, window_title):
        """Create a new window with the the contents of a text file.
        """
        
        # Create the window
        my_window = tk.Toplevel(
            master = self.parent_window,
        )

        # Set the window's title
        my_window.title(window_title)
        
        # Create the text box
        my_textbox = tk.Text(
            master = my_window,
            font = "TkDefaultFont",
            wrap = tk.WORD,
            padx = 5,
            pady = 5,
        )
        
        # Regular expression to match the titles
        # (digits followed by closing paranthesis and text)
        text_regex = re.compile(r"(?m)^\d+\).*$")
        
        # Open the text file and get its lines
        with open(text_file, "r") as obj_file:
            
            # Create the formating tags for titles and normal text
            my_textbox.tag_configure(
                "title",
                font = ("Georgia", "16", "bold"),
            )
            my_textbox.tag_configure(
                "normal",
                font = ("Georgia", "12"),
            )

            # Iterate through all lines in the file
            for line in obj_file:
                
                # Determine if the line is a title or not
                is_title = text_regex.match(line)
                
                # Add line to the text box
                if is_title:
                    # Title (bold and bigger)
                    my_textbox.insert(tk.END, line, ("title",))
                else:
                    # Normal text
                    my_textbox.insert(tk.END, line, ("normal",))
                
            
            # Disable the text box so the user cannot change the contents (but can still copy)
            my_textbox["state"] = tk.DISABLED

            # Create the scrollbar for the text box
            my_scrollbar = tk.Scrollbar(
                master = my_window,
                orient = tk.VERTICAL,       # Vertical scrolling
                command = my_textbox.yview  # Get the vertical position from the text box
            )

            # Associate the textbox to the scrollbar
            my_textbox["yscrollcommand"] = my_scrollbar.set

            # Pack the scrollbar to the window
            my_scrollbar.pack(
                side = tk.RIGHT,    # Add to the right of the window
                fill = tk.Y,        # Fill the whole height of the window
            )

            # Pack the textbox to the window
            my_textbox.pack(
                side = tk.RIGHT,    # Add next to the the scrollbar
                expand = True,      # Text box can be resized
                fill = tk.BOTH,     # Text box expands to fill all the available space
            )

            # Close duplicate window
            if self.open_windows.get(window_title, None):
                self.open_windows[window_title].destroy()
            
            # Store the opened window on the dictionary
            self.open_windows.update({window_title: my_window})
    
    def help(self, *event):
        """Create a Help window from the contents of the "Help.txt" file.
        """
        self.__create_window("lib\Help.txt", "Help")

    def about(self, *event):
        """Create a About window from the contents of the "About.txt" file.
        """
        self.__create_window("lib\Help.txt", "About")

# Instantiate the class
info_window = new_window(main_window)

# Make the Help window to be opened the F1 shortcut
main_window.bind("<F1>", info_window.help)

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
menubar.add_cascade(menu=menu_file, label="File", underline=0)
menubar.add_cascade(menu=menu_edit, label="Edit", underline=0)
menubar.add_cascade(menu=menu_help, label="Help", underline=0)

# Add File commands
menu_file.add_command(
    label = "Import spectra...",
    command = spectrum_box.import_files,
    accelerator = "Ctrl+O",
    underline = 0,  # Underline I during keyboard traversal
)
menu_file.add_command(
    label = "New diagram",
    accelerator = "Ctrl+N",
    underline = 0,  # Underline N during keyboard traversal
    command = new_diagram,
)

menu_file.add_separator()

menu_file.add_command(
    label = "Save chromaticity diagram...",
    accelerator = "Ctrl+S",
    underline = 5,  # Underline D during keyboard traversal
    command = save_diagram,
)

menu_file.add_command(
    label = "Save spectral distribution...",
    underline = 5,          # Underline S during keyboard traversal
    accelerator = "Ctrl+D",
    command = save_sd,
    state = tk.DISABLED,    # Will be enabled when a spectrum is imported
)

menu_file.add_command(
    label = "Export all color coordinates...",
    accelerator = "Ctrl+E",
    underline = 0,          # Underline E during keyboard traversal
    command = export_coordinates,
    state = tk.DISABLED,    # Will be enabled when a spectrum is imported
)

menu_file.add_separator()

menu_file.add_command(
    label = "Close",
    accelerator = "Alt+F4",
    underline = 0,          # Underline C during keyboard traversal
    command = clean_exit,
)

# Add Edit commands
menu_edit.add_checkbutton(
    label = "Show grid lines",
    variable = show_gridlines,
    onvalue = True,
    offvalue = False,
    accelerator = "F2",
    underline = 5,          # Underline G during keyboard traversal
    command = toggle_gridlines,
)

menu_edit.add_checkbutton(
    label = "Show axis",
    variable = show_axis,
    onvalue = True,
    offvalue = False,
    accelerator = "F3",
    underline = 5,          # Underline A during keyboard traversal
    command = toggle_axis,
)

menu_edit.add_checkbutton(
    label = "Show labels",
    variable = show_labels,
    onvalue = True,
    offvalue = False,
    accelerator = "F4",
    underline = 5,          # Underline L during keyboard traversal
    command = toggle_labels,
)

menu_edit.add_separator()

menu_edit.add_command(
    label = "Select all spectra",
    accelerator = "Ctrl+A",
    command = select_all,
    state = tk.DISABLED,    # Will be enabled when a spectrum is imported
)
menu_edit.add_command(
    label = "Remove selected spectra",
    accelerator = "Del",
    command = delete_selected,
    state = tk.DISABLED,    # Will be enabled when a spectrum is imported
)
menu_edit.add_command(
    label = "Remove all spectra",
    command = delete_all,
    state = tk.DISABLED,    # Will be enabled when a spectrum is imported
)

# Add Help commands
menu_help.add_command(
    label = "Help",
    accelerator = "F1",
    underline = 0,
    command = info_window.help,
)

menu_help.add_separator()

menu_help.add_command(
    label = "About",
    underline = 0,
    command = info_window.about,
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

# Spectral distribution

frame_sd = tk.Frame(
    master = frame_color_info,
    borderwidth = 2,
    relief = tk.SUNKEN,
    width = 280,
    height = 210,
)

# Create the canvas for the Spectral Distribution
canvas_sd = canvas_sd = FigureCanvasTkAgg(plot.fig_sd, master = frame_sd)

canvas_sd.get_tk_widget().pack(
        expand = True,
        fill = tk.BOTH,
    )

frame_sd.grid(
    column = 0,
    row = 4,
    columnspan = 3,
    sticky = "nsew",
    padx = 3,
    pady = 3,
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
frame_color_info.rowconfigure(
    4,
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
canvas_CIE = FigureCanvasTkAgg(plot.fig_CIE, master = frame_cie)
canvas_CIE.get_tk_widget().pack(
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

canvas_CIE.draw()

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

toolbar = NavigationToolbar2Tk_modified(canvas_CIE, main_window, pack_toolbar=False)
toolbar.update()
toolbar.grid(
    column = 1,
    row = 0,
    sticky = "w",
)

# toolbar.message.get()
#-----------------------------------------------------------------------------------------------------------------

main_window.mainloop()