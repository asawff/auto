#!/bin/bash
for pid in `ps aux|grep -P 'watch_dog.py|main.py'|grep -v grep|awk '{print $2}'`;do
    kill -9 $pid
done