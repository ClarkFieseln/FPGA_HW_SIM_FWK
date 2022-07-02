# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtGui import QFont, QIntValidator
from time import gmtime, strftime
from .Ui_mainWindow import Ui_MainWindow
import configuration
import init
from inspect import currentframe
import os
import logging
import traceback
import threading
import time
import random
from sys import platform
from playsound import playsound
import matplotlib.pyplot as plt
import tkinter
import tkinter.messagebox
from tkinter import filedialog
import functools

# TODOs:
# - test on Windows11 (problems with access to shared files?)
# - plot signals
# - add analog sensor (e.g. CPU load)
# - add serial communication (UART, SPI, I2C,..) e.g. to pass sensor values

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

# init logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)

# current frame
cf = currentframe()

# module definitions and variables:
FILE_NAME_RESET_HIGH = None
FILE_NAME_RESET_LOW = None
FILE_NAME_CLOCK = None
FILE_NAME_DI_HIGH = []
FILE_NAME_DI_LOW = []
SYNC_DI = []
ASYNC_DI = []
FILE_NAME_DO_HIGH = []
FILE_NAME_DO_LOW = []
FILE_NAME_SW_HIGH = []
FILE_NAME_SW_LOW = []
FILE_NAME_BTN_HIGH = []
FILE_NAME_BTN_LOW = []
FILE_NAME_LED_ON = []
FILE_NAME_LED_OFF = []
CLOCK_PERIOD_SEC = None
CLOCK_PERIOD_NS = None
DI_PERIOD_SEC = None
SWITCH_PERIOD_SEC = None
BUTTON_PERIOD_SEC = None
LED_PERIOD_SEC = None
DO_PERIOD_SEC = None


# here only variables/definitions are changed
# in updateGuiConfig() we change also GUI and other derived things.
def updateGuiDefs():
    global FILE_NAME_RESET_HIGH
    global FILE_NAME_RESET_LOW
    global FILE_NAME_CLOCK
    global FILE_NAME_DI_HIGH
    global FILE_NAME_DI_LOW
    global SYNC_DI
    global ASYNC_DI
    global FILE_NAME_DO_HIGH
    global FILE_NAME_DO_LOW
    global FILE_NAME_SW_HIGH
    global FILE_NAME_SW_LOW
    global FILE_NAME_BTN_HIGH
    global FILE_NAME_BTN_LOW
    global FILE_NAME_LED_ON
    global FILE_NAME_LED_OFF
    global CLOCK_PERIOD_SEC
    global CLOCK_PERIOD_NS
    global DI_PERIOD_SEC
    global SWITCH_PERIOD_SEC
    global BUTTON_PERIOD_SEC
    global LED_PERIOD_SEC
    global DO_PERIOD_SEC
    # platform
    logging.info("platform = " + platform)  # "linux" or "linux2", "win32", "darwin" # OS X
    if (platform == "linux") or (platform == "linux2"):
        if ":" in configuration.FILE_PATH:
            configuration.FILE_PATH = "/tmp/hw_sim_fwk/"
            logging.warning("configuration.FILE_PATH changed to platform specific path: " + configuration.FILE_PATH)
    elif (platform == "win32"):
        if ":" not in configuration.FILE_PATH:
            configuration.FILE_PATH = "C:/tmp/hw_sim_fwk/"
            logging.warning("configuration.FILE_PATH changed to platform specific path: " + configuration.FILE_PATH)
    FILE_NAME_RESET_HIGH = configuration.FILE_PATH + "reset_high"
    FILE_NAME_RESET_LOW = configuration.FILE_PATH + "reset_low"
    # clock
    FILE_NAME_CLOCK = configuration.FILE_PATH + "clock"
    # check max nr. of DIs and DOs  
    if configuration.NR_DIS > configuration.MAX_NR_DI:
        configuration.NR_DIS = configuration.MAX_NR_DI
        logging.warning("maximum nr. of digital inputs limited to " + str(configuration.MAX_NR_DI))
        tkinter.messagebox.showwarning(title="WARNING", message="maximum nr. of digital inputs limited to " + str(
            configuration.MAX_NR_DI))
        root.update()
    if configuration.NR_DOS > configuration.MAX_NR_DO:
        configuration.NR_DOS = configuration.MAX_NR_DO
        logging.warning("maximum nr. of digital outputs limited to " + str(configuration.MAX_NR_DO))
        tkinter.messagebox.showwarning(title="WARNING", message="maximum nr. of digital outputs limited to " + str(
            configuration.MAX_NR_DO))
        root.update()
    # digital inputs
    FILE_NAME_DI_HIGH_PART = configuration.FILE_PATH + "di_high_"  # temporary variable
    FILE_NAME_DI_LOW_PART = configuration.FILE_PATH + "di_low_"  # temporary variable
    FILE_NAME_DI_HIGH = []
    FILE_NAME_DI_LOW = []
    for i in range(configuration.NR_DIS):
        FILE_NAME_DI_HIGH.append(FILE_NAME_DI_HIGH_PART + str(i))
        FILE_NAME_DI_LOW.append(FILE_NAME_DI_LOW_PART + str(i))
    SYNC_DI = []
    ASYNC_DI = []
    for i in range(configuration.NR_SYNC_DI):
        SYNC_DI.append(i)
    for i in range(configuration.NR_ASYNC_DI):
        ASYNC_DI.append(configuration.NR_ASYNC_DI + i)
    # digital outputs
    FILE_NAME_DO_HIGH_PART = configuration.FILE_PATH + "do_high_"  # temporary variable
    FILE_NAME_DO_LOW_PART = configuration.FILE_PATH + "do_low_"  # temporary variable
    FILE_NAME_DO_HIGH = []
    FILE_NAME_DO_LOW = []
    for i in range(configuration.NR_DOS):
        FILE_NAME_DO_HIGH.append(FILE_NAME_DO_HIGH_PART + str(i))
        FILE_NAME_DO_LOW.append(FILE_NAME_DO_LOW_PART + str(i))
    # switches        
    if configuration.NR_SWITCHES > configuration.MAX_NR_SW:
        configuration.NR_SWITCHES = configuration.MAX_NR_SW
        logging.warning("maximum nr. of switches limited to " + str(configuration.MAX_NR_SW))
        tkinter.messagebox.showwarning(title="WARNING",
                                       message="maximum nr. of switches limited to " + str(configuration.MAX_NR_SW))
        root.update()
    FILE_NAME_SW_HIGH_PART = configuration.FILE_PATH + "switch_high_"
    FILE_NAME_SW_LOW_PART = configuration.FILE_PATH + "switch_low_"
    FILE_NAME_SW_HIGH = []
    FILE_NAME_SW_LOW = []
    for i in range(configuration.NR_SWITCHES):
        FILE_NAME_SW_HIGH.append(FILE_NAME_SW_HIGH_PART + str(i))
        FILE_NAME_SW_LOW.append(FILE_NAME_SW_LOW_PART + str(i))
    # buttons
    if configuration.NR_BUTTONS > configuration.MAX_NR_BTN:
        configuration.NR_BUTTONS = configuration.MAX_NR_BTN
        logging.warning("maximum nr. of buttons limited to " + str(configuration.MAX_NR_BTN))
    FILE_NAME_BTN_HIGH_PART = configuration.FILE_PATH + "button_high_"
    FILE_NAME_BTN_LOW_PART = configuration.FILE_PATH + "button_low_"
    FILE_NAME_BTN_HIGH = []
    FILE_NAME_BTN_LOW = []
    for i in range(configuration.NR_BUTTONS):
        FILE_NAME_BTN_HIGH.append(FILE_NAME_BTN_HIGH_PART + str(i))
        FILE_NAME_BTN_LOW.append(FILE_NAME_BTN_LOW_PART + str(i))
    # LEDs
    if configuration.NR_LEDS > configuration.MAX_NR_LED:
        configuration.NR_LEDS = configuration.MAX_NR_LED
        logging.warning("maximum nr. of LEDs limited to " + str(configuration.MAX_NR_LED))
    FILE_NAME_LED_ON_PART = configuration.FILE_PATH + "led_on_"
    FILE_NAME_LED_OFF_PART = configuration.FILE_PATH + "led_off_"
    FILE_NAME_LED_ON = []
    FILE_NAME_LED_OFF = []
    for i in range(configuration.NR_LEDS):
        FILE_NAME_LED_ON.append(FILE_NAME_LED_ON_PART + str(i))
        FILE_NAME_LED_OFF.append(FILE_NAME_LED_OFF_PART + str(i))
        # check ranges
    if configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS <= 0:
        # NOTE: 100 ms hardcoded rescue value.
        configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS = 100
        logging.error("min. clock period shall be greater than zero. Now set to value = 100 ms")
        tkinter.messagebox.showerror(title="ERROR",
                                     message="min. clock period shall be greater than zero. Now set to value = 100 ms")
        root.update()
    if int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) <= 0:
        configuration.CLOCK_PERIOD_EXTERNAL = str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms"
        logging.error("clock period shall be greater than zero. Now set to minimum value = " + str(
            configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms")
        tkinter.messagebox.showerror(title="ERROR",
                                     message="clock period shall be greater than zero. Now set to minimum value = " +
                                             str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms")
        root.update()
    # NOTE: CLOCK_PERIOD_SEC corresponds exactly to one period in VHDL code.
    if " fs" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000000000
    elif " ps" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000000
    elif " ns" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000
    elif " us" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000
    elif " ms" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000
    elif " sec" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])
    elif " min" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) * 60
    elif " min" in configuration.CLOCK_PERIOD_EXTERNAL:
        CLOCK_PERIOD_SEC = int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) * 3600
    else:
        logging.error("Error: unknown time units in CLOCK_PERIOD_EXTERNAL!")
        traceback.print_exc()
        exit(cf.f_lineno)
    logging.info("CLOCK_PERIOD_SEC = " + str(CLOCK_PERIOD_SEC))
    # digital input period
    DI_PERIOD_SEC = CLOCK_PERIOD_SEC * configuration.DI_PER_IN_CLK_PER
    logging.info("DI_PERIOD_SEC = " + str(DI_PERIOD_SEC))
    # switch period
    SWITCH_PERIOD_SEC = CLOCK_PERIOD_SEC * configuration.SW_PER_IN_CLK_PER
    logging.info("SWITCH_PERIOD_SEC = " + str(SWITCH_PERIOD_SEC))
    # button period
    BUTTON_PERIOD_SEC = CLOCK_PERIOD_SEC * configuration.BUTTON_PER_IN_CLK_PER
    logging.info("BUTTON_PERIOD_SEC = " + str(BUTTON_PERIOD_SEC))
    # LED period
    # ASSUMPTION: in worst case the LEDs are switched in every edge of the clock (both rising and falling edges)
    #             under consideration of jitter we need to be faster than that when polling possible changes,
    #             thus we define the period to be 1/4th of the clock period.
    LED_PERIOD_SEC = CLOCK_PERIOD_SEC / 4
    logging.info("LED_PERIOD_SEC = " + str(LED_PERIOD_SEC))
    # digital output period
    # ASSUMPTION: in worst case the DOs are switched in every edge of the clock (both rising and falling edges)
    #             under consideration of jitter we need to be faster than that when polling possible changes,
    #             thus we define the period to be 1/4th of the clock period.
    DO_PERIOD_SEC = CLOCK_PERIOD_SEC / 4
    logging.info("DO_PERIOD_SEC = " + str(DO_PERIOD_SEC))


