from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui.mainWindow import MainWindow
import sys
import configuration
import logging
import configparser



def initConfig():
    # configuration parameters determined during initialization from .ini file:
    ###########################################################################
    logging.info("main.py: load config.ini file.")
    config = configparser.ConfigParser(allow_no_value=True)
    config_filename = configuration.PATH_PREFIX + configuration.CONFIG_FILENAME
    # Load the configuration file (to read only a few parameters here, rest read in init.py)
    ########################################################################################
    logging.info("main.py: reading "+config_filename)
    try:
        config.read(config_filename)
        logging.info("sections: " +  str(config.sections()))
        if "myConfig" in config:
            logging.info("keys in section myConfig:")
            if "LOGGING_LEVEL" in config["myConfig"]:
                configuration.LOGGING_LEVEL = config['myConfig']['LOGGING_LEVEL']
                logging.info("LOGGING_LEVEL = " + configuration.LOGGING_LEVEL)
            if "FONT_SIZE_APP" in config["myConfig"]:
                    configuration.FONT_SIZE_APP = int(config['myConfig']['FONT_SIZE_APP'])
                    logging.info("FONT_SIZE_APP = " +  str(int(config['myConfig']['FONT_SIZE_APP'])))
    except (configparser.NoSectionError, configparser.MissingSectionHeaderError):
        logging.error("Exception raised in main.py trying to load config file!\n")
        pass
    logging_level = logging.INFO
    if configuration.LOGGING_LEVEL == "logging.DEBUG":
        logging_level = logging.DEBUG
    if configuration.LOGGING_LEVEL == "logging.INFO":
        logging_level = logging.INFO
    if configuration.LOGGING_LEVEL == "logging.WARNING":
        logging_level = logging.WARNING
    if configuration.LOGGING_LEVEL == "logging.ERROR":
        logging_level = logging.ERROR
    if configuration.LOGGING_LEVEL == "logging.CRITICAL":
        logging_level = logging.CRITICAL    
    # if the severity level is INFO, the logger will handle only INFO, WARNING, ERROR, and CRITICAL messages and will ignore DEBUG messages
    # log with details
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s', datefmt='%H:%M:%S', level=logging_level)
    # start logger
    logging.info("set logging level to " + configuration.LOGGING_LEVEL)

def main():
    logging.info("entering main()..")
    initConfig()
    app = QApplication(sys.argv)
    app.setStyleSheet('QMainWindow{border-color: darkgray;border: 1px solid black;}')
    font = QFont()
    font.setPointSize(configuration.FONT_SIZE_APP)
    app.setFont(font) 
    ui = MainWindow(app)
    ui.show()
    ui.activateWindow() # to bring window to foreground
    # NOTE: this needs to be called in the "main loop":
    ui.plotThread()
    # NOTE: because of the previous call to ui.plotThread() this point is actually never reached
    sys.exit(app.exec_())
    logging.info("leaving main()..")

# call main()
if __name__=="__main__":
   main()
   logging.info("main() left!")

    


