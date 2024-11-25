import serial

def run_server():
    try:
        ser = serial.Serial('COM11', 9600, timeout=1)
        print("Server is running on COM11...")

        while True:

            if ser.in_waiting > 0:

                message = ser.readline().decode().strip()
                print(f"Received from client: {message}")


                modified_message = message.upper() + " Connected to Server"
                ser.write(f"{modified_message}\n".encode())
                print(f"Sent to client: {modified_message}")
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        ser.close()
        print("Serial port closed.")

if __name__ == "__main__":
    run_server()
