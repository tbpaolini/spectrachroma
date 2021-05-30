import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        "spec2cie_ui.py",
        base=base,
        icon=r"lib\icon.ico",
        copyright="(c) Tiago Becerra Paolini",
        target_name="SpectraChroma",
        # shortcut_name = "SpectraChroma",
        # shortcut_dir = "DesktopFolder",
    )
]

build_exe_options = {
    "packages": ["spec2cie", "colour", "matplotlib", "scipy.spatial.transform._rotation_groups"],
    "include_files": [
        (r"lib\icon.png", r"lib\icon.png"),
        (r"lib\Help.txt", r"lib\Help.txt"),
        (r"lib\About.txt", r"lib\About.txt")
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
    "install_icon": "lib\icon.ico",
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