# encoding: utf-8
from flask import jsonify


class Result:
    """
    Web调用结果
    """

    def __init__(self):
        self.status = ''
        self.description = ''
        self.data = []

    @staticmethod
    def to_json(self):
        return jsonify(self)


class Status:
    SUCCESS = 'success'
    ERROR = 'error'
    INVALID_PARAMETER = 'Invalid parameter'


class Description:
    SUCCESS = ''
    ERROR = ''
    INVALID_PARAMETER = ''
