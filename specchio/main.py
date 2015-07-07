#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time

from watchdog.observers import Observer

from specchio.handlers import SpecchioEventHandler
from specchio.utils import init_logger, logger


def main():
    """Main function for specchio

    Example: specchio test/ user@host:test/

    :return: None
    """
    init_logger()
    if os.popen("whereis ssh").read() == "":
        return logger.error("Specchio need `ssh`, "
                            "but there is no `ssh` in the system")
    if os.popen("whereis rsync").read() == "":
        return logger.error("Specchio need `rsync`, "
                            "but there is no `rsync` in the system")
    if len(sys.argv) == 3:
        src_path = sys.argv[1].strip()
        dst_ssh, dst_path = sys.argv[2].strip().split(":")
        logger.info("Initialize Specchio")
        event_handler = SpecchioEventHandler(
            src_path=src_path, dst_ssh=dst_ssh, dst_path=dst_path
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
        print """Usage: specchio src/ user@host:dst/"""
