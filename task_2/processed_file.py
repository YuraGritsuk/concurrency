from __future__ import print_function

from contextlib import contextmanager
from functools import wraps
import multiprocessing as mp
import os
import random
import signal
import tempfile
from time import sleep

from .command_line_parser import setup_parser


def ignore_ctrl_c(func):
    @wraps(func)
    def deco(*args, **kwargs):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        return func(*args, **kwargs)
    return deco


class _SwitchMode(object):
    def __init__(self, can_read, can_write):
        self.__read_mode = mp.Lock()
        self.__can_read = can_read
        self.__readers_cnt = mp.Value('i', 0)
        self.__write_mode = mp.Lock()
        self.__can_write = can_write
        self.__writers_cnt = mp.Value('i', 0)

    @contextmanager
    def write_mode(self):
        self.write_mode_acquire()
        try:
            yield
        finally:
            self.write_mode_release()

    def write_mode_acquire(self):
        with self.__write_mode:
            if not self.__writers_cnt.value:
                self.__can_read.acquire()
            self.__writers_cnt.value += 1

    def write_mode_release(self):
        with self.__write_mode:
            self.__writers_cnt.value -= 1
            if not self.__writers_cnt.value:
                self.__can_read.release()

    @contextmanager
    def read_mode(self):
        self.read_mode_acquire()
        try:
            yield
        finally:
            self.read_mode_release()

    def read_mode_acquire(self):
        with self.__read_mode:
            if not self.__readers_cnt.value:
                self.__can_write.acquire()
            self.__readers_cnt.value += 1

    def read_mode_release(self):
        with self.__read_mode:
            self.__readers_cnt.value -= 1
            if not self.__readers_cnt.value:
                self.__can_write.release()


class RWLock(_SwitchMode, object):
    def __init__(self, sim_readers_cnt):
        self.__can_write = mp.Lock()
        self.__can_read = mp.Lock()
        self.__max_sim_readers = mp.BoundedSemaphore(sim_readers_cnt)
        self.__one_reader = mp.Lock()
        super(RWLock, self).__init__(self.__can_read, self.__can_write)

    @contextmanager
    def write_lock(self):
        with self.write_mode():
            with self.__can_write:
                yield

    @contextmanager
    def read_lock(self):
        with self.__max_sim_readers:
            with self.__one_reader:
                with self.__can_read:
                    self.read_mode_acquire()
            try:
                yield
            finally:
                self.read_mode_release()


class ProcessedFile(RWLock, object):
    def __init__(self, file_path, readers_cnt=10, writers_cnt=2, sim_readers_cnt=3, write_gap=50):
        self.file_path = file_path
        self.readers_cnt = readers_cnt
        self.writers_cnt = writers_cnt
        self.sim_readers_cnt = sim_readers_cnt
        self.write_gap = write_gap

        self._cnt = mp.Value('i', 0)
        self._closed = mp.Event()
        self.__print_msg_lock = mp.Lock()
        super(ProcessedFile, self).__init__(self.sim_readers_cnt)

    def _print_msg(self, msg):
        with self.__print_msg_lock:
            print(msg)

    @ignore_ctrl_c
    def _write_forever(self):
        try:
            while not self._closed.is_set():
                with self.write_lock():
                    with open(self.file_path, 'w') as file_:
                        file_.write('%s %s' % (mp.current_process().ident, self._cnt.value))
                    self._cnt.value += 1
                sleep(random.uniform(0, self.write_gap * 1e-3))
        except Exception as e:
            self._print_msg(e)
            self._closed.set()

    @ignore_ctrl_c
    def _read_forever(self):
        try:
            while not self._closed.is_set():
                with self.read_lock():
                    with open(self.file_path) as file_:
                        file_content = file_.read()
                        msg = '%s: %s' % (mp.current_process().name, file_content)
                self._print_msg(msg)
        except Exception as e:
            self._print_msg(e)
            self._closed.set()

    def share(self):
        with open(self.file_path, 'w'):
            pass

        w_processes = [mp.Process(target=self._write_forever) for _ in range(self.writers_cnt)]
        for w in w_processes:
            w.start()
        r_processes = [mp.Process(target=self._read_forever) for _ in range(self.readers_cnt)]
        for r in r_processes:
            r.start()

        try:
            while not self._closed.is_set():
                sleep(0.1)
        except KeyboardInterrupt:
            self._closed.set()
        finally:
            print('Waiting for terminating r/w processes')
            for w in w_processes:
                w.join()
            for r in w_processes:
                r.join()


if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    _, file_path = tempfile.mkstemp()
    pf = ProcessedFile(file_path, args.readers_cnt, args.writers_cnt, args.sim_readers_cnt, args.write_gap)
    try:
        pf.share()
    finally:
        os.remove(file_path)
