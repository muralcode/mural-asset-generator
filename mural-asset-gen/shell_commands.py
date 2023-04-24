"""
Author/Engineer: Lerato Mokoena

This file houses shell commands that are frequently required during the process of asset generation.
"""
import shlex
import subprocess
import sys
import os

import windows

IS_WIN = (sys.platform == 'win32')

def find_bin(command_name):
    """
    :param command_name: name of the application to find the binary for
    :return: either windows or linux/unix command name
    """
    if IS_WIN:
        return windows.get_windows_command(command_name)
    else:
        return command_name


def update_env():
    """
    :return: a copy of the environment variables
    """
    env = os.environ.copy()
    if IS_WIN:
        return windows.update_env(env)
    else:
        return env


ENV = update_env()
CONVERT_BIN = find_bin('convert')
COMPOSITE_BIN = find_bin('composite')
INKSCAPE_BIN = find_bin('inkscape')
WEBP_BIN = find_bin('cwebp')

IMAGE_MAGICK_CHECK = CONVERT_BIN + ' -version'
IMAGE_MAGICK_ERROR = 'image_magick not found, skipping icon generation'

INKSCAPE_CHECK = INKSCAPE_BIN + ' --version'
INKSCAPE_ERROR = 'inkscape not found, trying image_magick with launcher.png'

IMAGE_MAGICK_SQUARE_COMMAND = CONVERT_BIN + ' "{input}" -resize {size}x{size}! "{output}"'
IMAGE_MAGICK_COMMAND = CONVERT_BIN + ' "{input}" -resize {size} "{output}"'
IMAGE_MAGICK_COLOR_COMMAND = CONVERT_BIN + ' "{input}" +level-colors "{color}" "{output}"'
IMAGE_MAGICK_COMBINE_COMMAND = COMPOSITE_BIN + ' "{output}" "{input}" "{output}"'
IMAGE_MAGICK_FLATTEN_COMMAND = CONVERT_BIN + ' "{input}" -alpha remove -alpha off -flatten "{output}"'

INKSCAPE_SQUARE_COMMAND = INKSCAPE_BIN + ' -z -e "{output}" -w {size} -h {size} "{input}"'
INKSCAPE_COMMAND = INKSCAPE_BIN + ' -z -e "{output}" -w {size} "{input}"'
INKSCAPE_CONVERT = INKSCAPE_BIN + ' -z -e "{output}" "{input}"'

WEBP_COMMAND = WEBP_BIN + ' -q 75 "{input}" -o "{output}"'


def has_command(command_string, error_message=None):
    """
    :param command_string: bin name and version flag
    :param error_message: message supplied for indicating absence of software
    :return: boolean indicating whether or not the application is present
    """
    command = shlex.split(command_string)
    try:
        subprocess.check_output(command)
        return True
    except OSError:
        if error_message is not None:
            print(error_message)
        return False


def has_image_magick():
    """
    :return: whether or not imagemagick is available
    """
    return has_command(IMAGE_MAGICK_CHECK, IMAGE_MAGICK_ERROR)


def has_inkscape():
    """
    :return: whether or not inkscape is available
    """
    return has_command(INKSCAPE_CHECK, IMAGE_MAGICK_ERROR)
