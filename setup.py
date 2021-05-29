import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("spec2cie_ui.py", base=base, icon="icon.ico", copyright="(c) Tiago Becerra Paolini", target_name="SpectraChroma")]
build_exe_options = {
    "packages": ["spec2cie", "colour", "matplotlib", "scipy.spatial.transform._rotation_groups"],
    "include_files": ["lib\icon.png"],
    "optimize": 1,
    "include_msvcr": True,
    "zip_include_packages": "*",
    "zip_exclude_packages": ["scipy"],
}

setup(
    name="SpectraChroma",
    version="1.0.0",
    description="Spectrum to CIE 1931 Chromaticity Diagram",
	options = {"build_exe": build_exe_options},
    executables=executables,
)