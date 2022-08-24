import oclock
import logging
import configuration
import os
import threading
import tkinter
from integer_output import integer_output



# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

FILE_NAME_SAMPLING_PULSE_HIGH = []
FILE_NAME_SAMPLING_PULSE_LOW = []
ADC_SAMPLING_PERIOD_SEC = None
MAX_INT = configuration.MAX_INT
MIN_INT = configuration.MIN_INT
MAX_VAL = configuration.MAX_VAL
MIN_VAL = configuration.MIN_VAL



class adc_app:
##############
    CLOCK_PERIOD_SEC = None
    __event = None
    __wait_sampling_pulse_set = 0
    __evt_set_one = oclock.Event()
    __evt_set_zero = oclock.Event()
    __integer_output = None

    def __init__(self, event, CLOCK_PERIOD_SEC):
        logging.info('init digital_inputs')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC
        self.updateGuiDefs()
        self.createTempFiles()
        # sync threads only used to create FIFOs
        thread_name = "__thread_set_one"
        thread_set_one = threading.Thread(name=thread_name, target=self.__thread_set_one, args=(thread_name,))
        thread_set_one.start()
        thread_name = "__thread_set_zero"
        thread_set_zero = threading.Thread(name=thread_name, target=self.__thread_set_zero, args=(thread_name,))
        thread_set_zero.start()
        # instantiate integer_output
        self.__integer_output = integer_output(event, "LT2314_data_out")

    def updateGuiDefs(self):
        global FILE_NAME_SAMPLING_PULSE_HIGH
        global FILE_NAME_SAMPLING_PULSE_LOW
        global ADC_SAMPLING_PERIOD_SEC
        FILE_NAME_SAMPLING_PULSE_HIGH = configuration.FILE_PATH + "LT2314_sampling_pulse_high"
        FILE_NAME_SAMPLING_PULSE_LOW = configuration.FILE_PATH + "LT2314_sampling_pulse_low"
        # ADC sampling period
        ADC_SAMPLING_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] * configuration.ADC_SAMPLING_PERIOD_IN_CLK_PER
        logging.info("DI_PERIOD_SEC = " + str(ADC_SAMPLING_PERIOD_SEC))

    def createTempFiles(self):
        if os.path.exists(FILE_NAME_SAMPLING_PULSE_HIGH):
            os.remove(FILE_NAME_SAMPLING_PULSE_HIGH)

    # Manage file-handling in a separate thread.
    def __thread_set_one(self, name):
        logging.info("Thread %s: starting", name)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # blocking call
            self.__evt_set_one.wait()
            self.__evt_set_one.clear()
            if os.path.isfile(FILE_NAME_SAMPLING_PULSE_LOW):
                renamed = False
                while renamed == False:
                    try:
                        os.replace(FILE_NAME_SAMPLING_PULSE_LOW, FILE_NAME_SAMPLING_PULSE_HIGH)
                        renamed = True
                    except:
                        # logging.warning("File cannot be renamed, we try again. File = " + FILE_NAME_DI_LOW[i])
                        logging.debug("File cannot be renamed, we try again. File = " + FILE_NAME_SAMPLING_PULSE_LOW)
            else:
                created = False
                while created == False:
                    try:
                        f = open(FILE_NAME_SAMPLING_PULSE_HIGH, "w+")
                        f.close()
                        created = True
                    except:
                        # logging.warning("File cannot be created, we try again. File = " + FILE_NAME_SAMPLING_PULSE_HIGH)
                        logging.debug("File cannot be created, we try again. File = " + FILE_NAME_SAMPLING_PULSE_HIGH)
            # debug code
            logging.debug("sampling_pulse set to ONE")
            # clear automatically...after a short time (but at least CLOCK_PERIOD_SEC)
            ##########################################################################
            self.__event.evt_wake_up.wait(self.CLOCK_PERIOD_SEC[0])
            self.__evt_set_zero.set()
            ##########################################################################
        logging.info("Thread %s: finished!", name)

    # Manage file-handling in a separate thread.
    def __thread_set_zero(self, name):
        logging.info("Thread %s: starting", name)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # blocking call
            self.__evt_set_zero.wait()
            self.__evt_set_zero.clear()
            if os.path.isfile(FILE_NAME_SAMPLING_PULSE_HIGH):
                renamed = False
                while renamed == False:
                    try:
                        os.replace(FILE_NAME_SAMPLING_PULSE_HIGH, FILE_NAME_SAMPLING_PULSE_LOW)
                        renamed = True
                    except:
                        # logging.warning("File cannot be renamed, we try again. File = " + FILE_NAME_SAMPLING_PULSE_HIGH)
                        logging.debug("File cannot be renamed, we try again. File = " + FILE_NAME_SAMPLING_PULSE_HIGH)
            else:
                created = False
                while created == False:
                    try:
                        f = open(FILE_NAME_SAMPLING_PULSE_LOW, "w+")
                        f.close()
                        created = True
                    except:
                        # logging.warning("File cannot be created, we try again. File = " + FILE_NAME_SAMPLING_PULSE_LOW)
                        logging.debug("File cannot be created, we try again. File = " + FILE_NAME_SAMPLING_PULSE_LOW)
            # debug code
            logging.debug("sampling_pulse set to ZERO")
        logging.info("Thread %s: finished!", name)

    def set_sampling_pulse(self):
        self.__evt_set_one.set()

    def clear_sampling_pulse(self):
        self.__evt_set_zero.set()

    def get_data_out(self):
        # update value
        self.__integer_output.do_int_out()
        # get and transform value according to this formula
        # relating the range of the acquired value with the range of the real measurement (e.g. physical temperature)
        # y = y1 + (x - x1)*((y2 - y1)/(x2 - x1))
        ret_val = MIN_VAL + (self.__integer_output.INT_OUT - MIN_INT) * ((MAX_VAL - MIN_VAL) / (MAX_INT - MIN_INT))
        # return transformed value
        return ret_val




