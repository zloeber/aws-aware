import os
from pprint import pprint

try:
    # python 2
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from BaseHTTPServer import HTTPServer as BaseHTTPServer
except ImportError:
    # python 3
    from http.server import HTTPServer as BaseHTTPServer, SimpleHTTPRequestHandler

PORT = 10000

class HTTPHandler(SimpleHTTPRequestHandler):
    """This handler uses server.base_path instead of always using os.getcwd()"""
    def translate_path(self, path):
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.base_path, relpath)
        return fullpath

class HTTPServer(BaseHTTPServer):
    """The main server, you pass in base_path which is the path you want to serve requests from"""
    def __init__(self, base_path, server_address, RequestHandlerClass=HTTPHandler):
        self.base_path = base_path
        BaseHTTPServer.__init__(self, server_address, RequestHandlerClass)


#Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
#Handler.extensions_map.update({
#    '.webapp': 'application/x-web-app-manifest+json',
#});
#HTTPD = SocketServer.TCPServer(("", PORT), Handler)

WEBDIR = os.path.join(os.path.dirname(__file__), '../var/www/')
HTTPD = HTTPServer(WEBDIR, ("", PORT))

#pprint('Shutting down prior running instance if found')
#try:
#    HTTPD.shutdown()
#except KeyboardInterrupt:
#    pass

pprint('Starting HTTP server.')
pprint('- Path: {0}'.format(WEBDIR))
pprint('- Port: {0}'.format(PORT))
try:
    HTTPD.serve_forever()
except KeyboardInterrupt:
    HTTPD.shutdown()
