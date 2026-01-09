import argparse
import os
# -*- coding: utf-8 -*-
import sys
import threading
import time


class RepeatedTimer():
    """
    RepeatedTimer class to schedule jobs
    """

    # https://stackoverflow.com/questions/474528/how-to-repeatedly-execute-a-function-every-x-seconds
    def __init__(self, interval, function, *args, **kwargs):
        """
        Args:
            interval: interval time in seconds
            function: function to be called
            *args: args for the function
            **kwargs: kwargs for the function
        """
        self._timer = None
        self.interval = interval  # value in seconds
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self):
        """
        function to run in the timer.
        """
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        """
        Start the timer.
        """
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        """
        stop the timer
        """
        self._timer.cancel()
        self.is_running = False
