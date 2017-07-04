# -*- coding: utf-8 -*-
from flask import jsonify


class Result:
    """
    Web调用结果
    """

    status = u''
    detail = u''
    data = None

    class Status:
        SUCCESS = u'success'
        ERROR = u'error'
        BAD_REQUEST = u'bad_request'                        # 400
        UNAUTHORIZED = u'unauthorized'                      # 401
        FORBIDDEN = u'forbidden'                            # 403
        NOT_FOUND = u'not_found'                            # 404
        INVALID_METHOD = u'method_not_allowed'              # 405
        INTERNAL_ERROR = u'internal_server_error'           # 500


    class Detail:
        SUCCESS = u'Success.'
        ERROR = u'Failed.'
        BAD_REQUEST = u'Bad request.'
        UNAUTHORIZED = u'Login required'
        FORBIDDEN = u'No permission to access target resource.'
        NOT_FOUND = u'Resource is not found.'
        INVALID_METHOD = u'Method for this url is not allowed.'
        INTERNAL_ERROR = u'Internal server error.'

    def __init__(self):
        pass

    def to_json(self):
        return {u'status': self.status, u'detail': self.detail, u'data': self.data}


def bad_request(message=None):
    result = Result()
    result.status = Result.Status.BAD_REQUEST
    result.detail = Result.Detail.BAD_REQUEST
    result.data = message
    response = jsonify(result.to_json())
    response.status_code = 400
    return response


def unauthorized(message=None):
    result = Result()
    result.status = Result.Status.UNAUTHORIZED
    result.detail = Result.Detail.UNAUTHORIZED
    result.data = message
    response = jsonify(result.to_json())
    response.status_code = 401
    return response


def forbidden(message=None):
    result = Result()
    result.status = Result.Status.FORBIDDEN
    result.detail = Result.Detail.FORBIDDEN
    result.data = message
    response = jsonify(result.to_json())
    response.status_code = 403
    return response


def not_found(message=None):
    result = Result()
    result.status = Result.Status.NOT_FOUND
    result.detail = Result.Detail.NOT_FOUND
    result.data = message
    response = jsonify(result.to_json())
    response.status_code = 404
    return response


def method_not_allowed(message=None):
    result = Result()
    result.status = Result.Status.INVALID_METHOD
    result.detail = Result.Detail.INVALID_METHOD
    result.data = message
    response = jsonify(result.to_json())
    response.status_code = 405
    return response


def internal_server_error(message=None):
    result = Result()
    result.status = Result.Status.INTERNAL_ERROR
    result.detail = Result.Detail.INTERNAL_ERROR
    result.data = message
    response = jsonify(result.to_json())
    response.status_code = 500
    return response
