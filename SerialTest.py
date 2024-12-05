import serial
import struct

class MySerial(serial.Serial):
    def __init__(self, port, baud_rate):
        super().__init__(port, baud_rate, timeout=1, 
                         parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE,
                         bytesize=serial.EIGHTBITS)
    
    def write_data(self, data_list):
        try:
            packed_data = b''
            for data in data_list:
                if isinstance(data, float):
                    packed_data += struct.pack('f', data)  # 将浮点数打包成二进制数据
                elif isinstance(data, int):
                    packed_data += struct.pack('i', data)  # 将整数打包成二进制数据
                elif isinstance(data, str):
                    packed_data += data.encode('utf-8')  # 将字符串编码成二进制数据
                else:
                    raise ValueError("Unsupported data type")
            self.write(packed_data)
            print(f"Sent: {packed_data} (原始数据: {data_list})")
        except Exception as e:
            print(f"Failed to send data: {e}")
    
    def read_data(self, data_type):
        try:
            if data_type == 'float' and self.in_waiting >= 4:  # 浮点数占4个字节
                data = self.read(4)
                unpacked_data = struct.unpack('f', data)[0]  # 将二进制数据解包成浮点数
            elif data_type == 'int' and self.in_waiting >= 4:  # 整数占4个字节
                data = self.read(4)
                unpacked_data = struct.unpack('i', data)[0]  # 将二进制数据解包成整数
            elif data_type == 'str' and self.in_waiting > 0:
                data = self.read(self.in_waiting)  # 读取所有可用字节
                unpacked_data = data.decode('utf-8')  # 将二进制数据解码成字符串
                return unpacked_data
            else:
                return  # 如果没有足够的数据，则直接返回
            print(f"Received: {unpacked_data}")
        except Exception as e:
            print(f"Failed {e}")

    def run_serial(self, data_list):
        if self and self.is_open:
            try:
                print("Sending data...")
                self.write_data(data_list)  # 发送多个浮点数数据
                #self.write_data([123, 456])  # 发送多个整数数据
                #self.write_data(["Hello", "World"])  # 发送多个字符串数据
                # while True:
                #     self.read_data('float')
                #     self.read_data('int')
                #     self.read_data('str')
            finally:
                self.close()
                print("closed")

if __name__ == "__main__":
    ser = MySerial("/dev/ttyUSB0", 115200)
    ser.run_serial([3.14169276788, 5.21123123123])