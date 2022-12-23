import configuration
import os
import logging
import threading
import oclock
from common_fifo import create_r_fifo
from sys import platform
if platform == "win32":
    import win32file
import tkinter
import time


###################################################
# TODO: implement TX of 'Z' value
#       (adapt VHDL code as well)
#       For now we TX '0' instead, which works fine
###################################################

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

# fifo names
FILE_NAME_SPI_nCS = []
FILE_NAME_SPI_CLK = []
# file names
FILE_NAME_SPI_DIN_HIGH = []
FILE_NAME_SPI_DIN_LOW = []
NR_DATA_OUT = 16
NR_DATA_OUT_VAL = (NR_DATA_OUT - 2)
###########################################################################################
# TODO: check if NBLANKBITS = 2 is ok, or if we need to change the logic
#       so NBLANKBITS = 1 matches what the receiver side expects/configured.
#       At the moment the first blank bit is NOT seen by the VHDL simulation, so we send 2.
#       As a workaround we use the "positive" flanks of self.__SPI_SCK instead of the neg.
#       At the moment following combinations work: NBLANKBITS = 1, __SPI_SCK positive
#                                                  NBLANKBITS = 2, __SPI_SCK negative
###########################################################################################
NBLANKBITS = 1 # 2 # 1



class LT2314:
#############
    CLOCK_PERIOD_SEC = None
    __event = None
    __pc_sensor = None
    __SPI_nCS = 1 # value read from FIFO (named pipe), set by VHDL code
    __fifo_r_nCS = None
    __SPI_SCK = 0  # value read from FIFO (named pipe), set by VHDL code
    __fifo_r_SCK = None
    __evt_nCS_is_zero = oclock.Event()
    __evt_SCK_is_zero = oclock.Event()
    __SPI_DIN = '0'
    __rawdata = ['0']*NR_DATA_OUT_VAL
    __temperature = 0

    def __init__(self, CLOCK_PERIOD_SEC_ARG, event, pc_sensor):
        logging.info('init LT2314')
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.__event = event
        self.__pc_sensor = pc_sensor
        self.updateGuiDefs()
        # threads
        thread_name = "fifo_r_nCS_thread"
        nCS_thread = threading.Thread(name=thread_name, target=self.__thread_fifo_r_nCS, args=(thread_name,))
        nCS_thread.start()
        thread_name = "fifo_r_SCK_thread"
        SCK_thread = threading.Thread(name=thread_name, target=self.__thread_fifo_r_SCK, args=(thread_name,))
        SCK_thread.start()
        thread_name = "adc_thread"
        adc_thread = threading.Thread(name=thread_name, target=self.__thread_adc, args=(thread_name,))
        adc_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_SPI_nCS
        global FILE_NAME_SPI_SCK
        global FILE_NAME_SPI_DIN_HIGH
        global FILE_NAME_SPI_DIN_LOW
        FILE_NAME_SPI_nCS = configuration.FIFO_PATH + "LT2314_SPI_nCS"
        FILE_NAME_SPI_SCK = configuration.FIFO_PATH + "LT2314_SPI_SCK"
        FILE_NAME_SPI_DIN_HIGH = configuration.FILE_PATH + "LT2314_SPI_DIN_high"
        FILE_NAME_SPI_DIN_LOW = configuration.FILE_PATH + "LT2314_SPI_DIN_low"

    def createTempFiles(self):
        if os.path.exists(FILE_NAME_SPI_DIN_HIGH):
            os.remove(FILE_NAME_SPI_DIN_HIGH)

    def set_spi_din_to_zero(self):
        if os.path.isfile(FILE_NAME_SPI_DIN_HIGH):
            renamed = False
            while renamed == False:
                try:
                    os.replace(FILE_NAME_SPI_DIN_HIGH, FILE_NAME_SPI_DIN_LOW)
                    renamed = True
                except:
                    logging.warning("File cannot be renamed, we try again. File =  " + FILE_NAME_SPI_DIN_HIGH)
        else:
            f = open(FILE_NAME_SPI_DIN_LOW, "w+")
            f.close()

    def set_spi_din_to_one(self):
        if os.path.isfile(FILE_NAME_SPI_DIN_LOW):
            renamed = False
            while renamed == False:
                try:
                    os.replace(FILE_NAME_SPI_DIN_LOW, FILE_NAME_SPI_DIN_HIGH)
                    renamed = True
                except:
                    logging.warning(
                        "File cannot be renamed, we try again. File =  " + FILE_NAME_SPI_DIN_LOW)
        else:
            f = open(FILE_NAME_SPI_DIN_HIGH, "w+")
            f.close()

    # implementation based on LT2314_tb.vhd found here:
    # https://imperix.com/doc/implementation/fpga-based-spi-communication-ip
    def __thread_adc(self, name):
        logging.info("Thread %s: starting", name)
        # initialize things
        # now nCS is 1, that is, state = ACQ
        # instead of 'Z', for now we just set SPI_DIN to zero, the current VHDL code only checks for file HIGH value anyways
        self.__SPI_DIN = '0'  # 'Z'
        self.set_spi_din_to_zero()
        # set counter
        counter = (NR_DATA_OUT_VAL - 1) + NBLANKBITS
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # blocking call (wait for negative flank on nCS)
            # BUG 10ms delay
            # self.__evt_nCS_is_zero.wait()
            while self.__evt_nCS_is_zero.is_set() is False:
                time.sleep(self.CLOCK_PERIOD_SEC[0] / 4)
            self.__evt_nCS_is_zero.clear()
            # get raw data
            # NOTE: data is "always" acquired asynchronous to scheduler, no matter if call get_cpu_percent_int()
            # or get_cpu_percent_int_sync(). This thread is triggered by events which in turn depend on SPI_SCK
            # which is determined by the VHDL-code.
            # NOTE: for now we take the CPU percent as a replacement of the temperature!
            temperature = self.__pc_sensor.get_cpu_percent_int()
            # get also the temperature in °C (as float) to pass it to GUI when requested
            ############################################################################
            self.__temperature = self.__pc_sensor.get_cpu_percent()
            # inform GUI so it can get the "temperature" directly from the pc_sensor
            self.__event.evt_gui_temperature_update.set()
            ############################################################################
            # check range
            if (temperature >= configuration.MAX_INT) or (temperature < configuration.MIN_INT): # 2**14 = 16384
                logging.error("temperature = "+str(temperature)+"value outside of valid range!")
                temperature = 0
                self.__temperature = 0.0
            # debug info
            logging.debug("temp int = " + str(temperature))
            logging.debug("temp flt = " + str(self.__temperature))
            # convert to binary representation (as a string)
            self.__rawdata = bin(temperature)[2:].zfill(NR_DATA_OUT_VAL)
            # reverse string
            self.__rawdata = self.__rawdata[::-1]
            # debug info
            logging.debug("temp = "+ str(self.__rawdata))
            logging_info = ""
            # now nCS is 0, that is, state = CONV
            while self.__SPI_nCS == 0:
                # BUG 10ms delay
                # self.__evt_SCK_is_zero.wait()
                while self.__evt_SCK_is_zero.is_set() is False:
                    time.sleep(self.CLOCK_PERIOD_SEC[0] / 4)
                self.__evt_SCK_is_zero.clear()
                if (counter > (NR_DATA_OUT_VAL - 1) or counter < 0):
                    if self.__SPI_DIN != '0':
                        self.__SPI_DIN = '0'
                        self.set_spi_din_to_zero()
                    # debug info
                    logging_info = logging_info + "(0)"
                else:
                    if self.__SPI_DIN != self.__rawdata[counter]:
                        self.__SPI_DIN = self.__rawdata[counter];
                        if self.__SPI_DIN == '0':
                            self.set_spi_din_to_zero()
                        else:
                            self.set_spi_din_to_one()
                    # debug info
                    logging_info = logging_info + str(self.__SPI_DIN)
                counter = counter - 1
            # now nCS is 1, that is, state = ACQ
            # instead of 'Z', for now we just set SPI_DIN to zero, the current VHDL code only checks for file HIGH value anyways
            self.__SPI_DIN = '0' # 'Z'
            self.set_spi_din_to_zero()
            # debug info
            logging_info = logging_info + "(Z)"
            logging.debug(logging_info)
            # set counter
            counter = (NR_DATA_OUT_VAL - 1) + NBLANKBITS
        logging.info("Thread %s: finished!", name)

    def __thread_fifo_r_nCS(self, name):
        logging.info("Thread %s: starting", name)
        # open FIFO for reading
        self.__fifo_r_nCS = create_r_fifo(FILE_NAME_SPI_nCS)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # read SPI_nCS FIFO
            ###################
            if platform == "win32":
                try:
                    line = win32file.ReadFile(self.__fifo_r_nCS, 64*1024)
                    # temp_line_int = int.from_bytes(line[1]); # str(line[1], 'utf-8') # TODO: why nok?
                    temp_line_str = str(line[1], 'utf-8')
                except:
                    logging.error("could not read from pipe of SPI_nCS")
                    win32file.CloseHandle(self.__fifo_r_nCS)
            else:
                temp_line_str = self.__fifo_r_nCS.read()
            try:
                temp_line_int = int(temp_line_str)
            except ValueError:
                temp_line_int = 0
                logging.error("SPI_nCS set to 0 because of wrong int = " + temp_line_str)
            # process SPI_nCS info from FIFO
            ################################
            if temp_line_int != self.__SPI_nCS:
                self.__SPI_nCS = temp_line_int
                if self.__SPI_nCS == 0:
                    self.__evt_nCS_is_zero.set()
        logging.info("Thread %s: finished!", name)

    def __thread_fifo_r_SCK(self, name):
        logging.info("Thread %s: starting", name)
        # open FIFO for reading
        self.__fifo_r_SCK = create_r_fifo(FILE_NAME_SPI_SCK)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # read SPI_SCK FIFO
            ###################
            if platform == "win32":
                try:
                    line = win32file.ReadFile(self.__fifo_r_SCK, 64*1024)
                    # temp_line_int = int.from_bytes(line[1]); # str(line[1], 'utf-8') # TODO: why nok?
                    temp_line_str = str(line[1], 'utf-8')
                except:
                    logging.error("could not read from pipe of SPI_SCK")
                    win32file.CloseHandle(self.__fifo_r_SCK)
            else:
                temp_line_str = self.__fifo_r_SCK.read()
            try:
                temp_line_int = int(temp_line_str)
            except ValueError:
                temp_line_int = 0
            # process SPI_SCK info from FIFO
            ################################
            if self.__SPI_SCK != temp_line_int:
                self.__SPI_SCK = temp_line_int
                # WORKAROUND for now..
                # if self.__SPI_SCK == 0:
                if self.__SPI_SCK == 1:
                    self.__evt_SCK_is_zero.set()
        logging.info("Thread %s: finished!", name)

    def get_temperature(self):
        ret_val = self.__temperature
        return ret_val




