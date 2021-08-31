REM START PYFF PRESENTATION MODULE

@echo OFF
title PYFF Bat

echo Hello! This is a batch to start pyff.

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
REM conda activate only works after setting it up, use call to allways work
call activate neuroprime


REM SIMULATE SIGNAL ACQUISITION - REPLAY DATA ********
REM EEG ***
echo "START EEG FILE STREAM PLAYER CONSOLE"
start "FILE STREAM PLAYER CONSOLE" cmd /c python "%src_path%utils\simulate\file_stream_player.py"
timeout /T 5 /nobreak >nul

exit

