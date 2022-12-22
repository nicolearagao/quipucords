from datetime import datetime
from multiprocessing import Process


class SingletonMeta(type):
    """
    Metaclass designed to force classes to behave as singletons.

    Shamelesly copied from https://refactoring.guru/design-patterns/singleton
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class DummyScanManager(metaclass=SingletonMeta):
    WORK_TIMEOUT_SECONDS = 9

    def __init__(self):
        self._queue = []
        self._start_dt = None

    def put(self, job):
        self._queue.append(job)

    def is_alive(self):
        return True

    @property
    def timed_out(self):
        elapsed_time = datetime.now() - self._start_dt
        if elapsed_time.seconds > self.WORK_TIMEOUT_SECONDS:
            return True
        return False

    def work(self):
        self._start_dt = datetime.now()
        if self.timed_out:
            return
        while self._queue:
            current_job: Process = self._queue.pop()
            current_job.start()
            while current_job.exitcode is None:
                if self.timed_out:
                    current_job.kill()
                    return

    def kill(self, job, command):
        ...
