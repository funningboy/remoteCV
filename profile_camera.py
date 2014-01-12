""" profile poll_camera """

gbType = 'poll_camera2'

from multiprocessing import Process, Pipe, Queue
import timeit
import gevent
from zmq import green as zmq
import logging
from guppy import hpy
import re

if gbType in ['poll_camera']:
    from poll_camera import Server, Client
else:
    from poll_camera2 import Server, Client

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


gb_context = zmq.Context()
gb_poller = zmq.Poller()
gb_jobs = []
gb_server, gb_client = None, None

@profile
def init_server():
    global gb_context, gb_server
    gb_server = Server(gb_context)
    gb_server.setup_client('inproc://polltest1')
    gb_server.setup_camera(0, (400,300))

@profile
def init_client():
    global gb_context, gb_poller, gb_client
    gb_client = Client(gb_context, gb_poller)
    gb_client.setup_server('inproc://polltest1')

@profile
def run_capture_img():
    global gb_jobs, gb_server
    gb_jobs.append(gevent.spawn(gb_server.capture_img, 0.5, 100))

@profile
def run_send_img():
    global gb_jobs, gb_server
    gb_jobs.append(gevent.spawn(gb_server.send_img, 0.5))

@profile
def run_receive_img():
    global gb_jobs, gb_client
    gb_jobs.append(gevent.spawn(gb_client.receive_img, 0.5, 100))

@profile
def run_show_img():
    global gb_jobs, gb_client
    gb_jobs.append(gevent.spawn(gb_client.show_img, 0.5))

def server_monitor(wait=10):
    """ monitor resource usage at server side """
    global gb_server

    @profile
    def monitor(wait=0):
        pass

    while not gb_server.is_done():
        monitor()
        gevent.sleep(wait)

def client_monitor(wait=10):
    """ monitor resource usage at client side """
    global gb_client

    @profile
    def monitor(wait=0):
        pass

    while not gb_client.is_done():
        monitor()
        gevent.sleep(wait)

def run_server_monitor():
    global gb_jobs
    gb_jobs.append(gevent.spawn(server_monitor, 10))

def run_client_monitor():
    global gb_jobs
    gb_jobs.append(gevent.spawn(client_monitor, 10))

def join_all():
    global gb_jobs
    gevent.joinall(gb_jobs)

if __name__ == '__main__':
    init_client()
    init_server()

    run_capture_img()
    run_send_img()
    run_receive_img()
    run_show_img()

    run_server_monitor()
    run_client_monitor()

    join_all()

