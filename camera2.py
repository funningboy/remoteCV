import cv
import time
import numpy as np
import json

cv.NamedWindow("camera", 1)
capture = cv.CreateCameraCapture(0)

width = None #leave None for auto-detection
height = None #leave None for auto-detection

if width is None:
    width = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
else:
  cv.SetCaptureProperty(capture,cv.CV_CAP_PROP_FRAME_WIDTH,width)

if height is None:
  height = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
else:
  cv.SetCaptureProperty(capture,cv.CV_CAP_PROP_FRAME_HEIGHT,height)

while True:
    #ref pycam
    img = cv.QueryFrame(capture)
    tmp = cv.CreateImage(cv.GetSize(img),cv.IPL_DEPTH_8U,3)
    #cv.CvtColor(img,tmp,cv.CV_BGR2RGB)
    cv.Copy(img,tmp)
    arr = np.asarray(cv.GetMat(tmp), dtype=np.uint8)
    msg = json.dumps({
            'size' : ','.join([str(i) for i in cv.GetSize(img)]),
            'code' : 'RGB',
            'data' : arr.tolist()})
    rec = json.loads(msg)
    size = tuple([int(i) for i in rec['size'].split(',')])
    tmp = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
    arr = cv.fromarray(np.asarray(rec['data'], dtype=np.uint8))
    cv.Copy(arr, tmp)
    cv.ShowImage("cc", tmp)
    k = cv.WaitKey(5);
    if k == 'f':
        break
