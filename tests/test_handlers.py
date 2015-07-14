#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch
import re
from unittest import TestCase

import mock
from watchdog.events import (DirCreatedEvent, FileCreatedEvent,
                             FileDeletedEvent, FileModifiedEvent,
                             FileMovedEvent)

from specchio.handlers import SpecchioEventHandler


class SpecchioEventHandlerTest(TestCase):

    def setUp(self):
        with mock.patch.object(
            SpecchioEventHandler, "init_gitignore"
        ) as _init_gitignore:
            _init_gitignore.return_value = True
            self.handler = SpecchioEventHandler(
                src_path="/a/",
                dst_ssh="user@host",
                dst_path="/b/a/"
            )
        self.handler.init_gitignore = mock.Mock()
        self.handler.gitignore_dict = {
            "/a/.gitignore": {
                1: [],
                2: [re.compile(fnmatch.translate("1.py"))],
                3: [re.compile(fnmatch.translate("test.py"))]
            }
        }
        self.handler.gitignore_list = ["/a/"]

    def test_specchio_init_with_init_remote(self):
        with mock.patch.object(
            SpecchioEventHandler, "init_gitignore"
        ) as _init_gitignore:
            with mock.patch.object(
                SpecchioEventHandler, "init_remote"
            ) as _init_remote:
                _init_gitignore.return_value = True
                _init_remote.return_value = True
                SpecchioEventHandler(
                    src_path="/a/", dst_ssh="user@host",
                    dst_path="/b/a/", is_init_remote=True
                )
                _init_remote.assert_called_once_with()

    def test_is_ignore_git_folder(self):
        _file_or_dir_path = mock.Mock("/a/")
        _file_or_dir_path.startswith.return_value = True
        result = self.handler.is_ignore(_file_or_dir_path)
        self.assertEqual(result, True)
        _file_or_dir_path.startswith.called_once_with(self.handler.git_path)

    @mock.patch("specchio.handlers.walk_get_gitignore")
    @mock.patch("specchio.handlers.get_all_re")
    def test_init_gitignore(self, _get_all_re, _walk_get_gitignore):
        _walk_get_gitignore.return_value = ["/a/.gitignore"]
        _get_all_re.return_value = {
            "/a/.gitignore": {
                1: [],
                2: [re.compile(fnmatch.translate("1.py"))],
                3: [re.compile(fnmatch.translate("test.py"))]
            }
        }
        handler = SpecchioEventHandler(
            src_path="/a/",
            dst_ssh="user@host",
            dst_path="/b/a/"
        )
        _walk_get_gitignore.called_once_with("/a/")
        self.assertEqual(handler.gitignore_list, ["/a/"])
        self.assertEqual(handler.gitignore_dict, {
            "/a/.gitignore": {
                1: [],
                2: [re.compile(fnmatch.translate("1.py"))],
                3: [re.compile(fnmatch.translate("test.py"))]
            }
        })

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    def test_on_created_folder(self, _remote_create_folder, _os):
        _remote_create_folder.return_value = True
        _os.path.abspath.return_value = "/a/test1.py"
        _os.path.join.return_value = "/b/a/test1.py"
        _event = DirCreatedEvent(src_path="/a/test1.py")
        self.handler.on_created(_event)
        _remote_create_folder.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            dst_path="/b/a/test1.py"
        )

    @mock.patch("specchio.handlers.remote_create_folder")
    @mock.patch("specchio.handlers.rsync")
    @mock.patch("specchio.handlers.os")
    def test_on_created_file(self, _os, _rsync,
                             _remote_create_folder):
        with mock.patch.object(
                self.handler,
                "update_gitignore"
        ) as _update_gitignore:
            _os.path.abspath.return_value = "/a/.gitignore"
            _rsync.return_value = True
            _update_gitignore.return_value = True
            _remote_create_folder.return_value = True
            _os.path.join.return_value = "/b/a/.gitignore"
            _event = FileCreatedEvent(src_path="/a/.gitignore")
            self.handler.on_created(_event)
            _remote_create_folder.assert_called_once_with(
                dst_ssh=self.handler.dst_ssh,
                dst_path="/b/a/"
            )
            _rsync.assert_called_once_with(dst_ssh=self.handler.dst_ssh,
                                           dst_path="/b/a/.gitignore",
                                           src_path="/a/.gitignore")
            _update_gitignore.assert_called_once_with("/a/.gitignore")

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    def test_on_created_ignore(self, _remote_create_folder, _os):
        _remote_create_folder.return_value = True
        _os.path.abspath.return_value = "/a/test.py"
        _event = FileCreatedEvent(src_path="/a/test.py")
        self.handler.on_created(_event)
        self.assertEqual(_remote_create_folder.call_count, 0)

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    @mock.patch("specchio.handlers.rsync")
    def test_on_modified(self, _rsync, _remote_create_folder, _os):
        with mock.patch.object(
                self.handler,
                "update_gitignore"
        ) as _update_gitignore:
            _rsync.return_value = True
            _remote_create_folder.return_value = True
            _os.path.abspath.return_value = "/a/.gitignore"
            _os.path.join.return_value = "/b/a/.gitignore"
            _update_gitignore.return_value = True
            _event = FileModifiedEvent(src_path="/a/.gitignore")
            self.handler.on_modified(_event)
            _rsync.assert_called_once_with(
                dst_ssh=self.handler.dst_ssh,
                src_path="/a/.gitignore",
                dst_path="/b/a/.gitignore"
            )
            _remote_create_folder.assert_called_once_with(
                dst_ssh=self.handler.dst_ssh,
                dst_path="/b/a/"
            )
            _update_gitignore.assert_called_once_with(
                "/a/.gitignore"
            )

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_create_folder")
    @mock.patch("specchio.handlers.rsync")
    def test_on_modifited_ignore(self, _rsync, _remote_create_folder, _os):
        _rsync.return_value = True
        _remote_create_folder.return_value = True
        _os.path.abspath.return_value = "/a/test.py"
        _event = FileModifiedEvent(src_path="/a/test.py")
        self.handler.on_modified(_event)
        self.assertEqual(_remote_create_folder.call_count, 0)
        self.assertEqual(_rsync.call_count, 0)

    @mock.patch("specchio.handlers.get_all_re")
    def test_update_gitignore(self, _get_all_re):
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
                    2: [re.compile(fnmatch.translate("1.py"))],
                    3: [re.compile(fnmatch.translate("test.py"))]
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

    def test_del_gitignore(self):
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
    @mock.patch("specchio.handlers.remote_rm")
    def test_on_deleted(self, _remote_rm, _os):
        with mock.patch.object(
            self.handler,
            "del_gitignore"
        ) as _del_gitignore:
            _os.path.abspath.return_value = "/a/.gitignore"
            _os.path.join.return_value = "/b/a/.gitignore"
            _remote_rm.return_value = True
            _del_gitignore.return_value = True
            _event = FileDeletedEvent(src_path="/a/.gitignore")
            self.handler.on_deleted(_event)
            _os.path.abspath.assert_called_once_with("/a/.gitignore")
            _os.path.join.assert_called_once_with(
                "/b/a/",
                ".gitignore"
            )
            _remote_rm.assert_called_once_with(
                dst_ssh=self.handler.dst_ssh,
                dst_path="/b/a/.gitignore"
            )
            _del_gitignore.assert_called_once_with("/a/.gitignore")

    @mock.patch("specchio.handlers.os")
    def test_on_delete_ignore(self, _os):
        _os.path.abspath.return_value = "/a/test.py"
        _event = FileDeletedEvent(src_path="/a/test.py")
        self.handler.on_deleted(_event)
        _os.path.abspath.assert_called_once_with(
            "/a/test.py"
        )
        self.assertEqual(_os.path.join.call_count, 0)

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.remote_mv")
    def test_on_moved(self, _mv, _os):
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
    def test_on_moved_all_ignore(self, _rsync, _mv, _create_folder, _rm, _os):
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
    def test_on_moved_src_ignore(self, _rsync, _create_folder, _os):
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
    def test_on_moved_dst_ignore(self, _rm, _os):
        _rm.return_value = True
        _os.path.abspath.side_effect = ["/a/1.py", "/a/test.py"]
        _os.path.join.side_effect = ["/b/a/1.py", "/b/a/test.py"]
        _event = FileMovedEvent(src_path="1.py", dest_path="/a/test.py")
        self.handler.on_moved(_event)
        _rm.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh,
            dst_path="/b/a/1.py"
        )

    @mock.patch("specchio.handlers.os")
    @mock.patch("specchio.handlers.rsync")
    @mock.patch("specchio.handlers.remote_create_folder")
    def test_init_remote(self, _create_folder, _rsync, _os):
        _os.walk.return_value = [["/a/", [], ["1.py", "2.py"]]]
        _os.path.abspath.side_effect = [
            "/a/", "/a/1.py", "/a/2.py"
        ]
        _os.path.join.side_effect = [
            "/b/a",
            "/a/1.py", "/b/a/1.py",
            "/a/2.py", "/b/a/2.py"
        ]
        _rsync.return_value = True
        _create_folder.return_value = True
        with mock.patch.object(self.handler, "is_ignore") as _is_ignore:
            _is_ignore.side_effect = [False, True, False]
            self.handler.init_remote()
        _create_folder.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh, dst_path="/b/a"
        )
        _rsync.assert_called_once_with(
            dst_ssh=self.handler.dst_ssh, src_path="/a/2.py",
            dst_path="/b/a/2.py",
        )
