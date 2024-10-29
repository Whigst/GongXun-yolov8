from ultralytics import YOLO
import cv2
model = YOLO('./models/cirAndMat.engine', task='detect')

# Open the video file as source
# video_path = "0"#该为你要推理的视频路径
# cap = cv2.VideoCapture(int(video_path))

#use camera
cap = cv2.VideoCapture("/dev/video0")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
cap.set(cv2.CAP_PROP_FPS,30)

# Loop through the video frames
count=0
max_id=0
font = cv2.FONT_HERSHEY_SIMPLEX
while cap.isOpened():

    t1 = cv2.getTickCount()
    # Read a frame from the video
    success, frame = cap.read()

    if success:
        # Run YOLOv8 tracking on the frame, persisting tracks between frames
        results=model.predict(source=frame, conf=0.90, imgsz=320)

        for result in results:
            if result.boxes.id is not None:
                print(result.boxes.id.cpu().numpy().astype(int))
                if count<result.boxes.id.cpu().numpy().astype(int)[-1]:
                    count=result.boxes.id.cpu().numpy().astype(int)[-1]

        # Visualize the results on the frame
        annotated_frame = results[0].plot()
        #fps
        t2 = cv2.getTickCount()
        time = (t2 - t1) / cv2.getTickFrequency()
        fps = int(1/time)
        #plot annotate
        cv2.putText(annotated_frame,"total %d"%count,[40,40], cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0))
        cv2.putText(annotated_frame, "fps %d" % fps, [40, 80], cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0))
        # Display the annotated frame
        #cv2.imshow("YOLOv8 onnx Tracking", annotated_frame)
        cv2.imshow("result", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
