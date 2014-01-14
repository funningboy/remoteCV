

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
import timeit


def detect_edge(name, img):
    """ detect edge """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edge = cv2.Canny(gray, 500, 1000, apertureSize=5)
    img /= 2
    img[edge != 0] = (0, 255, 0)
    return name, img

def detect_circle(name, img):
    """ detect circle """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(gray, cv2.cv.CV_HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=5, maxRadius=20)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0,:]:
            cv2.circle(img, (i[0],i[1]),i[2],(0,255,0),1)
            cv2.circle(img, (i[0],i[1]),2,(0,0,255),3)
    return name, img


def detect_rectangle(name, img):
    """ detect rectangle """
    return name, img


def detect_line(name, img):
    """ detect line """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edge = cv2.Canny(gray, 150, 200, apertureSize=3)
    lines = cv2.HoughLinesP(edge, 1, np.pi/180, 150, minLineLength=100, maxLineGap=10)
    if lines is not None:
        for x1,y1,x2,y2 in lines[0]:
            cv2.line(img, (x1,y1), (x2,y2), (0,255,0), 2)
    return name, img


def detect_face(name, img):
    """ detect human face """

    def _train_data(cascade_fn='./data/haarcascades/haarcascade_frontalface_alt.xml', nested_fn='./data/haarcascades/haarcascade_eye.xml'):
        _cascade_fn = cv2.CascadeClassifier(cascade_fn)
        _nested_fn  = cv2.CascadeClassifier(nested_fn)
        return _cascade_fn, _nested_fn

    def _detect(img, cascade):
        rects = cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30), flags = cv.CV_HAAR_SCALE_IMAGE)
        if len(rects) == 0:
            return []
        rects[:,2:] += rects[:,:2]
        return rects

    def _draw_rects(img, rects, color):
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        return img

    _cascade_fn, _nested_fn = _train_data()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    rects = _detect(gray,  _cascade_fn)
    _draw_rects(img, rects, (0, 255, 0))

    for x1, y1, x2, y2 in rects:
        roi = gray[y1:y2, x1:x2]
        img_roi = img[y1:y2, x1:x2]
        subrects = _detect(roi.copy(), _nested_fn)
        img = _draw_rects(img, subrects, (255, 0, 0))
    return name, img


