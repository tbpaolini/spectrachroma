import sys
from cx_Freeze import setup, Executable
from pathlib import Path

"""NOTE
In order to build a SpectraChroma executable you need to have installed Python 3,
and the following Python modules (and their dependencies):
    colour-science
    matplotlib
    XlsxWriter
    cx_freeze

If you are on Ubuntu (Linux), you also need to install these Linux packages:
    python3-tk
    patchelf

Once those requirements are installed, open a shell (command prompt) on the
directory where is SpectraChroma's source and run the one of following commands:
    python setup.py build
    python setup.py bdist_msi

If you are on Linux, you might need to use the command "python3" instead of "python".
The argument "build" only creates a standalone program for Windows or Linux (depending
on which Operating System you are using). The argument "bdist_msi" creates both a
standalone program and a Windows installer (needless to say, this only works on Windows).

After the script finishes running, the standalone program is placed on the "build"
subdirectory, while the installer goes to the "dist" subdirectory.
"""

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        "spec2cie_ui.py",
        base=base,
        icon=str(Path("lib", "icon.ico")),
        copyright="(c) Tiago Becerra Paolini",
        target_name="SpectraChroma",
        # shortcut_name = "SpectraChroma",
        # shortcut_dir = "DesktopFolder",
    )
]

build_exe_options = {
    "packages": ["spec2cie", "colour", "matplotlib", "scipy.spatial.transform._rotation_groups"],
    "include_files": [
        (str(Path("lib", "icon.png")), str(Path("lib", "icon.png"))),
        (str(Path("lib", "Help.txt")), str(Path("lib", "Help.txt"))),
        (str(Path("lib", "About.txt")), str(Path("lib", "About.txt"))),
        (str(Path("lib", "License.txt")), "License.txt"),
        (str(Path("lib", "License.txt")), str(Path("lib", "License.txt"))),
        (str(Path("lib", "Citation.txt")), "Citation.txt"),
        (str(Path("lib", "Citation.txt")), str(Path("lib", "Citation.txt"))),
    ],
    "optimize": 1,
    "include_msvcr": True,
    "zip_include_packages": "*",
    "zip_exclude_packages": ["scipy"],
}

# https://docs.microsoft.com/en-us/windows/win32/msi/shortcut-table
shortcut_table = [
    ("DesktopShortcut",                 # Shortcut
     "DesktopFolder",                   # Directory_
     "SpectraChroma",                   # Name
     "TARGETDIR",                       # Component_
     "[TARGETDIR]SpectraChroma.exe",    # Target
     None,                              # Arguments
     None,                              # Description
     None,                              # Hotkey
     None,                              # Icon
     None,                              # IconIndex
     None,                              # ShowCmd
     'TARGETDIR'                        # WkDir
     ),

     ("ProgramMenuShortcut",            # Shortcut
     "ProgramMenuFolder",               # Directory_
     "SpectraChroma",                   # Name
     "TARGETDIR",                       # Component_
     "[TARGETDIR]SpectraChroma.exe",    # Target
     None,                              # Arguments
     None,                              # Description
     None,                              # Hotkey
     None,                              # Icon
     None,                              # IconIndex
     None,                              # ShowCmd
     'TARGETDIR'                        # WkDir
     )
    ]

msi_data = {"Shortcut": shortcut_table}

bdist_msi_options = {
    "product_code": "{A2536964-4A51-43F1-AC11-7E0D64296FC1}",
    "upgrade_code": "{239D6203-0061-4630-B97A-42E33E37C078}",
    "target_name": "SpectraChroma-1.0.1-Windows-Installer",
    "add_to_path": False,
    "install_icon": str(Path("lib", "icon.ico")),
    # "initial_target_dir": "ProgramFiles64Folder",
    "all_users": True,
    "summary_data": {
        "author": "Tiago Becerra Paolini",
        "comments": "Spectrum to CIE 1931 Chromaticity Diagram",
        "keywords": "chromaticity; diagram; CIE; spectrum; color; colorimetry; spectroscopy",
    },
    'data': msi_data,
}

setup(
    name="SpectraChroma",
    version="1.0.1",
    description="Spectrum to CIE 1931 Chromaticity Diagram",
	options = {"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)