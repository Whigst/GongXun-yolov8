from ultralytics import YOLO
import logging
import logging.handlers
from pyzbar.pyzbar import decode
import cv2
import time
from queue import Queue
from threading import Thread
from SerialTest import MySerial

itemColorFlag = 0
QR_Mission_Flag = 0
first_number = ''
second_number = ''
decoded_objects = []

# LOG_FORMAT = "%(asctime)s - %(levelname)s - %(thread)s - %(message)s"
# DATE_FORMAT = "%m/%d/%Y %H:%M:%S"
logger = logging.getLogger('mylogger')


# logging.basicConfig(filename="SentINFO.log", level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)

class LoggerFilter(logging.Filter):
    def __init__(self, filter_str):
        super().__init__()
        self.filter_str = filter_str

    def filter(self, record):
        return self.filter_str in record.getMessage()

#主要为与模型有关的类， 包括模型加载， 预测， 预加热， 处理帧
class MyYolo(Thread):
    def __init__(self, *args):
        super().__init__()  # 初始化线程
        self.model = YOLO("models/cirAndMat_2.engine", task='detect')  # 加载模型
        self.flag = False  # 标志位， 用于判断是否需要处理帧
        if not len(args) == 0:
            self.frame_queue = args[0]
            self.result_queue = args[1]
            self.point_queue = args[2]
            self.flag = True
    
    def predict(self, source, conf, iou, imgsz):    # 预测函数
        return self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
    
    def preheating_predict(self, source, conf, iou, imgsz):    # 预加热函数
        for _ in range(100):
            self.model.predict(source=source, conf=conf, iou=iou, imgsz=imgsz)
            
    def model_Load(self):    # 模型加载函数
        s = time.time()
        self.preheating_predict(source="ultralytics/assets/3.jpg", conf=0.75, iou=0.50, imgsz=640)
        e = time.time()
        print(f"take {e - s} seconds to load the model")
        
    def process_frame(self):    # 处理帧函数
        global itemColorFlag  # 声明使用全局变量
        while True:
            if not self.frame_queue.empty():
                t1 = cv2.getTickCount()
                frame = self.frame_queue.get()
                results = self.model.predict(source=frame, conf=0.9, imgsz=640, iou=0.50)
                min_distance = float('inf')
                min_distance_item = None
                min_item_point = None
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy.tolist()[0]
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        distance = ((center_x - frame.shape[1]/2)**2 + (center_y - frame.shape[0]/2)**2)**0.5
                        if distance < min_distance:
                            min_distance = distance
                            min_distance_item = r.names[box.cls.item()]
                            min_item_point_x = center_x
                            min_item_point_y = center_y
                if min_distance_item is not None:
                    if min_distance_item == 'redItem':
                        itemColorFlag = 1
                    elif min_distance_item == 'greenItem':
                        itemColorFlag = 2
                    elif min_distance_item == 'blueItem':
                        itemColorFlag = 3
                    elif min_distance_item == 'redcircle':
                        itemColorFlag = 4
                    elif min_distance_item == 'greencircle':
                        itemColorFlag = 5
                    elif min_distance_item == 'bluecircle':
                        itemColorFlag = 6
                    else:
                        itemColorFlag = 0
                    # print(f"Item color flag: {itemColorFlag}")
                    if not self.point_queue.full():
                        self.point_queue.put((min_item_point_x, min_item_point_y, itemColorFlag))
                t2 = cv2.getTickCount()
                elapsed_time = (t2 - t1) / cv2.getTickFrequency()
                fps = int(1/elapsed_time)
                # print(f"process_frames: {fps} fps")
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
        global logger
        global first_number
        global second_number
        global decoded_objects
        s = time.time()
        #QR_ser = MySerial("/dev/ttyUSB0", 115200)
        QR_ser = MySerial("/dev/bluetooth", 115200)
        print(self.cap.isOpened())
        print(f"\n\n{decoded_objects}\n\n")
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                decoded_objects = decode(frame)
                if decoded_objects and len(decoded_objects) > 0:
                    print(f'{first_number},{second_number},{decoded_objects}')
                    for obj in decoded_objects:
                        # print(f"Decoded Data: {obj.data.decode('utf-8')}")
                        logger.info("QR_DATA: %s", obj.data.decode('utf-8'))
                        data = obj.data.decode('utf-8')
                        numbers = data.split('+')
                        if len(numbers) == 2 and all(len(number) == 3 and number.isdigit() for number in numbers):
                            first_number = ''.join(numbers[0])
                            second_number = ''.join(numbers[1])
                            # QR_ser.write_data(first_number.encode('utf-8'))
                            # QR_ser.write_data(second_number.encode('utf-8'))
                        else:
                            # print("Invalid QR data format")
                            logger.error("Invalid QR data format")
                        # QR_ser.write_data(obj.data.decode('utf-8'))
                        # QR_data = f'c3,2,1d\r\n'.encode('utf-8')
                        QR_data = f'c{first_number[0]},{first_number[1]},{first_number[2]},{second_number[0]},{second_number[1]},{second_number[2]}b'
                        QR_ser.write_data(QR_data)
                        e = time.time()
                        # print(f"take {e - s} seconds to decode the QR")
                    data = ''
                    ret = None
                    frame = None
                    first_number = ''
                    second_number = ''
                    decoded_objects = []
                    print("\n\ncleared\n\n")
                    print(f'{first_number},{second_number},{data},{decoded_objects}')
                    break
                else:
                    continue
            else:
                print("No frame captured")
                logger.error("No frame captured")
        print("\n\n\nExited\n\n\n")

                
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
        if len(args) == 3:
            self.result_queue = args[1]
            self.point_queue = args[2]
        else:
            self.result_queue = None
            self.point_queue = None
            
    def mergeResults(self):    # 结果合并函数
        while True:
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
            if not self.merged_results_queue.empty():
                results = self.merged_results_queue.get()
                annotated_frame = results[0].plot()
                t1 = cv2.getTickCount()
                # cv2.imshow("result", annotated_frame)
                t2 = cv2.getTickCount()
                elapsed_time = (t2 - t1) / cv2.getTickFrequency()
                fps = int(1/elapsed_time)
                # print(f"display_results: {fps} fps")
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
    def __init__(self, ser, point_queue):
        super().__init__()
        self.ser = ser
        self.point_queue = point_queue
        self.last_sent_time = time.time()
    
    

    def run(self):
        global logger
        while True:
            current_time = time.time()
            if not self.point_queue.empty():
                point = self.point_queue.get()
                # Check if 0.02 seconds have passed since the last send
                if current_time - self.last_sent_time >= 0.05:
                    data = f"a{point[0]:5.1f},{point[1]:5.1f},{point[2]:d}d\r\n".encode('utf-8')
                    # data = f"a{point[0]:5.1f},{point[1]:5.1f}d\r\n".encode('utf-8')
                    self.ser.write(data)
                    # print(f"\n\n\nSent: {data}\n\n\n")
                    # logging.log(logging.INFO, "%s", data)
                    logger.info("Sent: %s", data)
                    self.last_sent_time = current_time
            else:
                time.sleep(0.0001)

