#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch
import re
from unittest import TestCase

import mock
from watchdog.events import DirCreatedEvent, FileModifiedEvent, FileMovedEvent

from specchio.handlers import SpecchioEventHandler


class SpecchioEventHandlerTest(TestCase):

    def setUp(self):
        SpecchioEventHandler.init_gitignore = mock.Mock()
        SpecchioEventHandler.init_gitignore.return_value = True
        self.handler = SpecchioEventHandler(
            src_path="/a/",
            dst_ssh="user@host",
            dst_path="/b/a/"
        )
        self.handler.gitignore_dict = {
            "/a/.gitignore": {
                1: [],
                2: [re.compile(fnmatch.translate("/a/1.py"))],
                3: [re.compile(fnmatch.translate("/a/test.py"))]
            }
        }
        self.handler.gitignore_list = ["/a/"]

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    def on_created_test(self, _remote_create_folder, _os):
        _remote_create_folder.return_value = True
        _os.path.abspath.return_value = "/a/test1.py"
        _os.path.join.return_value = "/b/a/test1.py"
        _event = DirCreatedEvent(src_path="/a/test1.py")
        self.handler.on_created(_event)
        _remote_create_folder.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            dst_path="/b/a/test1.py"
        )

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    def on_created_ignore_test(self, _remote_create_folder, _os):
        _remote_create_folder.return_value = True
        _os.path.abspath.return_value = "/a/test.py"
        _event = DirCreatedEvent(src_path="/a/test.py")
        self.handler.on_created(_event)
        self.assertEqual(_remote_create_folder.call_count, 0)

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    @mock.patch("specchio.handlers.rsync")
    def on_modified_test(self, _rsync, _remote_create_folder, _os):
        _rsync.return_value = True
        _remote_create_folder.return_value = True
        _os.path.abspath.return_value = "/a/test1.py"
        _os.path.join.return_value = "/b/a/test1.py"
        _event = FileModifiedEvent(src_path="/test1.py")
        self.handler.on_modified(_event)
        _rsync.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            src_path="/a/test1.py",
            dst_path="/b/a/test1.py"
        )
        _remote_create_folder.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            dst_path="/b/a/"
        )

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    @mock.patch("specchio.handlers.rsync")
    def on_modifited_ignore_test(self, _rsync, _remote_create_folder, _os):
        _rsync.return_value = True
        _remote_create_folder.return_value = True
        _os.path.abspath.return_value = "/a/test.py"
        _event = FileModifiedEvent(src_path="/a/test.py")
        self.handler.on_modified(_event)
        self.assertEqual(_remote_create_folder.call_count, 0)
        self.assertEqual(_rsync.call_count, 0)

    @mock.patch("specchio.handlers.get_all_re")
    def update_gitignore_test(self, _get_all_re):
        _get_all_re.return_value = {
            "/a/b/.gitignore": {
                1: [],
                2: [],
                3: []
            }
        }
        _handler_gitignore_list = list(self.handler.gitignore_list)
        _handler_gitignore_dict = dict(self.handler.gitignore_dict)
        self.handler.update_gitignore("/a/b/.gitignore")
        self.assertEqual(
            self.handler.gitignore_list,
            ["/a/b/", "/a/"]
        )
        self.assertEqual(
            self.handler.gitignore_dict,
            {
                "/a/.gitignore": {
                    1: [],
                    2: [re.compile(fnmatch.translate("/a/1.py"))],
                    3: [re.compile(fnmatch.translate("/a/test.py"))]
                },
                "/a/b/.gitignore": {
                    1: [],
                    2: [],
                    3: []
                }
            }
        )
        self.handler.gitignore_list = _handler_gitignore_list
        self.handler.gitignore_dict = _handler_gitignore_dict

    def del_gitignore_test(self):
        _handler_gitignore_list = list(self.handler.gitignore_list)
        _handler_gitignore_dict = dict(self.handler.gitignore_dict)
        self.handler.del_gitignore("/a/.gitignore")
        self.assertEqual(
            self.handler.gitignore_list,
            []
        )
        self.assertEqual(
            self.handler.gitignore_dict,
            {}
        )
        self.handler.gitignore_list = _handler_gitignore_list
        self.handler.gitignore_dict = _handler_gitignore_dict

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_mv")
    def on_moved_test(self, _mv, _os):
        _mv.return_value = True
        _os.path.abspath.side_effect = ["/a/1.py", "/a/2.py"]
        _os.path.join.side_effect = ["/b/a/1.py", "/b/a/2.py"]
        _event = FileMovedEvent(src_path="/a/1.py", dest_path="/a/2.py")
        self.handler.on_moved(_event)
        _mv.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            src_path="/b/a/1.py",
            dst_path="/b/a/2.py"
        )

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_rm")
    @mock.patch("specchio.handlers.remote_create_folder")
    @mock.patch("specchio.handlers.remote_mv")
    @mock.patch("specchio.handlers.rsync")
    def on_moved_all_ignore_test(self, _rsync, _mv, _create_folder, _rm, _os):
        _mv.return_value = True
        _create_folder.return_value = True
        _rm.return_value = True
        _rsync.return_value = True
        _os.path.abspath.side_effect = ["/a/test.py", "/a/test.py"]
        _os.path.join.side_effect = ["/b/a/test.py", "/b/a/test.py"]
        _event = FileMovedEvent(src_path="/a/test.py", dest_path="/a/test.py")
        self.handler.on_moved(_event)
        self.assertEqual(_mv.call_count, 0)
        self.assertEqual(_rm.call_count, 0)
        self.assertEqual(_create_folder.call_count, 0)
        self.assertEqual(_rsync.call_count, 0)

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    @mock.patch("specchio.handlers.rsync")
    def on_moved_src_ignore_test(self, _rsync, _create_folder, _os):
        _create_folder.return_value = True
        _rsync.return_value = True
        _os.path.abspath.side_effect = ["/a/test.py", "/a/1.py"]
        _os.path.join.side_effect = ["/b/a/test.py", "/b/a/1.py"]
        _event = FileMovedEvent(src_path="test.py", dest_path="/a/1.py")
        self.handler.on_moved(_event)
        _create_folder.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            dst_path="/b/a/"
        )
        _rsync.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            src_path="/a/1.py",
            dst_path="/b/a/1.py"
        )

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_rm")
    def on_moved_dst_ignore_test(self, _rm, _os):
        _rm.return_value = True
        _os.path.abspath.side_effect = ["/a/1.py", "/a/test.py"]
        _os.path.join.side_effect = ["/b/a/1.py", "/b/a/test.py"]
        _event = FileMovedEvent(src_path="1.py", dest_path="/a/test.py")
        self.handler.on_moved(_event)
        _rm.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            dst_path="/b/a/1.py"
        )
