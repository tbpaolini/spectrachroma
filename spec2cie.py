import colour, re, gc, sys
import matplotlib.pyplot as plt
from colour.plotting import *
from tkinter.filedialog import askopenfilenames
from pathlib import Path
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

#-----------------------------------------------------------------------------
# Calculation of color coordinates from spectrum file
#-----------------------------------------------------------------------------
class spectrum_to_cie:
    """Takes a text file with a luminescence emission spectrum,
    and returns an object with the coordinates of the perceived color in the color spaces: XYZ, CIE 1931, sRGB.
    """

    # Initialize class variables

    # Regular expression that extracts the spectrum points from a text file
    # It catches the X coordinate on Group 1, and the Y coordinate on Group 2
    data_regex = re.compile(r"(?mi)^[\s;]*((?:\+|-)?\d+(?:\.|,)?\d*(?:e(?:\+|-)?\d+)?)[\s;]+((?:\+|-)?\d+(?:\.|,)?\d*(?:e(?:\+|-)?\d+)?)[\s;]*$")

    # Color matching function
    cmfs = colour.MSDS_CMFS['CIE 1931 2 Degree Standard Observer']

    # Illuminant for ambient lighting correction
    illuminant = colour.SDS_ILLUMINANTS['D65']

    # Import the spectrum and create the sprectrum object
    def __init__(self, file_path):
        
        # Instance variables
        self.file_path = file_path                  # Absolute file system path to the spectrum file
        self.file_name = Path(file_path).stem       # Name of the file without the extension
        self.success = False                        # If the file import has been successful  
        self.XYZ = None                             # Coordinates on the XYZ color space
        self.xy = None                              # Coordinates on the CIE xy color space
        self.RGB = None                             # Coordinates on the sRGB color space
        
        # Import spectrum from file
        imported_spectrum = self.get_spectrum_from_file(file_path)  # Function returns False if it could not import the spectrum
        
        if imported_spectrum:
            
            # The file has been parsed successfuly
            self.success = True

            # Unmodified spectrum
            self.spectrum_raw = colour.SpectralDistribution(imported_spectrum)

            # Interpolate the spectrum so the spacing between consecutive points is exactly 1 nm,
            # and slice the spectrum to the range of 380 to 780 nm (the visible region)
            self.spectrum_corrected = (self.spectrum_raw.copy()).interpolate(colour.SpectralShape(interval=1))
            """The model used to calculate the CIE color coordinates requires two things:
                1. That all points are uniformly spaced
                2. That the spacing between the points is EXACTLY 1, 5, 10 or 20 nm

                The reason is because the experimental data do build said model also used those conditions.
                In any other condition the calculation of the CIE coordinates fails.
                Therefore we are interpolating our raw spectrum so all points are spaced by 1 nm (maximum resolution allowed).

                The interpolation is made according to the 'CIE 167:2005' recommendation:
                - Sprague Interpolation, if the raw data is evenly spaced
                - Cubic Spline Interpolation, if the raw data is NOT evenly spaced
            """

            # Convert spectrum to a point in the XYZ color space
            # array(X, Y, Z)
            self.XYZ = colour.sd_to_XYZ(self.spectrum_corrected, self.cmfs, self.illuminant)

            # Convert a point on the XYZ color space to xy color coordinates on the CIE chromaticity diagram
            # array(CIEx, CIEy)
            self.xy = colour.XYZ_to_xy(self.XYZ)
            self.x, self.y = self.xy    # For convenience, store the values on separate variables as floats

            # Cobvert a point on the XYZ color space to the sRGB color space
            # array(R, G, B)
            self.RGB = colour.XYZ_to_sRGB(self.XYZ / self.XYZ[1])   # Normalisation of XYZ and conversion to sRGB

            for n in range(3):
                self.RGB[n] = max(min(self.RGB[n], 1.0), 0.0)       # Clamp each component to the [0.0, 1.0] range

            """Normalisation: each component of the XYZ array was divided by Y. This way, normalised Y = 1.
            With the normalisation, we can display the color without it looking "darkened".

            This is necessary for the conversion to sRGB, because Y represents the relative luminance.
            (Y = 1 is the maximum luminance on the sRGB color space)
            (Y = 0 would be no luminance: you would see no color)
            """
            self.R, self.G, self.B = self.RGB   # For convenience, store the values on separate variables as floats
    
    def get_spectrum_from_file(self, file_path):
        """Extracts the spectral coordinates (x,y) from a text file,
        and returns the data as a dictionary {x1: y1, x2: y2, ...}.
        It ignores the headers on the file and just get the data.

        It is considered as valid data a line in which there are exactly 2 real numbers
        separated by a space, tabulation or semicolon. And nothing else besides that.
        """

        try:
            spectrum_file = open(file_path)
        except FileNotFoundError:
            print(f"Error: File not found - {file_path}")
            return False
        
        # Dictionary for the spectral coordinates
        spectrum_data = {}

        # Loop through the file line by line and extracts the data
        try:
            line_number = 0
            for line in spectrum_file:
                line_number += 1

                # Perform the regular expression search (x-axis gets to Group 1, and y-axis to Group 2)
                coordinate_data = self.data_regex.search(line)

                if coordinate_data:
                    try:
                        # Get the spectrum coordinate (as string)
                        wavelenght = coordinate_data.group(1)
                        intensity = coordinate_data.group(2)

                        # If the decimal separator is a comma, replace it by a dot
                        if "," in wavelenght:
                            wavelenght = wavelenght.replace(",", ".", 1)
                        if "," in intensity:
                            intensity = intensity.replace(",", ".", 1)
                        
                        # Convert the coordinate from string to float
                        wavelenght = float(wavelenght)
                        intensity = float(intensity)

                        # Store the coordinates on the dictionary
                        spectrum_data.update({wavelenght: intensity})
                    except ValueError:
                        # Fail-safe for the case there's some edge case that the regex couldn't handle properly
                        # This exception should never happen if the regex was crafted correctly
                        print(f"Error: Not a valid floating point number - Line {line_number} of {file_path}")
                        continue

        except UnicodeDecodeError:
            print(f"Error: File could not be opened as a plain text document - {file_path}")
            spectrum_file.close()
            return False
        
        # Close the file and return the dictionary
        spectrum_file.close()
        return spectrum_data
    
