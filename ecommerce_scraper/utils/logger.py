import os
import logging

from sys import stdout

def config_logger(module_name):
    if not 'logs' in os.listdir('../'):
        os.mkdir('../logs')

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    default_formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M   ")

    file_handler = logging.FileHandler('../logs/scraper.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(default_formatter)

    console_handler = logging.StreamHandler(stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(default_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
