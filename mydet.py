from ultralytics import YOLO
from pyzbar.pyzbar import decode
import cv2
import time
from queue import Queue
from threading import Thread

class MyYolo(Thread):
    def __init__(self):
        super().__init__()
        self.model = YOLO("models/cirAndMat.engine", task='detect')
    def predict(self, source, conf, iou, imgsz):
        return self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
    def preheating_predict(self, source, conf, iou, imgsz):
        for _ in range(100):
            self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
    def model_Load(self):
        s = time.time()
        self.preheating_predict(source="ultralytics/assets/3.jpg", conf=0.90, iou=0.50, imgsz=320)
        e = time.time()
        print(f"take {e - s} seconds to load the model")
    def run(self):
        self.model_Load()

class CVLoaderAndQRScan(Thread):
    def __init__(self, cap):
        super().__init__()
        self.cap = cap
    def run(self):
        s = time.time()
        print(self.cap.isOpened())
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                decoded_objects = decode(frame)
                if decoded_objects and len(decoded_objects) > 0:
                    for obj in decoded_objects:
                        print(f"Decoded Data: {obj.data.decode('utf-8')}")
                        e = time.time()
                        print(f"take {e - s} seconds to decode the QR")
                    break
                else:
                    continue
            else:
                print("No frame captured")

class CaptureFrames(Thread):
    def __init__(self, cap, frame_queue):
        super().__init__()
        self.cap = cap
        self.frame_queue = frame_queue
    def run(self):
        while self.cap.isOpened():
            if self.frame_queue.empty():
                ret, frame = self.cap.read()
                if ret and not self.frame_queue.full():
                    self.frame_queue.put(frame)

class ProcessFrames(Thread):
    def __init__(self, model, frame_queue, result_queue):
        super().__init__()
        self.model = model
        self.frame_queue = frame_queue
        self.result_queue = result_queue
    def run(self):
        while True:
            if not self.frame_queue.empty():
                t1 = cv2.getTickCount()
                frame = self.frame_queue.get()
                results = self.model.model.predict(source=frame, conf=0.90, imgsz=320, iou=0.50)
                t2 = cv2.getTickCount()
                elapsed_time = (t2 - t1) / cv2.getTickFrequency()
                fps = int(1/elapsed_time)
                print(f"process_frames: {fps} fps")
                if not self.result_queue.full():
                    self.result_queue.put(results)
            else:
                time.sleep(0.0001)

class MergeResults(Thread):
    def __init__(self, result_queue, merged_results_queue):
        super().__init__()
        self.result_queue = result_queue
        self.merged_results_queue = merged_results_queue
    def run(self):
        while True:
            if not self.result_queue.empty():
                results = []
                while not self.result_queue.empty():
                    results.extend(self.result_queue.get())
                if not self.merged_results_queue.full():
                    self.merged_results_queue.put(results)
            else:
                time.sleep(0.0001)

class DisplayResults(Thread):
    def __init__(self, merged_results_queue):
        super().__init__()
        self.merged_results_queue = merged_results_queue
    def run(self):
        while True:
            if not self.merged_results_queue.empty():
                results = self.merged_results_queue.get()
                annotated_frame = results[0].plot()
                t1 = cv2.getTickCount()
                cv2.imshow("result", annotated_frame)
                t2 = cv2.getTickCount()
                elapsed_time = (t2 - t1) / cv2.getTickFrequency()
                fps = int(1/elapsed_time)
                print(f"display_results: {fps} fps")
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                time.sleep(0.0001)

class Main:
    def __init__(self):
        self.frame_queue = Queue(maxsize=1000)
        self.result_queue = Queue(maxsize=1000)
        self.merged_results_queue = Queue(maxsize=1000)
        self.model = MyYolo()
        self.cap = cv2.VideoCapture("/dev/video1")

    def run(self):
        t1 = CVLoaderAndQRScan(self.cap)
        #t2 = ModelLoader(self.model)
        t2 = self.model
        t2.start()
        t1.start()
        t1.join()
        print("cv_Loader_And_QR_Scan finished")
        t2.join()
        print("model_Loader finished")
        print(f"{self.frame_queue.empty()}")
        t3 = CaptureFrames(self.cap, self.frame_queue)
        t4 = ProcessFrames(self.model, self.frame_queue, self.result_queue)
        t5 = ProcessFrames(self.model, self.frame_queue, self.result_queue)
        t6 = ProcessFrames(self.model, self.frame_queue, self.result_queue)
        t7 = MergeResults(self.result_queue, self.merged_results_queue)
        t8 = DisplayResults(self.merged_results_queue)
        t3.start()
        t4.start()
        t5.start()
        t6.start()
        t7.start()
        t8.start()

if __name__ == "__main__":
    main = Main()
    main.run()
