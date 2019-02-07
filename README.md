# nefis-cython
Neutral File System (NEFIS) Processing using a pre-built NEFIS library in Cython

This is a thin wrapper around a pre-built NEFIS Cython library which was provided by Deltares. This was made after
several unsuccessful attempts at re-compiling the official OpenEarth nefis-python package on github using Cython. The .dll and .pyd files
needed for this program are supplied in the releases tab.

## Installation
Navigate to the repo folder and run this command in your (anaconda) prompt:
~~~~
pip install -e .
~~~~


## Usage in Python script
```python
import nefiscython as ne

f1 = 'trim-f34.dat'

# Get all data in a dictionary of dicts.
ff = ne.openfile(f1)
d1 = ne.getalldata(ff)
ne.closefile(ff)

# Convert to netCDF
ne.nefis2nc(f1)
```


## Run from batch file in command line mode
~~~~
rem Must have Python 2.7 installed with netCDF4 installed via conda.

rem SET PATH TO PYTHON 2.7
set py27=C:\Users\username\AppData\Local\Continuum\anaconda3\envs\py27

rem SET PATH TO NEFISMAIN SCRIPT. THERE IS A COPY ON THE K NETWORK DRIVE.
set nefispy=C:\Users\username\github\nefis-cython\nefismain.py

set PATH=%py27%;%PATH%

rem First argument is the function (nefis2nc)
rem Second argument is the input file name (.dat)
rem Run this batch file from the same directory as your input file.
python.exe %nefispy% nefis2nc trim-f34.dat
pause
~~~~
