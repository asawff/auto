#!/bin/bash


funSeperate(){
    root=/
    g_res=`echo $1|grep /`
    if [ $g_res ];then
        len=${#1}
        pos=$((len-1))
        while [ 1 ];do
            if [ "${1:$pos:1}" = "/" ];then
                break;
            fi
            pos=$((pos-1))
        done
        echo "${root}${1:0:$pos} $1"
    else
        echo "$root $1"
    fi
}


mapdir=''
if [ $1 ];then
    mapdir=$1
else
    mapdir="AutoTrade"
fi
echo "[Map] ./ ==> $mapdir"
cnt=0
dirmsg=''
for f in `git status -s|awk '{print $2}'`;do
    dir_f=`funSeperate $f`
    a[$cnt]=$dir_f
    if [ $cnt -eq 0 ];then
        dirmsg=$dir_f
    else
        dirmsg="$dirmsg $dir_f"
    fi
    cnt=$((cnt+1))

done

cnt=0
for f in `echo $dirmsg|sort`;do
    if [ $((cnt%2==0)) -eq 1 ];then
    #偶数
        if [ $cnt -eq 0 ];then
            dir=$f
        else
            if [ $dir != $f ];then
                echo "[dir]=[$dir]"
                echo "[flist]=[$flist]"
                scp $flist ayun:~/$mapdir$dir
                dir=$f
                flist=''
            fi
        fi
    else
    #奇数
        if [ $cnt -eq 1 ];then
            flist=$f
        else
            flist="$flist $f"
        fi
    fi
    cnt=$((cnt+1))
done
echo "[dir]=[$dir]"
echo "[flist]=[$flist]"
scp $flist ayun:~/$mapdir$dir