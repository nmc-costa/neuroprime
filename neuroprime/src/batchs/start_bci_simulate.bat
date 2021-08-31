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



REM START SIGNAL PRESENTATION (PYFF) ********
REM EEG
echo "START EEG FILE STREAM PLAYER CONSOLE"
start "PYFF CONSOLE" cmd /c call start_pyff_windows.bat
timeout /T 5 /nobreak >nul

REM SIMULATE SIGNAL ACQUISITION - REPLAY DATA ********
REM EEG ***
echo "START EEG FILE STREAM PLAYER CONSOLE"
start "FILE STREAM PLAYER CONSOLE" cmd /c python "%src_path%utils\simulate\file_stream_player.py"
timeout /T 5 /nobreak >nul
REM GSR&HR ***
echo "START GSR&HR STREAM PLAYER CONSOLE"
start "GSR&HR simulate" cmd /c call start_gsr_hr_simulate.bat
timeout /T 5 /nobreak >nul


REM Windows System Timer Tool - in start_gui.bat*****
REM The default timer resolution in some Windows versions is 16 ms, which can limit the precision of timings. It is strongly recommended to run the following tool and set the resolution to 1 ms or lower: https://vvvv.org/contribution/windows-system-timer-tool
REM START ["title"] [/D path]
REM start "" "%src_path%TimerTool_v3.exe" -t 0.5 -minimized


REM CALL PYTHON BCI SIGNAL PROCESSING********
REM use call or start "CONSOLE" cmd /c (create new console)
timeout /T 5 /nobreak >nul
echo "START BCI SIMULATE CONSOLE"
start "BCI SIMULATE CONSOLE" cmd /c python "%src_path%brain_interfaces\e2_bci\e2_bci_simulate.py" ^& pause
pause
exit










REM OPTIONS *****

REM There are two ways: 1)(TODO) start anaconda prompt (already does the work for you with the paths, and you never need to use cmd directly) -  CALL \Anaconda2\Scripts\activate.bat; 2) ADD persistant paths to PATH environmental variables, then you can use cmd directly

REM FAQs *****





REM start cmd.exe /k "more-batch-commands-here" OR start cmd.exe /c "more-batch-commands-here"
REM /c Carries out the command specified by string and then terminates
REM /k Carries out the command specified by string but remains

REM Run a program and pass a filename parameter:
REM CMD /c write.exe c:\docs\sample.txt

REM Run a program and pass a long filename:
REM CMD /c write.exe "c:\sample documents\sample.txt"

REM Spaces in program path:
REM CMD /c ""c:\Program Files\Microsoft Office\Office\Winword.exe""

REM Spaces in program path + parameters:
REM CMD /c ""c:\Program Files\demo.cmd"" Parameter1 Param2
REM CMD /k ""c:\batch files\demo.cmd" "Parameter 1 with space" "Parameter2 with space""

REM Launch demo1 and demo2:
REM CMD /c ""c:\Program Files\demo1.cmd" & "c:\Program Files\demo2.cmd""


