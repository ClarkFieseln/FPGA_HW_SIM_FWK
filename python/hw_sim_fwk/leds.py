import configuration
import oclock
import logging
import tkinter
import os



# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

FILE_NAME_LED_ON = []
FILE_NAME_LED_OFF = []
LED_PERIOD_SEC = None
# NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = oclock.Event()



class leds:
###########
    CLOCK_PERIOD_SEC = None
    __event = None
    # TODO: implement getter/setter for LED_ON[]
    LED_ON = []
    for i in range(configuration.NR_LEDS):
        LED_ON.append(0)

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG):
        logging.info('init leds')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.updateGuiDefs()
        self.__updateMemberVariables()

    def updateGuiDefs(self):
        global FILE_NAME_LED_ON
        global FILE_NAME_LED_OFF
        global LED_PERIOD_SEC
        if configuration.NR_LEDS > configuration.MAX_NR_LED:
            configuration.NR_LEDS = configuration.MAX_NR_LED
            logging.warning("maximum nr. of LEDs limited to " + str(configuration.MAX_NR_LED))
        FILE_NAME_LED_ON_PART = configuration.FILE_PATH + "led_on_"
        FILE_NAME_LED_OFF_PART = configuration.FILE_PATH + "led_off_"
        FILE_NAME_LED_ON = []
        FILE_NAME_LED_OFF = []
        for i in range(configuration.NR_LEDS):
            FILE_NAME_LED_ON.append(FILE_NAME_LED_ON_PART + str(i))
            FILE_NAME_LED_OFF.append(FILE_NAME_LED_OFF_PART + str(i))
        # LED period
        # ASSUMPTION: in worst case the LEDs are switched in every edge of the clock (both rising and falling edges)
        #             under consideration of jitter we need to be faster than that when polling possible changes,
        #             thus we define the period to be 1/4th of the clock period.
        LED_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] / 4
        logging.info("LED_PERIOD_SEC = " + str(LED_PERIOD_SEC))

    def createTempFiles(self):
        for i in range(configuration.NR_LEDS):
            if os.path.exists(FILE_NAME_LED_ON[i]):
                os.remove(FILE_NAME_LED_ON[i])
        for i in range(configuration.NR_LEDS):
            f = open(FILE_NAME_LED_OFF[i], "w+")
            f.close()

    # TODO: need to update threads as well?
    def __updateMemberVariables(self):
        self.LED_ON = []
        for i in range(configuration.NR_LEDS):
            self.LED_ON.append(0)

    def do_led(self):
        for i in range(configuration.NR_LEDS):
            if self.LED_ON[i] == 0:
                if os.path.isfile(FILE_NAME_LED_ON[i]):
                    removed = False
                    while removed == False:
                        try:
                            os.remove(FILE_NAME_LED_ON[i])
                            removed = True
                        except:
                            logging.warning("File cannot be removed, we try again. File = " + FILE_NAME_LED_ON[i])
                    # clean up just in case (we assume signal cannot be set faster than we poll)
                    if os.path.isfile(FILE_NAME_LED_OFF[i]):
                        removed = False
                        while removed == False:
                            try:
                                os.remove(FILE_NAME_LED_OFF[i])
                                removed = True
                            except:
                                logging.warning("File cannot be removed, we try again. File = " + FILE_NAME_LED_OFF[i])
                    logging.debug("LED %s is ON", str(i))  # logging.info("LED %s is ON", str(i))
                    self.LED_ON[i] = 1
            else:
                if os.path.isfile(FILE_NAME_LED_OFF[i]):
                    removed = False
                    while removed == False:
                        try:
                            os.remove(FILE_NAME_LED_OFF[i])
                            removed = True
                        except:
                            logging.warning("File cannot be removed, we try again. File = " + FILE_NAME_LED_OFF[i])
                    # clean up just in case (we assume signal cannot be set faster than we poll)
                    if os.path.isfile(FILE_NAME_LED_ON[i]):
                        removed = False
                        while removed == False:
                            try:
                                os.remove(FILE_NAME_LED_ON[i])
                                removed = True
                            except:
                                logging.warning("File cannot be removed, we try again. File = " + FILE_NAME_LED_ON[i])
                    logging.debug("LED %s is OFF", str(i))  # logging.info("LED %s is OFF", str(i))
                    self.LED_ON[i] = 0
        # inform GUI
        self.__event.evt_gui_led_update.set()


