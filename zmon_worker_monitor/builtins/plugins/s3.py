#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import json
import logging

import functools
import requests
import cStringIO

from botocore.exceptions import ClientError

from zmon_worker_monitor.adapters.ifunctionfactory_plugin import IFunctionFactoryPlugin, propartial
from zmon_worker_monitor.zmon_worker.errors import S3BotoClientError

logging.getLogger('botocore').setLevel(logging.WARN)
logger = logging.getLogger('zmon-worker.s3-function')


def logged(func):
    """
    Logging a functional call in case of errors
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientError, exp:
            logger.exception('S3 boto client error: %s', exp)
            raise S3BotoClientError(exp.message)
        except Exception as exp:
            logger.error(exp, exc_info=True)
            raise
    return wrapper


class S3BucketWrapper(IFunctionFactoryPlugin):
    def __init__(self):
        super(S3BucketWrapper, self).__init__()

    def configure(self, conf):
        return

    def create(self, factory_ctx):
        """
        Automatically called to create the check function's object
        :param factory_ctx: (dict) names available for Function instantiation
        :return: an object that implements a check function
        """
        return propartial(S3Wrapper, region=factory_ctx.get('entity').get('region', None))


def get_region():
    r = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=3)
    return r.json()['region']


class S3Wrapper(object):
    def __init__(self, region=None):
        if not region:
            region = get_region()
        self._try_connect(region)

    @logged
    def _try_connect(self, region):
        self.__client = boto3.client('s3', region_name=region)

    @logged
    def get_object_metadata(self, bucket_name, key):
        """
        Get metadata on the object in the given bucket and accessed with the given key.
        The metadata is retieved without fetching the object so it can be safely used with large
        S3 objects
        :param bucket_name: the name of the S3 Bucket
        :param key: the key that identifies the S3 Object within the S3 Bucket
        :return: an S3ObjectMetadata object
        """
        response = self.__client.head_object(Bucket=bucket_name, Key=key)
        return S3ObjectMetadata(response)

    @logged
    def get_object(self, bucket_name, key):
        """
        Get the object in the given bucket and accessed with the given key.
        The S3 Object is read into memory and the data within can be accessed as a string or parsed as JSON.
        :param bucket_name: the name of the S3 Bucket
        :param key: the key that identifies the S3 Object within the S3 Bucket
        :return: an S3Object object
        """
        data = cStringIO.StringIO()
        try:
            self.__client.download_fileobj(bucket_name, key, data)
            result = data.getvalue()
            return S3Object(result)
        finally:
            data.close()


class S3Object(object):

    def __init__(self, key_value):
        self.__key_value = key_value

    def json(self):
        """
        Get the S3 Object data and parse it as JSON
        :return: a dict containing the parsed JSON
        """
        if self.exists():
            return json.loads(self.__key_value)
        else:
            return None

    def text(self):
        """
        Get the S3 Object data (we assume it's text)
        :return: the raw S3 Object data
        """
        return self.__key_value

    def exists(self):
        """
        Does this object exist?
        :return: True if the object exists
        """
        return self.__key_value is not None

    def size(self):
        """
        How large (in bytes) is the object data
        :return: the size in bytes of the object, or -1 if the object does not exist.
        """
        if self.exists():
            return len(self.__key_value)
        else:
            return -1


class S3ObjectMetadata(object):

    def __init__(self, response):
        self.__response = response

    def exists(self):
        """
        Does this object exist?
        :return: True if the object exists
        """
        return len(self.__response) > 0

    def size(self):
        """
        How large (in bytes) is the object data
        :return: the size in bytes of the object, or -1 if the object does not exist.
        """
        if self.exists():
            return self.__response['ContentLength']
        else:
            return -1
