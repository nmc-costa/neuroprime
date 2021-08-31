REM START MAIN MODULE

@echo OFF
title BRAIN INTERFACE Bat

echo Hello! This is a batch to start experiment

REM GET PATHS ******
set script_path=%~dp0
echo %script_path%

REM start pycorder - add shortcut to batch folder ******
start "" "%script_path%pycorder.lnk"

exit




