###############################
# on Linux
###############################
# create virtual environment
# --------------------------
# cd ~
# python3 -m venv hw_sim_fwk_env
source ~/hw_sim_fwk_env/bin/activate
~/hw_sim_fwk_env/bin/pip install --upgrade pip
~/hw_sim_fwk_env/bin/python updateRequirements.py
~/hw_sim_fwk_env/bin/pip install -r requirements.txt
# optional if pyinstaller not yet installed
# -----------------------------------------
# ~/hw_sim_fwk_env/bin/pip install pyinstaller
# also this?
# ----------
# # ~/hw_sim_fwk_env/bin/pip install sounddevice
~/hw_sim_fwk_env/bin/pyinstaller --onefile main_linux.spec

# then execute with absolute path:
# --------------------------------
# /media/user/device/fpga_hw_sim_fwk/python/hw_sim_fwk/dist/main

# may get this when executing:
# ----------------------------
# playsound is relying on another python subprocess. Please use `pip install pygobject` if you want playsound to run more efficiently.
# pip install pygobject
# or ?
# ~/hw_sim_fwk_env/bin/pip install pygobject



