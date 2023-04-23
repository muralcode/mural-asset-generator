"""
Small wrapper class, makes getting environment variables more verbose, prevents importing os where only env vars are
wanted/needed.
"""
import os


def get_environ_val(key):
    """
    :param key: the key to look up in environment
    :return: the value stored under that key
    """
    return os.environ[key]
