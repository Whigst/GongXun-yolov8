from ultralytics import YOLO
from pyzbar.pyzbar import decode
import cv2
import time
from queue import Queue
from threading import Thread

frame_queue = Queue(maxsize=1000)
result_queue = Queue(maxsize=1000)
merged_results_queue = Queue(maxsize=1000)

# Load YOLO model
def model_Loader():
    s = time.time()
    global model
    model = YOLO("models/cirAndMat.engine", task='detect')
    for _ in range(100):
        model.predict(source="ultralytics/assets/3.jpg", conf=0.90, iou=0.50, imgsz=320)
    e = time.time()
    print(f"take {e - s} seconds to load the model")

# Load cv and decode QR
def cv_Loader_And_QR_Scan():
    s = time.time()
    global cap
    cap = cv2.VideoCapture("/dev/video1")
    print(cap.isOpened())
    while cap.isOpened():
        ret, frame = cap.read()
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

#capture frames
def capture_frames():
    global cap
    while cap.isOpened():
        if frame_queue.empty():
            ret, frame = cap.read()
            if ret and not frame_queue.full():
                frame_queue.put(frame)

#process frames
def process_frames():
    while True:
        if not frame_queue.empty():
            t1 = cv2.getTickCount()
            frame = frame_queue.get()
            results = model.predict(source=frame, conf=0.90, imgsz=320, iou=0.50)
            t2 = cv2.getTickCount()
            elapsed_time = (t2 - t1) / cv2.getTickFrequency()
            fps = int(1/elapsed_time)
            print(f"process_frames: {fps} fps")
            if not result_queue.full():
                result_queue.put(results)
        else:
            time.sleep(0.0001)

#merge results
def merge_results():
    while True:
        if not result_queue.empty():
            results = []
            while not result_queue.empty():
                results.extend(result_queue.get())
            if not merged_results_queue.full():
                merged_results_queue.put(results)
        else:
            time.sleep(0.0001)

#display results
def display_results():
    while True:
        if not merged_results_queue.empty():
            results = merged_results_queue.get()
            # for result in results:
            #     if result.boxes.id is not None:
            #         print(f"aaaaaaaaaaaaaaaaaaaaaaaaa{result.boxes.id.cpu().numpy().astype(int)}")
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

def main():
    t1 = Thread(target=cv_Loader_And_QR_Scan)
    t2 = Thread(target=model_Loader)
    t2.start()
    t1.start()
    t1.join()
    print("cv_Loader_And_QR_Scan finished")
    t2.join()
    print("model_Loader finished")
    print(f"{frame_queue.empty()}")
    t3 = Thread(target=capture_frames)
    t4 = Thread(target=process_frames)
    t5 = Thread(target=process_frames)
    t6 = Thread(target=process_frames)
    t7 = Thread(target=merge_results)
    t8 = Thread(target=display_results)
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    t7.start()
    t8.start()
    

if __name__ == "__main__":
    main()
