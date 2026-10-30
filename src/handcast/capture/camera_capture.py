import cv2


class CameraCapture:
    def __init__(self, camera_index: int = 0):
        self._open(camera_index)

    def __del__(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def get_frame(self) -> cv2.Mat:
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from camera")
        return frame

    def _open(self, camera_index: int) -> None:
        print("Init CameraCapture...")
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open cv2.VideoCapture({camera_index})")
        print("CameraCapture initialized successfully.")
