

"""
    multithreaded remoteCV edge processing sample
"""
import gevent
from zmq import green as zmq
import numpy as np
import cv2
from multiprocessing.pool import ThreadPool
from multiprocessing import Process
from collections import deque
from poll_camera2 import Server, Client
import timeit

class NewServer(Server):
    """ new server """

    def __init__(self, context):
        super(NewServer, self).__init__(context)


def detect_edge(name, img, thrs1, thrs2):
    """ detect edge """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edge = cv2.Canny(gray, thrs1, thrs2, apertureSize=5)
    vis = img.copy()
    vis /= 2
    vis[edge != 0] = (0, 255, 0)
    return name, vis

def detect_circle(name):
    """ detect circle """
    pass

class NewClient(Client):
    """ new client """

    def __init__(self, context, poller):
        super(NewClient, self).__init__(context, poller)

        self._threadn = cv2.getNumberOfCPUs()
        self._pool = ThreadPool(processes = self._threadn)
        self._pending = deque()


    def run_img(self, wait=0.5):
        """ run img proc """
        img_it = self.fetch_img()

        for img in img_it:
            while len(self._pending) >0 and self._pending[0].ready():
                name, res = self._pending.popleft().get()

                if name == 'proc0':
                    cv2.imshow('thread proc0', res)
                elif name == 'proc1':
                    cv2.imshow('thread proc1', res)

                ch = cv2.waitKey(1)
                gevent.sleep(wait)

            if len(self._pending) < self._threadn:
                tasks = [ self._pool.apply_async(detect_edge, ('proc0', img.copy(), 200, 400)),
                          self._pool.apply_async(detect_edge, ('proc1', img.copy(), 10, 100)) ]

            [self._pending.append(task) for task in tasks]


if __name__ == '__main__':

    context = zmq.Context()
    poller = zmq.Poller()
    # client side
    client = NewClient(context, poller)
    client.setup_server('inproc://polltest1')

    # server side
    server = NewServer(context)
    server.setup_client('inproc://polltest1')
    server.setup_camera(0, (400,300))

    # spawn all jobs
    jobs = [ gevent.spawn(server.capture_img, 0.5, 100),
             gevent.spawn(server.send_img, 0.5),
             gevent.spawn(client.receive_img, 0.5, 100),
             gevent.spawn(client.run_img, 0.5) ]

    gevent.joinall(jobs)

