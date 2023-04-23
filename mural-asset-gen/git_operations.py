"""
Author/Engineer: Lerato Mokoena

This file houses the common git commands / execution required in gathering app white-labelling repository statistics and
information used to identify unique app builds.
"""
import os
import shlex
import subprocess

import shell_commands

GIT_BIN = 'git'
GIT_COMMIT_COUNT = GIT_BIN + ' log --oneline'
GIT_COMMIT_HASH = GIT_BIN + ' rev-parse HEAD'
GIT_COMMIT_SHORT_HASH = GIT_BIN + ' rev-parse --short HEAD'
GIT_CLONE = GIT_BIN + ' clone {url} clients'
GIT_BRANCH = GIT_BIN + ' branch'


def work_dir(path=""):
    """
    :param path: relative path
    :return: full path
    """
    if len(path) > 0:
        if path[0] is "/":
            return path
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
    return file_path


def get_commits(path=""):
    """
    :param path: possible relative path
    :return: commit count
    """
    command = shlex.split(GIT_COMMIT_COUNT)
    work_dir_path = work_dir(path)
    output = subprocess.check_output(command, env=shell_commands.ENV, cwd=work_dir_path).strip()
    return output


def get_commit_count(path=""):
    """
    :param path: possible relative path
    :return: adjusted (corrected) commit count
    """
    return get_commits(path).decode("utf-8").count('\n') + 1


def get_hash(path=""):
    """
    :param path: possible relative path
    :return: hash of current checked-out branch
    """
    work_dir_path = work_dir(path)
    command = shlex.split(GIT_COMMIT_HASH)
    return subprocess.check_output(command, env=shell_commands.ENV, cwd=work_dir_path).decode("utf-8").strip()


def get_short_hash(path=""):
    """
    :param path: possible relative path
    :return: short hash of current checked-out branch
    """
    work_dir_path = work_dir(path)
    command = shlex.split(GIT_COMMIT_SHORT_HASH)
    return subprocess.check_output(command, env=shell_commands.ENV, cwd=work_dir_path).decode("utf-8").strip()


def clone(url):
    """
    :param url: git url to clone
    :return: clone output
    """
    command = shlex.split(GIT_CLONE.format(url=url))
    return subprocess.check_output(command, env=shell_commands.ENV).strip()


def git_branch(path):
    """
    :param path: possible relative path
    :return: current checked out git branch
    """
    get_branch_command = shlex.split(GIT_BRANCH)
    branch_raw = subprocess.check_output(get_branch_command, env=shell_commands.ENV, cwd=path)
    # find the line that starts with a *
    branch_list = branch_raw.split(b'\n')
    for branch in branch_list:
        if branch.startswith(b'*'):
            actual = branch[2:]
            return actual.decode("utf-8")
    return 'master'


# Uncomment below to test file locally
# print("{}".format(get_commits("client")))
# print("{}".format(get_commits()))

# print("{}".format(get_commit_count("client")))
# print("{}".format(get_commit_count()))
