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
import timeit



class NewServer(Server):
    """ new server """

    def __init__(self, context):
        super(NewServer, self).__init__(context)


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

                cv2.imshow(name, res)

                ch = cv2.waitKey(1)
                gevent.sleep(wait)

            if len(self._pending) < self._threadn:
                tasks = [ self._pool.apply_async(detect_edge, ('detect_edge', img.copy())),
                          self._pool.apply_async(detect_line, ('detect_line', img.copy())),
                          self._pool.apply_async(detect_circle, ('detect_circle', img.copy())),
                          self._pool.apply_async(detect_face, ('detect_face', img.copy())) ]

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

