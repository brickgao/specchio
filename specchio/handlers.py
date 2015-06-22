#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from watchdog.events import (DirCreatedEvent, FileModifiedEvent,
                             FileSystemEventHandler)

from specchio.utils import remote_create_folder, remote_rm, rsync


class SpecchioEventHandler(FileSystemEventHandler):

    def __init__(self, gitignore_dict, src_path, dst_ssh, dst_path):
        """Constructor of `SpecchioEventHandler`

        :param gitignore_dict: dict -- the return value of
                                       specchio.utils.get_all_re
        :param src_path: str -- source path
        :param dst_ssh: str -- user name and host name of destination path
                               just like: user@host
        :param dst_path: str -- destination path
        :return: None
        """
        self.gitignore_dict = gitignore_dict
        # Match file or folder from the nearest `.gitignore`
        _gitignore_list = sorted(gitignore_dict.keys())[::-1]
        for index in range(len(_gitignore_list)):
            # Change '/test/.gitignore' to '/test/'
            _gitignore_list[index] = _gitignore_list[index][:-10]
        self.gitignore_list = _gitignore_list
        self.src_path = src_path
        self.dst_ssh = dst_ssh
        self.dst_path = dst_path
        super(SpecchioEventHandler, self).__init__()

    def is_ignore(self, file_or_dir_path):
        for gitignore_path in self.gitignore_list:
            if file_or_dir_path.startswith(gitignore_path):
                for _re in self.gitignore_dict[gitignore_path][2]:
                    if _re.match(file_or_dir_path):
                        return False
                for _re in self.gitignore_dict[gitignore_path][3]:
                    if _re.match(file_or_dir_path):
                        return True
        return False

    # TODO if the file is `.gitignore`

    def on_created(self, event):
        if self.is_ignore(event.src_path()):
            return
        if isinstance(event, DirCreatedEvent):
            dst_path = os.path.join(self.dst_path, event.src_path())
            remote_create_folder(dst_ssh=self.dst_ssh, dst_path=dst_path)

    def on_modified(self, event):
        if self.is_ignore(event.src_path()):
            return
        if isinstance(event, FileModifiedEvent):
            dst_path = os.path.join(self.dst_path, event.src_path())
            abs_src_path = os.path.abspath(event.src_path())
            # Create folder of file
            dst_folder_path = dst_path[:-len(dst_path.split('/')[-1])]
            remote_create_folder(dst_ssh=self.dst_ssh,
                                 dst_path=dst_folder_path)
            rsync(dst_ssh=self.dst_ssh, src_path=abs_src_path,
                  dst_path=dst_path)

    def on_deleted(self, event):
        if self.is_ignore(event.src_path()):
            return
        dst_path = os.path.join(self.dst_path, event.src_path())
        remote_rm(dst_ssh=self.dst_ssh, dst_path=dst_path)
