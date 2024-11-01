import socket
import cv2

class UDPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cap = cv2.VideoCapture(0)

    def send_frame(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture image")
                break

            # 压缩图像
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = imgencode.tobytes()

            # 发送图像
            self.sock.sendto(data, (self.server_ip, self.server_port))
            print("Frame sent")

            # 显示图像
            cv2.imshow('Client', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    client = UDPClient("192.168.1.192", 12345)
    client.send_frame()
