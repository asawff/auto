import threading
class Queue:
    def __init__(self):
        self.__vec = []

    def __len__(self):
        return len(self.__vec)

    def push(self,obj):
        self.__vec.append(obj)

    def front(self):
        if len(self.__vec) == 0:
            return None
        else:
            return self.__vec[0]

    def pop(self):
        ret = self.front()
        if ret != None:
            del self.__vec[0]

class ConcurrentQueue:
    def __init__(self):
        self.__q = Queue()
        self.__sem_s = threading.Semaphore(1)
        self.__sem_n = threading.Semaphore(0)

    def put(self,o):
        self.__sem_s.acquire()
        self.__q.push(o)
        self.__sem_s.release()
        self.__sem_n.release()

    def get_with_wait(self):
        self.__sem_n.acquire()
        self.__sem_s.acquire()
        o = self.__q.front()
        self.__q.pop()
        self.__sem_s.release()
        return o