def init_file_path():
    # remove dir if it exists (this will clean everything up)
    if os.path.exists(configuration.FILE_PATH):
        # Remove files
        logging.info("FILE_PATH = " + configuration.FILE_PATH + " exists..")
    else:
        # create temporary directory
        os.mkdir(configuration.FILE_PATH)
        logging.info("FILE_PATH = " + configuration.FILE_PATH + " created..")


def createTempFiles():
    # remove temporary files with "active" value: in this case HIGH, ON,..
    if os.path.exists(FILE_NAME_RESET_HIGH):
        os.remove(FILE_NAME_RESET_HIGH)
    if os.path.exists(FILE_NAME_CLOCK):
        os.remove(FILE_NAME_CLOCK)
    for i in range(configuration.NR_DIS):
        if os.path.exists(FILE_NAME_DI_HIGH[i]):
            os.remove(FILE_NAME_DI_HIGH[i])
    for i in range(configuration.NR_SWITCHES):
        f = open(FILE_NAME_SW_LOW[i], "w+")
        f.close()
        if os.path.exists(FILE_NAME_SW_HIGH[i]):
            os.remove(FILE_NAME_SW_HIGH[i])
    for i in range(configuration.NR_BUTTONS):
        if os.path.exists(FILE_NAME_BTN_HIGH[i]):
            os.remove(FILE_NAME_BTN_HIGH[i])
    for i in range(configuration.NR_LEDS):
        if os.path.exists(FILE_NAME_LED_ON[i]):
            os.remove(FILE_NAME_LED_ON[i])
    for i in range(configuration.NR_DOS):
        if os.path.exists(FILE_NAME_DO_HIGH[i]):
            os.remove(FILE_NAME_DO_HIGH[i])
    # create temporary files with "inactive" value: in this case LOW, OFF,..
    f = open(FILE_NAME_RESET_LOW, "w+")
    f.close()
    if os.path.exists(FILE_NAME_CLOCK) == False:
        os.mkfifo(FILE_NAME_CLOCK)
    for i in range(configuration.NR_DIS):
        f = open(FILE_NAME_DI_LOW[i], "w+")
        f.close()
    for i in range(configuration.NR_SWITCHES):
        f = open(FILE_NAME_SW_LOW[i], "w+")
        f.close()
    for i in range(configuration.NR_BUTTONS):
        f = open(FILE_NAME_BTN_LOW[i], "w+")
        f.close()
    for i in range(configuration.NR_LEDS):
        f = open(FILE_NAME_LED_OFF[i], "w+")
        f.close()
    for i in range(configuration.NR_DOS):
        f = open(FILE_NAME_DO_LOW[i], "w+")
        f.close()


# events used in threads:
evt_set_power_on = threading.Event()
evt_set_power_off = threading.Event()
evt_set_reset_high = threading.Event()
evt_set_reset_low = threading.Event()
evt_pause = threading.Event()
evt_resume = threading.Event()
evt_step_on = threading.Event()
evt_do_step = threading.Event()
# NOTE: we use threading.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = threading.Event()
# these events improve performance by indicating exactly when the GUI shall update which widgets.
evt_gui_di_update = threading.Event()
evt_gui_do_update = threading.Event()
evt_gui_led_update = threading.Event()
evt_gui_remain_run_time_update = threading.Event()

# update GUI definitions
updateGuiDefs()

# file path
init_file_path()

# create temporary files
createTempFiles()


