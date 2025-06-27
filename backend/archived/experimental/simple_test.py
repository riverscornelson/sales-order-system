#!/usr/bin/env python3
import http.server
import socketserver
import json

class SimpleHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = json.dumps({"status": "healthy", "message": "Simple server working"})
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    PORT = 8001
    with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
        print(f"🚀 Simple test server at http://127.0.0.1:{PORT}")
        print(f"🏥 Health check: http://127.0.0.1:{PORT}/health")
        httpd.serve_forever()