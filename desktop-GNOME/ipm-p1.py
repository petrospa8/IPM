#!/usr/bin/env python3
# coding: utf-8

from controller import Controller

Controller()

if __name__ == '__main__':
    # Workaround for CTRL-C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
