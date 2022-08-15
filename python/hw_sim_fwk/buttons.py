import oclock
import logging
import configuration
import os
import threading
import tkinter
from multiple_events import big_event

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

FILE_NAME_BTN_HIGH = []
FILE_NAME_BTN_LOW = []
BUTTON_PERIOD_SEC = None
# NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = oclock.Event()



class buttons:
##############
    CLOCK_PERIOD_SEC = None
    __event = None
    toggle_button = True # TODO: create getter/setter
    # events
    # TODO: getter/setter?
    evt_set_button_on = []
    evt_set_button_off = []
    # to avoid polling:
    evt_set_button_on_or_off = []

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG):
        logging.info('init buttons')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.updateGuiDefs()
        self.createTempFiles() # TODO: __createTempFiles() as private method ???
        # create events
        for i in range(configuration.NR_SWITCHES):
            # switch events
            be = threading.Event()
            e1 = big_event(be)
            e2 = big_event(be)
            ############
            # TODO: investigate why these events don't work with oclock.Event()
            self.evt_set_button_on.append(e1)
            self.evt_set_button_off.append(e2)
            ############
            self.evt_set_button_on_or_off.append(be)
        # auto toggle
        if configuration.BUTTON_TOGGLE_AUTO == False:
            for i in range(configuration.NR_BUTTONS):
                thread_name = "button_thread_" + str(i)
                button_thread = threading.Thread(name=thread_name, target=self.thread_button,
                                                 args=(thread_name, i,))
                button_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_BTN_HIGH
        global FILE_NAME_BTN_LOW
        global BUTTON_PERIOD_SEC
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
        # button period
        BUTTON_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] * configuration.BUTTON_PER_IN_CLK_PER
        logging.info("BUTTON_PERIOD_SEC = " + str(BUTTON_PERIOD_SEC))

    def createTempFiles(self):
        for i in range(configuration.NR_BUTTONS):
            if os.path.exists(FILE_NAME_BTN_HIGH[i]):
                os.remove(FILE_NAME_BTN_HIGH[i])
        for i in range(configuration.NR_BUTTONS):
            f = open(FILE_NAME_BTN_LOW[i], "w+")
            f.close()

    def do_button(self):
        if self.toggle_button == False:
            for i in range(configuration.NR_BUTTONS):
                if os.path.isfile(FILE_NAME_BTN_HIGH[i]):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_BTN_HIGH[i],FILE_NAME_BTN_LOW[i])
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_BTN_HIGH[i])
                else:
                    f = open(FILE_NAME_BTN_LOW[i], "w+")
                    f.close()
            logging.debug("Buttons set to LOW (auto)")
        else:
            for i in range(configuration.NR_BUTTONS):
                if os.path.isfile(FILE_NAME_BTN_LOW[i]):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_BTN_LOW[i],FILE_NAME_BTN_HIGH[i])
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_BTN_LOW[i])
                else:
                    f = open(FILE_NAME_BTN_HIGH[i], "w+")
                    f.close()
            logging.debug("Buttons set to HIGH (auto)")
        self.toggle_button = not self.toggle_button

    def thread_button(self, name, i):
        logging.info("Thread %s(%s): starting", name, str(i))
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            if self.evt_set_button_on[i].is_set() == False:
                if os.path.isfile(FILE_NAME_BTN_HIGH[i]):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_BTN_HIGH[i],FILE_NAME_BTN_LOW[i])
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_BTN_HIGH[i])
                else:
                    f = open(FILE_NAME_BTN_LOW[i], "w+")
                    f.close()
                logging.info("Button (" + str(i) + ") = LOW")
                self.evt_set_button_on[i].wait()
            else:
                if os.path.isfile(FILE_NAME_BTN_LOW[i]):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_BTN_LOW[i],FILE_NAME_BTN_HIGH[i])
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_BTN_LOW[i])
                else:
                    f = open(FILE_NAME_BTN_HIGH[i], "w+")
                    f.close()
                logging.info("Button (" + str(i) + ") = HIGH")
                self.evt_set_button_off[i].wait()



