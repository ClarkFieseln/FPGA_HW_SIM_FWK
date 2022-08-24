import psutil
import logging
from threading import Lock
import threading
import configuration



# NOTE: for a realistic emulation the sensor value __secsleft runs "asynchronously", independent of the scheduler.
#       Another possibility is to trigger the update of the readings in the scheduler by calling do_batt().
##########################################################################################################
PC_UTIL_PERIOD_SEC = None
MAX_INT = configuration.MAX_INT
MIN_INT = configuration.MIN_INT
MAX_VAL = configuration.MAX_VAL
MIN_VAL = configuration.MIN_VAL



class pc_sensor():
    CLOCK_PERIOD_SEC = None
    __event = None
    __count = 0
    __secsleft = 0
    __lock = Lock()
    __count_sync = 0
    __secsleft_sync = 0
    __lock_sync = Lock()
    __cpu_percent = 0
    __cpu_percent_sync = 0
    __lock_cpu = Lock()
    __lock_cpu_sync = Lock()

    def __init__(self, event, CLOCK_PERIOD_SEC):
        logging.info('init pc_sensor')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC
        self.updateGuiDefs()
        thread_name = "pc_sensor_thread"
        pc_info_thread = threading.Thread(name=thread_name, target=self.__thread_pc_sensor, args=(thread_name,))
        pc_info_thread.start()

    def updateGuiDefs(self):
        global PC_UTIL_PERIOD_SEC
        PC_UTIL_PERIOD_SEC = self.CLOCK_PERIOD_SEC[0] * configuration.PC_UTIL_PER_IN_CLK_PER
        logging.info("PC_UTIL_PERIOD_SEC = " + str(PC_UTIL_PERIOD_SEC))

    def __thread_pc_sensor(self, name):
        logging.info("Thread %s: starting", name)
        # thread loop
        while self.__event.evt_close_app.is_set() == False:
            # battery
            b = psutil.sensors_battery()
            if int(b.secsleft) > 0:
                self.__lock.acquire()
                self.__secsleft = int(b.secsleft)
                self.__lock.release()
            else:
                self.__count = self.__count + 1
                self.__lock.acquire()
                self.__secsleft = self.__count
                self.__lock.release()
            # CPU percent
            self.__lock_cpu.acquire()
            self.__cpu_percent = psutil.cpu_percent()
            self.__lock_cpu.release()
            # this runs close to scheduler clock but still asynchronous to it..
            self.__event.evt_wake_up.wait(PC_UTIL_PERIOD_SEC)
        logging.info("Thread %s: finished!", name)

    def do_pc_info(self):
        # battery
        b = psutil.sensors_battery()
        if int(b.secsleft) > 0:
            self.__lock_sync.acquire()
            self.__secsleft_sync = int(b.secsleft)
            self.__lock_sync.release()
        else:
            self.__count_sync = self.__count_sync + 1
            self.__lock_sync.acquire()
            self.__secsleft_sync = self.__count_sync
            self.__lock_sync.release()
        # CPU percent
        self.__lock_cpu_sync.acquire()
        self.__cpu_percent_sync = psutil.cpu_percent()
        self.__lock_cpu_sync.release()

    def get_secsleft(self):
        self.__lock.acquire()
        __secsleft = self.__secsleft
        self.__lock.release()
        return __secsleft

    def get_secsleft_sync(self):
        self.__lock_sync.acquire()
        __secsleft_sync = self.__secsleft_sync
        self.__lock_sync.release()
        return __secsleft_sync

    def get_cpu_percent(self):
        self.__lock_cpu.acquire()
        __cpu_percent = self.__cpu_percent
        self.__lock_cpu.release()
        return __cpu_percent

    def get_cpu_percent_sync(self):
        self.__lock_cpu_sync.acquire()
        __cpu_percent_sync = self.__cpu_percent_sync
        self.__lock_cpu_sync.release()
        return __cpu_percent_sync

    def get_cpu_percent_int(self):
        # transform value according to this formula
        # relating the range of the real measurement (e.g. physical temperature) with the range of the
        # integer variable we need to use in the FPGA
        # y = y1 + (x - x1)*((y2 - y1)/(x2 - x1))
        self.__lock_cpu.acquire()
        ret_val = int(MIN_INT + (self.__cpu_percent - MIN_VAL) * ((MAX_INT - MIN_INT) / (MAX_VAL - MIN_VAL)))
        self.__lock_cpu.release()
        return ret_val

    def get_cpu_percent_sync_int(self):
        # transform value according to this formula
        # relating the range of the real measurement (e.g. physical temperature) with the range of the
        # integer variable we need to use in the FPGA
        # y = y1 + (x - x1)*((y2 - y1)/(x2 - x1))
        self.__lock_cpu_sync.acquire()
        ret_val = int(MIN_INT + (self.__cpu_percent_sync - MIN_VAL) * ((MAX_INT - MIN_INT) / (MAX_VAL - MIN_VAL)))
        self.__lock_cpu_sync.release()
        return ret_val


