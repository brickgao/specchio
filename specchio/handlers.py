#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from watchdog.events import (DirCreatedEvent, FileModifiedEvent,
                             FileSystemEventHandler)

from specchio.utils import (dfs_get_gitignore, get_all_re,
                            remote_create_folder, remote_mv, remote_rm, rsync)


class SpecchioEventHandler(FileSystemEventHandler):

    def __init__(self, src_path, dst_ssh, dst_path):
        """Constructor of `SpecchioEventHandler`

        :param src_path: str -- source path
        :param dst_ssh: str -- user name and host name of destination path
                               just like: user@host
        :param dst_path: str -- destination path
        :return: None
        """
        self.init_gitignore(src_path)
        self.src_path = src_path
        self.dst_ssh = dst_ssh
        self.dst_path = dst_path
        super(SpecchioEventHandler, self).__init__()

    def is_ignore(self, file_or_dir_path):
        for gitignore_folder_path in self.gitignore_list:
            gitignore_path = gitignore_folder_path + ".gitignore"
            if file_or_dir_path.startswith(gitignore_folder_path):
                for _re in self.gitignore_dict[gitignore_path][2]:
                    if _re.match(file_or_dir_path):
                        return False
                for _re in self.gitignore_dict[gitignore_path][3]:
                    if _re.match(file_or_dir_path):
                        return True
        return False

    def init_gitignore(self, src_path):
        gitignore_list = dfs_get_gitignore(src_path)
        self.gitignore_dict = get_all_re(gitignore_list)
        # Match file or folder from the nearest `.gitignore`
        _gitignore_list = sorted(self.gitignore_dict.keys())[::-1]
        for index in range(len(_gitignore_list)):
            # Change '/test/.gitignore' to '/test/'
            _gitignore_list[index] = _gitignore_list[index][:-10]
        self.gitignore_list = _gitignore_list

    def update_gitignore(self, gitignore_path):
        _re_dict = get_all_re([gitignore_path])
        self.gitignore_dict.update(_re_dict)
        self.gitignore_list.append(gitignore_path[:-10])
        self.gitignore_list = sorted(self.gitignore_list)[::-1]

    def del_gitignore(self, gitignore_path):
        del self.gitignore_dict[gitignore_path]
        self.gitignore_list.remove(gitignore_path[:-10])

    def on_created(self, event):
        abs_src_path = os.path.abspath(event.src_path)
        if self.is_ignore(abs_src_path):
            return
        if isinstance(event, DirCreatedEvent):
            dst_path = os.path.join(self.dst_path, event.src_path)
            remote_create_folder(dst_ssh=self.dst_ssh, dst_path=dst_path)

    def on_modified(self, event):
        abs_src_path = os.path.abspath(event.src_path)
        if self.is_ignore(abs_src_path):
            return
        if isinstance(event, FileModifiedEvent):
            dst_path = os.path.join(self.dst_path, event.src_path)
            # Create folder of file
            dst_folder_path = dst_path[:-len(dst_path.split("/")[-1])]
            # If the file is `.gitignore`, update gitignore dict and list
            if dst_path.split("/")[-1] == ".gitignore":
                self.update_gitignore(abs_src_path)
            remote_create_folder(dst_ssh=self.dst_ssh,
                                 dst_path=dst_folder_path)
            rsync(dst_ssh=self.dst_ssh, src_path=abs_src_path,
                  dst_path=dst_path)

    def on_deleted(self, event):
        abs_src_path = os.path.abspath(event.src_path)
        if self.is_ignore(abs_src_path):
            return
        dst_path = os.path.join(self.dst_path, event.src_path)
        # If the file is `.gitignore`, remove this `gitignore` in dict and list
        if dst_path.split("/")[-1] == ".gitignore":
            self.del_gitignore(abs_src_path)
        remote_rm(dst_ssh=self.dst_ssh, dst_path=dst_path)

    def on_moved(self, event):
        abs_src_src_path = os.path.abspath(event.src_path)
        abs_src_dst_path = os.path.abspath(event.src_path)
        src_ignore_tag, dst_ignore_tag = (
            self.is_ignore(abs_src_src_path), self.is_ignore(abs_src_dst_path)
        )
        dst_src_path = os.path.join(self.dst_path, event.src_path)
        dst_dst_path = os.path.join(self.dst_path, event.dest_path)
        if src_ignore_tag and dst_ignore_tag:
            return
        elif dst_ignore_tag:
            remote_rm(dst_ssh=self.dst_ssh, dst_path=dst_src_path)
        elif src_ignore_tag:
            dst_folder_path = dst_dst_path[:-len(dst_dst_path.split("/")[-1])]
            remote_create_folder(dst_ssh=self.dst_ssh,
                                 dst_path=dst_folder_path)
            rsync(dst_ssh=self.dst_ssh, src_path=abs_src_dst_path,
                  dst_path=dst_dst_path)
        else:
            remote_mv(dst_ssh=self.dst_ssh, src_path=dst_src_path,
                      dst_path=dst_dst_path)
        self.init_gitignore(self.src_path)
