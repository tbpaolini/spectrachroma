import sys
from cx_Freeze import setup, Executable
from pathlib import Path

"""NOTE
In onder to create a build, this file needs to be run from the shell with the
"build" or "bdist_msi" parameters (without the quotes):
    python setup.py build
    python setup.py bdist_msi

build: creates only a standalone Windows program (no installation required)
bdist_msi: creates a Windows installer for the program, AND a standalone program

The standalone version goes to the "build" folder, while the installer goes to
the "dist" folder.
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
        (str(Path("lib", "About.txt")), str(Path("lib", "About.txt")))
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
    "product_code": "{84E3FDE9-F250-4FEE-8C2A-E6162ED74632}",
    "upgrade_code": "{239D6203-0061-4630-B97A-42E33E37C078}",
    "target_name": "SpectraChroma-1.0-Windows-Installer",
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
    version="1.0.0",
    description="Spectrum to CIE 1931 Chromaticity Diagram",
	options = {"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)