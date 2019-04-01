#!/bin/bash -vx
#
# FUKUSEI_TOROKU.CGI
#
# 仕入伝票複製登録
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
today=$(date +%Y%m%d)
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
# LV3ディレクトリ
lv3d=$homd/SCM/LV3
ERROR_CHECK



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

# POSTデータ取得
denno=$(nameread 選択伝票番号 $tmp-name )


# 消費税区分
cat $lv3d/SHOHIZEI_MASTER                        |
#  1:消費税区分 2:消費税区分名称 3:税率 4:デフォルトフラグ
self 3 2 4                                       |
#  1:税率 2:消費税区分名称 3:デフォルトフラグ
fsed 's/1/selected/3' 's/0/_/3'                  |
cat                                              >$tmp-shohizei
ERROR_CHECK

# 伝票種類取得
cat $lv3d/SIRE_DENPYO_SYURUI                    |
#  1:コード 2:名称
cat                                             >$tmp-denpyosyurui
ERROR_CHECK

# 仕入部門取得
cat $lv3d/SIRE_BUMON                             |
#  1:コード 2:名称
cat                                             >$tmp-bumon
ERROR_CHECK

# 仕入先マスタ取得
# cat $lv3d/SIRESAKI_MASTER |
# self 1 3 > $tmp-siresaki_master
cat $lv3d/SIRESAKI/SIRESAKI                     |
tagself 仕入先コード 仕入先名                   |
tail -n +2                                      > $tmp-siresaki_master
ERROR_CHECK

# 明細データ
cat $lv1d/*/SIRE_MEISAI*                           |
#  1:伝票番号  2:伝票明細番号 3:商品コード 4:商品名 5:数量       
#  6:単価      7:単位         8:入数       9:値引   10:金額      
#  11:消費税率 12:消費税額    13:合計金額  14:摘要  15:削除フラグ
#  16:更新日時
msort key=1@2@NF@NF-1r                           |
upl key=1@2 -                                    |
delr NF-1 1                                      |
selr 1 $denno                                    |
self 3/14                                        |
cat                                              >$tmp-meisai
ERROR_CHECK
#  1:商品コード 2:商品名 3:数量 4:単価     5:単位     
#  6:入数       7:値引   8:金額 9:消費税率 10:消費税額
#  11:合計金額  12:摘要 

meisaigyo=$(gyo $tmp-meisai)
gyosu=$((50 - $meisaigyo))
# 空行作成
echo "_"                                         |
fpad _ 12                                         |
ransu $gyosu                                     |
cat                                              >$tmp-karadata
ERROR_CHECK 
#  1:商品コード 2:商品名 3:数量 4:単価     5:単位     
#  6:入数       7:値引   8:金額 9:消費税率 10:消費税額
#  11:合計金額  12:摘要 


# 明細マージ
cat $tmp-meisai $tmp-karadata                    |
#  1:商品コード 2:商品名 3:数量 4:単価     5:単位     
#  6:入数       7:値引   8:金額 9:消費税率 10:消費税額
#  11:合計金額  12:摘要 
juni                                             |
#  1:シーケンシャル番号 2:商品コード 3:商品名 4:数量 5:単価     
#  6:単位               7:入数       8:値引   9:金額 10:消費税率
#  11:消費税額          12:合計金額  13:摘要 
cat                                               >$tmp-data
ERROR_CHECK
#  1:シーケンシャル番号 2:商品コード 3:商品名 4:数量 5:単価     
#  6:単位               7:入数       8:値引   9:金額 10:消費税率
#  11:消費税額          12:合計金額  13:摘要 


# 消費税はフォームはめで表示するためname形式データ作成
cat $tmp-data                                    |
#  1:シーケンシャル番号 2:商品コード 3:商品名 4:数量 5:単価     
#  6:単位               7:入数       8:値引   9:金額 10:消費税率
#  11:消費税額          12:合計金額  13:摘要 
self 1 10                                        |
strcat '"消費税区分_"'+1 2                       |
cat                                              >$tmp-bumondata
ERROR_CHECK




# 仕入伝票LV1ヘッダデータ読込
# DENPYO_DATA
cat $lv1d/*/SIRE_HEAD*                             |
#  1:伝票番号    2:仕入日付 3:伝票種類 4:取引先コード 5:発注日     
#  6:小計        7:消費税額 8:合計金額 9:支払先       10:支払予定日
#  11:先方担当者 12:摘要    13:顛末    14:削除フラグ  15:更新日時  
msort key=1@NF@NF-1r                             |
upl key=1 -                                      |
delr 14 1                                        |
selr 1 $denno                                    |
cat                                              >$tmp-head
ERROR_CHECK
#  1:伝票番号    2:仕入日付 3:伝票種類 4:取引先コード 5:発注日     
#  6:小計        7:消費税額 8:合計金額 9:支払先       10:支払予定日
#  11:先方担当者 12:摘要    13:顛末    14:削除フラグ  15:更新日時  

