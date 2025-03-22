import socket
import select
import threading

HOST = 'localhost'  # Replace with the target hostname or IP address
PORT = 6502            # Port to connect to (80 for HTTP)



def main():
    timeout = 0.1

    def input_loop(s):
        while True:
            ip = input() + '\n'
            if ip =='QUIT':
                exit()
            s.sendall(ip.encode("ascii"))


    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Connecting to {HOST}:{PORT}...")
        s.connect((HOST, PORT))
        print("Connected.")
        input_thread = threading.Thread(target=input_loop, args=(s,),daemon=True)
        input_thread.start()

        while True:
            ready_to_read, _, _ = select.select([s], [], [], timeout)
            if ready_to_read:
                data = s.recv(10000)
                print(data.decode('ascii'),end='')
            

if __name__ == "__main__":
    main()