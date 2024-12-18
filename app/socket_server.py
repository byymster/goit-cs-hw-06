import os
import socket
from datetime import datetime
from pymongo import MongoClient

# Read environment variables
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
DB_NAME = os.getenv('DB_NAME', 'message_db')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'messages')
SOCKET_SERVER_PORT = int(os.getenv('SOCKET_SERVER_PORT', 5000))


def save_to_mongo(data):
    client = MongoClient(MONGO_HOST, MONGO_PORT)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    collection.insert_one(data)


def run_socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', SOCKET_SERVER_PORT))
    server_socket.listen(5)
    print(f"Socket Server running on port {SOCKET_SERVER_PORT}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        data = client_socket.recv(1024).decode('utf-8')
        username, message = data.split('|')
        document = {
            "date": datetime.now().isoformat(),
            "username": username.strip(),
            "message": message.strip()
        }
        save_to_mongo(document)
        client_socket.close()


if __name__ == "__main__":
    run_socket_server()