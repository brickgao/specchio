#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from watchdog.events import (DirCreatedEvent, FileModifiedEvent,
                             FileSystemEventHandler)

from specchio.utils import (get_all_re, logger, remote_create_folder,
                            remote_mv, remote_rm, rsync, walk_get_gitignore)


class SpecchioEventHandler(FileSystemEventHandler):

    def __init__(self, src_path, dst_ssh, dst_path, is_init_remote=False):
        """Constructor of `SpecchioEventHandler`

        :param src_path: str -- source path
        :param dst_ssh: str -- user name and host name of destination path
                               just like: user@host
        :param dst_path: str -- destination path
        :param is_init_remote: bool -- initialize the file remotely or not
        :return: None
        """
        self.init_gitignore(src_path)
        self.src_path = src_path
        self.dst_ssh = dst_ssh
        self.dst_path = dst_path
        self.git_path = os.path.join(os.path.abspath(self.src_path),
                                     ".git/")
        super(SpecchioEventHandler, self).__init__()
        if is_init_remote:
            logger.info("Starting to initialize the file remotely first")
            self.init_remote()
            logger.info("Initialization of the remote file has been done")

    def init_remote(self):
        # Rsync all files to remote system
        for root_path, dirs_path, files_path in os.walk(self.src_path):
            relative_src_folder_path = self.get_relative_src_path(
                root_path
            )
            dst_folder_path = os.path.join(
                self.dst_path, relative_src_folder_path
            )
            remote_create_folder(dst_ssh=self.dst_ssh,
                                 dst_path=dst_folder_path)
            for file_path in files_path:
                src_file_path = os.path.join(root_path, file_path)
                abs_src_file_path = os.path.abspath(src_file_path)
                relative_src_file_path = self.get_relative_src_path(
                    src_file_path
                )
                dst_file_path = os.path.join(
                    self.dst_path, relative_src_file_path
                )
                if not self.is_ignore(abs_src_file_path):
                    rsync(dst_ssh=self.dst_ssh, src_path=abs_src_file_path,
                          dst_path=dst_file_path)

    def is_ignore(self, file_or_dir_path):
        if file_or_dir_path.startswith(self.git_path):
            return True
        for gitignore_folder_path in self.gitignore_list:
            gitignore_path = gitignore_folder_path + ".gitignore"
            if file_or_dir_path.startswith(gitignore_folder_path):
                _relative_file_or_dir_path = (
                    file_or_dir_path[len(gitignore_folder_path):]
                )
                for _re in self.gitignore_dict[gitignore_path][2]:
                    if _re.match(_relative_file_or_dir_path):
                        return False
                for _re in self.gitignore_dict[gitignore_path][3]:
                    if _re.match(_relative_file_or_dir_path):
                        return True
        return False

    def init_gitignore(self, src_path):
        logger.info("Loading ignore pattern from all `.gitignore`")
        gitignore_list = walk_get_gitignore(src_path)
        self.gitignore_dict = get_all_re(gitignore_list)
        # Match file or folder from the nearest `.gitignore`
        _gitignore_list = sorted(self.gitignore_dict.keys())[::-1]
        for index in range(len(_gitignore_list)):
            # Change '/test/.gitignore' to '/test/'
            _gitignore_list[index] = _gitignore_list[index][:-10]
        self.gitignore_list = _gitignore_list
        logger.info("All ignore pattern has been loaded")

    def update_gitignore(self, gitignore_path):
        _re_dict = get_all_re([gitignore_path])
        self.gitignore_dict.update(_re_dict)
        self.gitignore_list.append(gitignore_path[:-10])
        self.gitignore_list = sorted(self.gitignore_list)[::-1]

    def del_gitignore(self, gitignore_path):
        del self.gitignore_dict[gitignore_path]
        self.gitignore_list.remove(gitignore_path[:-10])

    def get_relative_src_path(self, path):
        _src_path = (self.src_path if self.src_path.endswith("/")
                     else self.src_path + "/")
        ret = path[len(_src_path):]
        return "" if ret == "." else ret

    def on_created(self, event):
        abs_src_path = os.path.abspath(event.src_path)
        if self.is_ignore(abs_src_path):
            return
        relative_path = self.get_relative_src_path(event.src_path)
        dst_path = os.path.join(self.dst_path, relative_path)
        if isinstance(event, DirCreatedEvent):
            logger.info("Create {} remotely".format(dst_path))
            remote_create_folder(dst_ssh=self.dst_ssh, dst_path=dst_path)
        else:
            dst_path = os.path.join(self.dst_path, relative_path)
            # Create folder of file
            dst_folder_path = dst_path[:-len(dst_path.split("/")[-1])]
            remote_create_folder(dst_ssh=self.dst_ssh,
                                 dst_path=dst_folder_path)
            logger.info("Rsync {} remotely".format(dst_path))
            rsync(dst_ssh=self.dst_ssh, src_path=abs_src_path,
                  dst_path=dst_path)
            if dst_path.split("/")[-1] == ".gitignore":
                logger.info("Update ignore pattern, because changed "
                            "file({}) named `.gitignore` locally".format(
                                abs_src_path
                            ))
                self.update_gitignore(abs_src_path)

    def on_modified(self, event):
        abs_src_path = os.path.abspath(event.src_path)
        if self.is_ignore(abs_src_path):
            return
        if isinstance(event, FileModifiedEvent):
            relative_path = self.get_relative_src_path(event.src_path)
            dst_path = os.path.join(self.dst_path, relative_path)
            # Create folder of file
            dst_folder_path = dst_path[:-len(dst_path.split("/")[-1])]
            # If the file is `.gitignore`, update gitignore dict and list
            if dst_path.split("/")[-1] == ".gitignore":
                logger.info("Update ignore pattern, because changed "
                            "file({}) named `.gitignore` locally".format(
                                abs_src_path
                            ))
                self.update_gitignore(abs_src_path)
            remote_create_folder(dst_ssh=self.dst_ssh,
                                 dst_path=dst_folder_path)
            logger.info("Rsync {} remotely".format(dst_path))
            rsync(dst_ssh=self.dst_ssh, src_path=abs_src_path,
                  dst_path=dst_path)

    def on_deleted(self, event):
        abs_src_path = os.path.abspath(event.src_path)
        if self.is_ignore(abs_src_path):
            return
        relative_path = self.get_relative_src_path(event.src_path)
        dst_path = os.path.join(self.dst_path, relative_path)
        # If the file is `.gitignore`, remove this `gitignore` in dict and list
        if dst_path.split("/")[-1] == ".gitignore":
            logger.info("Remove some ignore pattern, because changed "
                        "file({}) named `.gitignore` locally".format(
                            abs_src_path
                        ))
            self.del_gitignore(abs_src_path)
        logger.info("Remove {} remotely".format(dst_path))
        remote_rm(dst_ssh=self.dst_ssh, dst_path=dst_path)

    def on_moved(self, event):
        abs_src_src_path = os.path.abspath(event.src_path)
        abs_src_dst_path = os.path.abspath(event.dest_path)
        src_ignore_tag, dst_ignore_tag = (
            self.is_ignore(abs_src_src_path), self.is_ignore(abs_src_dst_path)
        )
        relative_src_path = self.get_relative_src_path(event.src_path)
        relative_dst_path = self.get_relative_src_path(event.dest_path)
        dst_src_path = os.path.join(self.dst_path, relative_src_path)
        dst_dst_path = os.path.join(self.dst_path, relative_dst_path)
        if src_ignore_tag and dst_ignore_tag:
            return
        elif dst_ignore_tag:
            remote_rm(dst_ssh=self.dst_ssh, dst_path=dst_src_path)
            logger.info("Remove {} remotely".format(dst_src_path))
        elif src_ignore_tag:
            dst_folder_path = dst_dst_path[:-len(dst_dst_path.split("/")[-1])]
            remote_create_folder(dst_ssh=self.dst_ssh,
                                 dst_path=dst_folder_path)
            rsync(dst_ssh=self.dst_ssh, src_path=abs_src_dst_path,
                  dst_path=dst_dst_path)
            logger.info("Rsync {} remotely".format(dst_dst_path))
        else:
            remote_mv(dst_ssh=self.dst_ssh, src_path=dst_src_path,
                      dst_path=dst_dst_path)
            logger.info("Move {} to {} remotely".format(
                dst_src_path, dst_dst_path
            ))
        logger.info("Because of move method, try to update all ignore pattern")
        self.init_gitignore(self.src_path)
