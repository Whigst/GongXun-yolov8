import cv2

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # 画十字
        center = (frame.shape[1] // 2, frame.shape[0] // 2)     # 获取图像的中心点
        cv2.line(frame, (center[0] - 10, center[1]), (center[0] + 10, center[1]), (0, 0, 255), 1)    # 画水平线      
        cv2.line(frame, (center[0], center[1] - 10), (center[0], center[1] + 10), (0, 0, 255), 1)    # 画垂直线
        cv2.circle(frame, center, 1, (0, 0, 255), 2)    # 画圆
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()

