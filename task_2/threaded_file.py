from __future__ import print_function

from contextlib import contextmanager
import os
import random
import tempfile
import threading
from time import sleep

from .command_line_parser import setup_parser


class _SwitchMode(object):
    def __init__(self, mode_lock):
        self._counter = 0
        self._mutex = threading.Lock()
        self._mode_lock = mode_lock

    def acquire(self):
        with self._mutex:
            if not self._counter:
                self._mode_lock.acquire()
            self._counter += 1

    __enter__ = acquire

    def release(self):
        with self._mutex:
            self._counter -= 1
            if not self._counter:
                self._mode_lock.release()

    def __exit__(self, *_):
        self.release()


class RWLock(object):
    def __init__(self, max_readers_cnt=1):
        self.max_readers_cnt = max_readers_cnt
        self._can_read = threading.Lock()
        self._can_write = threading.Lock()
        self._read_mode = _SwitchMode(self._can_write)
        self._write_mode = _SwitchMode(self._can_read)
        self._one_reader = threading.Lock()
        self._max_sim_readers = threading.BoundedSemaphore(max_readers_cnt)

    @contextmanager
    def read(self):
        with self._max_sim_readers:
            with self._one_reader:
                with self._can_read:
                    self._read_mode.acquire()
            try:
                yield
            finally:
                self._read_mode.release()

    @contextmanager
    def write(self):
        with self._write_mode:
            with self._can_write:
                yield


class ThreadedFile(object):
    def __init__(self, file_path, readers_cnt=10, writers_cnt=2, sim_readers_cnt=3, write_gap=50):
        self._file_path = file_path
        self._readers_cnt = readers_cnt
        self._writers_cnt = writers_cnt
        self._sim_readers_cnt = sim_readers_cnt
        self._write_gap = write_gap
        self._rwlock = RWLock(sim_readers_cnt)
        self._closed = threading.Event()
        self._print_msg_lock = threading.Lock()
        self._cnt = 0

    def _print_msg(self, msg):
        with self._print_msg_lock:
            print(msg)

    def _read_forever(self):
        try:
            while not self._closed.is_set():
                with self._rwlock.read():
                    with open(self._file_path, 'r') as file_:
                        file_content = file_.read()
                msg = '%s: %s' % (threading.current_thread().name, file_content)
                self._print_msg(msg)
        except Exception as e:
            self._print_msg(e)
            self._closed.set()

    def _write_forever(self):
        try:
            while not self._closed.is_set():
                with self._rwlock.write():
                    with open(self._file_path, 'w') as file_:
                        msg = '%s %s' % (threading.current_thread().ident, self._cnt)
                        file_.write(msg)
                    self._cnt += 1
                sleep(random.uniform(0, self._write_gap * 1e-3))
        except Exception as e:
            self._print_msg(e)
            self._closed.set()

    def share(self):
        if not os.path.exists(self._file_path):
            with open(self._file_path, 'w'):
                pass
        self._closed.clear()

        w_threads = [threading.Thread(target=self._write_forever) for _ in range(self._writers_cnt)]
        r_threads = [threading.Thread(target=self._read_forever) for _ in range(self._readers_cnt)]
        for w_thr in w_threads:
            w_thr.start()
        for r_thr in r_threads:
            r_thr.start()

        try:
            while not self._closed.is_set():
                sleep(0.1)
        except KeyboardInterrupt:
            self._closed.set()
        finally:
            print('Waiting readers/writers exiting...')
            for r_thr in r_threads:
                r_thr.join()
            for w_thr in w_threads:
                w_thr.join()


if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    _, file_path = tempfile.mkstemp()
    tf = ThreadedFile(file_path, args.readers_cnt, args.writers_cnt, args.sim_readers_cnt, args.write_gap)
    try:
        tf.share()
    finally:
        os.remove(file_path)
