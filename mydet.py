from ultralytics import YOLO
from pyzbar.pyzbar import decode
import cv2
import time
from queue import Queue
from threading import Thread, Event
from SerialTest import MySerial

#主要为与模型有关的类， 包括模型加载， 预测， 预加热， 处理帧
class MyYolo(Thread):
    def __init__(self, *args):
        super().__init__()  # 初始化线程
        self.model = YOLO("models/cirAndMat.engine", task='detect')  # 加载模型
        self.flag = False  # 标志位， 用于判断是否需要处理帧
        if not len(args) == 0:
            self.frame_queue = args[1]
            self.result_queue = args[2]
            self.point_queue = args[3]
            self.qr_scanned_event = args[0]
            self.flag = True
    
    def predict(self, source, conf, iou, imgsz):    # 预测函数
        return self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
    
    def preheating_predict(self, source, conf, iou, imgsz):    # 预加热函数
        for _ in range(10):
            self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
            
    def model_Load(self):    # 模型加载函数
        s = time.time()
        self.preheating_predict(source="ultralytics/assets/3.jpg", conf=0.95, iou=0.50, imgsz=320)
        e = time.time()
        print(f"take {e - s} seconds to load the model")
        
    def process_frame(self):    # 处理帧函数
        while True:
            self.qr_scanned_event.wait()
            if not self.frame_queue.empty():
                t1 = cv2.getTickCount()
                frame = self.frame_queue.get()
                results = self.model.predict(source=frame, conf=0.90, imgsz=320, iou=0.50)
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy.tolist()[0]
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        if not self.point_queue.full():
                            self.point_queue.put((center_x, center_y))
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
        self.cap = args[0]
        self.qr_scanned_event = args[1]
        if len(args) == 3:
            self.frame_queue = args[2]
        else:
            self.frame_queue = None
        
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
                        self.qr_scanned_event.set()
                        e = time.time()
                        print(f"take {e - s} seconds to decode the QR")
                    break
                else:
                    continue
            else:
                break
                
    def CaptureFrames(self):    # 捕获帧函数
        self.qr_scanned_event.wait()
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
        self.qr_scanned_event = args[0]
        self.merged_results_queue = args[1]
        if len(args) == 4:
            self.result_queue = args[2]
            self.point_queue = args[3]
        else:
            self.result_queue = None
            self.point_queue = None
            
    def mergeResults(self):    # 结果合并函数
        while True:
            self.qr_scanned_event.wait()
            if not self.result_queue.empty():
                results = []
                while not self.result_queue.empty():
                    result = self.result_queue.get()
                    results.extend(result)
                    # 获取结果的中心点并放入point_queue
                    # for box in result.boxes:
                    #     x1, y1, x2, y2 = box.xyxy.tolist()[0]
                    #     center_x = (x1 + x2) / 2
                    #     center_y = (y1 + y2) / 2
                    #     self.point_queue.put((center_x, center_y))
                if not self.merged_results_queue.full():
                    self.merged_results_queue.put(results)
            else:
                time.sleep(0.0001)
                
    def display_results(self):    # 结果显示函数
        while True:
            self.qr_scanned_event.wait()
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

# 串口发送线程类
class SerialSend(Thread):
    def __init__(self, qr_scanned_event, ser, point_queue):
        super().__init__()
        self.qr_scanned_event = qr_scanned_event
        self.ser = ser
        self.point_queue = point_queue

    def run(self):
        while True:
            self.qr_scanned_event.wait()
            if not self.point_queue.empty():
                point = self.point_queue.get()
                data = f"a{point[0]:5.1f},{point[1]:5.1f}d\r\n".encode('utf-8')
                self.ser.write(data)
                print(f"Sent: {data}")
            else:
                time.sleep(0.0001)

# 守护线程类
class DaemonThread(Thread):
    def __init__(self, *args):
        super().__init__()
        self.capture_thread = args[0]
        self.qr_scanned_event = args[1]
        if len(args) == 3:
            self.frame_queue = args[2]
        else:
            self.frame_queue = None

    def run(self):
        while True:
            if not self.capture_thread.is_alive():
                print("Capture thread is not alive, restarting...")
                try:
                    self.capture_thread.cap.release()
                except:
                    pass
                self.capture_thread.cap = self.initialize_camera()
                if self.frame_queue is not None:
                    self.capture_thread = Capture(self.capture_thread.cap, self.qr_scanned_event, self.frame_queue)
                else:
                    self.capture_thread = Capture(self.capture_thread.cap, self.qr_scanned_event)
                self.capture_thread.start()
                self.qr_scanned_event.clear()
            time.sleep(1)

    def initialize_camera(self):
        for i in range(2):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"Camera {i} opened successfully")
                return cap
        raise Exception("No camera could be opened")

#主函数， 用于初始化线程
class Main:
    def __init__(self):
        self.frame_queue = Queue(maxsize=1000)    # 帧队列
        self.result_queue = Queue(maxsize=1000)    # 结果队列
        self.merged_results_queue = Queue(maxsize=1000)    # 合并结果队列
        self.point_queue = Queue(maxsize=1000)    # 中心点坐标队列
        self.model = MyYolo()    # 模型线程， 先加载模型
        self.cap = self.initialize_camera()    # 初始化摄像头
        self.ser = MySerial("/dev/ttyUSB0", 115200)
        self.qr_scanned_event = Event()
        self.qr_scanned_event.clear()
    
    def initialize_camera(self):
        for i in range(2):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"Camera {i} opened successfully")
                return cap
        raise Exception("No camera could be opened")
    
    def run(self):
        t1 = Capture(self.cap, self.qr_scanned_event)    # 加载cv和二维码扫描线程
        d1 = DaemonThread(t1, self.qr_scanned_event)    # 守护线程， 用于捕获帧线程的异常，防止摄像头路径突然改变
        #ser_t = Thread(target=self.ser.run_serial, args=(self.point_queue,))
        t2 = self.model
        #ser_t.start()
        t2.start()
        t1.start()
        d1.start()
        t1.join()
        print("cv_Loader_And_QR_Scan finished")
        t2.join()
        print("model_Loader finished")
        print(f"{self.frame_queue.empty()}")
        t3 = Capture(self.cap, self.qr_scanned_event, self.frame_queue)    # 捕获帧线程
        d2 = DaemonThread(t3, self.qr_scanned_event, self.frame_queue)    # 守护线程， 用于捕获帧线程的异常，防止摄像头路径突然改变
        t4 = MyYolo(self.qr_scanned_event, self.frame_queue, self.result_queue, self.point_queue)    # 处理帧线程
        t5 = MyYolo(self.qr_scanned_event, self.frame_queue, self.result_queue, self.point_queue)
        t6 = MyYolo(self.qr_scanned_event, self.frame_queue, self.result_queue, self.point_queue)
        t7 = PostProcess(self.qr_scanned_event, self.merged_results_queue, self.result_queue, self.point_queue)    # 结果处理线程
        t8 = PostProcess(self.qr_scanned_event, self.merged_results_queue)    # 结果显示线程
        t9 = SerialSend(self.qr_scanned_event, self.ser, self.point_queue)    # 串口发送线程
        t3.start()
        d2.start()
        t4.start()
        t5.start()
        t6.start()
        t7.start()
        t8.start()
        t9.start()
        self.qr_scanned_event.set()  # 设置事件为已扫描二维码
        

if __name__ == "__main__":
    main = Main()
    main.run()
