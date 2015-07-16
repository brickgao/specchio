#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch
import logging
import logging.config
import os
import re

from specchio.config.logging import LOGGING_CONFIG


def get_re_from_single_line(line):
    """Get regular expression from a single line in `.gitignore`
    The rules of `.gitingore` followed http://git-scm.com/docs/gitignore

    :param line: str -- single line from `.gitignore`
    :return: tuple
        0, None -- noting to match
        1, str -- hash to match
        2, str -- negate ignore path to match
        3, str -- ignore path to match
    """
    _line = line.strip()
    # Deal with file name end with ` `
    line = (
        _line + " " if _line.endswith("\\") and (
            line.endswith(" \r\n") or line.endswith("\n")
        ) else _line
    )
    line = line.replace("\\ ", " ")
    # Deal with `**` in folder path
    line = line.replace("**", "*")
    if line.endswith("/"):
        line += "*"
    if line == "":
        # A blank line matches no files
        return 0,  None
    elif line.startswith("#"):
        # A line starting with `#` serves as a comment
        return 0, None
    elif line.startswith("\\#"):
        # A line starting with `\#` serves as a pattern for hash
        return 1, line.split("#")[-1].strip()
    else:
        if line.startswith("!"):
            # A line starting with `!` negates the pattern
            re_type = 2
            line = line[1:]
        else:
            re_type = 3
        # Deal with escape string
        line = line.replace("\\", "")
        if line.startswith("./"):
            # Dealing with line start with `./`, just remove the head
            return re_type, fnmatch.translate(line[2:])
        else:
            return re_type, fnmatch.translate(line)


def walk_get_gitignore(base_path):
    """Use os.walk to get all `.gitignore` under base_path

    :param base_path: str -- the path to deal with
    :return: list of str -- the path of all `.gitignore`
    """
    base_path = os.path.abspath(base_path)
    result = []
    for root_path, dirs_path, files_path in os.walk(base_path):
        for _file_path in files_path:
            if _file_path == ".gitignore":
                file_path = os.path.join(root_path, _file_path)
                abs_file_path = os.path.abspath(file_path)
                result.append(abs_file_path)
    return result


def get_all_re(gitignore_path_list):
    """Get all compiled regular expression from gitignore_list

    :param gitignore_path_list: list of str -- the path of all `.gitignore`
    :return: dict -- the absolute path of `.gitignore` is the key,
                     the value in dict is another dict, like
                     result[path of `.gitignore`][key2]:
                        result[path][1]: list of hash to match
                        result[path][2]: list of negate ignore path to match
                        result[path][3]: list of ignore path to match
    """
    result = {}
    for gitignore_path in gitignore_path_list:
        with open(gitignore_path, "r") as gitignore_file:
            result[gitignore_path] = {1: [], 2: [], 3: []}
            for line in gitignore_file:
                ignore_type, ignore_pattern = get_re_from_single_line(line)
                # If match some file
                if ignore_type:
                    _re = re.compile(ignore_pattern)
                    result[gitignore_path][ignore_type].append(_re)
    return result


def remote_create_folder(dst_ssh, dst_path):
    """Create folder remotely by using ssh

    :param dst_ssh: str -- user name and host name of destination path
                           just like: user@host
    :param dst_path: str -- destination path
    :return: None
    """
    dst_command = "\"mkdir -p {}\"".format(dst_path)
    command = "ssh " + dst_ssh + " " + dst_command
    os.popen(command)


def remote_rm(dst_ssh, dst_path):
    """Remove file or folder remotely by using ssh

    :param dst_ssh: str -- user name and host name of destination path
                           just like: user@host
    :param dst_path: str -- destination path
    :return: None
    """
    dst_command = "\"rm -rf {}\"".format(dst_path)
    command = "ssh " + dst_ssh + " " + dst_command
    os.popen(command)


def remote_mv(dst_ssh, src_path, dst_path):
    """Move file or folder remotely by using mv

    :param dst_ssh: str -- user name and host name of destination path
                           just like: user@host
    :param src_path: str -- source of `mv` operator
    :param dst_path: str -- destination of `mv` operator
    :return: None
    """
    dst_command = "\"mv {0} {1}\"".format(src_path, dst_path)
    command = "ssh " + dst_ssh + " " + dst_command
    os.popen(command)


def rsync(dst_ssh, src_path, dst_path):
    """Rsync file remotely

    :param dst_ssh: str -- user name and host name of destination path
                           just like: user@host
    :param src_path: str -- source of file
    :param dst_path: str -- destination of file
    :return: None
    """
    command = "rsync -avz {0} {1}:{2}".format(src_path, dst_ssh, dst_path)
    os.popen(command)


def rsync_multi(dst_ssh, folder_path, src_paths, dst_path):
    """Rsync multiple files remotely

    :param dst_ssh: str -- user name and host name of destination path
                           just like: user@host
    :param folder_path: str -- source of folder path
    :param src_paths: list of str -- a list of src_path
    :param dst_path: str -- destination of file
    :return: None
    """
    _include_tuples = map(lambda s: "--include=\"/{}\"".format(s),
                          src_paths)
    command = "rsync -avrm {0} --exclude=\"*.*\" {1} {2}:{3}".format(
        " ".join(_include_tuples), folder_path, dst_ssh, dst_path
    )
    os.popen(command)


def init_logger():
    logging.config.dictConfig(LOGGING_CONFIG)


logger = logging.getLogger("specchio")
