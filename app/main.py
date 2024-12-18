import json
import mimetypes
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

# Environment variables
SOCKET_SERVER_HOST = os.getenv('SOCKET_SERVER_HOST', 'localhost')
SOCKET_SERVER_PORT = int(os.getenv('SOCKET_SERVER_PORT', 5000))
APP_PORT = int(os.getenv('APP_PORT', 3000))

# Resolve paths to ensure correct static directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to the app folder
STATIC_DIR = os.path.join(BASE_DIR, "static")  # Absolute path to static directory


class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.serve_file(os.path.join(STATIC_DIR, "index.html"), "text/html")
        elif self.path == "/message":
            self.serve_file(os.path.join(STATIC_DIR, "message.html"), "text/html")
        elif self.path.startswith("/"):
            self.serve_static_file(os.path.join(STATIC_DIR,self.path[1:]))
        else:
            self.send_error_page()

    def do_POST(self):
        """
        Handle POST requests from message.html form and forward them to the socket_server.
        """
        if self.path == "/message":
            try:
                # Retrieve the content length from headers
                content_length = int(self.headers["Content-Length"])

                # Read and decode the form data
                post_data = self.rfile.read(content_length).decode("utf-8")
                parsed_data = parse_qs(post_data)

                # Extract form fields
                username = parsed_data.get("username", ["Anonymous"])[0]
                message = parsed_data.get("message", [""])[0]

                # Log the received data (optional for debugging)
                print(f"Received POST: Username={username}, Message={message}")

                # Connect to the socket server
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((SOCKET_SERVER_HOST, SOCKET_SERVER_PORT))
                    # Send the data in "username|message" format
                    sock.sendall(f"{username}|{message}".encode('utf-8'))

                # Redirect back to /message on success
                self.send_response(302)
                self.send_header("Location", "/message")
                self.end_headers()

            except Exception as e:
                # Handle any errors that occur
                print(f"Error handling POST /message: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))
        else:
            # For unsupported POST endpoints
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Endpoint not found")


    def serve_file(self, file_path, content_type):
        try:
            with open(file_path, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error_page()

    def serve_static_file(self, file_path):
        content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        static_file_path = os.path.join(BASE_DIR, file_path)  # Ensure correct static file resolution
        self.serve_file(static_file_path, content_type)

    def send_error_page(self):
        error_file_path = os.path.join(STATIC_DIR, "error.html")
        self.serve_file(error_file_path, "text/html")


def run_http_server():
    server_address = ('', APP_PORT)
    httpd = HTTPServer(server_address, MyRequestHandler)
    print(f"HTTP Server running on port {APP_PORT}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run_http_server()