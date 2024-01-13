import inspect
import logging

from dotenv import load_dotenv, find_dotenv
from os import getenv
from pymongo import MongoClient
from types import TracebackType
from typing import Optional, Type

load_dotenv(find_dotenv('.env'))

client = MongoClient(getenv("MONGODB_CONNECTION_URI"))
db = client[getenv("DB_NAME")]

logger = logging.getLogger('pymongo')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='pymongo.log',
                              encoding='utf-8',
                              mode='a')
handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
logger.addHandler(handler)


class DbContext:

    def __init__(self):
        self.method_name = None

    def __enter__(self):
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        self.method_name = caller_frame.f_code.co_name
        arguments = inspect.getargvalues(caller_frame)
        logger.info(f'{self.method_name} :: {arguments.locals}')
        return db

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ):
        if exc_type and exc_value:
            logger.error(f'{self.method_name} :: {exc_type} :: {exc_value}')
