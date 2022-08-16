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

FILE_NAME_DO = []
DO_PERIOD_SEC = None
# NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = oclock.Event()



class digital_outputs:
######################
    CLOCK_PERIOD_SEC = None
    __event = None
    # TODO: implement getter/setter for DO_HIGH[]
    DO_HIGH = [] # value set "synchronously" with "asynchronous" variable in __FIFO_R_DO_HIGH[]
    __FIFO_R_DO_HIGH = [] # value read from FIFO (named pipe), set by VHDL code
    for i in range(configuration.NR_DOS):
        DO_HIGH.append(0)
        __FIFO_R_DO_HIGH.append(0)
    __fifo_r_do = []
    __lock_r_do = [] # lock to access __FIFO_R_DO_HIGH[]
    # fill with None or 0 for now...initialization in threads instead.
    for i in range(configuration.NR_DOS):
        __fifo_r_do.append(0) # open(FILE_NAME_DO[i], 'r'))
        __lock_r_do.append(Lock())

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG):
        logging.info('init digital_outputs')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.updateGuiDefs()
        self.__updateMemberVariables()
        for i in range(configuration.NR_DOS):
            thread_name = "fifo_r_do_thread_" + str(i)
            do_thread = threading.Thread(name=thread_name, target=self.__thread_fifo_r_do, args=(thread_name, i))
            do_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_DO
        global DO_PERIOD_SEC
        if configuration.NR_DOS > configuration.MAX_NR_DO:
            configuration.NR_DOS = configuration.MAX_NR_DO
            logging.warning("maximum nr. of digital outputs limited to " + str(configuration.MAX_NR_DO))
            tkinter.messagebox.showwarning(title="WARNING", message="maximum nr. of digital outputs limited to " + str(
                configuration.MAX_NR_DO))
            root.update()
        FILE_NAME_DO_PART = configuration.FIFO_PATH + "do_"  # temporary variable
        FILE_NAME_DO = []
        for i in range(configuration.NR_DOS):
            FILE_NAME_DO.append(FILE_NAME_DO_PART + str(i))
        # digital output period
        # ASSUMPTION: in worst case the DOs are switched in every edge of the clock (both rising and falling edges)
        #             under consideration of jitter we need to be faster than that when polling possible changes,
        #             thus we define the period to be 1/4th of the clock period.
        DO_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] / 4
        logging.info("DO_PERIOD_SEC = " + str(DO_PERIOD_SEC))

    def __thread_fifo_r_do(self, name, i):
        logging.info("Thread %s: starting", name)
        # open FIFO for reading
        self.__fifo_r_do[i] = create_r_fifo(FILE_NAME_DO[i])
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # read DO_x FIFO
            ################
            if platform == "win32":
                try:
                    line = win32file.ReadFile(self.__fifo_r_do[i], 64*1024)
                    # temp_line_int = int.from_bytes(line[1]); # str(line[1], 'utf-8') # TODO: why nok?
                    temp_line_str = str(line[1], 'utf-8')
                except:
                    logging.error("could not read from pipe of DO_" + str(i))
                    win32file.CloseHandle(self.__fifo_r_do[i])
            else:
                temp_line_str = self.__fifo_r_do[i].read()
            try:
                temp_line_int = int(temp_line_str)
            except ValueError:
                temp_line_int = 0
            # process DO_x info from FIFO
            #############################
            self.__lock_r_do[i].acquire()
            self.__FIFO_R_DO_HIGH[i] = temp_line_int
            self.__lock_r_do[i].release()
        logging.info("Thread %s: finished!", name)

    def do_do(self):
        for i in range(configuration.NR_DOS):
            if self.DO_HIGH[i] == 0:
                # first check if __FIFO_R_DO_HIGH[i] is currently being set
                # assumption: if locked, lock will be soon released, no need for max. retry count
                while self.__lock_r_do[i].locked()  == True:
                    logging.warning("lock for DO[" + str(i) + "] is locked!")
                    # assumption: we don't need to introduce a pause here e.g. with sleep or wait
                self.__lock_r_do[i].acquire()
                if self.__FIFO_R_DO_HIGH[i] == 1:
                    logging.debug("DO %s is HIGH", str(i))
                    self.DO_HIGH[i] = 1
                self.__lock_r_do[i].release()
            else:
                # first check if __FIFO_R_DO_HIGH[i] is currently being set
                # assumption: if locked, lock will be soon released, no need for max. retry count
                while self.__lock_r_do[i].locked() == True:
                    logging.warning("lock for DO[" + str(i) + "] is locked!")
                    # assumption: we don't need to introduce a pause here e.g. with sleep or wait
                self.__lock_r_do[i].acquire()
                if self.__FIFO_R_DO_HIGH[i] == 0:
                    logging.debug("DO %s is LOW", str(i))
                    self.DO_HIGH[i] = 0
                self.__lock_r_do[i].release()
        # inform GUI
        self.__event.evt_gui_do_update.set()

    # TODO: need to update threads as well?
    def __updateMemberVariables(self):
        self.DO_HIGH = []
        for i in range(configuration.NR_DOS):
            self.DO_HIGH.append(0)




