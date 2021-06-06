# SpectraChroma
SpectraChroma is a software for calculating and plotting the color coordinates of emission spectra in the CIE 1931 Chromaticity Diagram (2 Degree Standard Observer).

![SpectraChroma's screenshot](https://github.com/tbpaolini/spectrachroma/raw/master/assets/screenshots/SpectraChroma%20-%20v1.0.0.png)

## Features:
* Import multiple spectra at once
* Automatic data labeling
* Can save the Chromaticity Diagram in several image formats (including SVG, PNG, JPG, TIFF)
* Chromaticity Diagram customization by showing/hiding the axes, grid lines, and data labels
* Display the CIE color coordinates and the calculated perceived color
* Export all CIE color coordinates and the perceived colors to Microsoft Excel or plain text

## Downloads
SpectraChroma runs on Windows and Linux, without the need of installation. Just unzip and run the program:
* [Windows 10 64-bit (standalone)](https://github.com/tbpaolini/spectrachroma/releases/download/v1.0.0/SpectraChroma.1.0.0-Windows_10-x64.zip)
* [Linux (Ubuntu 20.04) 32/64-bit](https://github.com/tbpaolini/spectrachroma/releases/download/v1.0.0/SpectraChroma_1.0.0-Linux-x86_64.zip)

Optionally, an Windows installer is also available:
* [Windows Installer (64-bit)](https://github.com/tbpaolini/spectrachroma/releases/download/v1.0.0/SpectraChroma_1.0.0-Windows_Installer-x64.msi)

**Note:** *the program may work on earlier versions of Windows and other flavors of Linux, but that is not guaranteed. Windows 10 and Ubuntu 20.04 are the versions in which SpectraChroma as built and tested into.*

As a matter of convenience, some sample spectra are provided to be tested with SectraChroma:
* [Sample data](https://github.com/tbpaolini/spectrachroma/releases/download/v1.0.0/Sample_data-SpectraChroma.zip)

## Source Code
SpectraChroma is written in Python 3.9.4 and was exported to Windows and Linux executables using [cx_Freeze](https://marcelotduarte.github.io/cx_Freeze/), which means that no Python installation is required to run the executables.

But you can still get SpectraChorma's source code in Python, so you can run it in Python or build the executable yourself:
* [Source code (Python 3.9.4)](https://github.com/tbpaolini/spectrachroma/archive/refs/tags/v1.0.0.zip)

The following Python modules (and their dependencies) are required to run SpectraChroma from the source: `colour-science`, `matplotlib`, and `XlsxWriter`. To install all at once, you can run this command on the shell:
```sh
pip install colour-science matplotlib XlsxWriter
```

Aditionally, if you are on Ubuntu (Linux), you might need to also install the package `python3-tk`:
```sh
sudo apt-get install python3-tk
```

## About
SpectraChroma was made by Tiago Becerra Paolini (PhD in Chemistry), with valuable programming advice from Guilherme Wiethaus (professional programmer and MD in Chemistry).
