import sys
import logging

logger = logging.getLogger('pygaps')
logger.setLevel(logging.DEBUG)

# create console handler
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)

# add the handlers to the logger
logger.addHandler(ch)