#-----------------------------------------------------------------------------
# Container to store the results from the spectrum_to_cie() class
#-----------------------------------------------------------------------------
class spectrum_container():
    """Store spectra and their color coordinates.

    Instantiating the container:
        spectrum = spectrum_container()
    Optionally, the container can be bound to a specific Tk window, so it can generate events for that window:
        spectrum = spectrum_container(tk_window = window)
    
    New spectra can be added by calling the method .import_files:
        spectrum.import_files()     # Opens a file dialog to the user (multiple files can be selected at once)
    The spectra's color coordinates are calculated and stored on the container (sequentially).

    Then the container can have each spectrum accessed by index (like a list):
        [ spectrum[0], spectrum[1], spectrum[2], ...]
    
    Each spectrum[n] can have their color coordinates accessed by the attributes .xy or .RGB:
        spectrum[n].xy      # A numpy array with its (x, y) CIE 1931 color coordiates
        spectrum[n].RGB     # A numpy array with the approximate RGB values (R, G, B) - on the scale from 0 to 1
    Those values can also be accessed individually (as floats):
        spectrum[n].x , spectrum[n].y , spectrum[n].R , spectrum[n].G , spectrum[n].B
    
    Other attributes:
        spectrum[n].XYZ         # Coordinates on the XYZ color space - array(X, Y, Z)
        spectrum[n].file_path   # Absolute file system path to the spectrum file
        spectrum[n].file_name   # Name of the file without the extension
        spectrum[n].success     # If the file import has been successful  
    
    The container can also be iterated on a for loop, like as:
        for item in spectrum:
            print(item.xy)  # Each individual item can have its attributes acessed, as listed above
    
    The amount of spectra on the container can be obtained with the len() function:
        for n in range(len(spectrum)):
            spectrum[n] ... # Do something with each spectrum
    """

    def __init__(self, tk_window = None):
        # List of spectrum objects
        self.id = []
        # Optionally, bind the container to a Tk window
        self.window = tk_window
    
    def __getitem__(self, index):
        return self.id[index]
    
    def __len__(self):
        return len(self.id)
    
    def __iter__(self):
        self._index = 0
        self._max_index = len(self.id)
        return self
    
    def __next__(self):
        if self._index < self._max_index:
            obj_spectrum = self.id[self._index]
            self._index += 1
            return obj_spectrum
        else:
            raise StopIteration
    
    def import_files(self):
        """Open a file dialog for the user to choose the spectrum files.
        Then parse the files, calculate the color data, and stores it in an object inside the spectrum container.
        """

        if sys.platform == "win32":
            text_extensions = ("Text files", "*.txt;*.csv;*.prn;*.dat;*.asc")
        else:
            text_extensions = ("Text files", "*.txt")
        """NOTE
        Unlike Windows, Linux's "open file" dialog does not accept multiple
        extensions for a single file type. Or at least I was not able to find
        an way to. So I added this check to only include the "*.txt" extension
        for text files if the Operating System is not Windows.

        The other formats I included for Windows are all extensions that I saw
        an laboratory instrument generating when exporting data to text. Most
        of the extensions are from older equipment, nowadays it seems to be
        just regular "*.txt" extension, but I included the others for the
        sake of convenience.

        All of them in the end of the day are just plan text documents.
        """

        file_list = askopenfilenames(
            parent = self.window,
            filetypes = (text_extensions, ("All files", "*.*")),
            title = "Import spectra"
        )

        file_list_size = len(file_list)
        if file_list_size == 0:
            return False
        
        # Parse the spectrum files
        success_count = 0
        for file in file_list:
            
            # Spectrum object
            obj_spectrum = spectrum_to_cie(file)   # Parse the file and calculate the color coordinates
            
            if obj_spectrum.success:
                self.id.append(obj_spectrum)       # Add the spectrum object to the list
                success_count += 1
            
        if success_count > 0:
            if self.window:
                # Generate an event for Tkinter (so we can automatically update the diagram)
                self.window.event_generate("<<FilesImported>>", when="tail")
                self.window.update()
            return True
        else:
            return False
    
    def get_xy(self):
        xy_dict = {'x': [], 'y': []}
        for obj_spectrum in self.id:
            xy_dict['x'].append(obj_spectrum.xy[0])
            xy_dict['y'].append(obj_spectrum.xy[1])
        return xy_dict

