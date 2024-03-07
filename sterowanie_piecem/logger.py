import logging

from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler('../app.log', when="midnight", backupCount=7)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('MyLogger')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)