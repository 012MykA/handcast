from threading import Thread

import cv2

from handcast.capture.camera_capture import CameraCapture

class Application:
    def __init__(self):
        self.running = True
        self.cap = CameraCapture()

    def run(self):
        while self.running:
            cv2.imshow("Camera", self.cap.get_frame())

            if cv2.waitKey(1) & 0xFF == 27:
                self.running = False

    def _capture_worker(self):
        while self.running:
            self.cap.get_frame()
