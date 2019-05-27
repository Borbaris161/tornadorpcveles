#!/usr/bin/env python
# -*- coding: utf-8

import traceback
import tornado.wsgi
import tornado.web
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop

import jsonrpclibveles.payload
from jsonrpclibveles.server.utils import getcallargs

TYPES = (list, tuple)


class Config(object):
    verbose = True
    short_errors = True

config = Config()

class BaseRPCParser(object):

    def __init__(self, library, encode=None, decode=None):
        self.library = library
        if not encode:
            encode = getattr(library, 'dumps')
        if not decode:
            decode = getattr(library, 'loads')
        self.encode = encode
        self.decode = decode
        self.requests_in_progress = 0
        self.responses = []

    @property
    def faults(self):
        return Faults(self)

    def run(self, handler, request_body):
        self.handler = handler
        try:
            requests = self.parse_request(request_body)
        except:
            self.traceback()
            return self.handler.result(self.faults.parse_error())
        if not isinstance(requests, tuple):
            if isinstance(requests, str):
                return requests
            elif hasattr(requests, 'response'):
                return requests.response()
            elif hasattr(requests, 'faultCode'):
                return self.handler.result(requests)
            else:
                return requests
        self.handler._requests = len(requests)
        if len(requests) == 1:
            for request in requests:
                self.dispatch(request[0], request[1])

    def dispatch(self, method_name, params):
        if hasattr(tornado.web.RequestHandler, method_name):
            return self.handler.result(self.faults.method_not_found())
        method = self.handler
        method_list = dir(method)
        method_list.sort()
        attr_tree = method_name.split('.')
        try:
            for attr_name in attr_tree:
                method = self.check_method(attr_name, method)
        except AttributeError:
            return self.handler.result(self.faults.method_not_found())
        if not callable(method):
            return self.handler.result(self.faults.method_not_found())
        if method_name.startswith('_') or \
                getattr(method, 'private', False) is True:
            return self.handler.result(self.faults.method_not_found())
        args = []
        kwargs = {}
        if isinstance(params, dict):
            kwargs = params
        elif type(params) in (list, tuple):
            args = params
        else:
            return self.handler.result(self.faults.invalid_params())
        try:
            final_kwargs, extra_args = getcallargs(method, *args, **kwargs)
        except TypeError:

            return self.handler.result(self.faults.invalid_params())
        try:
            response = method(*extra_args, **final_kwargs)
        except Exception:
            self.traceback(method_name, params)
            return self.handler.result(self.faults.internal_error())
        return self.handler.result(response)

    def response(self, handler):
        handler._requests -= 1
        if handler._requests > 0:
            return
        if handler._RPC_finished:
            raise Exception("Error trying to send response twice.")
        handler._RPC_finished = True
        responses = tuple(handler._results)
        response_text = self.parse_responses(responses)
        if type(response_text) is not str:
            response_text = self.encode(response_text)
        handler.on_result(response_text)

    def traceback(self, method_name='REQUEST', params=[]):
        err_lines = traceback.format_exc().splitlines()
        err_title = "ERROR IN %s" % method_name
        if len(params) > 0:
            err_title = '%s - (PARAMS: %s)' % (err_title, repr(params))
        err_sep = ('-'*len(err_title))[:79]
        err_lines = [err_sep, err_title, err_sep]+err_lines
        if config.verbose:
            if len(err_lines) >= 7 and config.short_errors:
                print('\n'.join(err_lines[0:4]+err_lines[-3:]))
            else:
                print('\n'.join(err_lines))
        return

    def parse_request(self, request_body):
        return ([], [])

    def parse_responses(self, responses):
        return self.encode(responses)

    def check_method(self, attr_name, obj):
        if attr_name.startswith('_'):
            raise AttributeError('Private object or method.')
        attr = getattr(obj, attr_name)

        if getattr(attr, 'private', False):
            raise AttributeError('Private object or method.')
        return attr

class BaseRPCRequestHandler(tornado.web.RequestHandler):

    _RPC_ = None
    _results = None
    _requests = 0
    _RPC_finished = False

    def post(self):
        self._results = []
        request_body = self.request.body
        self._RPC_.run(self, request_body)

    def result(self, result, *results):
        if results:
            results = [result] + results
        else:
            results = result
        self._results.append(results)
        self._RPC_.response(self)

    def on_result(self, response_text):
        self.set_header('Content-Type', self._RPC_.content_type)
        self.finish(response_text)

class BaseRPCWebSocketHandler(tornado.websocket.WebSocketHandler):

    _RPC_ = None
    _results = None
    _requests = 0
    _RPC_finished = False
    _history = jsonrpclibveles.payload.History()

    def set_default_headers(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def open(self, *args):
        print("New connection")

    def on_message(self, request):
        self._history.add_request(request)
        self._results = []
        self._RPC_.run(self, request)

    def on_close(self):
        print(self._history.request)

    def result(self, result, *results):
        if results:
            results = [result] + results
        else:
            results = result
        self._results.append(results)
        self._RPC_.response(self)

    def on_result(self, response_text):
        self.write_message(response_text)


class FaultMethod(object):

    def __init__(self, fault, message, code=None):
        self.fault = fault
        self.code = code
        self.message = message

    def __call__(self, message=None):
        if message:
            self.message = message
        return self.fault(self.code, self.message)


class Faults(object):
    codes = {
        'parse_error': -32700,
        'method_not_found': -32601,
        'invalid_request': -32600,
        'invalid_params': -32602,
        'internal_error': -32603
    }

    messages = {}

    def __init__(self, parser, fault=None):
        self.library = parser.library
        self.fault = fault
        if not self.fault:
            self.fault = getattr(self.library, 'Fault')

    def __getattr__(self, attr):
        message = 'Error'
        if attr in self.messages.keys():
            message = self.messages[attr]
        else:
            message = ' '.join(map(str.capitalize, attr.split('_')))
        fault = FaultMethod(self.fault, message)
        return fault


class Application(tornado.web.Application):
    def __init__(self, handlers):
        self.webSocketsPool = []
        settings = {'static_url_prefix': '/static/'}
        super().__init__(handlers)


def start_server(handlers, route=r'/', address=None, port=None):
    application = Application(handlers)
    webSocketsPool = []
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port, address)
    loop_instance = tornado.ioloop.IOLoop.instance()
    loop_instance.start()
    tornado.wsgi.WSGIContainer(application)
    return loop_instance
