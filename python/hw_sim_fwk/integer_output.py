import configuration
import logging
from threading import Lock
import threading
from common_fifo import create_r_fifo
from sys import platform
if platform == "win32":
    import win32file
import tkinter



################################################################################################################
# NOTE: this is up to now the only module which does NOT map one-to-one to some digital signal(s) / interface(s)
#       Nevertheless, this convenience class allows passing data from VHDL to the app very efficiently in cases
#       where needed (e.g. to display internal FPGA information) and the HW simulation is not required.
################################################################################################################

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

FILE_NAME_INT_OUT = None



class integer_output:
######################
    __event = None
    __SIG_NAME = ""
    # TODO: implement getter/setter for INT_OUT
    INT_OUT = 0 # value set "synchronously" with "asynchronous" variable in __FIFO_R_INT_OUT
    __FIFO_R_INT_OUT = 0 # integer value read from FIFO (named pipe), set by VHDL code
    __fifo_r_int_out = 0
    __lock_r_int_out = Lock() # lock to access __FIFO_R_INT_OUT

    def __init__(self, event, __SIG_NAME):
        logging.info('init integer_output')
        self.__event = event
        self.__SIG_NAME = __SIG_NAME
        global FILE_NAME_INT_OUT
        FILE_NAME_INT_OUT = configuration.FIFO_PATH + self.__SIG_NAME
        thread_name = "int_out_thread"
        int_out_thread = threading.Thread(name=thread_name, target=self.__thread_fifo_r_int_out, args=(thread_name,))
        int_out_thread.start()

    def __thread_fifo_r_int_out(self, name):
        logging.info("Thread %s: starting", name)
        # open FIFO for reading
        self.__fifo_r_int_out = create_r_fifo(FILE_NAME_INT_OUT)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # read int out FIFO
            ###################
            if platform == "win32":
                try:
                    line = win32file.ReadFile(self.__fifo_r_int_out, 64*1024)
                    temp_line_str = line[1]
                except:
                    logging.error("could not read from pipe of " + str(FILE_NAME_INT_OUT))
                    win32file.CloseHandle(self.__fifo_r_int_out)
            else:
                temp_line_str = self.__fifo_r_int_out.read()
            try:
                temp_line_int = int(temp_line_str[0]) + 256*int(temp_line_str[1]) + 65535*int(temp_line_str[2]) + 16777216*int(temp_line_str[3])
                # debug code
                logging.debug("data_out = " + str(temp_line_int))
            except ValueError:
                temp_line_int = 0
            # process DO_x info from FIFO
            #############################
            self.__lock_r_int_out.acquire()
            self.__FIFO_R_INT_OUT = temp_line_int
            self.__lock_r_int_out.release()
            # inform GUI
            self.__event.evt_gui_int_out_update.set()
        logging.info("Thread %s: finished!", name)

    def do_int_out(self):
        if self.INT_OUT != self.__FIFO_R_INT_OUT:
            # first check if __FIFO_R_INT_OUT is currently being set
            # assumption: if locked, lock will be soon released, no need for max. retry count
            while self.__lock_r_int_out.locked()  == True:
                logging.warning("lock for int out " + FILE_NAME_INT_OUT + " is locked!")
                # assumption: we don't need to introduce a pause here e.g. with sleep or wait
            self.__lock_r_int_out.acquire()
            self.INT_OUT = self.__FIFO_R_INT_OUT
            self.__lock_r_int_out.release()
            logging.debug("int out for " + FILE_NAME_INT_OUT + " set to ", str(self.INT_OUT))



