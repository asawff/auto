class PQueue:
    def __init__(self,comparator = None):
        self.__vec = [0]
        self.__size = 0
        if comparator != None:
            self.__comparator = comparator
        else:
            self.__comparator = lambda a,b : a < b

    def __len__(self):
        return self.__size

    def top(self):
        if self.__size > 0:
            return self.__vec[1]
        return None

    def push(self,obj):
        self.__size += 1
        self.__vec.append(obj)
        cur_idx = self.__size
        while cur_idx > 1 and self.__comparator(self.__vec[int(cur_idx/2)] , obj):
            self.__vec[cur_idx] = self.__vec[int(cur_idx/2)]
            cur_idx = int(cur_idx/2)
        self.__vec[cur_idx] = obj


    def pop(self):
        if self.__size == 0:
            return
        obj = self.__vec[self.__size]
        del self.__vec[self.__size]
        self.__size -= 1
        if self.__size == 0:
            return
        cur_idx = 1
        while 2*cur_idx <= self.__size:
            chd_idx = 2*cur_idx
            if chd_idx+1 <= self.__size and self.__comparator(self.__vec[chd_idx] , self.__vec[chd_idx+1]):
                chd_idx += 1
            if self.__comparator(obj , self.__vec[chd_idx]):
                self.__vec[cur_idx] = self.__vec[chd_idx]
                cur_idx = chd_idx
            else:
                break
        self.__vec[cur_idx] = obj




"""
import random
TEST_N = 1000
pq = PQueue(False)
v = []
for i in range(0,TEST_N):
    rd = random.randint(-10000000,10000000)
    pq.push(rd)
    v.append(rd)
    if pq.top() != min(v):
        print("ERROR")


for i in range(0,int(TEST_N/2)):
    mx_val = pq.top()
    pq.pop()

    j = 0
    while j<len(v):
        if v[j] != mx_val:
            j += 1
        else:
            break
    del v[j]

    if len(v) >0 and pq.top() != min(v):
        print("ERROR")

for i in range(0,TEST_N):
    rd = random.randint(-10000000,10000000)
    pq.push(rd)
    v.append(rd)
    if pq.top() != min(v):
        print("ERROR")

for i in range(0,int(TEST_N/2)):
    mx_val = pq.top()
    pq.pop()

    j = 0
    while j<len(v):
        if v[j] != mx_val:
            j += 1
        else:
            break
    del v[j]

    if len(v) >0 and pq.top() != min(v):
        print("ERROR")

print("%d %d"%(len(pq),len(v)))
"""