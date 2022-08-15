
import configuration
import configparser
from tkinter.filedialog import askopenfilename,  asksaveasfilename
import os
from tkinter import *
import pathlib
import logging



# we need this, otherwise we see the Tk window
Tk().withdraw() 

    
class InitApp(object):
######################
    config = configparser.ConfigParser(allow_no_value=True)
    config_filename = configuration.CONFIG_FILENAME
    
    def __init__(self):
        # script or .exe?
        runningScript = os.path.basename(__file__)
        # we get different relative paths depending if we debug or run the executable file
        if(runningScript=="init.py"): 
            # .py script
            configuration.IS_SCRIPT = True 
            configuration.PATH_PREFIX = str(pathlib.Path().resolve()) + "/dist/" # "./dist/"
        else:
            # .exe file
            configuration.IS_SCRIPT = False
            configuration.PATH_PREFIX = str(pathlib.Path().resolve()) + "/" # "./"
        self.config_filename = configuration.PATH_PREFIX + self.config_filename        
        # Load the "default" configuration file
        self.loadConfigFile(self.config_filename)
        
    def loadConfig(self):
        files = [ # ('All Files', '*.*'),  
                ('Ini Files', '*.ini'), 
                ('Text Document', '*.txt')] 
        filename = askopenfilename(initialdir="./", filetypes = files, defaultextension = files) 
        if (filename is not None) and (filename != ""): 
            self.loadConfigFile(filename)
        return os.path.basename(filename)

    # NOTE: LOGGING_LEVEL is read in main.py
    def loadConfigFile(self,  filename):        
        logging.info("reading "+filename)
        try:
            self.config.read(filename)
            logging.info("sections: " +  str(self.config.sections()))
            if "myConfig" in self.config:
                logging.info("keys in section myConfig:")
                if "LOGGING_LEVEL" in self.config["myConfig"]:
                    configuration.LOGGING_LEVEL = self.config['myConfig']['LOGGING_LEVEL']
                    logging.info("LOGGING_LEVEL = " + str(configuration.LOGGING_LEVEL))
                if "LOG_TO_CSV" in self.config["myConfig"]:
                    configuration.LOG_TO_CSV = self.config.getboolean('myConfig','LOG_TO_CSV')
                    logging.info("LOG_TO_CSV = " +  str(configuration.LOG_TO_CSV))
                if "LOG_ON_POWER_ON_OFF" in self.config["myConfig"]:
                    configuration.LOG_ON_POWER_ON_OFF = self.config.getboolean('myConfig','LOG_ON_POWER_ON_OFF')
                    logging.info("LOG_ON_POWER_ON_OFF = " +  str(configuration.LOG_ON_POWER_ON_OFF))
                if "FONT_SIZE_APP" in self.config["myConfig"]:
                    configuration.FONT_SIZE_APP = int(self.config['myConfig']['FONT_SIZE_APP'])
                    logging.info("FONT_SIZE_APP = " +  str(int(self.config['myConfig']['FONT_SIZE_APP'])))
                if "SHOW_ADVANCED_SETTINGS" in self.config["myConfig"]:
                    configuration.SHOW_ADVANCED_SETTINGS = self.config.getboolean('myConfig','SHOW_ADVANCED_SETTINGS')
                    logging.info("SHOW_ADVANCED_SETTINGS = " + str(configuration.SHOW_ADVANCED_SETTINGS))
                if "GUI_UPDATE_PERIOD_IN_HZ" in self.config["myConfig"]:
                    configuration.GUI_UPDATE_PERIOD_IN_HZ = int(self.config['myConfig']['GUI_UPDATE_PERIOD_IN_HZ'])
                    logging.info("GUI_UPDATE_PERIOD_IN_HZ = " + str(configuration.GUI_UPDATE_PERIOD_IN_HZ))
                if "SHOW_LIVE_STATUS" in self.config["myConfig"]:
                    configuration.SHOW_LIVE_STATUS = self.config.getboolean('myConfig','SHOW_LIVE_STATUS')
                    logging.info("SHOW_LIVE_STATUS = " + str(configuration.SHOW_LIVE_STATUS))
                if "KEEP_PB_PRESSED" in self.config["myConfig"]:
                    configuration.KEEP_PB_PRESSED = self.config.getboolean('myConfig','KEEP_PB_PRESSED')
                    logging.info("KEEP_PB_PRESSED = " + str(configuration.KEEP_PB_PRESSED))                                        
                if "SHOW_PLOT" in self.config["myConfig"]:
                    configuration.SHOW_PLOT = self.config.getboolean('myConfig','SHOW_PLOT')
                    logging.info("SHOW_PLOT = " + str(configuration.SHOW_PLOT))
                if "TEXT_BOLD" in self.config["myConfig"]:
                    configuration.TEXT_BOLD = self.config.getboolean('myConfig','TEXT_BOLD')
                    logging.info("TEXT_BOLD = " + str(configuration.TEXT_BOLD))
                if "TEXT_SIZE" in self.config["myConfig"]:
                    configuration.TEXT_SIZE = self.config.getint('myConfig','TEXT_SIZE')
                    logging.info("TEXT_SIZE = " + str(configuration.TEXT_SIZE))
                if "TEXT_FAMILY" in self.config["myConfig"]:
                    configuration.TEXT_FAMILY = self.config['myConfig']['TEXT_FAMILY']
                    logging.info("TEXT_FAMILY = " + str(configuration.TEXT_FAMILY))
                if "SOUND_EFFECTS" in self.config["myConfig"]:
                    configuration.SOUND_EFFECTS = self.config.getboolean('myConfig','SOUND_EFFECTS')
                    logging.info("SOUND_EFFECTS = " + str(configuration.SOUND_EFFECTS))
                if "SHOW_PERFORMANCE" in self.config["myConfig"]:
                    configuration.SHOW_PERFORMANCE = self.config.getboolean('myConfig','SHOW_PERFORMANCE')
                    logging.info("SHOW_PERFORMANCE = " + str(configuration.SHOW_PERFORMANCE))
                # simulator options
                if "RUN_FOR_CLOCK_PERIODS" in self.config["myConfig"]:
                    configuration.RUN_FOR_CLOCK_PERIODS = self.config.getint('myConfig','RUN_FOR_CLOCK_PERIODS')
                    logging.info("RUN_FOR_CLOCK_PERIODS = " + str(configuration.RUN_FOR_CLOCK_PERIODS))                    
            # common configuration (to python and VHDL codes):
            if "commonConfig" in self.config:
                logging.info("keys in section commonConfig:")
                if "CLOCK_PERIOD_EXTERNAL" in self.config["commonConfig"]:
                    configuration.CLOCK_PERIOD_EXTERNAL = self.config['commonConfig']['CLOCK_PERIOD_EXTERNAL']
                    logging.info("CLOCK_PERIOD_EXTERNAL = " + str(configuration.CLOCK_PERIOD_EXTERNAL))
                if "CLOCK_PERIOD_EXTERNAL_MIN_MS" in self.config["commonConfig"]:
                    configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS = self.config.getfloat('commonConfig','CLOCK_PERIOD_EXTERNAL_MIN_MS')
                    logging.info("CLOCK_PERIOD_EXTERNAL_MIN_MS = " + str(configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS))
                if "RESET_FOR_SECONDS" in self.config["commonConfig"]:
                    configuration.RESET_FOR_SECONDS = self.config.getfloat('commonConfig','RESET_FOR_SECONDS')
                    logging.info("RESET_FOR_SECONDS = " + str(configuration.RESET_FOR_SECONDS))
                if "CLOCK_PERIOD_VHDL_NS" in self.config["commonConfig"]:
                    configuration.CLOCK_PERIOD_VHDL_NS = self.config['commonConfig']['CLOCK_PERIOD_VHDL_NS']
                    logging.info("CLOCK_PERIOD_VHDL_NS = " + str(configuration.CLOCK_PERIOD_VHDL_NS))
                if "FILE_PATH" in self.config["commonConfig"]:
                    configuration.FILE_PATH = self.config['commonConfig']['FILE_PATH']
                    logging.info("FILE_PATH = " + str(configuration.FILE_PATH))
                if "FIFO_PATH" in self.config["commonConfig"]:
                    configuration.FIFO_PATH = self.config['commonConfig']['FIFO_PATH']
                    logging.info("FIFO_PATH = " + str(configuration.FIFO_PATH))
                if "MAX_NR_DI" in self.config["commonConfig"]:
                    configuration.MAX_NR_DI = self.config.getint('commonConfig','MAX_NR_DI')
                    logging.info("MAX_NR_DI = " + str(configuration.MAX_NR_DI))   
                if "NR_DIS" in self.config["commonConfig"]:
                    configuration.NR_DIS = self.config.getint('commonConfig','NR_DIS')
                    logging.info("NR_DIS = " + str(configuration.NR_DIS))
                if "MAX_NR_SW" in self.config["commonConfig"]:
                    configuration.MAX_NR_SW = self.config.getint('commonConfig','MAX_NR_SW')
                    logging.info("MAX_NR_SW = " + str(configuration.MAX_NR_SW))    
                if "NR_SWITCHES" in self.config["commonConfig"]:
                    configuration.NR_SWITCHES = self.config.getint('commonConfig','NR_SWITCHES')
                    logging.info("NR_SWITCHES = " + str(configuration.NR_SWITCHES))    
                if "MAX_NR_BTN" in self.config["commonConfig"]:
                    configuration.MAX_NR_BTN = self.config.getint('commonConfig','MAX_NR_BTN')
                    logging.info("MAX_NR_BTN = " + str(configuration.MAX_NR_BTN))             
                if "NR_BUTTONS" in self.config["commonConfig"]:
                    configuration.NR_BUTTONS = self.config.getint('commonConfig','NR_BUTTONS')
                    logging.info("NR_BUTTONS = " + str(configuration.NR_BUTTONS))     
                if "MAX_NR_LED" in self.config["commonConfig"]:
                    configuration.MAX_NR_LED = self.config.getint('commonConfig','MAX_NR_LED')
                    logging.info("MAX_NR_LED = " + str(configuration.MAX_NR_LED))   
                if "NR_LEDS" in self.config["commonConfig"]:
                    configuration.NR_LEDS = self.config.getint('commonConfig','NR_LEDS')
                    logging.info("NR_LEDS = " + str(configuration.NR_LEDS))     
                if "MAX_NR_DO" in self.config["commonConfig"]:
                    configuration.MAX_NR_DO = self.config.getint('commonConfig','MAX_NR_DO')
                    logging.info("MAX_NR_DO = " + str(configuration.MAX_NR_DO))                       
                if "NR_DOS" in self.config["commonConfig"]:
                    configuration.NR_DOS = self.config.getint('commonConfig','NR_DOS')
                    logging.info("NR_DOS = " + str(configuration.NR_DOS))          
                # specific simulation parameters                       
                if "NR_ASYNC_DI" in self.config["commonConfig"]:
                    configuration.NR_ASYNC_DI = self.config.getint('commonConfig','NR_ASYNC_DI')
                    logging.info("NR_ASYNC_DI = " + str(configuration.NR_ASYNC_DI))    
                    # derived value:
                    configuration.NR_SYNC_DI = configuration.NR_DIS - configuration.NR_ASYNC_DI
                    logging.info("NR_SYNC_DI (calculated as NR_DIS - NR_ASYNC_DI) = " + str(configuration.NR_SYNC_DI))    
                if "MAX_DI_COUNT" in self.config["commonConfig"]:
                    configuration.MAX_DI_COUNT = self.config.getint('commonConfig','MAX_DI_COUNT')
                    logging.info("MAX_DI_COUNT = " + str(configuration.MAX_DI_COUNT))                 
                if "DI_PER_IN_CLK_PER" in self.config["commonConfig"]:
                    configuration.DI_PER_IN_CLK_PER = self.config.getint('commonConfig','DI_PER_IN_CLK_PER')
                    logging.info("DI_PER_IN_CLK_PER = " + str(configuration.DI_PER_IN_CLK_PER))     
                if "SW_PER_IN_CLK_PER" in self.config["commonConfig"]:
                    configuration.SW_PER_IN_CLK_PER = self.config.getint('commonConfig','SW_PER_IN_CLK_PER')
                    logging.info("SW_PER_IN_CLK_PER = " + str(configuration.SW_PER_IN_CLK_PER))                      
                if "BUTTON_PER_IN_CLK_PER" in self.config["commonConfig"]:
                    configuration.BUTTON_PER_IN_CLK_PER = self.config.getint('commonConfig','BUTTON_PER_IN_CLK_PER')
                    logging.info("BUTTON_PER_IN_CLK_PER = " + str(configuration.BUTTON_PER_IN_CLK_PER))  
                if "BUTTON_TOGGLE_AUTO" in self.config["commonConfig"]:
                    configuration.BUTTON_TOGGLE_AUTO = self.config.getboolean('commonConfig','BUTTON_TOGGLE_AUTO')
                    logging.info("BUTTON_TOGGLE_AUTO = " + str(configuration.BUTTON_TOGGLE_AUTO))
                if "SWITCH_TOGGLE_AUTO" in self.config["commonConfig"]:
                    configuration.SWITCH_TOGGLE_AUTO = self.config.getboolean('commonConfig','SWITCH_TOGGLE_AUTO')
                    logging.info("SWITCH_TOGGLE_AUTO = " + str(configuration.SWITCH_TOGGLE_AUTO))                    
                # from now on we have a new filename
                self.config_filename = filename
            else:
                logging.error("Could not load config file: "+filename)
        except (configparser.NoSectionError, configparser.MissingSectionHeaderError):
            logging.error("Exception raised in init.loadConfigFile() trying to load config file!\n")
            pass
        
    def saveConfigAs(self):
        files = [ # ('All Files', '*.*'),  
                ('Ini Files', '*.ini'), 
                ('Text Document', '*.txt')] 
        filename = asksaveasfilename(initialdir="./", filetypes = files, defaultextension = files) 
        if (filename is not None) and (filename != ""): 
            self.saveConfigFile(filename)
            return os.path.basename(filename)
        else:
            return ""
            
    def saveConfig(self):
        self.saveConfigFile(self.config_filename)
        return os.path.basename(self.config_filename)
                
    def saveConfigFile(self, filename):
        self.config['myConfig']['LOG_TO_CSV'] = str(configuration.LOG_TO_CSV)
        self.config['myConfig']['LOG_ON_POWER_ON_OFF'] = str(configuration.LOG_ON_POWER_ON_OFF)
        self.config['myConfig']['LOGGING_LEVEL'] = str(configuration.LOGGING_LEVEL)
        self.config['myConfig']['FONT_SIZE_APP'] = str(configuration.FONT_SIZE_APP)
        self.config['myConfig']['SHOW_ADVANCED_SETTINGS'] = str(configuration.SHOW_ADVANCED_SETTINGS)
        self.config['myConfig']['GUI_UPDATE_PERIOD_IN_HZ'] = str(configuration.GUI_UPDATE_PERIOD_IN_HZ)
        self.config['myConfig']['SHOW_LIVE_STATUS'] = str(configuration.SHOW_LIVE_STATUS)
        self.config['myConfig']['SHOW_PLOT'] = str(configuration.SHOW_PLOT)
        self.config['myConfig']['SHOW_PERFORMANCE'] = str(configuration.SHOW_PERFORMANCE)
        self.config['myConfig']['TEXT_BOLD'] = str(configuration.TEXT_BOLD)
        self.config['myConfig']['TEXT_SIZE'] = str(configuration.TEXT_SIZE)
        self.config['myConfig']['TEXT_FAMILY'] = configuration.TEXT_FAMILY
        self.config['myConfig']['SOUND_EFFECTS'] = str(configuration.SOUND_EFFECTS)
        # simulator options
        self.config['myConfig']['KEEP_PB_PRESSED'] = str(configuration.KEEP_PB_PRESSED)
        self.config['myConfig']['RUN_FOR_CLOCK_PERIODS'] = str(configuration.RUN_FOR_CLOCK_PERIODS)        
        # common:
        self.config['commonConfig']['CLOCK_PERIOD_EXTERNAL'] = configuration.CLOCK_PERIOD_EXTERNAL
        self.config['commonConfig']['CLOCK_PERIOD_EXTERNAL_MIN_MS'] = str('%.24f' % configuration.CLOCK_PERIOD_EXTERNAL_MIN_MS).rstrip('0').rstrip('.')
        self.config['commonConfig']['RESET_FOR_SECONDS'] = str('%.24f' % configuration.RESET_FOR_SECONDS).rstrip('0').rstrip('.')
        self.config['commonConfig']['CLOCK_PERIOD_VHDL_NS'] = configuration.CLOCK_PERIOD_VHDL_NS
        self.config['commonConfig']['FILE_PATH'] = configuration.FILE_PATH
        self.config['commonConfig']['FIFO_PATH'] = configuration.FIFO_PATH
        self.config['commonConfig']['NR_DIS'] = str(configuration.NR_DIS)
        self.config['commonConfig']['MAX_NR_SW'] = str(configuration.MAX_NR_SW)
        self.config['commonConfig']['NR_SWITCHES'] = str(configuration.NR_SWITCHES)
        self.config['commonConfig']['MAX_NR_BTN'] = str(configuration.MAX_NR_BTN)        
        self.config['commonConfig']['NR_BUTTONS'] = str(configuration.NR_BUTTONS)
        self.config['commonConfig']['MAX_NR_LED'] = str(configuration.MAX_NR_LED)
        self.config['commonConfig']['NR_LEDS'] = str(configuration.NR_LEDS)
        self.config['commonConfig']['NR_DOS'] = str(configuration.NR_DOS)
        # specific simulation parameters        
        self.config['commonConfig']['NR_ASYNC_DI'] = str(configuration.NR_ASYNC_DI)        
        self.config['commonConfig']['MAX_DI_COUNT'] = str(configuration.MAX_DI_COUNT)        
        self.config['commonConfig']['DI_PER_IN_CLK_PER'] = str(configuration.DI_PER_IN_CLK_PER) 
        self.config['commonConfig']['SW_PER_IN_CLK_PER'] = str(configuration.SW_PER_IN_CLK_PER) 
        self.config['commonConfig']['BUTTON_PER_IN_CLK_PER'] = str(configuration.BUTTON_PER_IN_CLK_PER) 
        self.config['commonConfig']['BUTTON_TOGGLE_AUTO'] = str(configuration.BUTTON_TOGGLE_AUTO) 
        self.config['commonConfig']['SWITCH_TOGGLE_AUTO'] = str(configuration.SWITCH_TOGGLE_AUTO) 
        # save configuration
        with open(filename, 'w') as configfile:
            # write new settings into file
            self.config.write(configfile)
            # from now on we have a new filename
            self.config_filename = filename



