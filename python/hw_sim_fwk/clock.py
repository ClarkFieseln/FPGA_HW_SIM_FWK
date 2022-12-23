import time

import configuration
import logging
import threading
import traceback
import tkinter
from inspect import currentframe



# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()
# current frame
cf = currentframe()



class clock:
############
    CLOCK_PERIOD_SEC = None
    __event = None

    def __init__(self, event, CLOCK_PERIOD_SEC):
        logging.info('init clock')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC
        self.updateGuiDefs()
        thread_clock = threading.Thread(name="clock_thread", target=self.thread_clock, args=("clock_thread",))
        thread_clock.start()

    def updateGuiDefs(self):
        # check ranges
        if configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS <= 0.0:
            # NOTE: 100 ms hardcoded rescue value.
            configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS = 100.0
            logging.error("min. clock period shall be greater than zero. Now set to value = 100 ms")
            tkinter.messagebox.showerror(title="ERROR",
                                         message="min. clock period shall be greater than zero. Now set to value = 100 ms")
            root.update()
        if float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) <= 0.0:
            configuration.CLOCK_PERIOD_EXTERNAL = str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms"
            logging.error("clock period shall be greater than zero. Now set to minimum value = " + str(
                configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms")
            tkinter.messagebox.showerror(title="ERROR",
                                         message="clock period shall be greater than zero. Now set to minimum value = " +
                                                 str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS) + " ms")
            root.update()
        # NOTE: self.CLOCK_PERIOD_SEC[0] corresponds exactly to one period in VHDL code.
        if " fs" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000000000.0
        elif " ps" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000000.0
        elif " ns" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000000.0
        elif " us" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000000.0
        elif " ms" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) / 1000.0
        elif " sec" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0])
        elif " min" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) * 60.0
        elif " min" in configuration.CLOCK_PERIOD_EXTERNAL:
            self.CLOCK_PERIOD_SEC[0] = float(configuration.CLOCK_PERIOD_EXTERNAL.partition(" ")[0]) * 3600.0
        else:
            logging.error("Error: unknown time units in CLOCK_PERIOD_EXTERNAL!")
            traceback.print_exc()
            exit(cf.f_lineno)
        logging.info("CLOCK_PERIOD_SEC = " + str(self.CLOCK_PERIOD_SEC[0]))

    def thread_clock(self, name):
        logging.info("Thread %s: starting", name)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # raise event for new clock transition
            self.__event.evt_clock.set()
            # wait half clock period
            # BUG - event.wait() has a delay of 10ms which limits the clock frequency to mas 100 Hz
            # self.__event.evt_wake_up.wait(self.CLOCK_PERIOD_SEC[0]/2)
            time.sleep(self.CLOCK_PERIOD_SEC[0]/2)
        logging.info("Thread %s: finished!", name)


