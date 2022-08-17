from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtGui import QFont, QIntValidator # , QDoubleValidator
from time import gmtime, strftime
from .Ui_mainWindow import Ui_MainWindow
from inspect import currentframe
from playsound import playsound
# import matplotlib.pyplot as plt
import tkinter
import tkinter.messagebox
from tkinter import filedialog
import functools
from sys import platform
# NOTE: with a time delay of 1 ~ 15 ms threading.Event.wait() works really bad!
#       We use oclock.Event.wait() together with set_resolution_ns() instead, which seems to work better, see
#       https://stackoverflow.com/questions/48984512/making-a-timer-timeout-inaccuracy-of-threading-event-wait-python-3-6
import os
import logging
import threading
import time
# own modules
import configuration
import init
import oclock
from clock import clock
from digital_inputs import digital_inputs
from digital_outputs import digital_outputs
from leds import leds
from leds_fifo import leds_fifo
from reset import reset
from switches import switches
from buttons import buttons
from scheduler import scheduler



USE_LED_FIFO = True # NOTE: this parameter is not in config.ini

# NOTE: minimize application windows when not needed in order to increase performance.
#       Intensive work on wave output on the simulator may also affect performance.
#       Stress tests with CLOCK_PERIOD:
#       100ms (almost no jitter)
#       50ms  (small jitter)
#       10ms  (medium jitter)
#       1ms   NOK
######################################################################################

# TODOs:
# - create common base classes, e.g. for digital_outputs and leds_fifo
# - add analog sensor (e.g. CPU load)
# - plot signals
# - add analog readings from file (reproducible tests!)
# - add serial communication (UART, SPI, I2C,..) e.g. to pass sensor values
# - improve VHDL code: use blocks, etc.
# - improve performance: use profiler to get rid of bottlenecks

# init logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)

# current frame
cf = currentframe()

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

# TODO: solve the bug before use: if user presses OK then it hangs!?
def timed_messagebox(message, type='info', timeout=3000):
    root = tkinter.Tk()
    root.withdraw()
    try:
        root.after(timeout, root.destroy)
        if type == 'info':
            tkinter.messagebox.showinfo('Info', message, master=root)
        elif type == 'warning':
            tkinter.messagebox.showwarning('Warning', message, master=root)
        elif type == 'error':
            tkinter.messagebox.showerror('Error', message, master=root)
    except:
        pass

# events used in threads:
class event():
    evt_set_power_on = oclock.Event()
    evt_set_power_off = oclock.Event()
    evt_set_reset_high = oclock.Event()
    evt_set_reset_low = oclock.Event()
    evt_pause = oclock.Event()
    evt_resume = oclock.Event()
    evt_step_on = oclock.Event()
    evt_do_step = oclock.Event()
    # NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
    #       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
    evt_wake_up = oclock.Event()
    evt_clock = oclock.Event()
    evt_close_app = oclock.Event()
    # these events improve performance by indicating exactly when the GUI shall update which widgets.
    # NOTE: using individual events for each of the DIs and DOs to "fine tune" GUI update decreases performance!
    evt_gui_di_update = oclock.Event()
    evt_gui_do_update = oclock.Event()
    evt_gui_led_update = oclock.Event()
    evt_gui_remain_run_time_update = oclock.Event()
# object/instance
event = event()



