import logging
import configuration
import os
import threading
import tkinter
from multiple_events import big_event



# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

FILE_NAME_SW_HIGH = []
FILE_NAME_SW_LOW = []
SWITCH_PERIOD_SEC = None



class switches:
###############
    CLOCK_PERIOD_SEC = None
    __event = None
    toggle_switch = True # TODO: create getter/setter
    # events
    # TODO: getter/setter?
    evt_set_switch_on = []
    evt_set_switch_off = []
    # to avoid polling:
    evt_set_switch_on_or_off = []

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG):
        logging.info('init switches')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.updateGuiDefs()
        self.createTempFiles()
        for i in range(configuration.NR_SWITCHES):
            # switch events
            be = threading.Event()
            e1 = big_event(be)
            e2 = big_event(be)
            ###################################################################
            # TODO: investigate why these events don't work with oclock.Event()
            self.evt_set_switch_on.append(e1)
            self.evt_set_switch_off.append(e2)
            ###################################################################
            self.evt_set_switch_on_or_off.append(be)
        if configuration.SWITCH_TOGGLE_AUTO == False:
            for i in range(configuration.NR_SWITCHES):
                thread_name = "switch_thread_" + str(i)
                switch_thread = threading.Thread(name=thread_name, target=self.thread_switch,
                                                 args=(thread_name, i,))
                switch_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_SW_HIGH
        global FILE_NAME_SW_LOW
        global SWITCH_PERIOD_SEC
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
        # switch period
        SWITCH_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] * configuration.SW_PER_IN_CLK_PER
        logging.info("SWITCH_PERIOD_SEC = " + str(SWITCH_PERIOD_SEC))

    def createTempFiles(self):
        for i in range(configuration.NR_SWITCHES):
            f = open(FILE_NAME_SW_LOW[i], "w+")
            f.close()
            if os.path.exists(FILE_NAME_SW_HIGH[i]):
                os.remove(FILE_NAME_SW_HIGH[i])
        for i in range(configuration.NR_SWITCHES):
            f = open(FILE_NAME_SW_LOW[i], "w+")
            f.close()

    # TODO: if we set configuration.SWITCH_TOGGLE_AUTO to True
    #       we may have a poor performance.
    #       Improve similar to buttons.do_button() if required!
    def do_switch(self):
        if self.toggle_switch == False:
            for i in range(configuration.NR_SWITCHES):
                if os.path.isfile(FILE_NAME_SW_HIGH[i]):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_SW_HIGH[i],FILE_NAME_SW_LOW[i])
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_SW_HIGH[i])
                else:
                    f = open(FILE_NAME_SW_LOW[i], "w+")
                    f.close()
        else:
            for i in range(configuration.NR_SWITCHES):
                if os.path.isfile(FILE_NAME_SW_LOW[i]):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_SW_LOW[i],FILE_NAME_SW_HIGH[i])
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_SW_HIGH[i])
                else:
                    f = open(FILE_NAME_SW_HIGH[i], "w+")
                    f.close()
        # toggle signal
        self.toggle_switch = not self.toggle_switch

    def thread_switch(self, name, i):
        logging.info("Thread %s(%s): starting", name, str(i))
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            if configuration.SWITCH_TOGGLE_AUTO == False:
                if self.evt_set_switch_on[i].is_set() == False:
                    if os.path.isfile(FILE_NAME_SW_HIGH[i]):
                        renamed = False
                        while renamed == False:
                            try:
                                os.replace(FILE_NAME_SW_HIGH[i],FILE_NAME_SW_LOW[i])
                                renamed = True
                            except:
                                logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_SW_HIGH[i])
                    else:
                        f = open(FILE_NAME_SW_LOW[i], "w+")
                        f.close()
                    logging.info("Switch (" + str(i) + ") = OFF")
                    self.evt_set_switch_on[i].wait()
                else:
                    if os.path.isfile(FILE_NAME_SW_LOW[i]):
                        renamed = False
                        while renamed == False:
                            try:
                                os.replace(FILE_NAME_SW_LOW[i],FILE_NAME_SW_HIGH[i])
                                renamed = True
                            except:
                                logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_SW_LOW[i])
                    else:
                        f = open(FILE_NAME_SW_HIGH[i], "w+")
                        f.close()
                    logging.info("Switch (" + str(i) + ") = ON")
                    self.evt_set_switch_off[i].wait()
            else:
                # NOTE: if required, use evt_set_switch_on_or_off[] to avoid polling
                #       # BUG 10ms delay
                #       # self.__event.evt_wake_up.wait(self.CLOCK_PERIOD_SEC[0] / 2)
                #       time.delay(self.CLOCK_PERIOD_SEC[0] / 2)
                self.evt_set_switch_on_or_off[i].wait()
        logging.info("Thread %s(%s): finished!", name, str(i))


