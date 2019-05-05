from __future__ import division
import multiprocessing
import threading
import timeit


INCR_CORES_CNT = multiprocessing.cpu_count() + 1
REPEATS_CNT = 3


def fact(num):
    assert isinstance(num, int) and num >= 0
    result = 1
    cur_num = num
    while cur_num:
        result *= cur_num
        cur_num -= 1
    return result


def evaluate_fact_consequently(fact_num):
    for _ in range(INCR_CORES_CNT):
        _ = fact(fact_num)


def evaluate_fact_via_threads(fact_num):
    threads = []
    for _ in range(INCR_CORES_CNT):
        t = threading.Thread(target=fact, args=(fact_num,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def evaluate_fact_via_processes(fact_num):
    processes = []
    for _ in range(INCR_CORES_CNT):
        p = multiprocessing.Process(target=fact, args=(fact_num,))
        p.start()
        processes.append(p)
    for p in processes:
        p.join()


def estimate_appropriate_fact_basis():
    num = 500
    working_time = 0
    while working_time < 1:
        num *= 2
        working_time = timeit.timeit('fact(%d)' % num, setup='from __main__ import fact', number=1)
    return num


if __name__ == '__main__':
    fact_num = estimate_appropriate_fact_basis()

    stmt = 'evaluate_fact_consequently(fact_num)'
    setup = 'from __main__ import evaluate_fact_consequently, fact_num'
    consequent_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    stmt = 'evaluate_fact_via_threads(fact_num)'
    setup = 'from __main__ import evaluate_fact_via_threads, fact_num'
    threads_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    stmt = 'evaluate_fact_via_processes(fact_num)'
    setup = 'from __main__ import evaluate_fact_via_processes, fact_num'
    processes_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    print('average consequent time: %f' % (consequent_time / REPEATS_CNT))
    print('average threads time: %f' % (threads_time / REPEATS_CNT))
    print('average processes time: %f' % (processes_time / REPEATS_CNT))
