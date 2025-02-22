import time
import datetime
from concurrent.futures import ThreadPoolExecutor

class DailySchJob:
    def __init__(self,thd_pool_size=10):
        self.__job_list = []
        self.__thd_pool = ThreadPoolExecutor(max_workers=thd_pool_size)

    def add(self,hour,minute,second,f,syn_mod=True,args=()):
        self.__job_list.append((hour*3600+minute*60+second,f,syn_mod,args))

    def _now_sec(self):
        now_dt = datetime.datetime.now()
        return now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second

    def run(self):
        self.__job_list = sorted(self.__job_list,key=lambda job:job[0])
        job_num = len(self.__job_list)
        if job_num == 0:return
        now_sec = self._now_sec()
        next_job_idx = 0
        while now_sec >= self.__job_list[next_job_idx][0]:
            next_job_idx += 1
            if next_job_idx == job_num:
                next_job_idx = 0
                now_sec -= 86400
        while True:
            sleep_tm = self.__job_list[next_job_idx][0]-now_sec
            if sleep_tm > 0:
                time.sleep(sleep_tm)
            job_item = self.__job_list[next_job_idx]
            if job_item[2]:
                job_item[1](*job_item[3])
            else:
                self.__thd_pool.submit(job_item[1],*job_item[3])
            next_job_idx += 1
            now_sec = self._now_sec()
            if next_job_idx == job_num:
                next_job_idx = 0
                now_sec -= 86400


if __name__ == "__main__":
    def _tf(a,b,c,d):
        print(a,b,c,d)
        time.sleep(10)

    schjobmgr = DailySchJob()
    schjobmgr.add(18,17,0,_tf,args=[1,2,3,4])
    schjobmgr.add(18,17,1,_tf,args=[6,7,8,9])
    schjobmgr.run()