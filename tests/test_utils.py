#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import logging
import sys
from unittest import TestCase

import mock
from specchio.utils import (get_all_re, get_re_from_single_line, init_logger,
                            remote_create_folder, remote_mv, remote_rm, rsync,
                            rsync_multi, walk_get_gitignore)
from testfixtures import LogCapture


class GetReFromSingleLineTest(TestCase):

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_from_blank_line(self, _fnmatch):
        result = get_re_from_single_line(" ")
        self.assertEqual(result, (0, None))
        self.assertEqual(_fnmatch.translate.call_count, 0)

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_from_comment_line(self, _fnmatch):
        result = get_re_from_single_line("# too simple")
        self.assertEqual(result, (0, None))
        self.assertEqual(_fnmatch.translate.call_count, 0)

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_from_hash_line(self, _fnmatch):
        result = get_re_from_single_line("\\#2A00BF")
        self.assertEqual(result, (1, "2A00BF"))
        self.assertEqual(_fnmatch.translate.call_count, 0)

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_from_simple_line(self, _fnmatch):
        result = get_re_from_single_line("excited/")
        self.assertEqual(result[0], 3)
        _fnmatch.translate.assert_called_once_with("excited/*")

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_with_negate_pattern(self, _fnmatch):
        result = get_re_from_single_line("!too_simple.py")
        self.assertEqual(result[0], 2)
        _fnmatch.translate.assert_called_once_with("too_simple.py")

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_with_double_asterisk(self, _fnmatch):
        result = get_re_from_single_line("young/**/simple/**/naive")
        self.assertEqual(result[0], 3)
        _fnmatch.translate.assert_called_once_with("young/*/simple/*/naive")

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_with_space(self, _fnmatch):
        result = get_re_from_single_line("too\\ young.py")
        self.assertEqual(result[0], 3)
        _fnmatch.translate.assert_called_once_with("too young.py")

    @mock.patch("specchio.utils.fnmatch")
    def test_get_re_with_head_slash(self, _fnmatch):
        result = get_re_from_single_line("./too_young.py")
        self.assertEqual(result[0], 3)
        _fnmatch.translate.assert_called_once_with("too_young.py")


class WalkGetGitignoreTest(TestCase):

    @mock.patch("specchio.utils.os")
    def test_walk_get_gitignore(self, _os):
        _os.walk.return_value = [
            ["/a/", ["c"], ["1.py", ".gitignore"]],
            ["/a/c/", [], ["1.py", ".gitignore"]],
        ]
        arg2join = {
            ("/a/", ".gitignore"): "/a/.gitignore",
            ("/a/c/", ".gitignore"): "/a/c/.gitignore"
        }
        _os.path.join.side_effect = (lambda *arg: arg2join[arg])
        arg2abs_path = {
            "/a/": "/a/",
            "/a/.gitignore": "/a/.gitignore",
            "/a/c/.gitignore": "/a/c/.gitignore"
        }
        _os.path.abspath.side_effect = (lambda arg: arg2abs_path[arg])
        result = walk_get_gitignore("/a/")
        self.assertEqual(
            result,
            [
                "/a/.gitignore",
                "/a/c/.gitignore"
            ]
        )


class GetAllReTest(TestCase):

    # Don't use mock_open, it doesn't support iter for file
    @mock.patch("__builtin__.open")
    @mock.patch("specchio.utils.re")
    @mock.patch("specchio.utils.get_re_from_single_line")
    def test_get_all_re(self, _get_re, _re, _open):
        _open.return_value = io.StringIO(u"simple text")
        _get_re.return_value = (1, "re_text")
        _re.compile.return_value = "compiled_re"
        result = get_all_re(["/young/simple/.gitignore"])
        _get_re.assert_called_once_with("simple text")
        _re.compile.assert_called_once_with("re_text")
        self.assertEqual(
            result,
            {
                "/young/simple/.gitignore": {
                    1: ["compiled_re"],
                    2: [],
                    3: []
                }
            }
        )


class RemoteCreateFloderTest(TestCase):

    @mock.patch("specchio.utils.os")
    def test_remote_create_folder(self, _os):
        _os.popen.return_value = True
        remote_create_folder("user@host", "/a/b/")
        _os.popen.assert_called_once_with("ssh user@host \"mkdir -p /a/b/\"")


class RemoteRmTest(TestCase):

    @mock.patch("specchio.utils.os")
    def test_remote_rm(self, _os):
        _os.popen.return_value = True
        remote_rm("user@host", "/a/b.py")
        _os.popen.assert_called_once_with("ssh user@host \"rm -rf /a/b.py\"")


class RemoteMvTest(TestCase):

    @mock.patch("specchio.utils.os")
    def test_remote_mv(self, _os):
        _os.popen.return_value = True
        remote_mv("user@host", "/a/b.py", "/c.py")
        _os.popen.assert_called_once_with("ssh user@host \"mv /a/b.py /c.py\"")


class RsyncTest(TestCase):

    @mock.patch("specchio.utils.os")
    def test_rsync(self, _os):
        _os.popen.return_value = True
        rsync("user@host", "/a/b.py", "/c.py")
        _os.popen.assert_called_once_with(
            "rsync -avz /a/b.py user@host:/c.py"
        )


class RsyncMultiTest(TestCase):

    @mock.patch("specchio.utils.os")
    def test_rsync_multi(self, _os):
        _os.popen.return_value = True
        rsync_multi("user@host", "/a", ["b.py", "c/1.py"], "/remote")
        _os.popen.assert_called_once_with(
            "rsync -avrm --include=\"/b.py\" --include=\"/c/1.py\""
            " --exclude=\"*.*\" /a user@host:/remote"
        )


class LoggingConfigurationTests(TestCase):

    def setUp(self):
        self.logger = logging.getLogger("specchio")
        self.orig_handlers = self.logger.handlers
        self.logger.handlers = []
        self.level = self.logger.level

    def tearDown(self):
        self.logger.handlers = self.orig_handlers
        self.logger.level = self.level

    def test_basic_configuration(self):

        init_logger()

        self.assertEqual(self.logger.level, logging.DEBUG)
        self.assertEqual(len(self.logger.handlers), 1)
        self.assertIsInstance(self.logger.handlers[0],
                              logging.StreamHandler)
        self.assertEqual(self.logger.handlers[0].stream,
                         sys.stdout)
        self.assertEqual(
            self.logger.handlers[0].formatter._fmt,
            "%(log_color)s[%(levelname)s]%(reset)s"
            " %(asctime)s %(name)s  %(message)s"
        )
        self.assertEqual(
            self.logger.handlers[0].formatter.datefmt,
            "%Y-%m-%d %H:%M:%S"
        )


class LoggingOutputTest(TestCase):

    def test_logger(self):
        logger = logging.getLogger("specchio")
        with LogCapture() as log_capture:
            logger.debug("DEBUG Test")
            logger.info("INFO Test")
            logger.warning("WARNING Test")
            logger.error("ERROR Test")
            log_capture.check(
                ("specchio", "DEBUG", "DEBUG Test"),
                ("specchio", "INFO", "INFO Test"),
                ("specchio", "WARNING", "WARNING Test"),
                ("specchio", "ERROR", "ERROR Test")
            )
