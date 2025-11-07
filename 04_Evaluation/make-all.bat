@echo off
REM run_all_make.bat
REM Execute all Makefiles via WSL

REM List of directories relative to WSL or mapped Windows paths
SET DIRS="Data/FeedbackOptimizer" "Data/SimpleAndRepeatedOptimization" "Data/ZadenooriOptimizationPrompt"

REM Loop over directories and run make in each
FOR %%D IN (%DIRS%) DO (
    ECHO ==================================================
    ECHO Entering directory: %%D
    REM Check if Makefile exists and run make via WSL
    wsl bash -c "if [ -f %%D/Makefile ]; then cd %%D && make; else echo 'No Makefile in %%D, skipping'; fi"
)
ECHO ==================================================
ECHO Building thesis document with latexmk
latexmk

ECHO ==================================================
ECHO Finished running all Makefiles.
PAUSE
