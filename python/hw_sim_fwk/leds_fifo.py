import configuration
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



class leds_fifo:
################
    __event = None
    # TODO: implement getter/setter for LED_ON[]
    LED_ON = [] # value set "synchronously" with "asynchronous" variable in __FIFO_R_LED_HIGH[]
    __FIFO_R_LED_HIGH = [] # value read from FIFO (named pipe), set by VHDL code
    __fifo_r_led = []
    __lock_r_led = [] # lock to access __FIFO_R_LED_HIGH[]

    def __init__(self, event):
        logging.info('init leds_fifo')
        self.__event = event
        for i in range(configuration.NR_LEDS):
            self.LED_ON.append(0)
            self.__FIFO_R_LED_HIGH.append(0)
        # fill with None or 0 for now...initialization in threads instead.
        for i in range(configuration.NR_LEDS):
            self.__fifo_r_led.append(0)
            self.__lock_r_led.append(Lock())
        self.updateGuiDefs()
        self.__updateMemberVariables()
        for i in range(configuration.NR_LEDS):
            thread_name = "fifo_r_led_thread_" + str(i)
            led_thread = threading.Thread(name=thread_name, target=self.__thread_fifo_r_led, args=(thread_name, i))
            led_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_LED
        if configuration.NR_LEDS > configuration.MAX_NR_LED:
            configuration.NR_LEDS = configuration.MAX_NR_LED
            logging.warning("maximum nr. of LEDs limited to " + str(configuration.MAX_NR_LED))
            tkinter.messagebox.showwarning(title="WARNING", message="maximum nr. of LEDs limited to " + str(
                configuration.MAX_NR_LED))
            root.update()
        FILE_NAME_LED_PART = configuration.FIFO_PATH + "led_"
        FILE_NAME_LED = []
        for i in range(configuration.NR_LEDS):
            FILE_NAME_LED.append(FILE_NAME_LED_PART + str(i))

    def createTempFiles(self):
        return

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




