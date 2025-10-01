import abc
from abc import ABC


class RedisType(ABC):
    @abc.abstractmethod
    def load(self):
        pass
