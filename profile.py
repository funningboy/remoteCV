""" profile """


import timeit
import logging
from guppy import hpy
import re

#__all__ =
reSIZE = re.compile(r"Total size = (\d+) bytes", re.M)

logging.basicConfig(filename='profile_remotecv.log',level=logging.DEBUG)


def profile(func): #decorator **kwargs
    """ profile running time and logging it """

    def wrapper(*args, **kwargs): # func *args, **kwargs
        """ profile run time """
        t = timeit.Timer()
        retval = func(*args, **kwargs)
        hp = hpy()
        found = reSIZE.findall(str(hp.heap()))
        logging.info("call func %s", func.__name__)
        logging.info("  run time %f s", t.timeit())
        logging.info("  run mem %d bytes", int(found[0]))
    return wrapper

