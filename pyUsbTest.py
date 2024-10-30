import serial

def open_serial(port, baud_rate):
    try:
        ser = serial.Serial(port, baud_rate, timeout=1, 
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS)
        if ser.is_open:
            print(f"Serial port {port} opened")
        return ser
    except Exception as e:
        print(f"Failed {e}")
        return None

def write_to_serial(ser, data):
    try:
        ser.write(data)
        print(f"Sent: {data}")
    except Exception as e:
        print(f"Failed {e}")

def main():
    # port = "/dev/ttyAMA1"
    port = "/dev/ttyUSB0"
    baud_rate = 115200

    ser = open_serial(port, baud_rate)
    if ser and ser.is_open:
        try:
            while True:
                write_to_serial(ser, b"Hello")
        finally:
            ser.close()
            print("closed")

if __name__ == "__main__":
    main()
