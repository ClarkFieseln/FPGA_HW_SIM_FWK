import logging
import configuration
from inspect import currentframe
from sys import platform
if platform == "win32":
    import win32file
import threading
import tkinter
from timeit import default_timer as cProfileTimer
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

    set_resolution_ns(1e-6 * NSEC_PER_SEC)  # / NSEC_PER_SEC

# NOTE: we need root so we can close the messagebox
root = tkinter.Tk()
root.withdraw()

# current frame
cf = currentframe()

# module definitions and variables:
FILE_NAME_CLOCK = None



class scheduler:
################
    CLOCK_PERIOD_SEC = None
    __event = None
    toggle = True  # TODO: add getter/setter
    csv_log = None
    # peripheral and app objects
    digital_inputs = None
    digital_outputs = None
    leds = None
    reset = None
    switches = None
    buttons = None
    pc_sensor = None
    adc_app = None
    # FIFO for clock
    fifo_w_clock = None
    class test():
        freq = 0
        prev_time = 0
        nr_cycles = 0
        log_buff = ""
        info_buff = ""
        start_time = 0
    test = test()

    def __init__(self, event, CLOCK_PERIOD_SEC_ARG, csv_log, ref):
        logging.info('init scheduler')
        self.__event = event
        self.CLOCK_PERIOD_SEC = CLOCK_PERIOD_SEC_ARG
        self.csv_log = csv_log
        self.reset = ref.reset
        self.leds = ref.leds
        self.switches = ref.switches
        self.digital_inputs = ref.digital_inputs
        self.digital_outputs = ref.digital_outputs
        self.buttons = ref.buttons
        self.pc_sensor = ref.pc_sensor
        self.adc_app = ref.adc_app
        self.updateGuiDefs()
        scheduler_thread = threading.Thread(name="scheduler_thread", target=self.thread_scheduler,
                                            args=("scheduler_thread",))
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
                self.start_time = cProfileTimer()
            # device on?
            if self.__event.evt_set_power_on.is_set() == True:
                # toggle signal
                if self.toggle == False:
                    # handle PC sensors/infos
                    #########################
                    # sync sensor values
                    if clock_periods % configuration.PC_UTIL_PER_IN_CLK_PER == 0:
                        self.pc_sensor.do_pc_info()
                        # logging.info("batt sync = " + str(self.pc_sensor.get_secsleft_sync()))
                    # async sensor values
                    # logging.info("batt asnc = " + str(self.pc_sensor.get_secsleft()))
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
                        win32file.WriteFile(self.fifo_w_clock, str.encode("0"))
                    else:
                        self.fifo_w_clock.write("0")
                        self.fifo_w_clock.flush()
                else:
                    # handle clock - raising edge
                    #############################
                    self.clock_high = True
                    # write clock = 1 = HIGH
                    if platform == "win32":
                        win32file.WriteFile(self.fifo_w_clock, str.encode("1"))
                    else:
                        self.fifo_w_clock.write("1")
                        self.fifo_w_clock.flush()
                    # ADC app
                    #########
                    if clock_periods % configuration.ADC_SAMPLING_PERIOD_IN_CLK_PER == 0:
                        self.adc_app.set_sampling_pulse()
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
                        self.test.nr_cycles = self.test.nr_cycles + 1
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
                    self.test.prev_time = self.start_time
            elif (self.__event.evt_step_on.is_set() == True):
                if self.clock_high == False:
                    while self.__event.evt_step_on.is_set() == True and self.__event.evt_do_step.is_set() == False:
                        self.__event.evt_do_step.wait(self.CLOCK_PERIOD_SEC[0] / 2)
                    if configuration.TEST:
                        self.test.prev_time = self.start_time
                else:
                    self.__event.evt_do_step.clear()  # step done!
                    self.__event.evt_clock.wait()
                    self.__event.evt_clock.clear()
            else:
                if configuration.TEST:
                    end_time = cProfileTimer()
                    tdiff = self.start_time - self.test.prev_time
                    self.test.prev_time = self.start_time
                    if tdiff != 0:
                        self.test.freq = 0.5 / (tdiff)
                        # self.test.log_buff += str(self.test.freq) + "\r\n"
                        self.test.log_buff += str(self.test.freq) + "," + str(self.test.nr_cycles) + "\r\n"
                        tdiff_sched = end_time - self.start_time
                        self.test.info_buff += str(tdiff_sched) + "\r\n"
                        # NOTE: uncomment next code to see warning..
                        # WARNING: logging this warning too often may worsen the problem
                        # if tdiff_sched > (self.CLOCK_PERIOD_SEC[0]/2):
                        # logging.warning("processing time in scheduler = "+str(tdiff_sched)+" sec exceeds CLOCK_PERIOD_SEC = "+str(self.CLOCK_PERIOD_SEC[0]))
                        # Note: if you get here you may need to select a higher value for CLOCK_PERIOD_SEC.
                        #       The events generated by thread_clock will not be processed in time by thread_scheduler.
                        #       If there are no external time dependencies, then the simulation may continue to run withtout problems,
                        #       but at a lower pace as expected/desired.
                self.__event.evt_clock.wait()
                self.__event.evt_clock.clear()
        logging.info("Thread %s finished!", name)