# main window
#############
class MainWindow(QMainWindow, Ui_MainWindow):
    # NOTE: be careful to initialize and/or use configuration within this part of the class.
    #       Instead, do all that inside __init__()
    #       This is true for all classes!
    cfg = None  # __init__.InitApp()
    appStarted = False
    status = ["/", "-", "\\", "|"]
    statusCnt = 0
    csv_file = None
    CLOCK_PERIOD_SEC = [0]
    clock_high = False
    remaining_time_to_run = 0
    # peripheral and app objects
    clock = None
    digital_inputs = None
    digital_outputs = None
    leds = None
    reset = None
    switches = None
    buttons = None
    scheduler = None
    # references to specific peripheral and app objects to be passed to scheduler as a single parameter
    class ref_scheduler():
        clock = None
        digital_inputs = None
        digital_outputs = None
        leds = None
        reset = None
        switches = None
        buttons = None
    # object/instance
    ref_scheduler = ref_scheduler()
    # widgets:
    pbKeepPbPressed = None
    button_wdg = []
    switch_wdg = []
    led_wdg = []
    di_wdg = []
    do_wdg = []

    # information message in terminal
    logging.info("INFO: start the VHDL tool if not yet started..GUI will then show up!")
    # information message in messagebox
    # TODO: solve bug before use: timed_messagebox("start the VHDL simulator if not done yet..GUI will then show up!", timeout=7000)
    tkinter.messagebox.showinfo(title="INFORMATION", message="Please start the VHDL tool if not yet started!")
    root.update()

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
            while event.evt_close_app.is_set() == False:
                event.evt_wake_up.wait(1 / configuration.GUI_UPDATE_PERIOD_IN_HZ)
                self.updated.emit("Hi")
            logging.info("left MyGuiUpdateThread:run()!")

    # thread to update GUI
    ######################
    def updateGui(self):
        # update status on GUI
        ######################
        if (self.lblStatus is not None):
            # device on?
            if event.evt_set_power_on.is_set() == True:
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
                if event.evt_gui_led_update.is_set():
                    event.evt_gui_led_update.clear()
                    for i in range(configuration.NR_LEDS):
                        if self.leds.LED_ON[i] == 1:
                            self.led_wdg[i].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_on.png'))
                        else:
                            self.led_wdg[i].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_off.png'))
                # digital inputs
                if event.evt_gui_di_update.is_set():
                    event.evt_gui_di_update.clear()
                    for i in range(configuration.NR_DIS):
                        self.di_wdg[i].setText(str(self.digital_inputs.DI_HIGH[i]))
                # digital outputs
                if event.evt_gui_do_update.is_set():
                    event.evt_gui_do_update.clear()
                    for i in range(configuration.NR_DOS):
                        self.do_wdg[i].setText(str(self.digital_outputs.DO_HIGH[i]))
                # update remaining time when running for time
                if event.evt_gui_remain_run_time_update.is_set():
                    event.evt_gui_remain_run_time_update.clear()
                    self.lblRemaining.setText(str(self.remaining_time_to_run))
            else:
                # stop blinking active LED                                            
                if self.pbActive.isChecked():
                    self.pbActive.setChecked(False)
                    self.pbActive.setChecked(self.pbActive.isChecked())
                    self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_off.png'))

    def updateGuiDefs(self):
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

    def init_file_path(self):
        # remove dir if it exists (this will clean everything up)
        if os.path.exists(configuration.FILE_PATH):
            # Remove files
            logging.info("FILE_PATH = " + configuration.FILE_PATH + " exists..")
        else:
            # create temporary directory
            os.mkdir(configuration.FILE_PATH)
            logging.info("FILE_PATH = " + configuration.FILE_PATH + " created..")

    def __init__(self, qApplication, parent=None, sdm_arg=None):
        # call super
        super(MainWindow, self).__init__(parent)
        # load .ini file and set values in GUI
        ######################################
        self.cfg = init.InitApp()
        # InitApp() has read config.ini thus we need to update all definitions
        self.updateGuiDefs()
        # file path
        self.init_file_path()
        # create file to log
        if configuration.LOG_TO_CSV == True:
            self.csv_file = open("log.csv", 'w')
            self.init_csv_log()
        # instantiate peripheral and app objects
        ########################################
        self.clock = clock(event, self.CLOCK_PERIOD_SEC) # NOTE: self.CLOCK_PERIOD_SEC is set within this call
        self.reset = reset(event)
        if USE_LED_FIFO == True:
            self.leds = leds_fifo(event)
        else:
            self.leds = leds(event)
        self.switches = switches(event, self.CLOCK_PERIOD_SEC)
        self.digital_inputs = digital_inputs(event, self.CLOCK_PERIOD_SEC)
        self.digital_outputs = digital_outputs(event)
        self.buttons = buttons(event, self.CLOCK_PERIOD_SEC)
        # fill "after" objects have been created
        self.ref_scheduler.clock = self.clock
        self.ref_scheduler.digital_inputs = self.digital_inputs
        self.ref_scheduler.digital_outputs = self.digital_outputs
        self.ref_scheduler.leds = self.leds
        self.ref_scheduler.reset = self.reset
        self.ref_scheduler.switches = self.switches
        self.ref_scheduler.buttons = self.buttons
        # instantiate scheculer
        self.scheduler = scheduler(event, self.CLOCK_PERIOD_SEC, self.csv_log, self.ref_scheduler)
        # setup Ui
        self.setupUi(self)
        # further Ui setup
        self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(self.tab_fpga)) # default tab is tab_fpga
        self.cbLogOnPowerOnOff.setToolTip("Log over power on/off in a single file if checked.")
        self.leFilePath.setText(configuration.FILE_PATH)
        self.leFifoPath.setText(configuration.FIFO_PATH)
        self.leClkPeriods.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leClkPeriods.setValidator(QIntValidator())
        self.leClkPeriodMs.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        # TODO: check why this validator is not working, impeding correct input on GUI
        # self.leClkPeriodMs.setValidator(QDoubleValidator()) # self.leClkPeriodMs.setValidator(QIntValidator())
        self.leGuiRefreshHz.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leGuiRefreshHz.setValidator(QIntValidator())
        self.leMinClockPeriodMs.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        # TODO: check why this validator is not working, impeding correct input on GUI
        # self.leMinClockPeriodMs.setValidator(QDoubleValidator()) # (QIntValidator())
        self.leResetSecs.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        # TODO: check why this validator is not working, impeding correct input on GUI
        # self.leResetSecs.setValidator(QDoubleValidator()) # (QIntValidator())
        self.leMaxDiCount.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leMaxDiCount.setValidator(QIntValidator())
        self.leDiPerInClkPer.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leDiPerInClkPer.setValidator(QIntValidator())
        self.leSwPerInClkPer.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leSwPerInClkPer.setValidator(QIntValidator())
        self.leBtnPerClkPer.setFont(QFont('Ubuntu Mono', configuration.TEXT_SIZE))
        self.leBtnPerClkPer.setValidator(QIntValidator())
        self.lblVersion.setToolTip(configuration.VERSION_TOOL_TIP)
        self.cbPlotShow.setChecked(configuration.SHOW_PLOT)
        self.cbSoundOn.setChecked(configuration.SOUND_EFFECTS)
        self.cbTest.setToolTip("execute test code, e.g. to measure performance.\nTest results will be logged to console after closing the window.")
        self.cbTest.setChecked(configuration.TEST)
        self.cbShowLiveStatus.setChecked(configuration.SHOW_LIVE_STATUS)
        self.cbLoggingOn.setChecked(configuration.LOG_TO_CSV)
        self.leMinClockPeriodMs.setText(str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS))
        self.leResetSecs.setText(str(configuration.RESET_FOR_SECONDS))
        self.cbLogOnPowerOnOff.setChecked(configuration.LOG_ON_POWER_ON_OFF)
        self.on_pbOnOff_toggled(configuration.LOG_ON_POWER_ON_OFF)
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
        if configuration.KEEP_PB_PRESSED:
            self.pbKeepPbPressed.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/jmp_on.png'))
        else:
            self.pbKeepPbPressed.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/jmp_off.png'))
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
        # digital inputs
        for i in range(configuration.NR_DIS):
            # di label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(575 - i * 2 * 12 - (i / 4) * 3, 490, 58, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("di_lbl_" + str(i))
            label.setText("" + str(i))
            # di label for value
            self.di_wdg.append(QtWidgets.QLabel(self.tab_fpga))
            self.di_wdg[i].setGeometry(QtCore.QRect(577 - i * 2 * 12 - (i / 4) * 3, 515, 58, 16))
            self.di_wdg[i].setStyleSheet("color: rgb(0, 0, 0);")
            self.di_wdg[i].setObjectName("di_" + str(i))
            self.di_wdg[i].setText(str(self.digital_inputs.DI_HIGH[i]))
        # digital outputs
        for i in range(configuration.NR_DIS):
            # do label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(975 - i * 2 * 12 - (i / 4) * 3, 490, 58, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("do_" + str(i))
            label.setText("" + str(i))
            # do label for value
            self.do_wdg.append(QtWidgets.QLabel(self.tab_fpga))
            self.do_wdg[i].setGeometry(QtCore.QRect(977 - i * 2 * 12 - (i / 4) * 3, 515, 58, 16))
            self.do_wdg[i].setStyleSheet("color: rgb(0, 0, 0);")
            self.do_wdg[i].setObjectName("do_" + str(i))
            self.do_wdg[i].setText(str(self.digital_outputs.DO_HIGH[i]))
        # buttons
        icon_button = QtGui.QIcon()
        icon_button.addPixmap(QtGui.QPixmap(":/btn_up/btn_up.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon_button.addPixmap(QtGui.QPixmap(":/btn_down/btn_down.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        for i in range(configuration.NR_BUTTONS):
            # button widget
            self.button_wdg.append(QtWidgets.QPushButton(self.tab_fpga))
            self.button_wdg[i].setGeometry(QtCore.QRect(225, 190 + i * 2 * 15, 31, 21))
            self.button_wdg[i].setText("")
            self.button_wdg[i].setIcon(icon_button)
            self.button_wdg[i].setIconSize(QtCore.QSize(33, 21))
            self.button_wdg[i].setAutoDefault(False)
            self.button_wdg[i].setDefault(False)
            self.button_wdg[i].setFlat(True)
            self.button_wdg[i].setAutoFillBackground(False)
            self.button_wdg[i].setObjectName("button_" + str(i))
            self.button_wdg[i].clicked.connect(lambda checked, arg=i: self.on_button_clicked(arg))
            self.button_wdg[i].pressed.connect(functools.partial(self.on_button_pressed, i))
            self.button_wdg[i].released.connect(functools.partial(self.on_button_released, i))
            # button enabled?
            if configuration.BUTTON_TOGGLE_AUTO == True:
                self.button_wdg[i].setEnabled(False)
            # button label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(270, 192 + i * 2 * 15, 58, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("label_btn_" + str(i))
            label.setText("btn " + str(i))
        # switches
        icon_sw = QtGui.QIcon()
        icon_sw.addPixmap(QtGui.QPixmap(":/switch_left/sw_left.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon_sw.addPixmap(QtGui.QPixmap(":/switch_right/sw_right.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        for i in range(configuration.NR_SWITCHES):
            # switch widget
            self.switch_wdg.append(QtWidgets.QPushButton(self.tab_fpga))
            self.switch_wdg[i].setGeometry(QtCore.QRect(337, 190 + i * 2 * 15, 37, 17))
            self.switch_wdg[i].setText("")
            self.switch_wdg[i].setIcon(icon_sw)
            self.switch_wdg[i].setIconSize(QtCore.QSize(37, 17))
            self.switch_wdg[i].setFlat(True)
            self.switch_wdg[i].setObjectName("switch_" + str(i))
            self.switch_wdg[i].clicked.connect(lambda checked, arg=i: self.on_switch_clicked(arg))
            # switch enabled?
            if configuration.SWITCH_TOGGLE_AUTO == True:
                self.switch_wdg[i].setEnabled(False)
            # switch label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(387, 190 + i * 2 * 15, 41, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("label_sw_" + str(i))
            label.setText("sw " + str(i))
        # LEDs
        icon_led = QtGui.QIcon()
        icon_led.addPixmap(QtGui.QPixmap(":/led_off/led_off.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon_led.addPixmap(QtGui.QPixmap(":/led_on/led_on.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        for i in range(configuration.NR_LEDS):
            # LED widget
            self.led_wdg.append(QtWidgets.QPushButton(self.tab_fpga))
            self.led_wdg[i].setGeometry(QtCore.QRect(900, 190 + i * 2 * 15, 31, 16))
            self.led_wdg[i].setStyleSheet("")
            self.led_wdg[i].setText("")
            self.led_wdg[i].setIcon(icon_led)
            self.led_wdg[i].setIconSize(QtCore.QSize(25, 11))
            self.led_wdg[i].setFlat(True)
            self.led_wdg[i].setObjectName("led " + str(i))
            # LED label
            label = QtWidgets.QLabel(self.tab_fpga)
            label.setGeometry(QtCore.QRect(940, 190 + i * 2 * 15, 31, 16))
            label.setStyleSheet("color: rgb(238, 238, 236);")
            label.setObjectName("label_led_" + str(i))
            label.setText("led " + str(i))
        # set color
        self.lblStatus.setStyleSheet('QLabel {color: green}')
        # disable pause, step and run_for_time
        self.pbRunPause.setEnabled(False)
        self.pbStep.setEnabled(False)
        self.pbRunForTime.setEnabled(False)
        # thread to update GUI periodically
        ###################################
        self._thread = self.MyGuiUpdateThread(self)
        self._thread.updated.connect(self.updateGui)
        self._thread.start()
        # set flag
        self.appStarted = True

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
            row = str(int(self.scheduler.toggle) + level) + ","
            level = level - 2
            row += str(int(event.evt_set_reset_high.is_set()) + level) + ","
            level = level - 2
            for i in range(configuration.NR_DIS):
                row += str(self.digital_inputs.DI_HIGH[configuration.NR_DIS - 1 - i] + level) + ","
                level = level - 2
            for i in range(configuration.NR_DOS):
                row += str(self.digital_outputs.DO_HIGH[configuration.NR_DOS - 1 - i] + level) + ","
                level = level - 2
            row += str(int(self.switches.toggle_switch) + level) + ","
            level = level - 2
            row += str(int(self.buttons.toggle_button) + level) + ","
            level = level - 2
            for i in range(configuration.NR_LEDS):
                row += str(self.leds.LED_ON[configuration.NR_LEDS - 1 - i] + level) + ","
                level = level - 2
            # logging.debug(row)
            row += "\n"
            self.csv_file.write(row)

    def updateGuiConfig(self):
        # update logging level
        self.updateLoggingLevel()
        # start logger
        format = '%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s'
        logging.basicConfig(format=format, datefmt='%H:%M:%S:%m', level=configuration.LOGGING_LEVEL)
        # simulator options        
        self.leClkPeriods.setText(str(configuration.RUN_FOR_CLOCK_PERIODS))
        self.leClkPeriodMs.setText(str(float(self.CLOCK_PERIOD_SEC[0] * 1000.0)))
        self.leGuiRefreshHz.setText(str(configuration.GUI_UPDATE_PERIOD_IN_HZ))
        self.pbKeepPbPressed.setChecked(configuration.KEEP_PB_PRESSED)

    def thread_buttonSound(self):
        playsound(configuration.PATH_PREFIX + 'sounds/buttonClick.mp3')

    def on_button_clicked(self, idx):
        if configuration.KEEP_PB_PRESSED == True:
            if configuration.SOUND_EFFECTS:
                buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
                buttonSoundThread.start()
            if self.buttons.evt_set_button_on[idx].is_set() == True:
                self.buttons.evt_set_button_on[idx].clear()
                self.buttons.evt_set_button_off[idx].set()
                self.button_wdg[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_up.png'))
            else:
                self.buttons.evt_set_button_off[idx].clear()
                self.buttons.evt_set_button_on[idx].set()
                self.button_wdg[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_down.png'))

    def on_button_pressed(self, idx):
        if configuration.KEEP_PB_PRESSED == False:
            if configuration.SOUND_EFFECTS:
                buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
                buttonSoundThread.start()
            self.buttons.evt_set_button_off[idx].clear()
            self.buttons.evt_set_button_on[idx].set()
            self.button_wdg[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_down.png'))

    def on_button_released(self, idx):
        if configuration.KEEP_PB_PRESSED == False:
            if configuration.SOUND_EFFECTS:
                buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
                buttonSoundThread.start()
            self.buttons.evt_set_button_on[idx].clear()
            self.buttons.evt_set_button_off[idx].set()
            self.button_wdg[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/btn_up.png'))

    def on_switch_clicked(self, idx):
        if configuration.SOUND_EFFECTS:
            buttonSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            buttonSoundThread.start()
        if self.switches.evt_set_switch_on[idx].is_set() == True:
            self.switches.evt_set_switch_on[idx].clear()
            self.switches.evt_set_switch_off[idx].set()
            self.switch_wdg[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/sw_left.png'))
        else:
            self.switches.evt_set_switch_off[idx].clear()
            self.switches.evt_set_switch_on[idx].set()
            self.switch_wdg[idx].setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/sw_right.png'))

    def thread_powerSound(self):
        playsound(configuration.PATH_PREFIX + 'sounds/power_on_off.mp3')

    @pyqtSlot()
    def closeEvent(self,event_arg):
        if configuration.TEST or self.scheduler.test.log_buff != "" or self.scheduler.test.info_buff != "":
            logging.info("printing log_buff:")
            logging.info(self.scheduler.test.log_buff)
            logging.info("printing info_buff:")
            logging.info(self.scheduler.test.info_buff)
        event.evt_close_app.set()
        logging.info("mainWindow closed!")
        # TODO: check this, not closing nicely..
        #       need probably to first unbound FIFOs, exit threads in specific order, etc.?
        self.close()
        # self.parent.close()
        # exit(0)
        # self._thread.terminate() # quit()

    @pyqtSlot(bool)
    def on_pbOnOff_toggled(self, checked):
        if checked == True:
            # create log file
            if configuration.LOG_ON_POWER_ON_OFF == False:
                if configuration.LOG_TO_CSV == True:
                    self.csv_file = open("log.csv", 'w')
                    self.init_csv_log()
            # power on
            event.evt_set_power_off.clear()
            event.evt_set_power_on.set()
            self.pbOnOff.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/off.png'))
            self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_on.png'))
            # set RESET to high for T/2 in order to initialize VHDL signals
            event.evt_set_reset_low.clear()
            event.evt_set_reset_high.set()
            time.sleep(configuration.RESET_FOR_SECONDS)
            event.evt_set_reset_high.clear()
            event.evt_set_reset_low.set()
            # time.sleep(self.CLOCK_PERIOD_SEC[0]/2) # need this?
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
            event.evt_set_power_on.clear()
            event.evt_set_power_off.set()
            self.pbOnOff.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/on.png'))
            self.pbActive.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/led_green_off.png'))
            # close log file
            if configuration.LOG_ON_POWER_ON_OFF == False:
                if configuration.LOG_TO_CSV == True:
                    self.csv_file.close()
        # on
        if configuration.SOUND_EFFECTS:
            powerSoundThread = threading.Thread(name="powerSound", target=self.thread_powerSound)
            powerSoundThread.start()

    @pyqtSlot(bool)
    def on_pbRunPause_toggled(self, checked):
        if event.evt_pause.is_set() == False:  # if checked == True:
            event.evt_resume.clear()
            event.evt_pause.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/run.png'))
        else:
            # check if we need to remove step
            if event.evt_step_on.is_set() == True:
                event.evt_step_on.clear()
            # resume
            event.evt_pause.clear()
            event.evt_resume.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/pause.png'))
        if configuration.SOUND_EFFECTS:
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            powerSoundThread.start()

    @pyqtSlot(bool)
    def on_pbStep_toggled(self, checked):
        if event.evt_step_on.is_set() == False:
            event.evt_step_on.set()
        event.evt_do_step.set()
        if event.evt_pause.is_set() == True:
            # resume
            event.evt_pause.clear()
            event.evt_resume.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/pause.png'))
        logging.info("STEP")
        if configuration.SOUND_EFFECTS:
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            powerSoundThread.start()

    def thread_runForTime(self):
        logging.info("Run for " + str(configuration.RUN_FOR_CLOCK_PERIODS) + " clock cycles.")
        # wait for specified time (dummy event evt_wake_up never comes)
        self.remaining_time_to_run = configuration.RUN_FOR_CLOCK_PERIODS
        while ((self.remaining_time_to_run > 0) and (event.evt_pause.is_set() == False) and (event.evt_step_on.is_set() == False)):
            event.evt_wake_up.wait(self.CLOCK_PERIOD_SEC[0])
            self.remaining_time_to_run = self.remaining_time_to_run - 1
            # update GUI
            event.evt_gui_remain_run_time_update.set()
        if self.remaining_time_to_run > 0:
            logging.info("Run for time expired, simulation was paused or stepped_on")
        else:
            # time expired, now pause
            event.evt_pause.set()
            event.evt_resume.clear()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/run.png'))
            logging.info("Run for time expired, now pause")
        # re-enable button
        self.pbRunForTime.setEnabled(True)

    @pyqtSlot(bool)
    def on_pbRunForTime_toggled(self, checked):
        # disable button during timed run
        self.pbRunForTime.setEnabled(False)
        # resume if necessary
        if event.evt_step_on.is_set():
            event.evt_step_on.clear()
        if (event.evt_pause.is_set() == True):
            # resume
            event.evt_pause.clear()
            event.evt_resume.set()
            self.pbRunPause.setIcon(QtGui.QIcon(configuration.PATH_PREFIX + 'icons/pause.png'))
        # run for time in a separate thread in order not to block
        runForTimeThread = threading.Thread(name="runForTime", target=self.thread_runForTime)
        runForTimeThread.start()
        if configuration.SOUND_EFFECTS:
            powerSoundThread = threading.Thread(name="buttonSound", target=self.thread_buttonSound)
            powerSoundThread.start()

    @pyqtSlot(bool)
    def on_pbReset_toggled(self, checked):
        if event.evt_set_reset_high.is_set() == True:
            event.evt_set_reset_high.clear()
            event.evt_set_reset_low.set()
            self.lblReset.setText("RESET: low")
        else:
            event.evt_set_reset_low.clear()
            event.evt_set_reset_high.set()
            self.lblReset.setText("RESET: high")
        if configuration.SOUND_EFFECTS:
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
            tempValue = float(self.leClkPeriodMs.text())
            if tempValue <= 0.0:
                # NOTE: set text to current value
                self.leClkPeriodMs.setText(str(float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])))
                logging.error("clock period shall be greater than zero")
                tkinter.messagebox.showerror(title="ERROR", message="clock period shall be greater than zero")
                root.update()
            elif tempValue < configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS:
                # NOTE: set text to current value
                self.leClkPeriodMs.setText(str(float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])))
                logging.warning("small clock periods may produce an inaccurate simulation!")
                tkinter.messagebox.showerror(title="ERROR",
                                             message="small clock periods may produce an inaccurate simulation!")
                root.update()
            else:
                configuration.CLOCK_PERIOD_EXTERNAL = str(tempValue * 1000000.0) + " ns"
                # update GUI definitions (e.g. values to change polling rate of threads)
                self.clock.updateGuiDefs() # NOTE: self.CLOCK_PERIOD_SEC is set within this call
                self.updateGuiDefs()
                self.buttons.updateGuiDefs()
                self.digital_inputs.updateGuiDefs()
                self.digital_outputs.updateGuiDefs()
                self.leds.updateGuiDefs()
                self.reset.updateGuiDefs()
                self.switches.updateGuiDefs()
                self.scheduler.updateGuiDefs()
        except:
            # NOTE: set text to current value
            self.leClkPeriodMs.setText(str(float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])))
            logging.error("clock periods shall be an integer value")
            tkinter.messagebox.showerror(title="ERROR", message="clock periods shall be an integer value")
            root.update()

    @pyqtSlot()
    def on_leResetSecs_editingFinished(self):
        try:
            tempValue = float(self.leResetSecs.text())
            if tempValue <= 0.0:
                # NOTE: set text to current value
                self.leResetSecs.setText(str('%.24f' % configuration.RESET_FOR_SECONDS).rstrip('0').rstrip('.'))
                logging.error("reset time shall be greater than zero")
                tkinter.messagebox.showerror(title="ERROR", message="reset time shall be greater than zero")
                root.update()
            else:
                configuration.RESET_FOR_SECONDS = str(tempValue)
                # update GUI definitions (e.g. values to change polling rate of threads)
                self.clock.updateGuiDefs()  # NOTE: self.CLOCK_PERIOD_SEC is set within this call
                self.updateGuiDefs()
                self.buttons.updateGuiDefs()
                self.digital_inputs.updateGuiDefs()
                self.digital_outputs.updateGuiDefs()
                self.leds.updateGuiDefs()
                self.reset.updateGuiDefs()
                self.switches.updateGuiDefs()
                self.scheduler.updateGuiDefs()
        except:
            # NOTE: set text to current value
            self.leResetSecs.setText(str('%.24f' % configuration.RESET_FOR_SECONDS).rstrip('0').rstrip('.'))
            logging.error("reset time shall be a float value")
            tkinter.messagebox.showerror(title="ERROR", message="reset time shall be a float value")
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
    def on_cbTest_clicked(self):
        configuration.TEST = not configuration.TEST
        self.cbTest.setChecked(configuration.TEST)

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
        '''
        # TODO:  this call just blocks forever. Investigate, and if possible call plt.close in Slot() instead.
        #             a "dead/blocked" thread remains in memory every time we switch off here.
        plt.close()
        # TODO: why can't we just do this instead?
        # plt.gcf().set_visible(False)
        # plt.draw() # needed to make previous call effective?
        '''

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
            # NOTE: if the severity level is INFO, the logger will handle only INFO, WARNING, ERROR, and CRITICAL messages and will ignore DEBUG messages
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
            self.init_file_path()
            # update GUI definitions
            self.clock.updateGuiDefs()  # NOTE: self.CLOCK_PERIOD_SEC is set within this call
            self.updateGuiDefs()
            self.buttons.updateGuiDefs()
            self.digital_inputs.updateGuiDefs()
            self.digital_outputs.updateGuiDefs()
            self.leds.updateGuiDefs()
            self.reset.updateGuiDefs()
            self.switches.updateGuiDefs()
            self.scheduler.updateGuiDefs()
            # create temporary files
            self.digital_inputs.createTempFiles()
            self.switches.createTempFiles()
            self.leds.createTempFiles()
            self.reset.createTempFiles()
            self.switches.createTempFiles()
            self.buttons.createTempFiles()
            logging.warning(
                "FILE_PATH updated. New value will take effect after saving configuration and restarting application!")
            tkinter.messagebox.showwarning(title="WARNING",
                                           message="FILE_PATH updated. New value will take effect after saving configuration and restarting application!")
            root.update()

    @pyqtSlot()
    def on_leFifoPath_editingFinished(self):
        configuration.FIFO_PATH = self.leFifoPath.text()
        logging.warning("FIFO_PATH updated. New value will take effect after saving configuration and restarting application!")
        tkinter.messagebox.showwarning(title="WARNING",message="FIFO_PATH updated. New value will take effect after saving configuration and restarting application!")
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
            tempValue = float(self.leMinClockPeriodMs.text())
            if tempValue <= 0.0:
                # NOTE: set text to current value
                self.leMinClockPeriodMs.setText(str('%.24f' % configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS).rstrip('0').rstrip('.'))
                logging.error("Min. clock period shall be greater than zero")
                tkinter.messagebox.showerror(title="ERROR", message="Min. clock period shall be greater than zero")
                root.update()
            else:
                configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS = tempValue
        except:
            # NOTE: set text to current value
            self.leMinClockPeriodMs.setText(str('%.24f' % configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS).rstrip('0').rstrip('.'))
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
                self.digital_inputs.updateNrDisOrAsyncDis()
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
            self.digital_inputs.updateNrDisOrAsyncDis()

    @pyqtSlot(int)
    def on_cbNrDos_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_DOS = index
        # TODO: need to update lists as in on_cbNrAsyncDis_currentIndexChanged() by calling something like
        #       digital_inputs.updateNrDisOrAsyncDis() ?

    @pyqtSlot(int)
    def on_cbNrBtns_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_BUTTONS = index
        # TODO: need to update lists as in on_cbNrAsyncDis_currentIndexChanged() by calling something like
        #       digital_inputs.updateNrDisOrAsyncDis() ?

    @pyqtSlot(int)
    def on_cbNrSwitches_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_SWITCHES = index
        # TODO: need to update lists as in on_cbNrAsyncDis_currentIndexChanged() by calling something like
        #       digital_inputs.updateNrDisOrAsyncDis() ?

    @pyqtSlot(int)
    def on_cbNrLeds_currentIndexChanged(self, index):
        if self.appStarted:
            configuration.NR_LEDS = index
        # TODO: need to update lists as in on_cbNrAsyncDis_currentIndexChanged() by calling something like
        #       digital_inputs.updateNrDisOrAsyncDis() ?

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



