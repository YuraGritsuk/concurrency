import argparse


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-N', '--readers-cnt', type=int, default=10,
                        help='Amount of threads trying to read from file')
    parser.add_argument('-n', '--sim-readers-cnt', type=int, default=3,
                        help='Amount of threads that can read simultaneously from file')
    parser.add_argument('-W', '--writers-cnt', type=int, default=2,
                        help='Amount of threads trying to write in file')
    parser.add_argument('-T', '--write-gap', type=int, default=50,
                        help='Max time gap before next writer will try to write in file')
    return parser
