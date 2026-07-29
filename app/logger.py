import logging
import sys
import contextvars

# 1. Create a ContextVar. This acts like a global variable, but it is strictly 
# isolated per active FastAPI request so different users' logs don't mix.
request_logs = contextvars.ContextVar("request_logs", default=[])

class BrowserNetworkHandler(logging.Handler):
    def emit(self, record):
        # Intercept the log, format it, and append it to the current request bucket
        msg = self.format(record)
        current_logs = request_logs.get()
        request_logs.set(current_logs + [msg])

def setup_logger(name="Ticketing_Logger"):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%H:%M:%S"
    )

    # storing logs in a file
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # Standard Terminal Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Attach our Custom Browser Handler
    network_handler = BrowserNetworkHandler()
    network_handler.setLevel(logging.DEBUG) # Catch everything
    # We use a simpler formatter for the network tab to keep headers clean
    network_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(network_handler)


    return logger

logger = setup_logger()