class SerialRead(Thread):
    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        # self.cap_middle = cap_middle
        self.last_sent_time = time.time()
    
    def run(self):
        global QR_Mission_Flag
        while True:
            if self.ser.in_waiting:
                data = self.ser.read_data(data_type='str')
                print(f"\n\nReceived: {data}\n\n")
                if data == 'e1f':
                    QR_Mission_Flag = 0
                    print(f"\n\n{QR_Mission_Flag}\n\n")
                print(f"\n\n{QR_Mission_Flag}\n\n")
            else:
                time.sleep(2)
            
            if QR_Mission_Flag == 0:
                print("\n\n\n\n")
                cap_middle = cv2.VideoCapture("/dev/video_camera_MIDDLE")
                t1 = Capture(cap_middle)
                t1.start()
                t1.join()
                del t1
                del cap_middle
                print("\n\nt1 deleted\n\n")
                print("\n\ncv_Loader_And_QR_Scan finished\n\n")
                QR_Mission_Flag = 1
                

#主函数， 用于初始化线程
class Main:
    def __init__(self):
        self.frame_queue = Queue(maxsize=1000)    # 帧队列
        self.result_queue = Queue(maxsize=1000)    # 结果队列
        self.merged_results_queue = Queue(maxsize=1000)    # 合并结果队列
        self.point_queue = Queue(maxsize=1000)    # 中心点坐标队列
        self.model = MyYolo()    # 模型线程， 先加载模型
        #self.cap = cv2.VideoCapture("/dev/video0")    # 摄像头
        self.cap = cv2.VideoCapture("/dev/video_camera_UP")
        #self.cap = cv2.VideoCapture(0)
        # self.cap_middle = cv2.VideoCapture("/dev/video_camera_MIDDLE")
        # self.cap_middle = cv2.VideoCapture(1)
        #self.ser = MySerial("/dev/ttyUSB0", 115200)
        self.ser = MySerial("/dev/bluetooth", 115200)
    def run(self):
        global logger
        logger.setLevel(logging.DEBUG)

        SentINFO_handler = logging.FileHandler('SentINFO.log')
        SentINFO_handler.setLevel(logging.INFO)
        SentINFO_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        SentINFO_handler.addFilter(LoggerFilter("Sent"))

        QR_DATA_handler = logging.FileHandler('QRDATA.log')
        QR_DATA_handler.setLevel(logging.INFO)
        QR_DATA_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        QR_DATA_handler.addFilter(LoggerFilter("QR_DATA"))

        ERROR_handler = logging.FileHandler('ERROR.log')
        ERROR_handler.setLevel(logging.ERROR)
        ERROR_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        logger.addHandler(SentINFO_handler)
        logger.addHandler(QR_DATA_handler)
        logger.addHandler(ERROR_handler)

        # Serial_read_thread = SerialRead(self.ser, self.cap_middle)
        Serial_read_thread = SerialRead(self.ser)
        Serial_read_thread.start()
        # t1 = Capture(self.cap_middle)    # 加载cv和二维码扫描线程
        #ser_t = Thread(target=self.ser.run_serial, args=(self.point_queue,))
        t2 = self.model
        #ser_t.start()
        t2.start()
        # t1.start()
        # t1.join()
        # print("cv_Loader_And_QR_Scan finished")
        t2.join()
        print("model_Loader finished")
        print(f"{self.frame_queue.empty()}")
        t3 = Capture(self.cap, self.frame_queue)    # 捕获帧线程
        t4 = MyYolo(self.frame_queue, self.result_queue, self.point_queue)    # 处理帧线程
        t5 = MyYolo(self.frame_queue, self.result_queue, self.point_queue)
        t6 = MyYolo(self.frame_queue, self.result_queue, self.point_queue)
        # t10 = MyYolo(self.frame_queue, self.result_queue, self.point_queue)
        t7 = PostProcess(self.merged_results_queue, self.result_queue, self.point_queue)    # 结果处理线程
        t8 = PostProcess(self.merged_results_queue)    # 结果显示线程
        t9 = SerialSend(self.ser, self.point_queue)    # 串口发送线程
        t3.start()
        t4.start()
        t5.start()
        t6.start()
        # t10.start()
        t7.start()
        t8.start()
        t9.start()

if __name__ == "__main__":
    main = Main()
    main.run()
