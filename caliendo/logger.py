import logging

def get_logger(name):
    logging.captureWarnings(True)
    format = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=format)
    return logging.getLogger(name)