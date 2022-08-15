import os
import logging
from inspect import currentframe
from sys import platform
if platform == "win32":
    import win32pipe, win32file, pywintypes



# current frame
cf = currentframe()



# create a fifo (named pipe) for writing
def create_w_fifo(FILE_NAME):
    fifo_w = None
    if os.path.exists(FILE_NAME) == False:
        # Windows
        if (platform == "win32"):
            try:
                fifo_w = win32pipe.CreateNamedPipe(
                    FILE_NAME,
                    win32pipe.PIPE_ACCESS_OUTBOUND, # | win32pipe.FILE_FLAG_OVERLAPPED,  # win32pipe.PIPE_ACCESS_DUPLEX,
                    # the pipe treats the bytes written during each write operation as a message unit:
                    ##################################################################################
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT, # win32pipe.PIPE_NOWAIT,
                    # pipe as a stream of bytes:
                    ############################
                    # win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT, # win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    1, 65536, 65536,
                    win32pipe.NMPWAIT_USE_DEFAULT_WAIT,  # 0,
                    None)
            except pywintypes.error as e:
                logging.error("could not create pipe for " + FILE_NAME)
                exit(cf.f_lineno)
        # Linux
        else:
            os.mkfifo(FILE_NAME)
    # open fifos (named pipes)
    # NOTE: this is possible only after we send RESET and CLOCK to VHDL Code
    ########################################################################
    # TODO: check if we need to close them and where
    if platform == "win32":
        try:
            logging.debug("waiting for client")
            win32pipe.ConnectNamedPipe(fifo_w, None)
            logging.debug("got client")
        except:
            win32file.CloseHandle(fifo_w)
            logging.error("could not connect to pipe of " + FILE_NAME)
            exit(cf.f_lineno)
    else:
        fifo_w = open(FILE_NAME, 'w')
    # return value
    return fifo_w

# create a fifo (named pipe) for reading
def create_r_fifo(FILE_NAME):
    fifo_r = None
    if platform == "win32":
        try:
            logging.info("client, create read named_pipe = " + FILE_NAME)
            fifo_r = win32pipe.CreateNamedPipe(
                FILE_NAME,
                win32pipe.PIPE_ACCESS_INBOUND,  # win32pipe.PIPE_ACCESS_DUPLEX,
                # the pipe treats the bytes written during each write operation as a message unit:
                ##################################################################################
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                # pipe as stream of bytes:
                ##########################
                # win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                1, 65536, 65536,
                win32pipe.NMPWAIT_USE_DEFAULT_WAIT,  # 0,
                None)
            try:
                logging.info("waiting for client (or VHDL-server?) for " + FILE_NAME)
                win32pipe.ConnectNamedPipe(fifo_r, None)
                logging.info("got client for " + FILE_NAME + " with handle/fifo = " + str(fifo_r))
            except:
                logging.error("could not connect to pipe of " + FILE_NAME)
                win32file.CloseHandle(fifo_r)
                exit(cf.f_lineno)
        except pywintypes.error as e:
            if e.args[0] == 109:
                logging.error("broken pipe, bye bye")
            else:
                logging.error("Error" + str(e))
            exit(cf.f_lineno)
    else:
        if os.path.exists(FILE_NAME == False):
            os.mkfifo(FILE_NAME)
        fifo_r = open(FILE_NAME, 'r')
    # return value
    return fifo_r


