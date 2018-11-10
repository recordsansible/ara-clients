import django
from django.core.servers.basehttp import ServerHandler as BaseServerHandler, WSGIRequestHandler


class ServerHandler(BaseServerHandler):
    def cleanup_headers(self):
        super().cleanup_headers()
        self.headers["Connection"] = "close"


class QuietWSGIRequestHandler(WSGIRequestHandler):
    def log_message(*args):
        pass

    # Django 2.2 fixes keep-alive support again, which should result in a performance
    # gain. For now we just disable keep-alive to be on the safe side.
    # See https://github.com/django/django/commit/934acf1126995f6e6ccba5947ec8f7561633c27f
    # for details on when keep-alive is usable.
    if django.VERSION < (2, 2):

        def handle(self):
            """Copy of WSGIRequestHandler.handle() but with different ServerHandler"""
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ""
                self.request_version = ""
                self.command = ""
                self.send_error(414)
                return

            if not self.parse_request():  # An error code has been sent, just exit
                return

            handler = ServerHandler(self.rfile, self.wfile, self.get_stderr(), self.get_environ())
            handler.request_handler = self  # backpointer for logging
            handler.run(self.server.get_app())
