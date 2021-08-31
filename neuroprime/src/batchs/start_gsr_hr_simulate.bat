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
REM conda activate only works for conda 4.6 and up, for prior use call
conda activate neuroprime


REM change dir to start pyff *****
cd "%GSR&HR_path%"

REM Start feedbackcontroller *******
REM use call or start "PYFF CONSOLE" cmd /c (create new console)
start "GSR&HR ONE CONSOLE" cmd /c python "%src_path%utils\simulate\simulate_GSR&HR_outlets.py 
exit

