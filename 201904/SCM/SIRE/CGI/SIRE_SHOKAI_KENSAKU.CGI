#!/bin/bash -vx
#
# SIRE_SHOKAI_KENSAKU.CGI
#
# 仕入伝票照会検索
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
	rm -f $tmp-*
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
lv1d=$homd/SCM/LV1
ERROR_CHECK
# POMPAディレクトリ
pomd=$apld/POMPA
ERROR_CHECK
#LV3ディレクトリ
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

##### 検索
# 空検索の対処と、メタ文字の削除
cat $tmp-name          |
ugrep -v " _$"         |
tr -d "\/\"\'"         > $tmp-name-search
ERROR_CHECK

# 伝票種類
cat $lv3d/SIRE_DENPYO_SYURUI                                   |
#  1:コード 2:名称
cat                                                            >$tmp-denpyosyurui
ERROR_CHECK

# 仕入先マスタ取得
cat $lv3d/SIRESAKI/SIRESAKI                     |
tagself 仕入先コード 仕入先名                   |
tail -n +2                                      > $tmp-siresaki_master
ERROR_CHECK


# 検索条件取得



# L3データ取得
#cat $lv3d/SIRE_HEAD/
: >$tmp-lv3
ERROR_CHECK
#  1:伝票種類 2:伝票番号 3:伝票日付 4:取引先 5:合計金額

# 仕入伝票ヘッダL1データ存在確認
cat $lv1d/*/SIRE_HEAD_*   >$tmp-sirehead
ERROR_CHECK


# L1データ取得
if [ -s $tmp-sirehead ] ; then 
cat $lv1d/*/SIRE_HEAD_*                                      |
#  1:伝票番号    2:伝票日付 3:伝票種類 4:取引先コード 5:発注日     
#  6:小計        7:消費税額 8:合計金額 9:支払先       10:支払予定日
#  11:先方担当者 12:摘要    13:顛末    14:削除フラグ  15:更新日時  
msort key=1@NF@NF-1r                                         |
upl key=1 -                                                  |
self 3 1 2 4 8                                              |
#  1:伝票種類 2:伝票番号 3:伝票日付 4:取引先コード 5:合計金額
cjoin2 key=1 $tmp-denpyosyurui                               |
#  1:伝票種類 2:伝票種類名称 3:伝票番号 4:伝票日付 5:取引先コード
#  6:合計金額
### self 5 2/4 6                                                 |
###  1:取引先コード 2:伝票種類名称 3:伝票番号 4:伝票日付 5:合計金額
### msort key=1 |
msort key=5 |
cjoin2 key=5 $tmp-siresaki_master -			     |
#  1:伝票種類 2:伝票種類名称 3:伝票番号 4:伝票日付 5:取引先コード
#  6:取引先名 7:合計金額
cat                                                          > $tmp-lv1
### self 3/5 2 6						     |
###  1:伝票種類 2:伝票番号 3:伝票日付 4:取引先 5:合計金額
## msort key=2 						     |
###cat                                                          >$tmp-lv1
ERROR_CHECK
else
	:>$tmp-lv1
fi

cat $tmp-lv3 $tmp-lv1 > $tmp-data


# tmp-dataの上書きを繰り返して検索絞り込み
if [ -s $tmp-name-search ]; then
  grep -q "^フリーワード" $tmp-name-search
  if [ $? -eq 0 ]; then
    awk '$0~/'"$(nameread フリーワード $tmp-name-search)"'/' $tmp-data > $tmp-data.new
    ERROR_CHECK 検索エラー（フリーワード）
    mv $tmp-data.new $tmp-data
  fi
  # 部分一致
  grep -q "^日付" $tmp-name-search
  if [ $? -eq 0 ]; then
    awk '$4~/'"$(nameread 日付 $tmp-name-search)"'/' $tmp-data > $tmp-data.new
    ERROR_CHECK 検索エラー（伝票日付）
    mv $tmp-data.new $tmp-data
  fi
  grep -q "^伝票番号" $tmp-name-search
  if [ $? -eq 0 ]; then
    awk '$3~/'"$(nameread 伝票番号 $tmp-name-search)"'/' $tmp-data > $tmp-data.new
    ERROR_CHECK 検索エラー（伝票番号）
    mv $tmp-data.new $tmp-data
  fi
  # セレクト（完全一致）
  grep -q "^伝票種類" $tmp-name-search
  if [ $? -eq 0 ]; then
    awk '$2=="'"$(nameread 伝票種類 $tmp-name-search)"'"' $tmp-data > $tmp-data.new
    ERROR_CHECK 検索エラー（伝票種類）
    mv $tmp-data.new $tmp-data
  fi
  grep -q "^取引先" $tmp-name-search
  if [ $? -eq 0 ]; then
    awk '$5=="'"$(nameread 取引先 $tmp-name-search)"'"' $tmp-data > $tmp-data.new
    ERROR_CHECK 検索エラー（取引先）
    mv $tmp-data.new $tmp-data
  fi
fi

cat $tmp-data                                                |
self 2 3 4 6 7	                              					     |
#  1:伝票種類 2:伝票番号 3:伝票日付 4:取引先 5:合計金額
msort key=2 						                                     |
juni                                                         >$tmp-data.new
#  1:シーケンシャル番号 2:伝票種類 3:伝票番号 4:伝票日付 5:取引先
#  6:合計金額          
ERROR_CHECK
mv $tmp-data.new $tmp-data
ERROR_CHECK

# HTML作成
cat $htmd/SIRE_SHOKAI.HTML                                  |
calsed '###LOGIN_ID###' "$loginid"                          |
calsed '###CURRENT_TIME###' "$curtime"                      |
# 検索条件部の伝票種類設定
mojihame -lDENPYO_SYURUI - $tmp-denpyosyurui                |
mojihame -lSIRESAKI_LIST - $tmp-siresaki_master             |
# formの内容
formhame -n_ - $tmp-name                                    |
# 検索結果部分を除去
mojihame -lSIRE_RECORDS - $tmp-data                         |
sed 's/%[0-9][0-9]*//g'                                     |
cat                                                         >$tmp-html
ERROR_CHECK


####################################################################
# 出力処理 
####################################################################
echo "Content-Type: text/html; charset=utf-8"
echo ""
cat $tmp-html
ERROR_CHECK

####################################################################
# 終了処理 
####################################################################
# rm -f $tmp-*
ERROR_CHECK
exit 0
