import socket
import threading
import time
from protocol import create_message, parse_message, MSG, KEEP_ALIVE, STATUS

class Client:
    def __init__(self, host, port, client_id):
        self.host = host
        self.port = port
        self.client_id = client_id  # Adicionar um identificador único para o cliente
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.keep_alive_interval = 60  # Intervalo de 60 segundos para Keep Alive
        self.keep_alive_missed = 0
        self.keep_alive_limit = 3  # Limite de 3 tentativas de Keep Alive antes de desconectar

    def start_listening(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)  # Escuta até 5 conexões pendentes
        print(f"Listening on {self.host}:{self.port}")

    def connect(self, target_host, target_port):
        # Criar um novo socket para a conexão
        connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection_socket.connect((target_host, target_port))
            print(f"Connected to {target_host}:{target_port}")
            self.send_message(create_message(STATUS, f"{self.client_id} online"), connection_socket)
            return connection_socket  # Retornar o socket conectado para comunicação
        except ConnectionRefusedError:
            print(f"Connection to {target_host}:{target_port} refused. Ensure the other client is listening.")
            connection_socket.close()
            return None

    def close_connection(self, conn=None):
        if conn:
            self.send_message(create_message(STATUS, f"{self.client_id} offline"), conn)
            conn.close()
        else:
            self.socket.close()

    def send_message(self, message, conn=None):
        try:
            message_with_id = f"{self.client_id}: {message}"  # Adicionar o identificador do cliente à mensagem
            if conn:
                conn.sendall(message_with_id.encode('utf-8'))
            else:
                self.socket.sendall(message_with_id.encode('utf-8'))
        except socket.error as e:
            print(f"Failed to send message: {e}")
            self.close_connection(conn)

    def receive_message(self, conn):
        while True:
            try:
                message = conn.recv(1024).decode('utf-8')
                if message:
                    message_type, data = parse_message(message)
                    if len(data) >= 2:
                        if message_type == MSG:
                            print(f"\n[{data[0]}]: {data[1]}")
                        elif message_type == STATUS:
                            print(f"\n[STATUS]: {data[0]} {data[1]}")
                    else:
                        print(f"\n[Malformed message]: {message}")
            except socket.error:
                print("Connection lost.")
                self.close_connection(conn)
                break

    def keep_alive(self, conn):
        while True:
            time.sleep(self.keep_alive_interval)
            try:
                self.send_message(create_message(KEEP_ALIVE, ""), conn)
            except socket.error:
                self.keep_alive_missed += 1
                if self.keep_alive_missed >= self.keep_alive_limit:
                    print("Keep Alive failed. Connection lost.")
                    self.close_connection(conn)
                    break

    def accept_connections(self):
        while True:
            conn, addr = self.socket.accept()
            print(f"New connection from {addr}")
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        while True:
            try:
                message = conn.recv(1024).decode('utf-8')
                if message:
                    message_type, data = parse_message(message)
                    if len(data) >= 2:
                        if message_type == MSG:
                            print(f"\n[{data[0]}]: {data[1]}")
                        elif message_type == STATUS:
                            print(f"\n[STATUS]: {data[0]} {data[1]}")
                    else:
                        print(f"\n[Malformed message]: {message}")
            except socket.error:
                print("Connection with client lost.")
                conn.close()
                break

    def start(self):
        # Permitir que o usuário escolha a porta ao escutar
        listening_port = int(input("Enter the listening port (different from the target port): "))
        self.port = listening_port
        self.start_listening()
        threading.Thread(target=self.accept_connections, daemon=True).start()

        # Conectar ao outro cliente
        try:
            target_host = input("Enter the target host IP: ")
            target_port = int(input("Enter the target port: "))
            if target_host and target_port:
                connection_socket = self.connect(target_host, target_port)
                if connection_socket:
                    threading.Thread(target=self.receive_message, args=(connection_socket,), daemon=True).start()
                    threading.Thread(target=self.keep_alive, args=(connection_socket,), daemon=True).start()

                    while True:
                        message = input("Enter message: ")
                        if message.lower() == "exit":
                            self.close_connection(connection_socket)
                            break
                        self.send_message(create_message(MSG, message), connection_socket)
        except KeyboardInterrupt:
            self.close_connection()

if __name__ == "__main__":
    client_id = input("Enter your client ID: ")  # Solicitar o identificador do cliente
    client = Client("localhost", 5000, client_id)
    client.start()
