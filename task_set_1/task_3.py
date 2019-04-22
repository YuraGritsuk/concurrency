from __future__ import division
import multiprocessing
import threading
import timeit

import requests

try:
    from Queue import Queue
except ImportError:
    from queue import Queue


INCR_CORES_CNT = multiprocessing.cpu_count() + 1
REPEATS_CNT = 3
URLS = [
    'http://www.sample-videos.com/video/mp4/720/big_buck_bunny_720p_2mb.mp4',
    'http://www.sample-videos.com/video/mp4/480/big_buck_bunny_480p_2mb.mp4',
    'http://www.sample-videos.com/video/mp4/360/big_buck_bunny_360p_2mb.mp4',
    'http://www.sample-videos.com/video/mp4/240/big_buck_bunny_240p_2mb.mp4',
    'http://www.sample-videos.com/video/flv/720/big_buck_bunny_720p_2mb.mp4',
    'http://www.sample-videos.com/video/flv/480/big_buck_bunny_480p_2mb.mp4',
    'http://www.sample-videos.com/video/flv/360/big_buck_bunny_360p_2mb.mp4',
    'http://www.sample-videos.com/video/flv/240/big_buck_bunny_240p_2mb.mp4',
    'http://www.sample-videos.com/video/mkv/720/big_buck_bunny_720p_2mb.mp4',
    'http://www.sample-videos.com/video/mkv/480/big_buck_bunny_480p_2mb.mp4',
    'http://www.sample-videos.com/video/mkv/360/big_buck_bunny_360p_2mb.mp4',
    'http://www.sample-videos.com/video/mkv/240/big_buck_bunny_240p_2mb.mp4',
]


def grab_files_consequently(urls):
    for url in urls:
        _ = requests.get(url)


def grab_files_via_threads(urls):
    def download_file_in_thread():
        while not q.empty():
            url = q.get()
            _ = requests.get(url)
            q.task_done()

    q = Queue()
    for url in urls:
        q.put(url)
    for _ in range(INCR_CORES_CNT):
        threading.Thread(target=download_file_in_thread).start()
    q.join()


def grab_files_via_processes(urls):
    def download_file_in_process():
        while not q.empty():
            url = q.get()
            _ = requests.get(url)
            q.task_done()

    q = multiprocessing.JoinableQueue()
    for url in urls:
        q.put(url)
    for _ in range(INCR_CORES_CNT):
        multiprocessing.Process(target=download_file_in_process).start()
    q.join()


if __name__ == '__main__':
    stmt = 'grab_files_consequently(URLS)'
    setup = 'from __main__ import grab_files_consequently, URLS'
    consequent_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    stmt = 'grab_files_via_threads(URLS)'
    setup = 'from __main__ import grab_files_via_threads, URLS'
    threads_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    stmt = 'grab_files_via_processes(URLS)'
    setup = 'from __main__ import grab_files_via_processes, URLS'
    processes_time = timeit.timeit(stmt=stmt, setup=setup, number=REPEATS_CNT)

    print('average consequent time: %f' % (consequent_time / REPEATS_CNT))
    print('average threads time: %f' % (threads_time / REPEATS_CNT))
    print('average processes time: %f' % (processes_time / REPEATS_CNT))