#-----------------------------------------------------------------------------
# Plot the values stored on the spectrum_container() class
#-----------------------------------------------------------------------------
class plot_container():
    """Plot and store the Chromaticity Diagram and the Spectral Distributions.
    The plots themselves are meant to be displayed by the Graphical User Interface.
    """
    def __init__(self):
        
        # The amount of points plotted on the CIE Chromaticity Diagram
        self.points_count = 0
        
        # Set the figures to be saved with 300 dpi
        plt.rcParams["savefig.dpi"] = 300

        # Create the Chromaticity Diagram figure and its axes
        self.fig_CIE, self.ax_CIE = plt.subplots(
            figsize = (4.8, 5.4),
            dpi = 100,
        )

        # Draw the Chromaticity Diagram
        plot_chromaticity_diagram_CIE1931(
            figure = self.fig_CIE,
            axes = self.ax_CIE,
            standalone = False,
            title = "CIE 1931 Chromaticity Diagram",
            bounding_box = (0.0, 0.8, 0.0, 0.9),
            tight_layout = True,
            transparent_background = False,
            show_spectral_locus = False,
        )
        """NOTE:
        "standalone = False" means that the figure isn't rendered yet, so it
        is still opened for plotting the coordinates.
        
        Setting "transparent_background = False" actually makes the background
        transparent, in spite of what the parameter name might suggest. We are
        making axes background transparent so we can set the figure to black
        and get the plot on a dark background too.

        "show_spectral_locus = False" makes prevents the function from drawing
        the wavelenghts around the spectrum. I don't like the style that the
        module use for the locus, however the module doesn't allow to change
        it easily. The locus will be drawn later, through a custom method, with
        a style that fits better with what I am going for.
        """

        # Set the diagram's background to black
        self.fig_CIE.set_facecolor("black")
        self.ax_CIE.set_facecolor("black")

        # Formatting the diagram's title (white bold text, with a bigger size)
        self.title_CIE = self.ax_CIE.set_title(
            self.ax_CIE.get_title(),
            color = "white",
            fontweight = "bold",
            fontsize = "large",
            pad = 10,
        )

        # Make white both axes and the bounding box
        self.ax_CIE.spines["bottom"].set_color("white")
        self.ax_CIE.spines["top"].set_color("white")
        self.ax_CIE.spines["left"].set_color("white")
        self.ax_CIE.spines["right"].set_color("white")

        # Formatting the text of the labels (white text)
        self.ax_CIE.set_xlabel(
            self.ax_CIE.get_xlabel(),
            color = "white",
            fontsize = "medium",
            labelpad = 5,
        )

        self.ax_CIE.set_ylabel(
            self.ax_CIE.get_ylabel(),
            color = "white",
            fontsize = "medium",
            labelpad = 5,
        )

        # Set the color of the tick values to white
        self.ax_CIE.tick_params(axis="x", colors="white")
        self.ax_CIE.tick_params(axis="y", colors="white")

        # Draw the spectral locus
        wave_labels = {
            450: (0.15664093257730705, 0.017704804990891335),
            470: (0.12411847672778557, 0.057802513373740476),
            480: (0.091293507002271151, 0.13270204248699027),
            520: (0.074302424773374967, 0.83380309134022801),
            540: (0.2296196726496402, 0.75432908990274372),
            560: (0.37310154386845751, 0.62445085979666115),
            580: (0.5124863667817966, 0.48659078806085709),
            600: (0.62703659976387227, 0.37249114521841825),
            620: (0.69150397296170174, 0.30834226055665592),
            700: (0.7346900232582807, 0.2653099767417193)
        }
        """NOTE
        The above values were calculated by the following script:
            import colour
            from pprint import pprint

            cmfs = colour.MSDS_CMFS['CIE 1931 2 Degree Standard Observer']

            wavelenghts = (450, 470, 480, 520, 540, 560, 580, 600, 620, 700)

            points = {}
            for i in wavelenghts:
                point_XYZ = colour.wavelength_to_XYZ(i, cmfs)
                point_xy = colour.XYZ_to_xy(point_XYZ)
                points.update({i: tuple(point_xy)})

            pprint(points)
        """

        # Draw the wavelenght tick labels to the diagram
        for point in wave_labels:
            
            # Set the position of the tick labels according to their values,
            # so they don't overlap the diagram
            if point < 520:
                my_xytext = (-7, 0)    # Text position in relation to the tick
                my_va = "center"        # Vertical alignment of the text in relation to the tick
                my_ha = "right"         # Horizontal alignment of the text in relation to the tick
            elif point > 520:
                my_xytext = (7, 0)
                my_va = "center"
                my_ha = "left"
            else:
                my_xytext = (7, 7)
                my_va = "bottom"
                my_ha = "center"
            
            # Draw the wavelenghts text and the tick lines (all in white)
            self.ax_CIE.annotate(
                point,                          # Wavelenght text
                xy = wave_labels[point],        # Coordinate on the plot where to draw
                xytext = my_xytext,             # Position of the text in relation to the plot coordinate
                textcoords = "offset points",   # Specify that the coordinate is relative to the plot coordinate
                color = "white",                # Color of the text
                fontsize = 8,                   # Size of the text
                va = my_va,                     # Vertical alignment of the text 
                ha = my_ha,                     # Horizontal alignment of the text
                
                arrowprops = dict(              # Draw the line
                    color = "white",            # Color of the line
                    arrowstyle = "-",           # Style of the line (no arrow heads)
                    shrinkA = 0,                # Distance the line tail is from the text
                    shrinkB = 2,                # Distance the line head is from the diagram
                )
            )
        
        # List for the point labels on the Chromaticity Diagram
        """NOTE
        Each point plotted on the diagram will have a number label over it.
        This list will hold those labels handlers, so batch operations can be applied to them.
        """
        self.label_CIE = []
        self.label_CIE_visible = True  # Whether the data labels are being shown on the diagram

        # List for the plotted coordinates
        """NOTE
        List to store each scatter plot of CIE coordinates, so operations can be applied later
        to them.
        """
        self.scatter_CIE = []

        # Initialize the figure for the spectral distributions (sd)
        """NOTE
        To speed up things, I am using a single figure with multiple axes (one for each sd).
        Then I will make the figure to render only one axis at a time.
        """
        self.fig_sd = plt.figure(
            figsize = (2.8, 2.1),
            dpi = 100,
        )
        
        self.ax_sd = {}    # Spectral Distribution dictionary
        """NOTE
        The dictionary will associate the spectrum ID to its axis on the sd figure:
        {spectrum: sd_axis, ...}
        """
    
    def plot_cie(self, CIEx, CIEy):
        """Take lists of CIE x an CIE y coordinates, and plot them on the Chromaticity diagram.
        """
        # Lenght of the lists
        len_CIEx = len(CIEx)
        len_CIEy = len(CIEy)

        if (len_CIEx == 0) or (len_CIEx != len_CIEy):
            return False    # Exit the function if the lists are empty or have different sizes
        
        # Plot the points to the Chromaticity Diagram
        my_scatter = self.ax_CIE.scatter(CIEx, CIEy, marker="o", color="#212121", s=3)
        self.scatter_CIE.append(my_scatter)
        #print(f"About to annotate points:\n{CIEx}\n{CIEy}")

        # Annotate with numbers the points on the diagram 
        point_index = 0
        for point in range(self.points_count, self.points_count + len_CIEx):

            my_label = self.ax_CIE.annotate(point + 1,          # The result of "point+1" is the text annotated to the current point
                color = "white",
                xy = (CIEx[point_index], CIEy[point_index]),    # Coordinate of the point
                xytext = (0, 0),                                # Place the text on the same coordinate as the point
                textcoords = "offset points",                   # Coordinates relative to the point
                ha = "center",                                  # Center the text over the point (horizontally)
                va = "center",                                  # Center the text over the point (vertically)
                fontfamily = "sans-serif",                      # Use a font without serif
                fontweight = "bold",                            # Bold text
                fontsize = 6,                                   # Text with size of 6 points
                bbox = dict(
                    boxstyle = "circle",                        # Place the text in a solid circle
                    color = "#212121",                          # Color of the circle
                )
            )

            my_label.set_visible(self.label_CIE_visible)    # Show or hide the label, based on the current setting

            #print(f"Point: {(CIEx[point_index], CIEy[point_index])} (index: {point_index})")
            point_index += 1

            # Add the label to the list
            self.label_CIE.append(my_label)
        
        self.points_count += len_CIEx   # How many points there are currently on the diagram
    
    def flush_cie(self):
        """Clear all plotted CIE points from the Chromaticity Diagram.
        """
        
        # Remove all labels
        for label in self.label_CIE:    # Loop through the list
            label.remove()              # Remove the specific item
        self.label_CIE.clear()          # Clear the entire list
        
        # Remove all plotted CIE coordinates
        for scatter_plot in self.scatter_CIE:   # Loop through the list
            scatter_plot.remove()               # Remove the specific item
        self.scatter_CIE.clear()                # Clear the entire list

        # Reset the points counter
        self.points_count = 0
    
    def show_labels_cie(self, display_labels):
        """ Show (True) or hide (False) the data labels on the Chromaticity Diagram.
        """
        self.label_CIE_visible = display_labels     # Change the current setting flag

        for label in self.label_CIE:                # Change the setting on each label
            label.set_visible(display_labels)

    def plot_sd(self, spectrum_list):
        """Plot a Spectral Distribution for each spectrum in a list.
        """
        
        if len(spectrum_list) == 0:
            return False
        
        for spectrum in spectrum_list:
            
            # Create the axis
            current_axis = self.fig_sd.subplots(sharex=True, sharey=True)
            current_axis.set_visible(False)
            
            # Plot the current spectral distribution
            plot_single_sd(
                spectrum.spectrum_corrected,        # Interpolated spectrum
                figure = self.fig_sd,
                axes = current_axis,
                axes_visible = False,               # No bounding box around the spectrum
                title = False,                      # No title
                standalone = False,
                transparent_background = False,     # No background
            )

            # Change the line width to 0.5 (from the default of 1.0)
            (current_axis.get_lines()[0]).set_linewidth(0.5)
            current_axis.set_xlim((380, 780))
            
            # Update dictionary of spectral distributions
            self.ax_sd.update({spectrum: current_axis})
        
        # Remove the blank spaces around the figure
        self.fig_sd.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
    
    def save_sd(self, spectral_distribution):
        """Export the Spectral Distribution to an image file.
        """
        # Find the spectrum handler on the container
        my_sd = False
        for spectrum,axis_sd in self.ax_sd.items():
            if axis_sd == spectral_distribution:
                my_sd = spectrum
                break
        
        # If no spectrum is found, exit the function
        if not my_sd:
            return False

        # Plot the spectral distribution from the raw spectrum data
        figure, axis = plot_single_sd(
            my_sd.spectrum_raw,              # Dictionary with the spectrum values
            axes_visible = True,
            title = "Spectral Distribution (CIE 1931)",
            standalone = False,
            transparent_background = False,
        )
        axis.get_yaxis().set_ticks([])                  # Remove tick labels from the y-axis
        axis.set_xlabel("Wavelength (nm)")              # Title of the x-axis
        axis.set_ylabel("Intensity (arbitrary units)")  # Title of the y-axis
        axis.set_xlim((380, 780))                       # x-axis range (380 to 780 nm)
        figure.subplots_adjust(left=0.05, bottom=0.11, right=0.95, top=0.93, wspace=0, hspace=0)    # Margins of the graph

        # Create a canvas for the plot
        canvas = FigureCanvasTkAgg(figure)

        # Create a toolbar for the plot
        toolbar = NavigationToolbar2Tk(canvas, None, pack_toolbar = False)
        toolbar.save_figure()
        """NOTE
        I am creating a toolbar because it already has a built-in method to
        save the figure, with several different file formats.
        This saves the time I would need to create those routines from scratch.
        """

        # Garbage collection of the plot
        figure.clf()                        # Clear figure
        axis.cla()                          # Clear axis
        toolbar.destroy()                   # Delete toolbar
        canvas.get_tk_widget().destroy()    # Delete canvas
        plt.close(figure)                   # Close plot
        del figure
        del axis
        
        # Run the garbage collector to free up memory immediately
        gc.collect()
    
    def __del__(self):
        """Ensure that the plots get closed when the object is deleted.
        """
        # Close all figures
        self.fig_CIE.clf()
        self.fig_sd.clf()
        plt.close("all")