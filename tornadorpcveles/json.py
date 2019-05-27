#!/usr/bin/env python
# -*- coding: utf-8

from tornadorpcveles.base import BaseRPCParser, BaseRPCRequestHandler, BaseRPCWebSocketHandler
from jsonprclibveles.jsonrpc import Fault, isbatch, dumps, loads


class JSONRPCParser(BaseRPCParser):

    def parse_request(self, request_body):
        try:
            request = loads(request_body)
        except:
            self.traceback()
            return self.faults.parse_error()
        self._requests = request
        self._batch = False
        request_list = []
        if isbatch(request):
            self._batch = True
            for req in request:
                req_tuple = (req['method'], req.get('params', []))
                request_list.append(req_tuple)
        else:
            self._requests = [request]
            request_list.append((request['method'], request.get('params', [])))
        return tuple(request_list)

    def parse_responses(self, responses):
        if isinstance(responses, Fault):
            return dumps(responses)
        if len(responses) != len(self._requests):
            return dumps(self.faults.internal_error())
        response_list = []
        for i in range(0, len(responses)):
            response = responses[i]
            try:
                response_json = dumps(response, methodresponse=True)
            except TypeError:
                return dumps(self.faults.server_error())
            response_list.append(response_json)
        if not self._batch:
            if len(response_list) < 1:
                return ''
            return response_list[0]
        return '[ %s ]' % ', '.join(response_list)


class JSONRPCLibraryWrapper(object):

    dumps = dumps
    loads = loads
    Fault = Fault


class JSONRPCHandler(BaseRPCRequestHandler):
    _RPC_ = JSONRPCParser(JSONRPCLibraryWrapper)


class JSONRPCWSHandler(BaseRPCWebSocketHandler):
    _RPC_ = JSONRPCParser(JSONRPCLibraryWrapper)
