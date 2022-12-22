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
    def __init__(self):
        self._queue = []

    def put(self, job):
        self._queue.append(job)

    def is_alive(self):
        return True

    def work(self):
        while self._queue:
            current_job = self._queue.pop()
            current_job.start()
            while current_job.exitcode is None:
                ...

    def kill(self, job, command):
        ...