# 表示項目の文字ハメ用データ作成
cat $tmp-head                                    |
self 1 6 7 8                                     |
#  1:伝票番号 2:小計 3:消費税額 4:合計金額
cat                                              >$tmp-mojihame
ERROR_CHECK
#  1:伝票番号 2:小計 3:消費税額 4:合計金額


# FORM_DATA(formhame用)
# 伝票番号   
denno=$(self 1 $tmp-head)
# 伝票種類  
denpyoshurui=$(self 3 $tmp-head)
# 仕入日付  
sirehiduke=$(self 2 $tmp-head)
# 取引先   
torihikisaki=$(self 4 $tmp-head)
# 発注日     
hattyubi=$(self 5 $tmp-head)
# 小計   
syokei=$(self 6 $tmp-head)
# 消費税額 
syohizeigaku=$(self 7 $tmp-head)
# 合計金額  
gokeikingaku=$(self 8 $tmp-head)
# 支払先    
siharaisaki=$(self 9 $tmp-head)
# 支払予定日
siharaiyoteibi=$(self 10 $tmp-head)
# 先方担当者  
tantosya=$(self 11 $tmp-head)
# 摘要
tekiyo=$(self 12 $tmp-head)
# 顛末  
tenmatu=$(self 13 $tmp-head)


# name形式データ作成
cat << FIN | decomment >$tmp-formhame
伝票番号＿hidden $denno 
伝票種類 $denpyoshurui
伝票日付 $sirehiduke
取引先 $torihikisaki
発注日 $hattyubi
小計 $syokei
値引 $nebiki
消費税額 $syohizeigaku
合計金額 $gokeikingaku
支払先 $siharaisaki
支払予定日 $siharaiyoteibi
先方担当者 $tantosya
摘要 $tekiyo
顛末 $tenmatu
FIN


# HTML作成
cat $htmd/FUKUSEI_TOROKU.HTML                       |
calsed '###LOGIN_ID###' "$loginid" |
calsed '###CURRENT_TIME###' "$curtime" |
# 伝票種類のセレクトボックス設定
mojihame -lDENPYO_SYURUI - $tmp-denpyosyurui     |
# 消費税区分のセレクトボックス設定
mojihame -lSHOHIZEI_LABEL - $tmp-shohizei        |
# 仕入先設定
mojihame -lSIRESAKI_LIST - $tmp-siresaki_master  |
# 行データ設定
mojihame -lMEISAI_DATA - $tmp-data               |
# 文字ハメ
mojihame -lDENPYO_DATA - $tmp-mojihame           |
# 部門をformhame
formhame -n_ - $tmp-bumondata                        |
# 全体formhame
formhame -n_ - $tmp-formhame                         |
# 残っている%除去
sed 's/%[0-9][0-9]*//g'                          |
cat                                              >$tmp-html
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
