import sys
import os
import logging
import traceback

# Set up logging to a file
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'application.log')
logging.basicConfig(level=logging.ERROR, filename=log_file, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Set up global exception handling
def log_uncaught_exceptions(ex_cls, ex, tb):
    logger.critical(''.join(traceback.format_tb(tb)))
    logger.critical('{0}: {1}'.format(ex_cls, ex))


sys.excepthook = log_uncaught_exceptions
