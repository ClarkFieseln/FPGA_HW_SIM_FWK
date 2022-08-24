from dataclasses import dataclass



# Version format: MAJOR.MINOR.BUGFIX
VERSION = "1.0.10"
VERSION_TOOL_TIP = "PoC (Proof of Concept):\n\
                    Basic set of features for demonstration purposes in Windows using FIFOs (named pipes) and shared files."

# execute test code, e.g. to measure performance
# test results will be logged to console after "closing" the window
TEST = True

# LOGGING_LEVEL specifies the lowest-severity log message a logger will handle, where debug is the lowest built-in severity level and critical is the highest built-in severity.
# For example, if the severity level is INFO, the logger will handle only INFO, WARNING, ERROR, and CRITICAL messages and will ignore DEBUG messages.
LOGGING_LEVEL = "logging.INFO"

# app font size
FONT_SIZE_APP = 14

# show advance settings
SHOW_ADVANCED_SETTINGS = False

# update period of GUI
# NOTE: it is useful to consider the refresh rate of the monitor used (e.g. 60Hz = 60 FPS).
#       Updates faster than that will not be displayed anyways.
#       In any case, due to the functionality of this tool 20 Hz may be sufficient even if the monitor is faster.
GUI_UPDATE_PERIOD_IN_HZ = 60

# show live status
SHOW_LIVE_STATUS = True

# keep push button pressed?
# generally, we use a "toggle" button i. o. a "press" button, so we set KEEP_PB_PRESSED = True,
# otherwise we have problems if we need to press more than one button at the same time,
# we don't have more than one finger in the simulation
KEEP_PB_PRESSED = True

# show plot
SHOW_PLOT = True

# logging
LOG_TO_CSV = True
LOG_ON_POWER_ON_OFF = False

# chat
TEXT_SIZE = 12
TEXT_BOLD = True
TEXT_FAMILY = "Arial"

# sound effects (e.g. when pushing buttons)
SOUND_EFFECTS = True

# performance (advanced settings)
SHOW_PERFORMANCE = True

# script or .exe?
# the following parameters are determined at runtime (not stored in config.ini)
IS_SCRIPT = True 
PATH_PREFIX = "./dist/"
CONFIG_FILENAME = "config.ini"

# common configuration (to python and VHDL codes)
CLOCK_PERIOD_EXTERNAL = "1000000000 ns" # 1 sec
CLOCK_PERIOD_EXTERNAL_MIN_MS = 0.0000000000001
RESET_FOR_SECONDS = 0.1
CLOCK_PERIOD_VHDL_NS = "20 ns" # to transform to time in FPGA time coordinates
FILE_PATH = "C:/tmp/hw_sim_fwk/" #"/tmp/hw_sim_fwk/"
FIFO_PATH = "\\\\.\\pipe\\"
# general parameters
MAX_NR_DI = 16
NR_DIS = 10
MAX_NR_SW = 10
NR_SWITCHES = 10
MAX_NR_BTN = 10
NR_BUTTONS = 10
MAX_NR_LED = 10
NR_LEDS = 10
MAX_NR_DO = 16
NR_DOS = 10
# specific simulation parameters
NR_ASYNC_DI = 5
NR_SYNC_DI = NR_DIS - NR_ASYNC_DI
MAX_DI_COUNT = 32
DI_PER_IN_CLK_PER = 4
SW_PER_IN_CLK_PER = 4
BUTTON_PER_IN_CLK_PER = 8
PC_UTIL_PER_IN_CLK_PER = 1
ADC_SAMPLING_PERIOD_IN_CLK_PER = 100
BUTTON_TOGGLE_AUTO = False
SWITCH_TOGGLE_AUTO = False

# values to adapt sensor data (e.g. temperature) to full range of integer value passed via SPI (ADC -> FPGA)
# TODO: implement in config.ini and in GUI if required
NR_BITS_INT = 14
MAX_INT = float(2.0**NR_BITS_INT)
MIN_INT = float(0.0)
MAX_VAL = 150.0
MIN_VAL = -50.0

# simulator options
RUN_FOR_CLOCK_PERIODS = 50

######################
@dataclass
class ConfigDataClass:
    CLOCK_PERIOD_EXTERNAL: str




