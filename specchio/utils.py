#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch
import os
import re


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


def dfs_get_gitignore(base_path):
    """Use depth first search to get all `.gitignore` under base_path

    :param base_path: str -- the path to deal with
    :return: list of str -- the path of all `.gitignore`
    """
    base_path = os.path.abspath(base_path)
    dir_list = os.listdir(base_path)
    result = []
    for file_or_dir in dir_list:
        file_or_dir_path = os.path.join(base_path, file_or_dir)
        if file_or_dir == ".gitignore" and not os.path.isdir(file_or_dir_path):
            result.append(file_or_dir_path)
        elif os.path.isdir(file_or_dir_path):
            # Continue to search `.gitignore`
            result += dfs_get_gitignore(file_or_dir_path)
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
