#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch


def get_re_from_single_line(line):
    """Get regular expression from a single line in `.gitignore`
    The rules of `.gitingore` followed http://git-scm.com/docs/gitignore

    :param line: str -- single line from `.gitignore`
    :return: tuple
        0, None -- noting to pattern
        1, str -- hash to pattern
        2, str -- negate ignore path to pattern
        3, str -- ignore path to pattern
    """
    _line = line.strip()
    # Deal with file name end with ` `
    line = (
        _line + " " if _line.endswith("\\") and line.endswith(" ") else _line
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
        if line.startswith("/"):
            # Dealing with line start with `/`, just remove the head
            return re_type, fnmatch.translate(line[1:])
        else:
            return re_type, fnmatch.translate(line)
