"""
Author/Engineer: Lerato Mokoena

This file contains convenience functions that support executing the asset generator on a MS Windows machine.
"""
import os

from environmentals import get_environ_val

COMMANDS = {'convert': 'ImageMagick',
            'composite': 'ImageMagick',
            'inkscape': 'Inkscape'}


def get_windows_path(program):
    """
    :param program:
    :return:
    """
    for location in ['ProgramW6432', 'ProgramFiles', 'ProgramFiles(x86)']:
        program_files = get_environ_val(location)
        path = [os.path.join(program_files, folder) for
                folder in os.listdir(program_files) if folder.startswith(program)]

        if len(path) is not 0:
            return path[0]

    return None


def format_command(path, binary):
    """
    :param path:
    :param binary:
    :return:
    """
    return '"{command}"'.format(command=os.path.join(path, binary))


def get_windows_command(binary):
    """
    :param binary:
    :return:
    """
    path = get_windows_path(COMMANDS[binary])
    if path is None:
        return False
    return format_command(path, binary)


def update_env(env):
    """
    :param env:
    :return:
    """
    env['PATH'] = get_windows_path(COMMANDS['convert']) + ';' + env['PATH']
    return env
