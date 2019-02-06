# nefis-cython
Neutral File System (NEFIS) Processing using a pre-built NEFIS library in Cython

This is a thin wrapper around a pre-built NEFIS Cython library which was provided by Deltares. This was made after
several unsuccessful attempts at re-compiling the official OpenEarth nefis-python package on github using Cython. The .dll and .pyd files
needed for this program are supplied in the releases tab.


This is not meant to be used as a python package, rather a program that converts NEFIS files to netCDF. Therefore I have omitted a setup file.
See run instructions below.


## Run from batch file in command line mode
~~~~
rem Must have Python 2.7 installed with netCDF4 installed via conda.

rem SET PATH TO PYTHON 2.7
set py27=C:\Users\ykala\AppData\Local\Continuum\anaconda3\envs\py27

rem SET PATH TO NEFISMAIN SCRIPT. THERE IS A COPY ON THE K NETWORK DRIVE.
set nefispy=C:\Users\ykala\github\nefis-cython\nefismain.py

set PATH=%py27%;%PATH%

rem First argument is the function (trim2nc or trih2nc)
rem Second argument is the input file name (.dat)
rem Run this batch file from the same directory as your input file.
python.exe %nefispy% trim2nc trim-f34.dat
pause
~~~~