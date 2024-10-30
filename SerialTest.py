import serial
import select
import sys
import termios
import tty
import struct

class MySerial(serial.Serial):
    def __init__(self, port, baud_rate):
        super().__init__(port, baud_rate, timeout=1, 
                         parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE,
                         bytesize=serial.EIGHTBITS)
    
    def write_data(self, data):
        try:
            packed_data = struct.pack(f'{len(data)}B', *data)
            self.write(packed_data)
            print(f"Sent: {packed_data}")
        except Exception as e:
            print(f"Failed to send data: {e}")
    
    def read_data(self):
        try:
            if self.in_waiting > 0:
                data = self.read(self.in_waiting)
                print(f"Received: {data}")
        except Exception as e:
            print(f"Failed {e}")

# def write_to_serial(ser, data):
#     try:
#         packed_data = struct.pack(f'{len(data)}B', *data)
#         ser.write(packed_data)
#         print(f"Sent: {packed_data}")
#     except Exception as e:
#         print(f"Failed {e}")

# def read_from_serial(ser):
#     try:
#         if ser.in_waiting > 0:
#             data = ser.read(ser.in_waiting)
#             print(f"Received: {data}")
#     except Exception as e:
#         print(f"Failed {e}")

def is_key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

def main():
    # port = "/dev/ttyAMA1"
    port = "/dev/ttyUSB0"
    baud_rate = 115200
    

    # ser = open_serial(port, baud_rate)
    ser = MySerial(port, baud_rate)
    if ser and ser.is_open:
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            print("Press 'f' to send data")
            while True:
                if is_key_pressed():
                    key = sys.stdin.read(1)
                    if key == 'f':
                        ser.write_data([0x02, 0x0d, 0x0a])
                ser.read_data()
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            ser.close()
            print("closed")

if __name__ == "__main__":
    main()
