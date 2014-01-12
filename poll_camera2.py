""" remoteCV
1. can add retry feature in timeout case
"""

import gevent
from zmq import green as zmq
import numpy as np
import cv2
import json
import timeit


GBDEBUG = False

def debug(msg):
    global GBDEBUG
    if GBDEBUG:
        print msg


class Server(object):
    """ broadcast vedio source to it's client"""

    def __init__(self, context):
        self._context = context
        self._socket = self._context.socket(zmq.PUSH)
        self._img = []
        self._capture = None
        self._stop_imgs = { 'capture' : 100,
                            'send'    : 100 }
        self._cur_img = { 'capture' : 0,
                          'send'    : 0 }

    def is_done(self):
        return self._stop_imgs == self._cur_img

    def setup_client(self, addr='inproc://polltest1'):
        """ """
        self._socket.connect(addr)

    def setup_camera(self, indx=0, size=(400, 300)):
        """ setup camera
            indx = tty/usb device id
            size = img width, high
        """
        capture = cv2.VideoCapture(indx)
        capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, size[0])
        capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, size[1])
        self._capture = capture

    def capture_img(self, wait=0.5, max_img=100):
        """ capture img from img buffer and store it in img queue """
        while self._stop_imgs['capture'] >= self._cur_img['capture']:
            ret, img = self._capture.read()
            msg = json.dumps({
                'size' : img.shape[0:-1],
                'code' : 'BGR',
                'data' : img.tolist()})
            self._img.append(msg)
            # constraint the img buf size
            if len(self._img) >= max_img:
                self._img.pop()
            self._cur_img['capture']+=1
            debug("server capture img")
            gevent.sleep(wait)

    def send_img(self, wait=0.5):
        """ send img from img queue """
        while self._stop_imgs['send'] >= self._cur_img['send']:
            if self._img:
                msg = self._img.pop()
                self._socket.send(msg)
                self._cur_img['send']+=1
                debug("server send img")
                gevent.sleep(wait)


class Client(object):
    """ client """

    def __init__(self, context, poller):
        self._context = context
        self._poller  = poller
        self._img = []
        self._rec = None
        self._stop_imgs = { 'receive' : 100,
                            'show' : 100 }
        self._cur_img = { 'receive' : 0,
                          'show' : 0 }

    def is_done(self):
        return self._stop_imgs == self._cur_img

    def setup_server(self, addr='inproc://polltest1'):
        """ create zmq context and bind to pull socketes """
        """ create poller and register receicer sockets """
        rec = self._context.socket(zmq.PULL)
        rec.bind(addr)
        self._poller.register(rec, zmq.POLLIN)
        self._rec = rec


    def receive_img(self, wait=0.5, max_img=100):
        """ receive img from zmq socket """
        while self._stop_imgs['receive'] >= self._cur_img['receive']:
            socks = dict(self._poller.poll())
            if self._rec in socks and socks[self._rec] == zmq.POLLIN:
                img = json.loads(self._rec.recv())
                arr = np.asarray(img['data'], dtype=np.uint8)
                self._img.append(arr)
                if len(self._img) >= max_img:
                    self._img.pop()
                self._cur_img['receive']+=1
                debug("client receive img")
                gevent.sleep(wait)


    def fetch_img(self, wait=0.5):
        while self._stop_imgs['show'] >= self._cur_img['show']:
            if self._img:
                yield self._img.pop()
                self._cur_img['show']+=1
                gevent.sleep(wait)


    def show_img(self, wait=0.5):
        """ show img """
        while self._stop_imgs['show'] >= self._cur_img['show']:
            if self._img:
                tmp = self._img.pop()
                debug("client show img")
                cv2.imshow("cc", tmp)
                self._cur_img['show']+=1
                cv2.waitKey(1)
                gevent.sleep(wait)


if __name__ == '__main__':

    context = zmq.Context()
    poller = zmq.Poller()
    # client side
    client = Client(context, poller)
    client.setup_server('inproc://polltest1')

    # server side
    server = Server(context)
    server.setup_client('inproc://polltest1')
    server.setup_camera(0, (400,300))

    # spawn all jobs
    jobs = [ gevent.spawn(server.capture_img, 0.5, 100),
             gevent.spawn(server.send_img, 0.5),
             gevent.spawn(client.receive_img, 0.5, 100),
             gevent.spawn(client.show_img, 0.5) ]

    gevent.joinall(jobs)

