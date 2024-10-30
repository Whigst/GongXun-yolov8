from ultralytics import YOLO
from pyzbar.pyzbar import decode
import cv2
import time
from queue import Queue
from threading import Thread

#主要为与模型有关的类， 包括模型加载， 预测， 预加热， 处理帧
class MyYolo(Thread):
    def __init__(self, *args):
        super().__init__()  # 初始化线程
        self.model = YOLO("models/cirAndMat.engine", task='detect')  # 加载模型
        self.flag = False  # 标志位， 用于判断是否需要处理帧
        if not len(args) == 0:
            self.frame_queue = args[0]
            self.result_queue = args[1]
            self.flag = True
    
    def predict(self, source, conf, iou, imgsz):    # 预测函数
        return self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
    
    def preheating_predict(self, source, conf, iou, imgsz):    # 预加热函数
        for _ in range(100):
            self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
            
    def model_Load(self):    # 模型加载函数
        s = time.time()
        self.preheating_predict(source="ultralytics/assets/3.jpg", conf=0.90, iou=0.50, imgsz=320)
        e = time.time()
        print(f"take {e - s} seconds to load the model")
        
    def process_frame(self):    # 处理帧函数
        while True:
            if not self.frame_queue.empty():
                t1 = cv2.getTickCount()
                frame = self.frame_queue.get()
                results = self.model.predict(source=frame, conf=0.90, imgsz=320, iou=0.50)
                t2 = cv2.getTickCount()
                elapsed_time = (t2 - t1) / cv2.getTickFrequency()
                fps = int(1/elapsed_time)
                print(f"process_frames: {fps} fps")
                if not self.result_queue.full():
                    self.result_queue.put(results)
            else:
                time.sleep(0.0001)
                
    def run(self):    # 线程运行函数
        if self.flag:
            self.process_frame()
        else:
            self.model_Load()
            
#主要为与摄像头有关的类， 包括摄像头加载与二维码扫描， 捕获帧
class Capture(Thread):
    def __init__(self, *args):
        super().__init__()
        if len(args) == 2:
            self.cap = args[0]
            self.frame_queue = args[1]
        elif len(args) == 1:
            self.cap = args[0]
            self.frame_queue = None
        else:
            raise ValueError("Capture thread must be initialized with either 1 or 2 arguments")
        
    def CapLoadAndQRScan(self):    # 摄像头加载与二维码扫描函数
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
                
    def CaptureFrames(self):    # 捕获帧函数
        while self.cap.isOpened():
            if self.frame_queue.empty():
                ret, frame = self.cap.read()
                if ret and not self.frame_queue.full():
                    self.frame_queue.put(frame)
                    
    def run(self):    # 线程运行函数
        if self.frame_queue is None:
            self.CapLoadAndQRScan()
        else:
            self.CaptureFrames()

#主要为与结果处理有关的类， 包括结果合并， 结果显示
class PostProcess(Thread):
    def __init__(self, *args):
        super().__init__()
        self.merged_results_queue = args[0]
        if len(args) == 2:
            self.result_queue = args[1]
        else:
            self.result_queue = None
            
    def mergeResults(self):    # 结果合并函数
        while True:
            if not self.result_queue.empty():
                results = []
                while not self.result_queue.empty():
                    results.extend(self.result_queue.get())
                if not self.merged_results_queue.full():
                    self.merged_results_queue.put(results)
            else:
                time.sleep(0.0001)
                
    def display_results(self):    # 结果显示函数
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
                
    def run(self):    # 线程运行函数
        if self.result_queue is None:
            self.display_results()
        else:
            self.mergeResults()

#主函数， 用于初始化线程
class Main:
    def __init__(self):
        self.frame_queue = Queue(maxsize=1000)    # 帧队列
        self.result_queue = Queue(maxsize=1000)    # 结果队列
        self.merged_results_queue = Queue(maxsize=1000)    # 合并结果队列
        self.model = MyYolo()    # 模型线程， 先加载模型
        self.cap = cv2.VideoCapture("/dev/video0")    # 摄像头

    def run(self):
        t1 = Capture(self.cap)    # 捕获帧线程
        t2 = self.model
        t2.start()
        t1.start()
        t1.join()
        print("cv_Loader_And_QR_Scan finished")
        t2.join()
        print("model_Loader finished")
        print(f"{self.frame_queue.empty()}")
        t3 = Capture(self.cap, self.frame_queue)    # 捕获帧线程
        t4 = MyYolo(self.frame_queue, self.result_queue)    # 处理帧线程
        t5 = MyYolo(self.frame_queue, self.result_queue)
        t6 = MyYolo(self.frame_queue, self.result_queue)
        t7 = PostProcess(self.merged_results_queue, self.result_queue)    # 结果处理线程
        t8 = PostProcess(self.merged_results_queue)    # 结果显示线程
        t3.start()
        t4.start()
        t5.start()
        t6.start()
        t7.start()
        t8.start()

if __name__ == "__main__":
    main = Main()
    main.run()
