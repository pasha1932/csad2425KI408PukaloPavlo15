import serial
import time

def run_client():
    try:
        ser = serial.Serial('COM12', 9600, timeout=1)
        print("Client is connected on COM12...")

        if ser.is_open:
            message = "Hello World!"
            ser.write(f"{message}\n".encode())
            print(f"Sent to server: {message}")

            time.sleep(1)
            response = ser.readline().decode().strip()
            print(f"Received from server: {response}")
        else:
            print("Failed to open serial port.")
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Client shutting down.")
    finally:
        ser.close()
        print("Serial port closed.")


if __name__ == "__main__":
    run_client()
