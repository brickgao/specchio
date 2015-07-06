#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
from unittest import TestCase

import mock
from testfixtures import LogCapture

from specchio.main import main


class mainTest(TestCase):

    @mock.patch("specchio.main.os")
    @mock.patch("specchio.main.sys")
    @mock.patch("specchio.main.SpecchioEventHandler")
    def test_main_invalid(self, _SpecchioEventHandler, _sys, _os):
        _sys.argv = ["specchio"]
        _arg2ret = {
            "ssh -V": io.StringIO(u"test_msg"),
            "rsync --version": io.StringIO(u"test_msg")
        }
        _os.popen.side_effect = (lambda arg: _arg2ret[arg])
        main()
        self.assertEqual(_SpecchioEventHandler.call_count, 0)

    @mock.patch("specchio.main.os")
    @mock.patch("specchio.main.sys")
    @mock.patch("specchio.main.init_logger")
    def test_main_no_ssh(self, _init_logger, _sys, _os):
        _init_logger.return_value = True
        _sys.argv = ["specchio"]
        _arg2ret = {
            "ssh -V": io.StringIO(u"")
        }
        _os.popen.side_effect = (lambda arg: _arg2ret[arg])
        with LogCapture() as log_capture:
            main()
            log_capture.check(
                ("specchio", "ERROR", "Specchio need `ssh`, "
                                      "but there is no `ssh` in the system")
            )

    @mock.patch("specchio.main.os")
    @mock.patch("specchio.main.sys")
    @mock.patch("specchio.main.init_logger")
    def test_main_no_rsync(self, _init_logger, _sys, _os):
        _init_logger.return_value = True
        _sys.argv = ["specchio"]
        _arg2ret = {
            "ssh -V": io.StringIO(u"test_msg"),
            "rsync --version": io.StringIO(u"")
        }
        _os.popen.side_effect = (lambda arg: _arg2ret[arg])
        with LogCapture() as log_capture:
            main()
            log_capture.check(
                ("specchio", "ERROR", "Specchio need `rsync`, "
                                      "but there is no `rsync` in the system")
            )

    @mock.patch("specchio.main.os")
    @mock.patch("specchio.main.sys")
    @mock.patch("specchio.main.time")
    @mock.patch("specchio.main.Observer")
    @mock.patch("specchio.main.SpecchioEventHandler")
    def test_main(self, _SpecchioEventHandler,
                  _Observer, _time, _sys, _os):
        _arg2ret = {
            "ssh -V": io.StringIO(u"test_msg"),
            "rsync --version": io.StringIO(u"test_msg")
        }
        _os.popen.side_effect = (lambda arg: _arg2ret[arg])
        _sys.argv = ["specchio", "/a/", "user@host:/b/a/"]
        _event_handler = mock.Mock()
        _SpecchioEventHandler.return_value = _event_handler
        _observer_object = mock.Mock()
        _Observer.return_value = _observer_object
        _time.sleep = mock.PropertyMock(side_effect=KeyboardInterrupt)
        main()
        _SpecchioEventHandler.assert_called_once_with(
            src_path="/a/", dst_ssh="user@host", dst_path="/b/a/"
        )
        _observer_object.schedule.assert_called_once_with(
            _event_handler, "/a/", recursive=True
        )
        _observer_object.stop.assert_called_once_with()
        _observer_object.join.assert_called_once_with()
