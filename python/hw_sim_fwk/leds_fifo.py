import configuration
import oclock
import logging
from threading import Lock
import threading
from common_fifo import create_r_fifo
from sys import platform
if platform == "win32":
    import win32file
import tkinter



# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

FILE_NAME_LED = []
LED_PERIOD_SEC = None
# NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = oclock.Event()



class leds_fifo:
######################
    CLOCK_PERIOD_SEC = None
    __event = None
    # TODO: implement getter/setter for LED_ON[]
    LED_ON = [] # value set "synchronously" with "asynchronous" variable in __FIFO_R_LED_HIGH[]
    __FIFO_R_LED_HIGH = [] # value read from FIFO (named pipe), set by VHDL code
    for i in range(configuration.NR_LEDS):
        LED_ON.append(0)
        __FIFO_R_LED_HIGH.append(0)
    __fifo_r_led = []
    __lock_r_led = [] # lock to access __FIFO_R_LED_HIGH[]
    # fill with None or 0 for now...initialization in threads instead.
    for i in range(configuration.NR_LEDS):
        __fifo_r_led.append(0) # open(FILE_NAME_LED[i], 'r'))
        __lock_r_led.append(Lock())

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG):
        logging.info('init leds_fifo')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.updateGuiDefs()
        self.__updateMemberVariables()
        for i in range(configuration.NR_LEDS):
            thread_name = "fifo_r_led_thread_" + str(i)
            led_thread = threading.Thread(name=thread_name, target=self.__thread_fifo_r_led, args=(thread_name, i))
            led_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_LED
        global LED_PERIOD_SEC
        if configuration.NR_LEDS > configuration.MAX_NR_LED:
            configuration.NR_LEDS = configuration.MAX_NR_LED
            logging.warning("maximum nr. of LEDs limited to " + str(configuration.MAX_NR_LED))
            tkinter.messagebox.showwarning(title="WARNING", message="maximum nr. of LEDs limited to " + str(
                configuration.MAX_NR_LED))
            root.update()
        FILE_NAME_LED_PART = configuration.FIFO_PATH + "led_"  # temporary variable
        FILE_NAME_LED = []
        for i in range(configuration.NR_LEDS):
            FILE_NAME_LED.append(FILE_NAME_LED_PART + str(i))
        # LED period
        # ASSUMPTION: in worst case the LEDs are switched in every edge of the clock (both rising and falling edges)
        #             under consideration of jitter we need to be faster than that when polling possible changes,
        #             thus we define the period to be 1/4th of the clock period.
        LED_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] / 4
        logging.info("LED_PERIOD_SEC = " + str(LED_PERIOD_SEC))

    def __thread_fifo_r_led(self, name, i):
        logging.info("Thread %s: starting", name)
        # open FIFO for reading
        self.__fifo_r_led[i] = create_r_fifo(FILE_NAME_LED[i])
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # read LED_x FIFO
            ################
            if platform == "win32":
                try:
                    line = win32file.ReadFile(self.__fifo_r_led[i], 64*1024)
                    # temp_line_int = int.from_bytes(line[1]); # str(line[1], 'utf-8') # TODO: why nok?
                    temp_line_str = str(line[1], 'utf-8')
                except:
                    logging.error("could not read from pipe of LED_" + str(i))
                    win32file.CloseHandle(self.__fifo_r_led[i])
            else:
                temp_line_str = self.__fifo_r_led[i].read()
            try:
                temp_line_int = int(temp_line_str)
            except ValueError:
                temp_line_int = 0
            # process LED_x info from FIFO
            #############################
            self.__lock_r_led[i].acquire()
            self.__FIFO_R_LED_HIGH[i] = temp_line_int
            self.__lock_r_led[i].release()
        logging.info("Thread %s: finished!", name)

    def do_led(self):
        for i in range(configuration.NR_LEDS):
            if self.LED_ON[i] == 0:
                # first check if __FIFO_R_LED_HIGH[i] is currently being set
                # assumption: if locked, lock will be soon released, no need for max. retry count
                while self.__lock_r_led[i].locked()  == True:
                    logging.warning("lock for LED[" + str(i) + "] is locked!")
                    # assumption: we don't need to introduce a pause here e.g. with sleep or wait
                self.__lock_r_led[i].acquire()
                if self.__FIFO_R_LED_HIGH[i] == 1:
                    logging.debug("LED %s is ON", str(i))
                    self.LED_ON[i] = 1
                self.__lock_r_led[i].release()
            else:
                # first check if __FIFO_R_LED_HIGH[i] is currently being set
                # assumption: if locked, lock will be soon released, no need for max. retry count
                while self.__lock_r_led[i].locked() == True:
                    logging.warning("lock for LED[" + str(i) + "] is locked!")
                    # assumption: we don't need to introduce a pause here e.g. with sleep or wait
                self.__lock_r_led[i].acquire()
                if self.__FIFO_R_LED_HIGH[i] == 0:
                    logging.debug("LED %s is OFF", str(i))
                    self.LED_ON[i] = 0
                self.__lock_r_led[i].release()
        # inform GUI
        self.__event.evt_gui_led_update.set()

    # TODO: need to update threads as well?
    def __updateMemberVariables(self):
        self.LED_ON = []
        for i in range(configuration.NR_LEDS):
            self.LED_ON.append(0)




