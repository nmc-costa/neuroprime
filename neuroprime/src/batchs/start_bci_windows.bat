REM START MAIN MODULE

@echo OFF
title BRAIN INTERFACE Bat

echo Hello! This is a batch to start experiment

REM GET PATHS ******
set script_path=%~dp0
echo %script_path%
set batchs_path=%script_path%
echo %batchs_path%
for %%a in ("%~dp0..\") do set "src_path=%%~fa"
echo %src_path%


REM SET ANACONDA PATHs environment (OPTIONAL - if not persistent) *******
REM This is used if you didtn't put them presistent - however is better to be persistent (go to environment variables)
REM SET PATH=C:\Users\admin.DDIAS4\Anaconda2;C:\Users\admin.DDIAS4\Anaconda2\Scripts;C:\Users\admin.DDIAS4\Anaconda2\Library\bin;%PATH%

REM ACTIVATE ENV ********
REM conda activate only works for conda 4.6 and up, for prior use call
conda activate neuroprime


REM Windows System Timer Tool - In start_gui.bat *****
REM The default timer resolution in some Windows versions is 16 ms, which can limit the precision of timings. It is strongly recommended to run the following tool and set the resolution to 1 ms or lower: https://vvvv.org/contribution/windows-system-timer-tool
REM START ["title"] [/D path]
REM start "" "%src_path%TimerTool_v3.exe" -t 0.5 -minimized


REM CALL PYTHON BCI - Add appropriate path
REM use call or start "CONSOLE" cmd /c (create new console)
start "BCI CONSOLE" cmd /c python "%src_path%brain_interfaces\e2_bci\e2_bci.py" ^& pause

exit




