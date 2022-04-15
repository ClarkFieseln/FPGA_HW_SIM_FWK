###############################
# on Windows
###############################
REM create environment:
REM -------------------
REM cd %USERPROFILE%
REM python -m venv hw_sim_fwk_env
REM in order to execute in environment path:
REM ----------------------------------------
REM cd %USERPROFILE%\hw_sim_fwk_env\Scripts
REM now we execute commands directly in project path pointing to corresponding python environment:
REM ----------------------------------------------------------------------------------------------
REM cd <project_path>
REM (NOTE: you may need to enter the user profile path explicitely)
%USERPROFILE%\hw_sim_fwk_env\Scripts\activate.bat
REM (NOTE: you may need to get out of environment path e.g. if you have it open in a separate console)
%USERPROFILE%\hw_sim_fwk_env\Scripts\pip install --upgrade pip
REM %USERPROFILE%\hw_sim_fwk_env\Scripts\pip install pipreqs
REM %USERPROFILE%\hw_sim_fwk_env\Scripts\pip list
%USERPROFILE%\hw_sim_fwk_env\Scripts\python updateRequirements.py
REM not working with --user: %USERPROFILE%\hw_sim_fwk_env\Scripts\pip install --user -r requirements.txt
%USERPROFILE%\hw_sim_fwk_env\Scripts\pip install -r requirements.txt
REM you may need to install pyinstaller
REM %USERPROFILE%\hw_sim_fwk_env\Scripts\pip install pyinstaller
%USERPROFILE%\hw_sim_fwk_env\Scripts\pyinstaller --onefile main_windows.spec
cd dist
.\main.exe


