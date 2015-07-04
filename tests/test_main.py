#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase

import mock

from specchio.main import main


class mainTest(TestCase):

    @mock.patch("specchio.main.sys")
    @mock.patch("specchio.main.init_logger")
    def test_main_invalid(self, _init_logger, _sys):
        _sys.argv = ["specchio"]
        main()
        self.assertEqual(_init_logger.call_count, 0)

    @mock.patch("specchio.main.sys")
    @mock.patch("specchio.main.time")
    @mock.patch("specchio.main.Observer")
    @mock.patch("specchio.main.SpecchioEventHandler")
    def test_main(self, _SpecchioEventHandler,
                  _Observer, _time, _sys):
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
