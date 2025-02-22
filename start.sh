#!/bin/bash
for pid in `ps aux|grep -P 'watch_dog.py|main.py'|grep -v grep|awk '{print $2}'`;do
    kill -9 $pid
done

nohup python3 main.py &> nohup.main &
nohup python3 watch_dog.py &> nohup.watch_dog &
exit