#!/bin/bash -vx
#
# SCMメインメニュー
#
# Usage : MENU.CGI
#
# Written by Katsuya Bando () : 2018/11/15

# 走行ログ
home=/home/$(whoami)
logd=$home/LOG
logfile=$logd/LOG.$(basename $0).$(date +%Y%m%d_%H%M%S)
exec 2> $logfile

# 変数の定義
export LANG=ja_JP.UTF-8
export PATH=/home/UTL:/home/TOOL:$PATH
tmp=/tmp/tmp_$(basename $0)_$$
todayhms=$(date +%Y%m%d%H%M%S)
curtime="$(dayslash -d $todayhms --output 'yyyy年 mm月 dd日 HH:MM:SS')"
today=$(date +%Y%m%d)
todayhms=$(date +%Y%m%d%H%M%S)

# ディレクトリの定義
semd=$home/SEMAPHORE
appd=$home/SCM/SIRE
cgid=$appd/CGI
htmd=$appd/HTML

# エラーチェックとエラー終了処理の定義
ERROR_CHECK(){
        [ $(plus ${PIPESTATUS[@]}) -eq 0 ] && return
        message=$1
        echo "Content-type:text/html charset=utf-8"
        echo ""
        echo "Error[$(basename $0)] : $message" 1>&2
        echo "$HOSTNAME $(basename $0) ERROR $(date +%Y%m%d_%H%M%S)" >> $logd/UP                                                                                               CNT
        touch $semd/$(basename $0).$HOSTNAME.ERROR.$today
        exit 1
}

# 起動処理
echo "$HOSTNAME $(basename $0) START $(date +%Y%m%d_%H%M%S)" >> $logd/UPCNT
touch $semd/$(basename $0).$HOSTNAME.START.$today

################################################################################                                                                                               ################
# ログインチェック

# 省略
loginid="_"
loginname="_"

################################################################################                                                                                               ################
# 出力内容の作成
: > $tmp-calsed
echo "###LOGINID###"   "$loginid"   >> $tmp-calsed
echo "###LOGINNAME###" "$loginname" >> $tmp-calsed

################################################################################                                                                                               ################
# ＨＴＭＬ出力
cat $htmd/MENU.HTML |
calsed '###LOGIN_ID###' "$loginid" |
calsed '###CURRENT_TIME###' "$curtime" |
calsed -f $tmp-calsed                         > $tmp-html
ERROR_CHECK ＨＴＭＬ作成エラー

################################################################################                                                                                               ################
# ＣＧＩ出力
echo "Content-type:text/html charset=utf-8"
echo ""

cat $tmp-html
ERROR_CHECK 出力エラー

################################################################################                                                                                               ################
# 正常終了処理
echo "$HOSTNAME $(basename $0) END $(date +%Y%m%d_%H%M%S)" >> $logd/UPCNT
touch $semd/$(basename $0).$HOSTNAME.END.$today

rm -rf $tmp-*
rm -f $logfile
exit 0
