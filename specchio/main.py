#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time

from watchdog.observers import Observer

from specchio.const import GENERAL_OPTIONS, MANUAL
from specchio.handlers import SpecchioEventHandler
from specchio.utils import init_logger, logger


def main():
    """Main function for specchio

    Example: specchio test/ user@host:test/

    :return: None
    """
    init_logger()
    _popen_str = os.popen("whereis ssh").read().strip()
    if _popen_str == "" or _popen_str == "ssh:":
        return logger.error("Specchio need `ssh`, "
                            "but there is no `ssh` in the system")
    _popen_str = os.popen("whereis rsync").read().strip()
    if _popen_str == "" or _popen_str == "rsync:":
        return logger.error("Specchio need `rsync`, "
                            "but there is no `rsync` in the system")
    if len(sys.argv) >= 3:
        src_path = sys.argv[-2].strip()
        dst_ssh, dst_path = sys.argv[-1].strip().split(":")
        option_valid = all((option in GENERAL_OPTIONS)
                           for option in sys.argv[1:-2])
        if option_valid:
            logger.info("Initialize Specchio")
            is_init_remote = "--init-remote" in sys.argv[1:-2]
            event_handler = SpecchioEventHandler(
                src_path=src_path, dst_ssh=dst_ssh, dst_path=dst_path,
                is_init_remote=is_init_remote
            )
            observer = Observer()
            observer.schedule(event_handler, src_path, recursive=True)
            observer.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
            logger.info("Specchio stopped, have a nice day :)")
        else:
            print MANUAL
    else:
        print MANUAL
