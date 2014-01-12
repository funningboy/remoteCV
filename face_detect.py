class FaceDetect(object):
    """ face detect """

    def __init__(self, cascade_fn='./data/haarcascades/haarcascade_frontalface_alt.xml', nested_fn='./data/haarcascades/haarcascade_eye.xml'):
        self._cascade = cv2.CascadeClassifier(cascade_fn)
        self._nested = cv2.CascadeClassifier(nested_fn)


    def _detect(self, img, cascade):
        rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30), flags = cv.CV_HAAR_SCALE_IMAGE)
        if len(rects) == 0:
            return []
        rects[:,2:] += rects[:,:2]
        return rects

    def _draw_rects(self, img, rects, color):
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)


    def run(self, img):
        """ run """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        rects = self._detect(gray, self._cascade)
        vis = img.copy()
        self._draw_rects(vis, rects, (0, 255, 0))
        for x1, y1, x2, y2 in rects:
            roi = gray[y1:y2, x1:x2]
            vis_roi = vis[y1:y2, x1:x2]
            subrects = self._detect(roi.copy(), self._nested)
            self._draw_rects(vis_roi, subrects, (255, 0, 0))

        cv2.imshow('facedetect', vis)
        cv2.waitKey(5)



