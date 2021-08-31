REM START MAIN MODULE

@echo OFF
title START GUIs

echo Hello! This is a batch to start the experiment

REM GET PATHS ******
set script_path=%~dp0
echo %script_path%


REM SET ANACONDA PATHs environment (OPTIONAL - if not persistent) *******
REM This is used if you didtn't put them presistent - however is better to be persistent (go to environment variables)
REM SET PATH=C:\Users\admin.DDIAS4\Anaconda2;C:\Users\admin.DDIAS4\Anaconda2\Scripts;C:\Users\admin.DDIAS4\Anaconda2\Library\bin;%PATH%

REM ACTIVATE ENV ********
REM conda activate only works for conda 4.6 and up, for prior use call
call activate neuroprime


REM Windows System Timer Tool *****
REM The default timer resolution in some Windows versions is 16 ms, which can limit the precision of timings. It is strongly recommended to run the following tool and set the resolution to 1 ms or lower: https://vvvv.org/contribution/windows-system-timer-tool
REM START ["title"] [/D path]
taskkill /IM "%src_path%TimerTool_v3.exe" /F
timeout /T 5 /nobreak >nul
start "" "%src_path%TimerTool_v3.exe" -t 0.5 -minimized


REM CALL PYTHON BCI - Add appropriate path
call python "%script_path%start_gui.py"

exit




