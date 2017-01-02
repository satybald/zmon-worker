#!/usr/bin/env python
# -*- coding: utf-8 -*-


class CheckError(Exception):
    pass


class NotificationError(Exception):
    pass


class SecurityError(Exception):
    pass


class ConfigurationError(CheckError):
    def __init__(self, message):
        message = 'Configuration error: {}'.format(message)

        super(ConfigurationError, self).__init__(message)


class InsufficientPermissionsError(CheckError):
    def __init__(self, user, entity):
        self.user = user
        self.entity = entity

    def __str__(self):
        return 'Insufficient permisions for user {} to access {}'.format(self.user, self.entity)


class JmxQueryError(CheckError):
    def __init__(self, message):
        self.message = message
        super(JmxQueryError, self).__init__()

    def __str__(self):
        return 'JMX Query failed: {}'.format(self.message)


class HttpError(CheckError):
    def __init__(self, message, url=None):
        self.message = message
        self.url = url
        super(HttpError, self).__init__()

    def __str__(self):
        return 'HTTP request failed for {}: {}'.format(self.url, self.message)


class DbError(CheckError):
    def __init__(self, message, operation=None):
        self.message = message
        self.operation = operation
        super(DbError, self).__init__()

    def __str__(self):
        return 'DB operation {} failed: {}'.format(self.operation, self.message)


class ResultSizeError(CheckError):
    def __init__(self, message):
        message = 'Result size error: {}'.format(message)

        super(ResultSizeError, self).__init__(message)


class S3BotoClientError(CheckError):
    def __init__(self, message):
        message = 'Boto Client Error: {}'.format(message)

        super(S3BotoClientError, self).__init__(message)
