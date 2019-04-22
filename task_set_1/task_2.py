from __future__ import division
import multiprocessing
import threading
import timeit
from time import sleep


INCR_CORES_CNT = multiprocessing.cpu_count() + 1
REPEATS_CNT = 3
SLEEP_SECS = 1


def execute_sleep_consequently():
    for _ in range(INCR_CORES_CNT):
        sleep(SLEEP_SECS)


def execute_sleep_via_threads():
    threads = []
    for _ in range(INCR_CORES_CNT):
        t = threading.Thread(target=sleep, args=(SLEEP_SECS,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def execute_sleep_via_processes():
    processes = []
    for _ in range(INCR_CORES_CNT):
        p = multiprocessing.Process(target=sleep, args=(SLEEP_SECS,))
        p.start()
        processes.append(p)
    for p in processes:
        p.join()


if __name__ == '__main__':
    stmt = 'execute_sleep_consequently()'
    setup = 'from __main__ import execute_sleep_consequently'
    consequent_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    stmt = 'execute_sleep_via_threads()'
    setup = 'from __main__ import execute_sleep_via_threads'
    threads_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    stmt = 'execute_sleep_via_processes()'
    setup = 'from __main__ import execute_sleep_via_processes'
    processes_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    print('average consequent time: %f' % (consequent_time / REPEATS_CNT))
    print('average threads time: %f' % (threads_time / REPEATS_CNT))
    print('average processes time: %f' % (processes_time / REPEATS_CNT))