# main window
#############
class MainWindow(QMainWindow, Ui_MainWindow):
    # variables:
    # app = None  # QApplication
    cfg = None  # __init__.InitApp()
    appStarted = False
    status = ["/", "-", "\\", "|"]
    statusCnt = 0
    csv_file = None
    toggle = True
    clock_high = False
    toggle_switch = True
    toggle_button = True
    toggle_di = True
    remaining_time_to_run = 0
    di_count = 0
    DI_HIGH = []
    for i in range(configuration.NR_DIS):
        DI_HIGH.append(0)
    DO_HIGH = []
    for i in range(configuration.NR_DOS):
        DO_HIGH.append(0)
    LED_ON = []
    for i in range(configuration.NR_LEDS):
        LED_ON.append(0)
    # widgets:
    pbKeepPbPressed = None
    button = []
    switch = []
    led = []
    di = []
    do = []
    # events:
    evt_set_button_on = []
    evt_set_button_off = []
    evt_set_switch_on = []
    evt_set_switch_off = []
    # evt_set_led_on = []
    # evt_set_led_off = []

    # open fifos (named pipes)
    ##########################
    # TODO: check if we need to close them and where
    fifo_w_clock = open(FILE_NAME_CLOCK, 'w')
    print("done")

    ######################################################################################
    # NOTE: we don't modify GUI objects from a QThread
    #       or even worse, from a python thread.
    #       Instead, we send a signal to the GUI / MainWindow.
    # Ref.: https://stackoverflow.com/questions/12083034/pyqt-updating-gui-from-a-callback
    ######################################################################################
    class MyGuiUpdateThread(QThread):
        logging.info("Thread MyGuiUpdateThread starting")
        updated = pyqtSignal(str)

        def run(self):
            logging.info("MyGuiUpdateThread:run()")
            while True:
                evt_wake_up.wait(1 / configuration.GUI_UPDATE_PERIOD_IN_HZ)
                self.updated.emit("Hi")

    # thread to update GUI
    ######################
    def updateGui(self):
        # update status on GUI
        ######################
        if (self.lblStatus is not None):
            # device on?
            if evt_set_power_on.is_set() == True:
                if configuration.SHOW_LIVE_STATUS:
                    # set alternating symbol
                    self.lblStatus.setText(" " + self.status[self.statusCnt])
                    self.statusCnt = (self.statusCnt + 1) % 4
                    # blink active LED
                    self.pbActive.setChecked(not self.pbActive.isChecked())
                    if self.pbActive.isChecked():
                        self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_on.png'))
                    else:
                        self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_off.png'))
                # output LEDs                
                if evt_gui_led_update.is_set():
                    evt_gui_led_update.clear()
                    for i in range(configuration.NR_LEDS):
                        if self.LED_ON[i] == 1:
                            self.led[i].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_on.png'))
                        else:
                            self.led[i].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_off.png'))
                # digital inputs
                if evt_gui_di_update.is_set():
                    evt_gui_di_update.clear()
                    for i in range(configuration.NR_DIS):
                        self.di[i].setText(str(self.DI_HIGH[i]))
                # digital outputs
                if evt_gui_do_update.is_set():
                    evt_gui_do_update.clear()
                    for i in range(configuration.NR_DOS):
                        self.do[i].setText(str(self.DO_HIGH[i]))
                # update remaining time when running for time
                if evt_gui_remain_run_time_update.is_set():
                    evt_gui_remain_run_time_update.clear()
                    self.lblRemaining.setText(str(self.remaining_time_to_run))
            else:
                # stop blinking active LED                                            
                if self.pbActive.isChecked():
                    self.pbActive.setChecked(False)
                    self.pbActive.setChecked(self.pbActive.isChecked())
                    self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_off.png'))

    # thread for scheduling synchronous signals
    ###########################################
    def thread_scheduler(self, name):
        logging.info("Thread %s starting", name)
        # nr. of counted clock periods
        clock_periods = 0
        # main loop (toggle signal and sleep)
        while True:
            # time measurement
            current_time = time.time()
            # device on?
            if evt_set_power_on.is_set() == True:
                # toggle signal
                if self.toggle == False:
                    # handle digital inputs
                    #######################
                    if clock_periods % configuration.DI_PER_IN_CLK_PER == 0:
                        # NOTE: uncomment of these options:
                        # self.do_di_toggle() 
                        self.do_di_count()
                    # handle switches
                    #################
                    if configuration.SWITCH_TOGGLE_AUTO == True:
                        if clock_periods % configuration.SW_PER_IN_CLK_PER == 0:
                            self.do_switch()
                    # handle buttons
                    ################
                    if configuration.BUTTON_TOGGLE_AUTO == True:
                        if clock_periods % configuration.BUTTON_PER_IN_CLK_PER == 0:
                            self.do_button()
                    # handle clock - falling edge
                    # NOTE: it is important to schedule all tasks first before emulating a clock change
                    ###################################################################################
                    self.clock_high = False
                    self.fifo_w_clock.write("0\r\n")
                    self.fifo_w_clock.flush()
                else:
                    # handle clock - raising edge
                    #############################
                    self.clock_high = True
                    self.fifo_w_clock.write("1\r\n")
                    self.fifo_w_clock.flush()
                    # handle digital outputs
                    ########################
                    self.do_do()
                    # handle LEDs
                    #############
                    self.do_led()
                    # increment clock periods
                    #########################
                    clock_periods = clock_periods + 1

                # log to csv
                ############
                if configuration.LOG_TO_CSV == True:
                    self.csv_log()
                # toggle clock signal
                #####################
                self.toggle = not self.toggle
            # wait without consuming resources
            ##################################
            if (evt_pause.is_set()) == True:
                evt_resume.wait(999999)
            elif (evt_step_on.is_set() == True):
                if self.clock_high == False:
                    while evt_step_on.is_set() == True and evt_do_step.is_set() == False:
                        evt_do_step.wait(CLOCK_PERIOD_SEC / 2)
                else:
                    evt_do_step.clear()  # step done!
                    evt_wake_up.wait(CLOCK_PERIOD_SEC / 2 - (time.time() - current_time))
            else:
                evt_wake_up.wait(CLOCK_PERIOD_SEC / 2 - (time.time() - current_time))

    def __init__(self, qApplication, parent=None, sdm_arg=None):
        # call super
        super(MainWindow, self).__init__(parent)
        # self.app = qApplication
        # load .ini file and set values in GUI
        ######################################
        self.cfg = init.InitApp()
        # InitApp() has read config.ini thus we need to update all definitions
        updateGuiDefs()
        # file path
        init_file_path()
        # create temporary files
        createTempFiles()
        # update member variables
        self.updateMemberVariables()
        # create file to log
        if configuration.LOG_TO_CSV == True:
            self.csv_file = open("log.csv", 'w')
            self.init_csv_log()
        # setup Ui
        self.setupUi(self)
        # further Ui setup
        self.cbLogOnPowerOnOff.setToolTip("Log over power on/off in a single file if checked.")
        self.leFilePath.setText(configuration.FILE_PATH)
        self.leClkPeriods.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leClkPeriods.setValidator(QIntValidator())
        self.leClkPeriodMs.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leClkPeriodMs.setValidator(QIntValidator())
        self.leGuiRefreshHz.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leGuiRefreshHz.setValidator(QIntValidator())
        self.leMinClockPeriodMs.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leMinClockPeriodMs.setValidator(QIntValidator())
        self.leMaxDiCount.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leMaxDiCount.setValidator(QIntValidator())
        self.leDiPerInClkPer.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leDiPerInClkPer.setValidator(QIntValidator())
        self.leSwPerInClkPer.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leSwPerInClkPer.setValidator(QIntValidator())
        self.leBtnPerClkPer.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leBtnPerClkPer.setValidator(QIntValidator())
        # set widgets according configuration
        self.lblVersion.setToolTip(configuration.VERSION_TOOL_TIP)
        self.cbPlotShow.setChecked(configuration.SHOW_PLOT)
        self.cbSoundOn.setChecked(configuration.SOUND_EFFECTS)
        self.cbShowLiveStatus.setChecked(configuration.SHOW_LIVE_STATUS)
        self.cbLoggingOn.setChecked(configuration.LOG_TO_CSV)
        self.leMinClockPeriodMs.setText(str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS))
        self.cbLogOnPowerOnOff.setChecked(configuration.LOG_ON_POWER_ON_OFF)
        self.leMaxDiCount.setText(str(configuration.MAX_DI_COUNT))
        self.leDiPerInClkPer.setText(str(configuration.DI_PER_IN_CLK_PER))
        self.leSwPerInClkPer.setText(str(configuration.SW_PER_IN_CLK_PER))
        self.leBtnPerClkPer.setText(str(configuration.BUTTON_PER_IN_CLK_PER))
        self.cbBtnToggleAuto.setChecked(configuration.BUTTON_TOGGLE_AUTO)
        self.cbSwToggleAuto.setChecked(configuration.SWITCH_TOGGLE_AUTO)
        # number of FPGA items
        for i in range(configuration.MAX_NR_DI + 1):
            self.cbNrDis.addItem(str(i))
        self.cbNrDis.setCurrentIndex(configuration.NR_DIS)
        for i in range(configuration.NR_DIS + 1):
            self.cbNrAsyncDis.addItem(str(i))
        self.cbNrAsyncDis.setCurrentIndex(configuration.NR_ASYNC_DI)
        for i in range(configuration.MAX_NR_DO + 1):
            self.cbNrDos.addItem(str(i))
        self.cbNrDos.setCurrentIndex(configuration.NR_DOS)
        for i in range(configuration.MAX_NR_BTN + 1):
            self.cbNrBtns.addItem(str(i))
        self.cbNrBtns.setCurrentIndex(configuration.NR_BUTTONS)
        for i in range(configuration.MAX_NR_SW + 1):
            self.cbNrSwitches.addItem(str(i))
        self.cbNrSwitches.setCurrentIndex(configuration.NR_SWITCHES)
        for i in range(configuration.MAX_NR_LED + 1):
            self.cbNrLeds.addItem(str(i))
        self.cbNrLeds.setCurrentIndex(configuration.NR_LEDS)
        # pbKeepPbPressed button
        icon_button = QtGui.QIcon()
        icon_button.addPixmap(QtGui.QPixmap(":/jmp_on/jmp_on.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon_button.addPixmap(QtGui.QPixmap(":/jmp_off/jmp_off.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.pbKeepPbPressed = QtWidgets.QPushButton(self.tab_fpga)
        self.pbKeepPbPressed.setGeometry(QtCore.QRect(175, 260, 30, 50))
        self.pbKeepPbPressed.setText("")
        self.pbKeepPbPressed.setIcon(icon_button)
        self.pbKeepPbPressed.setIconSize(QtCore.QSize(30, 50))
        self.pbKeepPbPressed.setAutoDefault(False)
        self.pbKeepPbPressed.setDefault(False)
        self.pbKeepPbPressed.setFlat(True)
        self.pbKeepPbPressed.setObjectName("jmpKeepPbPressed")
        self.pbKeepPbPressed.setChecked(configuration.KEEP_PB_PRESSED)
        self.pbKeepPbPressed.clicked.connect(functools.partial(self.on_pbKeepPbPressed_clicked))
        label = QtWidgets.QLabel(self.tab_fpga)
        label.setGeometry(QtCore.QRect(175, 215, 58, 56))
        label.setStyleSheet("color: rgb(238, 238, 236);")
        label.setObjectName("keep_pressed")
        label.setText("keep\npressed")
        label.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE - 3))
        label = QtWidgets.QLabel(self.tab_fpga)
        label.setGeometry(QtCore.QRect(175, 290, 58, 56))
        label.setStyleSheet("color: rgb(238, 238, 236);")
        label.setObjectName("keep_pressed_y_n")
        label.setText("y  n")
        label.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE - 3))
        # refresh rate of GUI
        label = QtWidgets.QLabel(self.tab_fpga)
        label.setGeometry(QtCore.QRect(990, 450, 58, 56))
        label.setStyleSheet("color: rgb(238, 238, 236);")
        label.setObjectName("refreh_gui")
        label.setText("GUI")
        label.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE - 3))
        # combo boxes for logging level
        self.cbLoggingLevel.addItem("logging.DEBUG")
        self.cbLoggingLevel.addItem("logging.INFO")
        self.cbLoggingLevel.addItem("logging.WARNING")
        self.cbLoggingLevel.addItem("logging.ERROR")
        self.cbLoggingLevel.addItem("logging.CRITICAL")
        self.updateLoggingLevel()
        # update GUI configuration
        self.updateGuiConfig()
        # title
        currentTime = strftime("%Y.%m.%d %H:%M:%S - ", gmtime()) + platform
        self.setWindowTitle("HW SIM FWK")
        self.lblVersion.setText(configuration.VERSION + "\n" + currentTime)
        # digital inputs and outputs
        label = QtWidgets.QLabel(self.tab_fpga)
        label.setGeometry(QtCore.QRect(453, 450, 58, 56))
        label.setStyleSheet("color: rgb(238, 238, 236);")
        label.setObjectName("dis")
        label.setText("DIx:")
        label.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE - 3))
        label = QtWidgets.QLabel(self.tab_fpga)
        label.setGeometry(QtCore.QRect(725, 450, 58, 56))
        label.setStyleSheet("color: rgb(238, 238, 236);")
        label.setObjectName("dos")
        label.setText("DOx:")
        label.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE - 3))
        for i in range(configuration.NR_DIS):
            # di label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(575 - i * 2 * 12 - (i / 4) * 3, 490, 58, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("di_lbl_" + str(i))
            label.setText("" + str(i))
            # di label for value
            self.di.append(QtWidgets.QLabel(self.tab_fpga))
            self.di[i].setGeometry(QtCore.QRect(577 - i * 2 * 12 - (i / 4) * 3, 515, 58, 16))
            self.di[i].setStyleSheet("color: rgb(0, 0, 0);")
            self.di[i].setObjectName("di_" + str(i))
            self.di[i].setText(str(self.DI_HIGH[i]))
            # do label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(975 - i * 2 * 12 - (i / 4) * 3, 490, 58, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("do_" + str(i))
            label.setText("" + str(i))
            # do label for value
            self.do.append(QtWidgets.QLabel(self.tab_fpga))
            self.do[i].setGeometry(QtCore.QRect(977 - i * 2 * 12 - (i / 4) * 3, 515, 58, 16))
            self.do[i].setStyleSheet("color: rgb(0, 0, 0);")
            self.do[i].setObjectName("do_" + str(i))
            self.do[i].setText(str(self.DO_HIGH[i]))
        # buttons
        icon_button = QtGui.QIcon()
        icon_button.addPixmap(QtGui.QPixmap(":/btn_up/btn_up.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon_button.addPixmap(QtGui.QPixmap(":/btn_down/btn_down.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        for i in range(configuration.NR_BUTTONS):
            # button widget
            self.button.append(QtWidgets.QPushButton(self.tab_fpga))
            self.button[i].setGeometry(QtCore.QRect(225, 190 + i * 2 * 15, 31, 21))
            self.button[i].setText("")
            self.button[i].setIcon(icon_button)
            self.button[i].setIconSize(QtCore.QSize(33, 21))
            self.button[i].setAutoDefault(False)
            self.button[i].setDefault(False)
            self.button[i].setFlat(True)
            self.button[i].setAutoFillBackground(False)
            self.button[i].setObjectName("button_" + str(i))
            self.button[i].clicked.connect(lambda checked, arg=i: self.on_button_clicked(arg))
            self.button[i].pressed.connect(functools.partial(self.on_button_pressed, i))
            self.button[i].released.connect(functools.partial(self.on_button_released, i))
            # button enabled?
            if configuration.BUTTON_TOGGLE_AUTO == True:
                self.button[i].setEnabled(False)
            # button label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(270, 192 + i * 2 * 15, 58, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("label_btn_" + str(i))
            label.setText("btn " + str(i))
            # button events
            self.evt_set_button_on.append(threading.Event())
            self.evt_set_button_off.append(threading.Event())
        # switches
        icon_sw = QtGui.QIcon()
        icon_sw.addPixmap(QtGui.QPixmap(":/switch_left/sw_left.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon_sw.addPixmap(QtGui.QPixmap(":/switch_right/sw_right.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        for i in range(configuration.NR_SWITCHES):
            # switch widget
            self.switch.append(QtWidgets.QPushButton(self.tab_fpga))
            self.switch[i].setGeometry(QtCore.QRect(337, 190 + i * 2 * 15, 37, 17))
            self.switch[i].setText("")
            self.switch[i].setIcon(icon_sw)
            self.switch[i].setIconSize(QtCore.QSize(37, 17))
            self.switch[i].setFlat(True)
            self.switch[i].setObjectName("switch_" + str(i))
            self.switch[i].clicked.connect(lambda checked, arg=i: self.on_switch_clicked(arg))
            # switch enabled?
            if configuration.SWITCH_TOGGLE_AUTO == True:
                self.switch[i].setEnabled(False)
            # switch label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(387, 190 + i * 2 * 15, 41, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("label_sw_" + str(i))
            label.setText("sw " + str(i))
            # button events
            self.evt_set_switch_on.append(threading.Event())
            self.evt_set_switch_off.append(threading.Event())
        # leds
        icon_led = QtGui.QIcon()
        icon_led.addPixmap(QtGui.QPixmap(":/led_off/led_off.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon_led.addPixmap(QtGui.QPixmap(":/led_on/led_on.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        for i in range(configuration.NR_LEDS):
            # led widget
            self.led.append(QtWidgets.QPushButton(self.tab_fpga))
            self.led[i].setGeometry(QtCore.QRect(900, 190 + i * 2 * 15, 31, 16))
            self.led[i].setStyleSheet("")
            self.led[i].setText("")
            self.led[i].setIcon(icon_led)
            self.led[i].setIconSize(QtCore.QSize(25, 11))
            self.led[i].setFlat(True)
            self.led[i].setObjectName("led " + str(i))
            # led label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(940, 190 + i * 2 * 15, 31, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("label_led_" + str(i))
            label.setText("led " + str(i))
            # led events (not needed for now)
            # self.evt_set_led_on.append(threading.Event())
            # self.evt_set_led_off.append(threading.Event())                 
        # set color
        self.lblStatus.setStyleSheet('QLabel {color: green}')
        # disable pause, step and run_for_time
        self.pbRunPause.setEnabled(False)
        self.pbStep.setEnabled(False)
        self.pbRunForTime.setEnabled(False)
        # TODO: remove? check why this is not working and if we actually need it.
        # pause to give user the chance after power on to select use of run, run-for-time or step.
        # self.on_pbRunPause_toggled(True)
        ##########################################################################################
        # thread to update GUI periodically
        ###################################
        self._thread = self.MyGuiUpdateThread(self)
        self._thread.updated.connect(self.updateGui)
        self._thread.start()
        # further threads
        #################
        scheduler_thread = threading.Thread(name="scheduler_thread", target=self.thread_scheduler,
                                            args=("scheduler_thread",))
        reset_thread = threading.Thread(name="reset_thread", target=self.thread_reset, args=("reset_thread",))
        reset_thread.start()
        for j in range(configuration.NR_ASYNC_DI):
            i = ASYNC_DI[j]
            thread_name = "di_thread" + str(i)
            di_thread = threading.Thread(name=thread_name, target=self.thread_di, args=(thread_name, i))
            di_thread.start()
        if configuration.SWITCH_TOGGLE_AUTO == False:
            for i in range(configuration.NR_SWITCHES):
                switch_thread = threading.Thread(name="switch_thread", target=self.thread_switch,
                                                 args=("switch_thread", i,))
                switch_thread.start()
        if configuration.BUTTON_TOGGLE_AUTO == False:
            for i in range(configuration.NR_BUTTONS):
                button_thread = threading.Thread(name="button_thread", target=self.thread_button,
                                                 args=("button_thread", i,))
                button_thread.start()
        scheduler_thread.start()
        # set flag
        self.appStarted = True

    def do_di_toggle(self):
        if self.toggle_di == False:
            for j in range(configuration.NR_SYNC_DI):
                i = SYNC_DI[j]
                if os.path.isfile(FILE_NAME_DI_HIGH[i]):
                    os.rename(FILE_NAME_DI_HIGH[i],
                              FILE_NAME_DI_LOW[i])
                else:
                    f = open(FILE_NAME_DI_LOW[i], "w+")
                    f.close()
                self.DI_HIGH[i] = 0
        else:
            for j in range(configuration.NR_SYNC_DI):
                i = SYNC_DI[j]
                if os.path.isfile(FILE_NAME_DI_LOW[i]):
                    os.rename(FILE_NAME_DI_LOW[i],
                              FILE_NAME_DI_HIGH[i])
                else:
                    f = open(FILE_NAME_DI_HIGH[i], "w+")
                    f.close()
                self.DI_HIGH[i] = 1
        # toggle signal
        self.toggle_di = not self.toggle_di
        # update GUI
        evt_gui_di_update.set()

    def do_di_count(self):
        for j in range(configuration.NR_SYNC_DI):
            i = SYNC_DI[j]
            if self.di_count & 2 ** j:
                if os.path.isfile(FILE_NAME_DI_LOW[i]):
                    os.rename(FILE_NAME_DI_LOW[i],
                              FILE_NAME_DI_HIGH[i])
                else:
                    f = open(FILE_NAME_DI_HIGH[i], "w+")
                    f.close()
                self.DI_HIGH[i] = 1
            else:
                if os.path.isfile(FILE_NAME_DI_HIGH[i]):
                    os.rename(FILE_NAME_DI_HIGH[i],
                              FILE_NAME_DI_LOW[i])
                else:
                    f = open(FILE_NAME_DI_LOW[i], "w+")
                    f.close()
                self.DI_HIGH[i] = 0
        # logging.debug(DI_HIGH[0:configuration.NR_SYNC_DI])
        self.di_count = (self.di_count + 1) % configuration.MAX_DI_COUNT
        # inform GUI
        evt_gui_di_update.set()

    def thread_di(self, name, i):
        logging.info("Thread %s: starting", name)
        toggle_di = False
        # thread loop
        while True:
            # device on and not paused?
            if (evt_set_power_on.is_set() == True) and (evt_pause.is_set() == False) and (
                    evt_step_on.is_set() == False):
                if toggle_di == False:
                    if os.path.isfile(FILE_NAME_DI_HIGH[i]):
                        os.rename(FILE_NAME_DI_HIGH[i],
                                  FILE_NAME_DI_LOW[i])
                    else:
                        f = open(FILE_NAME_DI_LOW[i], "w+")
                        f.close()
                    self.DI_HIGH[i] = 0
                else:
                    if os.path.isfile(FILE_NAME_DI_LOW[i]):
                        os.rename(FILE_NAME_DI_LOW[i],
                                  FILE_NAME_DI_HIGH[i])
                    else:
                        f = open(FILE_NAME_DI_HIGH[i], "w+")
                        f.close()
                    self.DI_HIGH[i] = 1
                # toggle signal
                toggle_di = not toggle_di
                # inform GUI
                evt_gui_di_update.set()
            # wait random time within defined limits
            evt_wake_up.wait(random.uniform(CLOCK_PERIOD_SEC, DI_PERIOD_SEC))

    def do_switch(self):
        if self.toggle_switch == False:
            for i in range(configuration.NR_SWITCHES):
                if os.path.isfile(FILE_NAME_SW_HIGH[i]):
                    os.rename(FILE_NAME_SW_HIGH[i],
                              FILE_NAME_SW_LOW[i])
                else:
                    f = open(FILE_NAME_SW_LOW[i], "w+")
                    f.close()
        else:
            for i in range(configuration.NR_SWITCHES):
                if os.path.isfile(FILE_NAME_SW_LOW[i]):
                    os.rename(FILE_NAME_SW_LOW[i],
                              FILE_NAME_SW_HIGH[i])
                else:
                    f = open(FILE_NAME_SW_HIGH[i], "w+")
                    f.close()
        # toggle signal
        self.toggle_switch = not self.toggle_switch

    def do_button(self):
        if self.toggle_button == False:
            for i in range(configuration.NR_BUTTONS):
                if os.path.isfile(FILE_NAME_BTN_HIGH[i]):
                    os.rename(FILE_NAME_BTN_HIGH[i],
                              FILE_NAME_BTN_LOW[i])
                else:
                    f = open(FILE_NAME_BTN_LOW[i], "w+")
                    f.close()
                # logging.debug("Button "+str(i)+" = LOW")
            logging.debug("Buttons set to LOW (auto)")
        else:
            for i in range(configuration.NR_BUTTONS):
                if os.path.isfile(FILE_NAME_BTN_LOW[i]):
                    os.rename(FILE_NAME_BTN_LOW[i],
                              FILE_NAME_BTN_HIGH[i])
                else:
                    f = open(FILE_NAME_BTN_HIGH[i], "w+")
                    f.close()
                # logging.debug("Button "+str(i)+" = HIGH")
            logging.debug("Buttons set to HIGH (auto)")
        self.toggle_button = not self.toggle_button

    def thread_switch(self, name, idx):
        logging.info("Thread %s(%s): starting", name, str(idx))
        # thread loop
        while True:
            if configuration.SWITCH_TOGGLE_AUTO == False:
                if self.evt_set_switch_on[idx].is_set() == False:
                    if os.path.isfile(FILE_NAME_SW_HIGH[idx]):
                        os.rename(FILE_NAME_SW_HIGH[idx],
                                  FILE_NAME_SW_LOW[idx])
                    else:
                        f = open(FILE_NAME_SW_LOW[idx], "w+")
                        f.close()
                    logging.info("Switch (" + str(idx) + ") = OFF")
                    self.evt_set_switch_on[idx].wait(999999)
                else:
                    if os.path.isfile(FILE_NAME_SW_LOW[idx]):
                        os.rename(FILE_NAME_SW_LOW[idx],
                                  FILE_NAME_SW_HIGH[idx])
                    else:
                        f = open(FILE_NAME_SW_HIGH[idx], "w+")
                        f.close()
                    logging.info("Switch (" + str(idx) + ") = ON")
                    self.evt_set_switch_off[idx].wait(999999)
            else:
                evt_wake_up.wait(CLOCK_PERIOD_SEC / 2)

    def thread_button(self, name, idx):
        logging.info("Thread %s(%s): starting", name, str(idx))
        # thread loop
        while True:
            if self.evt_set_button_on[idx].is_set() == False:
                if os.path.isfile(FILE_NAME_BTN_HIGH[idx]):
                    os.rename(FILE_NAME_BTN_HIGH[idx],
                              FILE_NAME_BTN_LOW[idx])
                else:
                    f = open(FILE_NAME_BTN_LOW[idx], "w+")
                    f.close()
                logging.info("Button (" + str(idx) + ") = LOW")
                self.evt_set_button_on[idx].wait(999999)
            else:
                if os.path.isfile(FILE_NAME_BTN_LOW[idx]):
                    os.rename(FILE_NAME_BTN_LOW[idx],
                              FILE_NAME_BTN_HIGH[idx])
                else:
                    f = open(FILE_NAME_BTN_HIGH[idx], "w+")
                    f.close()
                logging.info("Button (" + str(idx) + ") = HIGH")
                self.evt_set_button_off[idx].wait(999999)

    def thread_reset(self, name):
        logging.info("Thread %s: starting", name)
        # thread loop
        while True:
            if evt_set_reset_high.is_set() == False:
                if os.path.isfile(FILE_NAME_RESET_HIGH):
                    os.rename(FILE_NAME_RESET_HIGH,
                              FILE_NAME_RESET_LOW)
                else:
                    f = open(FILE_NAME_RESET_LOW, "w+")
                    f.close()
                logging.info("Reset set to LOW")
                evt_set_reset_high.wait(999999)
            else:
                if os.path.isfile(FILE_NAME_RESET_LOW):
                    os.rename(FILE_NAME_RESET_LOW,
                              FILE_NAME_RESET_HIGH)
                else:
                    f = open(FILE_NAME_RESET_HIGH, "w+")
                    f.close()
                logging.info("Reset set to HIGH")
                evt_set_reset_low.wait(999999)

    def do_led(self):
        for i in range(configuration.NR_LEDS):
            if self.LED_ON[i] == 0:
                if os.path.isfile(FILE_NAME_LED_ON[i]):
                    os.remove(FILE_NAME_LED_ON[i])
                    # TODO: check if we can remove this and instead cleanup e.g. just on reset.
                    #       That is, at places where we may create inconsistencies.
                    # clean up just in case (we assume signal cannot be set faster than we poll)                    
                    if os.path.isfile(FILE_NAME_LED_OFF[i]):
                        os.remove(FILE_NAME_LED_OFF[i])
                    logging.debug("LED %s is ON", str(i))  # logging.info("LED %s is ON", str(i))
                    self.LED_ON[i] = 1
            else:
                if os.path.isfile(FILE_NAME_LED_OFF[i]):
                    os.remove(FILE_NAME_LED_OFF[i])
                    # clean up just in case (we assume signal cannot be set faster than we poll)                    
                    if os.path.isfile(FILE_NAME_LED_ON[i]):
                        os.remove(FILE_NAME_LED_ON[i])
                    logging.debug("LED %s is OFF", str(i))  # logging.info("LED %s is OFF", str(i))
                    self.LED_ON[i] = 0
        # inform GUI
        evt_gui_led_update.set()

    def do_do(self):
        for i in range(configuration.NR_DOS):
            if self.DO_HIGH[i] == 0:
                if os.path.isfile(FILE_NAME_DO_HIGH[i]):
                    os.remove(FILE_NAME_DO_HIGH[i])
                    # clean up just in case (we assume signal cannot be set faster than we poll)
                    if os.path.isfile(FILE_NAME_DO_LOW[i]):
                        os.remove(FILE_NAME_DO_LOW[i])
                    logging.debug("DO %s is HIGH", str(i))
                    self.DO_HIGH[i] = 1
            else:
                if os.path.isfile(FILE_NAME_DO_LOW[i]):
                    os.remove(FILE_NAME_DO_LOW[i])
                    # clean up just in case (we assume signal cannot be set faster than we poll)
                    if os.path.isfile(FILE_NAME_DO_HIGH[i]):
                        os.remove(FILE_NAME_DO_HIGH[i])
                    logging.debug("DO %s is LOW", str(i))
                    self.DO_HIGH[i] = 0
        # inform GUI
        evt_gui_do_update.set()

    def init_csv_log(self):
        if self.csv_file.closed == False:
            row = "clock,"
            row += "reset,"
            for i in range(configuration.NR_DIS):
                row += "DI_" + str(configuration.NR_DIS - 1 - i) + ","
            for i in range(configuration.NR_DOS):
                row += "DO_" + str(configuration.NR_DOS - 1 - i) + ","
            row += "toggle_switch,"
            row += "toggle_button,"
            for i in range(configuration.NR_LEDS):
                row += "LED_" + str(configuration.NR_LEDS - 1 - i) + ","
            # logging.debug(row)
            row += "\n"
            self.csv_file.write(row)

    def csv_log(self):
        if self.csv_file.closed == False:
            level = 30
            row = str(int(self.toggle) + level) + ","
            level = level - 2
            row += str(int(evt_set_reset_high.is_set()) + level) + ","
            level = level - 2
            for i in range(configuration.NR_DIS):
                row += str(self.DI_HIGH[configuration.NR_DIS - 1 - i] + level) + ","
                level = level - 2
            for i in range(configuration.NR_DOS):
                row += str(self.DO_HIGH[configuration.NR_DOS - 1 - i] + level) + ","
                level = level - 2
            row += str(int(self.toggle_switch) + level) + ","
            level = level - 2
            row += str(int(self.toggle_button) + level) + ","
            level = level - 2
            for i in range(configuration.NR_LEDS):
                row += str(self.LED_ON[configuration.NR_LEDS - 1 - i] + level) + ","
                level = level - 2
            # logging.debug(row)
            row += "\n"
            self.csv_file.write(row)

    def updateMemberVariables(self):
        self.DI_HIGH = []
        for i in range(configuration.NR_DIS):
            self.DI_HIGH.append(0)
        self.DO_HIGH = []
        for i in range(configuration.NR_DOS):
            self.DO_HIGH.append(0)
        self.LED_ON = []
        for i in range(configuration.NR_LEDS):
            self.LED_ON.append(0)

    def updateGuiConfig(self):
        # update logging level
        self.updateLoggingLevel()
        # start logger
        format = '%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s'
        logging.basicConfig(format=format, datefmt='%H:%M:%S:%m', level=configuration.LOGGING_LEVEL)
        # simulator options        
        self.leClkPeriods.setText(str(configuration.RUN_FOR_CLOCK_PERIODS))
        self.leClkPeriodMs.setText(str(int(CLOCK_PERIOD_SEC * 1000)))
        self.leGuiRefreshHz.setText(str(configuration.GUI_UPDATE_PERIOD_IN_HZ))
        self.pbKeepPbPressed.setChecked(configuration.KEEP_PB_PRESSED)

    # thread
    def thread_buttonSound(self):
        playsound(configuration.PATH_PREFIX + 'sounds/buttonClick.mp3')

    # slot
    def on_button_clicked(self, idx):
        if configuration.KEEP_PB_PRESSED == True:
            if configuration.SOUND_EFFECTS:
                # play this sound in a separate thread in order not to block
                buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
                buttonSoundThread.start()
            if self.evt_set_button_on[idx].is_set() == True:
                self.evt_set_button_on[idx].clear()
                self.evt_set_button_off[idx].set()
                self.button[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_up.png'))
            else:
                self.evt_set_button_off[idx].clear()
                self.evt_set_button_on[idx].set()
                self.button[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_down.png'))

    # slot
    def on_button_pressed(self, idx):
        if configuration.KEEP_PB_PRESSED == False:
            if configuration.SOUND_EFFECTS:
                # play this sound in a separate thread in order not to block
                buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
                buttonSoundThread.start()
            self.evt_set_button_off[idx].clear()
            self.evt_set_button_on[idx].set()
            self.button[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_down.png'))

    # slot
    def on_button_released(self, idx):
        if configuration.KEEP_PB_PRESSED == False:
            if configuration.SOUND_EFFECTS:
                # play this sound in a separate thread in order not to block
                buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
                buttonSoundThread.start()
            self.evt_set_button_on[idx].clear()
            self.evt_set_button_off[idx].set()
            self.button[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_up.png'))

    def on_switch_clicked(self, idx):
        if configuration.SOUND_EFFECTS:
            # play this sound in a separate thread in order not to block
            buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            buttonSoundThread.start()
        if self.evt_set_switch_on[idx].is_set() == True:
            self.evt_set_switch_on[idx].clear()
            self.evt_set_switch_off[idx].set()
            self.switch[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/sw_left.png'))
        else:
            self.evt_set_switch_off[idx].clear()
            self.evt_set_switch_on[idx].set()
            self.switch[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/sw_right.png'))

    # thread
    def thread_powerSound(self):
        playsound(configuration.PATH_PREFIX + 'sounds/power_on_off.mp3')

    @pyqtSlot(bool)
    def on_pbOnOff_toggled(self, checked):
        if checked == True:
            # create log file
            if configuration.LOG_ON_POWER_ON_OFF == False:
                if configuration.LOG_TO_CSV == True:
                    self.csv_file = open("log.csv", 'w')
                    self.init_csv_log()
            # power on
            evt_set_power_off.clear()
            evt_set_power_on.set()
            self.pbOnOff.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/off.png'))
            self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_on.png'))
            # set RESET to high for T/2 in order to initialize VHDL signals
            evt_set_reset_low.clear()
            evt_set_reset_high.set()
            time.sleep((CLOCK_PERIOD_SEC / 2)*2)
            evt_set_reset_high.clear()
            evt_set_reset_low.set()
            # time.sleep(CLOCK_PERIOD_SEC/2) # need this?            
            # enable pause and step
            self.pbRunPause.setEnabled(True)
            self.pbStep.setEnabled(True)
            self.pbRunForTime.setEnabled(True)
        else:
            # disable pause and step
            self.pbRunPause.setEnabled(False)
            self.pbStep.setEnabled(False)
            self.pbRunForTime.setEnabled(False)
            # power off
            evt_set_power_on.clear()
            evt_set_power_off.set()
            self.pbOnOff.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/on.png'))
            self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_off.png'))
            # close log file
            if configuration.LOG_ON_POWER_ON_OFF == False:
                if configuration.LOG_TO_CSV == True:
                    self.csv_file.close()
        # on
        if configuration.SOUND_EFFECTS:
            # play this sound in a separate thread in order not to block
            powerSoundThread = threading.Thread(name="powerSound", target=self.thread_powerSound)
            powerSoundThread.start()

    @pyqtSlot(bool)
    def on_pbRunPause_toggled(self, checked):
        if evt_pause.is_set() == False:  # if checked == True:
            evt_resume.clear()
            evt_pause.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/run.png'))
        else:
            # check if we need to remove step
            if evt_step_on.is_set() == True:
                evt_step_on.clear()
            # resume
            evt_pause.clear()
            evt_resume.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/pause.png'))
        if configuration.SOUND_EFFECTS:
            # play this sound in a separate thread in order not to block
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            powerSoundThread.start()

    @pyqtSlot(bool)
    def on_pbStep_toggled(self, checked):
        if evt_step_on.is_set() == False:
            evt_step_on.set()
        evt_do_step.set()
        if evt_pause.is_set() == True:
            # resume
            evt_pause.clear()
            evt_resume.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/pause.png'))
        logging.info("STEP")
        if configuration.SOUND_EFFECTS:
            # play this sound in a separate thread in order not to block
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            powerSoundThread.start()

    # thread
    def thread_runForTime(self):
        logging.info("Run for " + str(configuration.RUN_FOR_CLOCK_PERIODS) + " clock cycles.")
        # wait for specified time (dummy event evt_wake_up never comes)
        self.remaining_time_to_run = configuration.RUN_FOR_CLOCK_PERIODS
        while ((self.remaining_time_to_run > 0) and (evt_pause.is_set() == False) and (evt_step_on.is_set() == False)):
            evt_wake_up.wait(CLOCK_PERIOD_SEC)
            self.remaining_time_to_run = self.remaining_time_to_run - 1
            # update GUI
            evt_gui_remain_run_time_update.set()
        if self.remaining_time_to_run > 0:
            logging.info("Run for time expired, simulation was paused or stepped_on")
        else:
            # time expired, now pause
            evt_pause.set()
            evt_resume.clear()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/run.png'))
            logging.info("Run for time expired, now pause")
        # re-enable button
        self.pbRunForTime.setEnabled(True)

    @pyqtSlot(bool)
    def on_pbRunForTime_toggled(self, checked):
        # disable button during timed run
        self.pbRunForTime.setEnabled(False)
        # resume if necessary
        if evt_step_on.is_set():
            evt_step_on.clear()
        if (evt_pause.is_set() == True):
            # resume
            evt_pause.clear()
            evt_resume.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/pause.png'))
        # run for time in a separate thread in order not to block
        runForTimeThread = threading.Thread(name="runForTime", target=self.thread_runForTime)
        runForTimeThread.start()
        if configuration.SOUND_EFFECTS:
            # play this sound in a separate thread in order not to block
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            powerSoundThread.start()

    @pyqtSlot(bool)
    def on_pbReset_toggled(self, checked):
        if evt_set_reset_high.is_set() == True:
            evt_set_reset_high.clear()
            evt_set_reset_low.set()
            self.lblReset.setText("RESET: low")
        else:
            evt_set_reset_low.clear()
            evt_set_reset_high.set()
            self.lblReset.setText("RESET: high")
        if configuration.SOUND_EFFECTS:
            # play this sound in a separate thread in order not to block
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_powerSound)
            powerSoundThread.start()

    @pyqtSlot()
    def on_leClkPeriods_editingFinished(self):
        try:
            configuration.RUN_FOR_CLOCK_PERIODS = int(self.leClkPeriods.text())
        except:
            # NOTE: set text to current value
            self.leClkPeriods.setText(str(configuration.RUN_FOR_CLOCK_PERIODS))
            logging.error("clock periods shall be an integer")
            tkinter.messagebox.showerror(title="ERROR", message="clock periods shall be an integer")
            root.update()

    @pyqtSlot()
    def on_leClkPeriodMs_editingFinished(self):
        try:
            tempValue = int(self.leClkPeriodMs.text())
            if tempValue <= 0:
                # NOTE: set text to current value
                self.leClkPeriodMs.setText(str(int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])))
                logging.error("clock period shall be greater than zero")
                tkinter.messagebox.showerror(title="ERROR", message="clock period shall be greater than zero")
                root.update()
            elif tempValue < configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS:
                # NOTE: set text to current value
                self.leClkPeriodMs.setText(str(int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])))
                logging.warning("small clock periods may produce an inaccurate simulation!")
                tkinter.messagebox.showerror(title="ERROR",
                                             message="small clock periods may produce an inaccurate simulation!")
                root.update()
            else:
                configuration.CLOCK_PERIOD_EXTERNAL = str(tempValue * 1000000) + " ns"
                # update GUI definitions (e.g. values to change polling rate of threads)
                updateGuiDefs()
        except:
            # NOTE: set text to current value
            self.leClkPeriodMs.setText(str(int(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])))
            logging.error("clock periods shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR", message="clock periods shall be an integer value")
            root.update()

    @pyqtSlot()
    def on_leGuiRefreshHz_editingFinished(self):
        try:
            tempValue = int(self.leGuiRefreshHz.text())
            if tempValue <= 0:
                # NOTE: set text to current value
                self.leGuiRefreshHz.setText(str(configuration.GUI_UPDATE_PERIOD_IN_HZ))
                logging.error("GUI refresh rate shall be greater than zero")
                tkinter.messagebox.showerror(title="ERROR", message="GUI refresh rate shall be greater than zero")
                root.update()
            else:
                configuration.GUI_UPDATE_PERIOD_IN_HZ = tempValue
        except:
            # NOTE: set text to current value
            self.leGuiRefreshHz.setText(str(configuration.GUI_UPDATE_PERIOD_IN_HZ))
            logging.error("GUI refresch rate shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR", message="GUI refresch rate shall be an integer value")
            root.update()

    @pyqtSlot()
    def on_pbKeepPbPressed_clicked(self):
        configuration.KEEP_PB_PRESSED = not configuration.KEEP_PB_PRESSED
        if configuration.KEEP_PB_PRESSED:
            self.pbKeepPbPressed.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/jmp_on.png'))
        else:
            self.pbKeepPbPressed.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/jmp_off.png'))
        if configuration.SOUND_EFFECTS:
            # play this sound in a separate thread in order not to block
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_powerSound)
            powerSoundThread.start()

    @pyqtSlot()
    def on_pbSettingsLoad_clicked(self):
        restorePlot = False
        # first close plot if active, otherwise thread sync error
        if configuration.SHOW_PLOT:
            configuration.SHOW_PLOT = False
            self.on_cbPlotShow_clicked()
            restorePlot = True
        # load config
        self.lblConfigFileName.setText(self.cfg.loadConfig())
        self.updateGuiConfig()
        # restore plot if required
        if restorePlot:
            configuration.SHOW_PLOT = True
            self.on_cbPlotShow_clicked()
        root.update()

    @pyqtSlot()
    def on_pbSettingsSave_clicked(self):
        self.lblConfigFileName.setText(self.cfg.saveConfig())

    @pyqtSlot()
    def on_pbSettingsSaveAs_clicked(self):
        restorePlot = False
        # first close plot if active, otherwise thread sync error
        if configuration.SHOW_PLOT:
            configuration.SHOW_PLOT = False
            self.on_cbPlotShow_clicked()
            restorePlot = True
        # save config as
        self.lblConfigFileName.setText(self.cfg.saveConfigAs())
        # restore plot if required
        if restorePlot:
            configuration.SHOW_PLOT = True
            self.on_cbPlotShow_clicked()
        root.update()

    def changeShowPlotThread(self):
        # TODO:  this call just blocks forever. Investigate, and if possible call plt.close in Slot() instead.
        #             a "dead/blocked" thread remains in memory every time we switch off here.
        plt.close()
        # TODO: by the way, why can't we just do this instead?
        # plt.gcf().set_visible(False)
        # plt.draw() # needed to make previous call effective?

    # called from the "main loop"
    def plotThread(self):
        # TODO: implement
        #################
        '''
        try:
            # build plot
            # IMPORTANT: FuncAnimation uses Tk and MUST run in main loop !!!
            ################################################################
            if configuration.PLOT_FFT:
                ...
            # this call BLOCKS as long as plt remains open
            ##############################################
            plt.show()
            # plt.close() was called
            logging.info("leave plotThread..")
        except Exception as e:
            logging.error("Exception in plotThread...leaving thread" + str(e))
        '''
        return

    @pyqtSlot()
    def on_cbPlotShow_clicked(self):
        if configuration.SHOW_PLOT != self.cbPlotShow.isChecked():
            configuration.SHOW_PLOT = self.cbPlotShow.isChecked()
            if configuration.SHOW_PLOT:
                # create and start plot thread anew..
                plotThread = threading.Thread(name="plotThread", target=self.plotThread)
                plotThread.start()
            else:
                # close plot thread in a separate thread which will BLOCK - that thread will call plt.close()
                changeShowPlotThread = threading.Thread(name="changeShowPlotThread", target=self.changeShowPlotThread)
                changeShowPlotThread.start()

    @pyqtSlot(str)
    def on_cbLoggingLevel_currentIndexChanged(self, p0):
        if self.appStarted:
            configuration.LOGGING_LEVEL = p0  # self.cbLoggingLevel.currentText()
            self.updateLoggingLevel()

    def updateLoggingLevel(self):
        index = self.cbLoggingLevel.findText(configuration.LOGGING_LEVEL,
                                             Qt.MatchFlag.MatchExactly)  # .findText(configuration.LOGGING_LEVEL, Qt.MatchFixedString)
        if index >= 0:
            self.cbLoggingLevel.setCurrentIndex(index)
            # if the severity level is INFO, the logger will handle only INFO, WARNING, ERROR, and CRITICAL messages and will ignore DEBUG messages
            # logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
            logging_level = logging.INFO
            if configuration.LOGGING_LEVEL == "logging.DEBUG":
                logging_level = logging.DEBUG
            if configuration.LOGGING_LEVEL == "logging.INFO":
                logging_level = logging.INFO
            if configuration.LOGGING_LEVEL == "logging.WARNING":
                logging_level = logging.WARNING
            if configuration.LOGGING_LEVEL == "logging.ERROR":
                logging_level = logging.ERROR
            if configuration.LOGGING_LEVEL == "logging.CRITICAL":
                logging_level = logging.CRITICAL
            logging.basicConfig(format='%(asctime)s.%(msecs)03d %(message)s', datefmt='%H:%M:%S', level=logging_level)
        else:
            self.cbLoggingLevel.setCurrentIndex(1)  # default INFO
            logging.basicConfig(format='%(asctime)s.%(msecs)03d %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

    @pyqtSlot()
    def on_cbShowLiveStatus_clicked(self):
        if configuration.SHOW_LIVE_STATUS != self.cbShowLiveStatus.isChecked():
            configuration.SHOW_LIVE_STATUS = self.cbShowLiveStatus.isChecked()
            if configuration.SHOW_LIVE_STATUS:
                self.lblStatus.setEnabled(True)
                self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_on.png'))
            else:
                self.lblStatus.setEnabled(False)

    @pyqtSlot()
    def on_cbLoggingOn_clicked(self):
        if configuration.LOG_TO_CSV != self.cbLoggingOn.isChecked():
            configuration.LOG_TO_CSV = self.cbLoggingOn.isChecked()
            if configuration.LOG_TO_CSV == True:
                self.csv_file = open("log.csv", 'w')
                self.init_csv_log()

    @pyqtSlot()
    def on_cbLogOnPowerOnOff_clicked(self):
        if configuration.LOG_ON_POWER_ON_OFF != self.cbLogOnPowerOnOff.isChecked():
            configuration.LOG_ON_POWER_ON_OFF = self.cbLogOnPowerOnOff.isChecked()

    @pyqtSlot()
    def on_pbFilePath_clicked(self):
        directory = filedialog.askdirectory()
        if directory != ():
            # set parameter
            configuration.FILE_PATH = directory + "/"
            # update widget
            self.leFilePath.setText(configuration.FILE_PATH)
            # initialize file path
            init_file_path()
            # create temporary files
            createTempFiles()
            logging.warning(
                "FILE_PATH updated. New value will take effect after saving configuration and restarting application!")
            tkinter.messagebox.showwarning(title="WARNING",
                                           message="FILE_PATH updated. New value will take effect after saving configuration and restarting application!")
            root.update()

    @pyqtSlot()
    def on_cbSoundOn_clicked(self):
        if configuration.SOUND_EFFECTS != self.cbSoundOn.isChecked():
            configuration.SOUND_EFFECTS = self.cbSoundOn.isChecked()

    @pyqtSlot()
    def on_leMaxDiCount_editingFinished(self):
        try:
            configuration.MAX_DI_COUNT = int(self.leMaxDiCount.text())
        except:
            # NOTE: set text to current value
            self.leMaxDiCount.setText(str(configuration.MAX_DI_COUNT))
            logging.error("Max. count value shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR", message="Max. count value shall be an integer value")
            root.update()

    @pyqtSlot()
    def on_leDiPerInClkPer_editingFinished(self):
        try:
            configuration.DI_PER_IN_CLK_PER = int(self.leDiPerInClkPer.text())
        except:
            # NOTE: set text to current value
            self.leDiPerInClkPer.setText(str(configuration.DI_PER_IN_CLK_PER))
            logging.error("DI period in clock periods shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR", message="DI period in clock periods shall be an integer value")
            root.update()

    @pyqtSlot()
    def on_leSwPerInClkPer_editingFinished(self):
        try:
            configuration.SW_PER_IN_CLK_PER = int(self.leSwPerInClkPer.text())
        except:
            # NOTE: set text to current value
            self.leSwPerInClkPer.setText(str(configuration.SW_PER_IN_CLK_PER))
            logging.error("Switch period in clock periods shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR",
                                         message="Switch period in clock periods shall be an integer value")
            root.update()

    @pyqtSlot()
    def on_leBtnPerClkPer_editingFinished(self):
        try:
            configuration.BUTTON_PER_IN_CLK_PER = int(self.leBtnPerClkPer.text())
        except:
            # NOTE: set text to current value
            self.leBtnPerClkPer.setText(str(configuration.BUTTON_PER_IN_CLK_PER))
            logging.error("Button period in clock periods shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR",
                                         message="Button period in clock periods shall be an integer value")
            root.update()

    @pyqtSlot()
    def on_leMinClockPeriodMs_editingFinished(self):
        try:
            tempValue = int(self.leMinClockPeriodMs.text())
            if tempValue <= 0:
                # NOTE: set text to current value
                self.leMinClockPeriodMs.setText(str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS))
                logging.error("Min. clock period shall be greater than zero")
                tkinter.messagebox.showerror(title="ERROR", message="Min. clock period shall be greater than zero")
                root.update()
            else:
                configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS = tempValue
        except:
            # NOTE: set text to current value
            self.leMinClockPeriodMs.setText(str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS))
            logging.error("Min. clock period shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR", message="Min. clock period shall be an integer value")
            root.update()

    @pyqtSlot(int)
    def on_cbNrDis_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_DIS = index
            # check if we need to update combobox to select NR_ASYNC_DI (and also NR_SYNC_DI)
            if self.cbNrAsyncDis.count() > configuration.NR_DIS:
                self.cbNrAsyncDis.clear()
                for i in range(configuration.NR_DIS + 1):
                    self.cbNrAsyncDis.addItem(str(i))
                configuration.NR_ASYNC_DI = configuration.NR_DIS
                self.cbNrAsyncDis.setCurrentIndex(configuration.NR_ASYNC_DI)
                # update NR_SYNC_DI and combobox
                configuration.NR_SYNC_DI = configuration.NR_DIS - configuration.NR_ASYNC_DI
                # update lists
                SYNC_DI.clear()
                ASYNC_DI.clear()
                for i in range(configuration.NR_SYNC_DI):
                    SYNC_DI.append(i)
                for i in range(configuration.NR_ASYNC_DI):
                    ASYNC_DI.append(configuration.NR_ASYNC_DI + i)
            elif configuration.NR_DIS + 1 > self.cbNrAsyncDis.count():
                count = self.cbNrAsyncDis.count()
                for i in range(configuration.NR_DIS + 1 - count):
                    self.cbNrAsyncDis.addItem(str(count + i))

    @pyqtSlot(int)
    def on_cbNrAsyncDis_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_ASYNC_DI = index
            configuration.NR_SYNC_DI = configuration.NR_DIS - configuration.NR_ASYNC_DI
            # update lists
            SYNC_DI.clear()
            ASYNC_DI.clear()
            for i in range(configuration.NR_SYNC_DI):
                SYNC_DI.append(i)
            for i in range(configuration.NR_ASYNC_DI):
                ASYNC_DI.append(configuration.NR_ASYNC_DI + i)

    @pyqtSlot(int)
    def on_cbNrDos_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_DOS = index

    @pyqtSlot(int)
    def on_cbNrBtns_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_BUTTONS = index

    @pyqtSlot(int)
    def on_cbNrSwitches_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_SWITCHES = index

    @pyqtSlot(int)
    def on_cbNrLeds_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_LEDS = index

    @pyqtSlot(int)
    def on_cbMaxDiCount_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.MAX_DI_COUNT = index

    @pyqtSlot()
    def on_cbBtnToggleAuto_clicked(self):
        if configuration.BUTTON_TOGGLE_AUTO != self.cbBtnToggleAuto.isChecked():
            configuration.BUTTON_TOGGLE_AUTO = self.cbBtnToggleAuto.isChecked()

    @pyqtSlot()
    def on_cbSwToggleAuto_clicked(self):
        if configuration.SWITCH_TOGGLE_AUTO != self.cbSwToggleAuto.isChecked():
            configuration.SWITCH_TOGGLE_AUTO = self.cbSwToggleAuto.isChecked()
