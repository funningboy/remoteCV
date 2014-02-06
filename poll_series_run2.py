"""
    multithreaded remoteCV edge processing sample
"""
import gevent
from zmq import green as zmq
import numpy as np
import cv2
import cv
from multiprocessing.pool import ThreadPool
from multiprocessing import Process
from collections import deque
from poll_camera2 import Server, Client
from poll_detect import *
from profile import *
import timeit



class NewServer(Server):
    """ new server """

    def __init__(self, context):
        super(NewServer, self).__init__(context)


class NewClient(Client):
    """ new client """

    def __init__(self, context, poller):
        super(NewClient, self).__init__(context, poller)

    def run_img(self, wait=0.5):
        """ run img proc """
        img_it = self.fetch_img()

        task_map = { 'detect_edge' : detect_edge,
                     'detect_line' : detect_lineP,
                     'detect_circle': detect_circle,
                     'detect_face' : detect_face }

        for img in img_it:
            for key, val in task_map.items():
                name, res = task_map[key](key, img.copy())

                cv2.imshow(name, res)

                ch = cv2.waitKey(1)
                gevent.sleep(wait)

gb_context = zmq.Context()
gb_poller = zmq.Poller()
gb_jobs = []
gb_server, gb_client = None, None

@profile
def init_server():
    global gb_context, gb_server
    gb_server = NewServer(gb_context)
    gb_server.setup_client('inproc://polltest1')
    gb_server.setup_camera(0, (400,300))

@profile
def init_client():
    global gb_context, gb_poller, gb_client
    gb_client = NewClient(gb_context, gb_poller)
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

@profile
def run_img():
    global gb_jobs, gb_client
    gb_jobs.append(gevent.spawn(gb_client.run_img, 0.5))

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
    run_img()

    run_server_monitor()
    run_client_monitor()

    join_all()

