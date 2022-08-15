import oclock
import logging
import configuration
import os
from common_fifo import create_w_fifo
from sys import platform
if platform == "win32":
    import win32file
import threading
import tkinter
from threading import Lock



# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

USE_DI_FIFO = False # NOTE: this parameter is not in config.ini
if USE_DI_FIFO:
    FILE_NAME_DI = []
else:
    FILE_NAME_DI_HIGH = []
    FILE_NAME_DI_LOW = []
SYNC_DI = []
ASYNC_DI = []
DI_PERIOD_SEC = None
# NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = oclock.Event()



class digital_inputs:
#####################
    CLOCK_PERIOD_SEC = None
    __event = None
    __di_count = 0
    __toggle_di = True
    # TODO: implement getter/setter for DI_HIGH[]
    DI_HIGH = []
    for i in range(configuration.NR_DIS):
        DI_HIGH.append(0)
    # fifo used
    if USE_DI_FIFO:
        __FIFO_W_DI_HIGH = [] # value written to FIFO (named pipe), set by python code
        for i in range(configuration.NR_DIS):
            __FIFO_W_DI_HIGH.append(0)
        __fifo_w_di = []
        # TODO: need __lock_w_di?
        __lock_w_di = [] # lock to access __FIFO_W_DI_HIGH[]
        # fill with None for now...initialization in threads instead.
        for i in range(configuration.NR_DIS):
            __fifo_w_di.append(0) # open(FILE_NAME_DI[i], 'w'))
            __lock_w_di.append(Lock())

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG):
        logging.info('init digital_inputs')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.updateGuiDefs()
        self.createTempFiles()
        self.__updateMemberVariables()
        for j in range(configuration.NR_ASYNC_DI):
            i = ASYNC_DI[j]
            thread_name = "di_thread_" + str(i)
            di_thread = threading.Thread(name=thread_name, target=self.__thread_di, args=(thread_name, i))
            di_thread.start()
        # sync DI threads only used to create FIFOs
        if USE_DI_FIFO:
            for j in range(configuration.NR_SYNC_DI):
                i = SYNC_DI[j]
                thread_name = "di_thread_sync_" + str(i)
                di_thread_sync = threading.Thread(name=thread_name, target=self.__thread_di_sync, args=(thread_name, i))
                di_thread_sync.start()

    def updateGuiDefs(self):
        if USE_DI_FIFO:
            global FILE_NAME_DI
        else:
            global FILE_NAME_DI_HIGH
            global FILE_NAME_DI_LOW
        global SYNC_DI
        global ASYNC_DI
        # check max nr. of DIs and DOs
        if configuration.NR_DIS > configuration.MAX_NR_DI:
            configuration.NR_DIS = configuration.MAX_NR_DI
            logging.warning("maximum nr. of digital inputs limited to " + str(configuration.MAX_NR_DI))
            tkinter.messagebox.showwarning(title="WARNING", message="maximum nr. of digital inputs limited to " + str(
                configuration.MAX_NR_DI))
            root.update()
        if USE_DI_FIFO:
            FILE_NAME_DI_PART = configuration.FIFO_PATH + "di_"  # temporary variable
            FILE_NAME_DI = []
            for i in range(configuration.NR_DIS):
                FILE_NAME_DI.append(FILE_NAME_DI_PART + str(i))
        else:
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
        # digital input period
        DI_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] * configuration.DI_PER_IN_CLK_PER
        logging.info("DI_PERIOD_SEC = " + str(DI_PERIOD_SEC))

    def createTempFiles(self):
        if USE_DI_FIFO == False:
            for i in range(configuration.NR_DIS):
                if os.path.exists(FILE_NAME_DI_HIGH[i]):
                    os.remove(FILE_NAME_DI_HIGH[i])

    # used only to create FIFOs for synch DIs
    def __thread_di_sync(self, name, i):
        logging.info("Thread %s: starting", name)
        # open FIFO for writing
        self.__fifo_w_di[i] = create_w_fifo(FILE_NAME_DI[i])

    # Simulate asynchronous DIs changing faster than DI period "expected" by receiver.
    # Alternatively, toggle_di may just toggle bits,
    # The period used can be set to random.
    def __thread_di(self, name, i):
        logging.info("Thread %s: starting", name)
        # open FIFO for writing
        if USE_DI_FIFO:
            self.__fifo_w_di[i] = create_w_fifo(FILE_NAME_DI[i])
        toggle_di = False
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # device on and not paused?
            if (self.__event.evt_set_power_on.is_set() == True) and (self.__event.evt_pause.is_set() == False) and (
                    self.__event.evt_step_on.is_set() == False):
                # NOTE: use one of the following codes
                ######################################
                # if random.randint(0, 1):
                if toggle_di == False:
                ######################################
                    self.DI_HIGH[i] = 0
                    # write DI_i = 0
                    if USE_DI_FIFO:
                        if platform == "win32":
                            win32file.WriteFile(self.__fifo_w_di[i], str.encode("0\r\n"))
                        else:
                            self.__fifo_w_di[i].write("0\r\n")
                            self.__fifo_w_di[i].flush()
                    else:
                        if os.path.isfile(FILE_NAME_DI_HIGH[i]):
                            renamed = False
                            while renamed == False:
                                try:
                                    os.replace(FILE_NAME_DI_HIGH[i] ,FILE_NAME_DI_LOW[i])
                                    renamed = True
                                except:
                                    logging.warning("File cannot be renamed, we try again. File =  " +FILE_NAME_DI_HIGH[i])
                        else:
                            f = open(FILE_NAME_DI_LOW[i], "w+")
                            f.close()
                else:
                    self.DI_HIGH[i] = 1
                    # write DI_i = 1
                    if USE_DI_FIFO:
                        if platform == "win32":
                            win32file.WriteFile(self.__fifo_w_di[i], str.encode("1\r\n"))
                        else:
                            self.__fifo_w_di[i].write("1\r\n")
                            self.__fifo_w_di[i].flush()
                    else:
                        if os.path.isfile(FILE_NAME_DI_LOW[i]):
                            renamed = False
                            while renamed == False:
                                try:
                                    os.replace(FILE_NAME_DI_LOW[i] ,FILE_NAME_DI_HIGH[i])
                                    renamed = True
                                except:
                                    logging.warning("File cannot be renamed, we try again. File =  " +FILE_NAME_DI_LOW[i])
                        else:
                            f = open(FILE_NAME_DI_HIGH[i], "w+")
                            f.close()
                # toggle signal
                toggle_di = not toggle_di
                # inform GUI
                self.__event.evt_gui_di_update.set()
            # NOTE: use one of the following codes
            ######################################
            # NOTE: although in theory we shall have a "repeatable and synchronized" behavior
            #       between sync and async DIs, in reality we don't due to inaccuracy of Event.wait().
            #       Therefore, the call to wait(DI_PERIOD_SEC) will not be in sync with the scheduler where
            #       sync DIs are updated.
            #       The complete DI values (sync + async) will not be regular/periodic in the wave output.
            # wait DI period
            evt_wake_up.wait(DI_PERIOD_SEC)
            # wait random time within defined limits
            # evt_wake_up.wait(random.uniform(self.CLOCK_PERIOD_SEC[0], DI_PERIOD_SEC))
            ######################################

    # TODO: investigate if it is possible to set DIs faster.
    #       Why does it take 1ms to rename/remove a file in Win11 ?
    # NOTE: 1ms is the default time it takes to set a DI by renaming the shared file or creating it for w+
    #       But when e.g. switches are used then it may sometimes take 2ms.
    #       When working intensively on VIVADO's wave-output, tests showed even higher values: 3ms, 4ms, 5ms,..
    def do_di_count(self):
        for j in range(configuration.NR_SYNC_DI):
            i = SYNC_DI[j]
            if self.__di_count & 2 ** j:
                # need to set bit?
                if self.DI_HIGH[i] != 1:
                    self.DI_HIGH[i] = 1
                    # write DI_i = 1
                    if USE_DI_FIFO:
                        if platform == "win32":
                            win32file.WriteFile(self.__fifo_w_di[i], str.encode("1\r\n"))
                        else:
                            self.__fifo_w_di[i].write("1\r\n")
                            self.__fifo_w_di[i].flush()
                    else:
                        if os.path.isfile(FILE_NAME_DI_LOW[i]):
                            renamed = False
                            while renamed == False:
                                try:
                                    os.replace(FILE_NAME_DI_LOW[i], FILE_NAME_DI_HIGH[i])
                                    renamed = True
                                except:
                                    logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_DI_LOW[i])
                        else:
                            f = open(FILE_NAME_DI_HIGH[i], "w+")
                            f.close()
            else:
                # need to clear bit?
                if self.DI_HIGH[i] != 0:
                    self.DI_HIGH[i] = 0
                    # write DI_i = 0
                    if USE_DI_FIFO:
                        if platform == "win32":
                            win32file.WriteFile(self.__fifo_w_di[i], str.encode("0\r\n"))
                        else:
                            self.__fifo_w_di[i].write("0\r\n")
                            self.__fifo_w_di[i].flush()
                    else:
                        if os.path.isfile(FILE_NAME_DI_HIGH[i]):
                            renamed = False
                            while renamed == False:
                                try:
                                    os.replace(FILE_NAME_DI_HIGH[i],FILE_NAME_DI_LOW[i])
                                    renamed = True
                                except:
                                    logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_DI_HIGH[i])
                        else:
                            f = open(FILE_NAME_DI_LOW[i], "w+")
                            f.close()
        self.__di_count = (self.__di_count + 1) % configuration.MAX_DI_COUNT
        # update GUI
        self.__event.evt_gui_di_update.set()

    def do_di_toggle(self):
        if self.__toggle_di == False:
            for j in range(configuration.NR_SYNC_DI):
                i = SYNC_DI[j]
                self.DI_HIGH[i] = 0
                # write DI_i = 0
                if USE_DI_FIFO:
                    if platform == "win32":
                        win32file.WriteFile(self.__fifo_w_di[i], str.encode("0\r\n"))
                    else:
                        self.__fifo_w_di[i].write("0\r\n")
                        self.__fifo_w_di[i].flush()
                else:
                    if os.path.isfile(FILE_NAME_DI_HIGH[i]):
                        renamed = False
                        while renamed == False:
                            try:
                                os.replace(FILE_NAME_DI_HIGH[i], FILE_NAME_DI_LOW[i])
                                renamed = True
                            except:
                                logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_DI_HIGH[i])
                    else:
                        f = open(FILE_NAME_DI_LOW[i], "w+")
                        f.close()
        else:
            for j in range(configuration.NR_SYNC_DI):
                i = SYNC_DI[j]
                self.DI_HIGH[i] = 1
                # write DI_i = 1
                if USE_DI_FIFO:
                    if platform == "win32":
                        win32file.WriteFile(self.__fifo_w_di[i], str.encode("1\r\n"))
                    else:
                        self.__fifo_w_di[i].write("1\r\n")
                        self.__fifo_w_di[i].flush()
                else:
                    if os.path.isfile(FILE_NAME_DI_LOW[i]):
                        renamed = False
                        while renamed == False:
                            try:
                                os.replace(FILE_NAME_DI_LOW[i], FILE_NAME_DI_HIGH[i])
                                renamed = True
                            except:
                                logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_DI_LOW[i])
                    else:
                        f = open(FILE_NAME_DI_HIGH[i], "w+")
                        f.close()
        # toggle signal
        self.__toggle_di = not self.__toggle_di
        # update GUI
        self.__event.evt_gui_di_update.set()

    # TODO: need to update threads as well?
    #       or just remove this function?
    def __updateMemberVariables(self):
        self.DI_HIGH = []
        for i in range(configuration.NR_DIS):
            self.DI_HIGH.append(0)

    def updateNrDisOrAsyncDis(self):
        # update lists
        SYNC_DI.clear()
        ASYNC_DI.clear()
        for i in range(configuration.NR_SYNC_DI):
            SYNC_DI.append(i)
        for i in range(configuration.NR_ASYNC_DI):
            ASYNC_DI.append(configuration.NR_ASYNC_DI + i)





