#!/bin/bash -vx
#
# SIRE_SHOKAI.CGI
#
# 仕入伝票照会
#
# K.Bando ()
# 2018/12/18
####################################################################

####################################################################
# ログ設定
####################################################################
logfile=/home/$(whoami)/LOG/LOG.$(basename $0).$(date +%Y%m%d_%H%M%S).$$
exec 2> $logfile


####################################################################
# 環境変数設定 
####################################################################
PATH=/home/UTL:/home/TOOL:$PATH
LANG=ja_JP.UTF-8


####################################################################
# エラーチェックと終了処理の定義 
####################################################################
# 一時ファイル
tmp=/tmp/tmp_$(basename $0)_$(date +%Y%m%d_%H%M%S)_$$
todayhms=$(date +%Y%m%d%H%M%S)
curtime="$(dayslash -d $todayhms --output 'yyyy年 mm月 dd日 HH:MM:SS')"

# POSTデータ受け取り
if [ ! -z "$CONTENT_LENGTH" ] ; then
	dd bs=$CONTENT_LENGTH |
	cgi-name -n_ -s_      >$tmp-name
else
	:>$tmp-name
fi


# エラーチェック 
ERROR_CHECK(){
	[ $(plus ${PIPESTATUS[@]}) -eq 0 ] && return

	echo "Content-type: text/html"
	echo "" 
	echo "システムエラー"
	exit 1
}

# ディレクトリ定義
# homeディレクトリ  
homd=/home/$(whoami)
ERROR_CHECK
# アプリケーションディレクトリ
apld=$homd/SCM/SIRE
ERROR_CHECK
# HTMLディレクトリ
htmd=$apld/HTML
ERROR_CHECK
# INPUTディレクトリ
inpd=$apld/INPUT
ERROR_CHECK
# POMPAディレクトリ
pomd=$apld/POMPA
ERROR_CHECK
# LV3ディレクトリ
lv3d=$homd/SCM/LV3



####################################################################
# ログインチェック
####################################################################

# 省略
loginid=""
loginname=""
companycode=""




####################################################################
# メイン処理 
####################################################################


# マスタ取得
cat $lv3d/SIRE_DENPYO_SYURUI                                |
#  1:コード 2:名称
cat                                                         >$tmp-denpyosyurui
ERROR_CHECK

# 取引先マスタ取得
cat $lv3d/SIRESAKI/SIRESAKI                                 |
tagself 仕入先コード 仕入先名                               |
tail -n +2                                                  > $tmp-siresaki_master
ERROR_CHECK

cat $htmd/SIRE_SHOKAI.HTML                                  |
calsed '###LOGIN_ID###' "$loginid" |
calsed '###CURRENT_TIME###' "$curtime" |
# 伝票種類を設定
mojihame -lDENPYO_SYURUI - $tmp-denpyosyurui                |
mojihame -lSIRESAKI_LIST - $tmp-siresaki_master             |
# 検索結果部分を除去
sed -n '/<!-- SIRE_RECORDS -->/,/<!-- SIRE_RECORDS -->/!p'  |
cat                                                         >$tmp-html
ERROR_CHECK


####################################################################
# 出力処理 
####################################################################
echo "Content-Type: text/html; charset=utf-8"
ERROR_CHECK
echo ""
ERROR_CHECK
cat $tmp-html
ERROR_CHECK

####################################################################
# 終了処理 
####################################################################
rm -f $tmp-*
ERROR_CHECK
exit 0
