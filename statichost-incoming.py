# -*- coding: utf-8 -*-

import mysql.connector

import signal
import logging
import inotify.adapters

import msgpack
import greenstalk

import multiprocessing as mp
from multiprocessing import Process, Queue, Lock
import time


_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
_LOGGER = logging.getLogger(__name__)

queue = greenstalk.Client(host='127.0.0.1', port=11300, encoding=None)

def _configure_logging():
    _LOGGER.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()

    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)

    _LOGGER.addHandler(ch)

def main():

    # TODO: Check for any files that already exist in incoming
    # If any exist, queue them for processing then start watching

    i = inotify.adapters.Inotify()

    i.add_watch(b'/opt/tazdij/statichost/incoming')

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                _LOGGER.info("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                             "WATCH-PATH=[%s] FILENAME=[%s]",
                             header.wd, header.mask, header.cookie, header.len, type_names,
                             watch_path.decode('utf-8'), filename.decode('utf-8'))
                if 'IN_CLOSE_WRITE' in type_names:
                    queue.put(msgpack.packb(watch_path + b'/' + filename))

    finally:
        i.remove_watch(b'/opt/tazdij/statichost/incoming')

if __name__ == '__main__':
    _configure_logging()
    main()
