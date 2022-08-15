import oclock
import logging
import configuration
from inspect import currentframe
from sys import platform
if platform == "win32":
    import win32file
import threading
import tkinter
import time
from common_fifo import create_w_fifo



# from https://discuss.python.org/t/higher-resolution-timers-on-windows/16153
if platform == "win32":
    import ctypes
    ntdll = ctypes.WinDLL('NTDLL.DLL')
    NSEC_PER_SEC = 1000000000
    def set_resolution_ns(resolution):
        # NtSetTimerResolution uses 100ns units
        resolution = ctypes.c_ulong(int(resolution // 100))
        current = ctypes.c_ulong()
        r = ntdll.NtSetTimerResolution(resolution, 1, ctypes.byref(current))
        # NtSetTimerResolution uses 100ns units
        return current.value * 100
    set_resolution_ns(1e-6 * NSEC_PER_SEC) # / NSEC_PER_SEC

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

# current frame
cf = currentframe()

# module definitions and variables:
FILE_NAME_CLOCK = None
# NOTE: we use oclock.Event.wait(timeout) i.o. time.sleep(timeout) otherwise the main thread is blocked.
#       The following event is never set, its only used to wait on it up to timeout and not block the main thread.
evt_wake_up = oclock.Event()



class scheduler:
################
    CLOCK_PERIOD_SEC = None
    __event = None
    toggle = True # TODO: add getter/setter
    csv_log = None
    # peripheral and app objects
    digital_inputs = None
    digital_outputs = None
    leds = None
    reset = None
    switches = None
    buttons = None
    # FIFO for clock
    fifo_w_clock = None # create_w_fifo(FILE_NAME_CLOCK)
    if configuration.TEST:
        freq = 0
        prev_time = 0
        nr_cycles = 0
        log_buff = ""
        info_buff = ""

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG, csv_log, reset, leds, switches, digital_inputs,\
                                   digital_outputs, buttons):
        logging.info('init scheduler')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.csv_log = csv_log
        self.reset = reset
        self.leds = leds
        self.switches = switches
        self.digital_inputs = digital_inputs
        self.digital_outputs = digital_outputs
        self.buttons = buttons
        self.updateGuiDefs()
        scheduler_thread = threading.Thread(name="scheduler_thread", target=self.thread_scheduler, args=("scheduler_thread",))
        scheduler_thread.start()

    def updateGuiDefs(self):
        global FILE_NAME_CLOCK
        FILE_NAME_CLOCK = configuration.FIFO_PATH + "clock"

    # thread for scheduling synchronous signals
    # NOTE: tests showed that DIs, DOs, LEDs need 1ms (sometimes 2ms).
    #       Intensive work on VIVADO simulator, e.g. on wave-output may increase this time up to 5ms.
    #       Therefore, a maximum data rate between App and VHDL of approx. 200 Hz can be reached.
    #       A higher rate of about 500Hz will work fine most of the time.
    #       Any configured rate will not affect the simulation results but just work slower than expected.
    # NOTE: in order to distribute the processing load we "output" signals (DIs, switches, buttons) in one flank and
    #       "input" signals (DOs, LEDs) in the other flank. Note the inverted direction with regards VHDL-simulator.
    ################################################################################################################
    def thread_scheduler(self, name):
        logging.info("Thread %s starting", name)
        # create FIFO for clock
        # (blocking call)
        self.fifo_w_clock = create_w_fifo(FILE_NAME_CLOCK)
        # nr. of counted clock periods
        clock_periods = 0
        # main loop (toggle signal and sleep)
        while self.__event.evt_close_app.is_set() == False:
            # time measurement
            if configuration.TEST:
                start_time = time.time()
            # device on?
            if self.__event.evt_set_power_on.is_set() == True:
                # toggle signal
                if self.toggle == False:
                    # handle digital inputs
                    #######################
                    if clock_periods % configuration.DI_PER_IN_CLK_PER == 0:
                        # NOTE: uncomment one of these options:
                        # self.digital_inputs.do_di_toggle()
                        self.digital_inputs.do_di_count()
                    # handle switches
                    #################
                    if configuration.SWITCH_TOGGLE_AUTO == True:
                        if clock_periods % configuration.SW_PER_IN_CLK_PER == 0:
                            self.switches.do_switch()
                    # handle buttons
                    ################
                    if configuration.BUTTON_TOGGLE_AUTO == True:
                        if clock_periods % configuration.BUTTON_PER_IN_CLK_PER == 0:
                            self.buttons.do_button()
                    # handle clock - falling edge
                    # NOTE: it is important to schedule all tasks first before emulating a clock change
                    ###################################################################################
                    self.clock_high = False
                    # write clock = 0 = LOW
                    if platform == "win32":
                        win32file.WriteFile(self.fifo_w_clock, str.encode("0")) # \r\n"))
                    else:
                        self.fifo_w_clock.write("0\r\n")
                        self.fifo_w_clock.flush()
                else:
                    # handle clock - raising edge
                    #############################
                    self.clock_high = True
                    # write clock = 1 = HIGH
                    if platform == "win32":
                        win32file.WriteFile(self.fifo_w_clock, str.encode("1")) # \r\n"))
                    else:
                        self.fifo_w_clock.write("1\r\n")
                        self.fifo_w_clock.flush()
                    # handle digital outputs
                    ########################
                    self.digital_outputs.do_do()
                    # handle LEDs
                    #############
                    self.leds.do_led()
                    # increment clock periods
                    #########################
                    clock_periods = clock_periods + 1
                    if configuration.TEST:
                        self.nr_cycles = self.nr_cycles + 1
                # log to csv
                ############
                if configuration.LOG_TO_CSV == True:
                    self.csv_log()
                # toggle clock signal
                #####################
                self.toggle = not self.toggle
            # wait without consuming resources
            ##################################
            if (self.__event.evt_pause.is_set()) == True:
                self.__event.evt_resume.wait()
                if configuration.TEST:
                    self.prev_time = start_time
            elif (self.__event.evt_step_on.is_set() == True):
                if self.clock_high == False:
                    while self.__event.evt_step_on.is_set() == True and self.__event.evt_do_step.is_set() == False:
                        self.__event.evt_do_step.wait(self.CLOCK_PERIOD_SEC[0] / 2)
                    if configuration.TEST:
                        self.prev_time = start_time
                else:
                    self.__event.evt_do_step.clear()  # step done!
                    self.__event.evt_clock.wait()
                    self.__event.evt_clock.clear()
            else:
                if configuration.TEST:
                    end_time = time.time()
                    tdiff = start_time - self.prev_time
                    self.prev_time = start_time
                    if tdiff != 0:
                        self.freq = 0.5/(tdiff)
                        # self.log_buff += str(self.freq) + "\r\n"
                        self.log_buff += str(self.freq) + "," + str(self.nr_cycles) + "\r\n"
                        tdiff_sched = end_time - start_time
                        self.info_buff += str(tdiff_sched) + "\r\n"
                        # WARNING: logging this warning too often may worsen the problem
                        if tdiff_sched > (self.CLOCK_PERIOD_SEC[0]/2):
                            logging.warning("processing time in scheduler = "+str(tdiff_sched)+" sec exceeds CLOCK_PERIOD_SEC = "+str(self.CLOCK_PERIOD_SEC[0]))
                            # Note: if you get here you may need to select a higher value for CLOCK_PERIOD_SEC.
                            #       The events generated by thread_clock will not be processed in time by thread_scheduler.
                            #       If there are no external time dependencies, then the simulation may continue to run withtout problems,
                            #       but at a lower pace as expected/desired.
                self.__event.evt_clock.wait()
                self.__event.evt_clock.clear()




