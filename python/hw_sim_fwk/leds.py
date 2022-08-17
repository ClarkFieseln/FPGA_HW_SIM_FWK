import configuration
import oclock
import logging
import tkinter
import os



####################################################################################################################
# TODO: improve do_led()
# taking as example __set_one()/__set_zero() in digital_inputs.do_di_count() we shall also use separate threads here
# in order not to block when doing file-handling sequentially.
# Because we will probably never use this module again anyways the solution may be to just remove this module!
####################################################################################################################

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

FILE_NAME_LED_ON = []
FILE_NAME_LED_OFF = []



class leds:
###########
    __event = None
    # TODO: implement getter/setter for LED_ON[]
    LED_ON = []

    def __init__(self, event):
        logging.info('init leds')
        self.__event = event
        for i in range(configuration.NR_LEDS):
            self.LED_ON.append(0)
        self.updateGuiDefs()
        self.__updateMemberVariables()

    def updateGuiDefs(self):
        global FILE_NAME_LED_ON
        global FILE_NAME_LED_OFF
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


