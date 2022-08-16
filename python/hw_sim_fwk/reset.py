import oclock
import logging
import configuration
import os
import threading
import tkinter



# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

# module definitions and variables:
FILE_NAME_RESET_HIGH = None
FILE_NAME_RESET_LOW = None
# NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = oclock.Event()



class reset:
############
    __event = None

    def __init__(self, event):
        logging.info('init reset')
        self.__event = event
        self.updateGuiDefs()
        self.createTempFiles()
        reset_thread = threading.Thread(name="reset_thread", target=self.thread_reset, args=("reset_thread",))
        reset_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_RESET_HIGH
        global FILE_NAME_RESET_LOW
        FILE_NAME_RESET_HIGH = configuration.FILE_PATH + "reset_high"
        FILE_NAME_RESET_LOW = configuration.FILE_PATH + "reset_low"
        if configuration.RESET_FOR_SECONDS <= 0.0:
            # NOTE: 100 ms hardcoded rescue value.
            configuration.RESET_FOR_SECONDS = 0.1
            logging.error("min. reset time shall be greater than zero. Now set to value = 1 ms")
            tkinter.messagebox.showerror(title="ERROR",
                                         message="min. reset time shall be greater than zero. Now set to value = 1 ms")
            root.update()

    def createTempFiles(self):
        if os.path.exists(FILE_NAME_RESET_HIGH):
            os.remove(FILE_NAME_RESET_HIGH)
        # create temporary files with "inactive" value: in this case LOW, OFF,..
        f = open(FILE_NAME_RESET_LOW, "w+")
        f.close()

    def thread_reset(self, name):
        logging.info("Thread %s: starting", name)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            if self.__event.evt_set_reset_high.is_set() == False:
                if os.path.isfile(FILE_NAME_RESET_HIGH):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_RESET_HIGH,FILE_NAME_RESET_LOW)
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_RESET_HIGH)
                else:
                    f = open(FILE_NAME_RESET_LOW, "w+")
                    f.close()
                logging.info("Reset set to LOW")
                self.__event.evt_set_reset_high.wait()
            else:
                if os.path.isfile(FILE_NAME_RESET_LOW):
                    renamed = False
                    while renamed == False:
                        try:
                            os.replace(FILE_NAME_RESET_LOW,FILE_NAME_RESET_HIGH)
                            renamed = True
                        except:
                            logging.warning("File cannot be renamed, we try again. File = "+FILE_NAME_RESET_LOW)
                else:
                    f = open(FILE_NAME_RESET_HIGH, "w+")
                    f.close()
                logging.info("Reset set to HIGH")
                self.__event.evt_set_reset_low.wait()
        logging.info("Thread %s: finished!", name)


