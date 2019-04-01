#!/bin/bash -vx
#
# REPORT_SIRE_ITIRAN.CGI
#
# 仕入一覧表示
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
tmp=/tmp/tmp_$(basename $0)_$(date +%Y%m%d)_$$
todayhms=$(date +%Y%m%d%H%M%S)

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

lv3d=$homd/SCM/LV3

# HTMLディレクトリ
htmd=$apld/HTML
ERROR_CHECK
# INPUTディレクトリ
lv1d=$homd/SCM/LV1
ERROR_CHECK
# POMPAディレクトリ
pomd=$apld/POMPA
ERROR_CHECK



####################################################################
# ログインチェック
####################################################################

# 省略
loginid=""
loginname=""
companycode=""





# 変数定義
today=$(date +%Y%m%d)
year=$(echo $today | self 1.1.4)
month=$(echo $today | self 1.5.2)
ymonth=$(echo $today | self 1.1.6)
todayhms=$(date +%Y%m%d%H%M%S)

# 指定範囲を取得
range_from=$(mdate -d ${today:0:6}m | self 1 )
range_to=$(mdate -d ${today:0:6}m | self NF )

####################################################################
# メイン処理 
####################################################################

# 初期設定
# 今月のデータを表示

# 仕入先マスタを取得
#  1:仕入先コード    2:仕入先コード規則 3:仕入先名    4:仕入先名称カナ     
#  5:形態            6:敬称             7:郵便番号    8:住所               
#  9:電話番号        10:FAX番号         11:HP         12:支払先            
#  13:先方請求担当者 14:締日            15:支払サイト 16:勘定科目・補助科目
#  17:メモ          
# cat $lv3d/SIRESAKI_MASTER  |
# 必要なフィールドのみを抽出
# self 1 3                   > $tmp-siresaki_master
#  1:仕入先コード 2:仕入先名
cat $lv3d/SIRESAKI/SIRESAKI                   |
tagself 仕入先コード 仕入先名                 |
tail -n +2                                    > $tmp-siresaki_master
ERROR_CHECK

# 決算期マスタを取得
cat $lv3d/KESSANKI_MASTER/KESSANKI_MASTER               |
tee $tmp-kessanki_master                                |
self 1                                                  > $tmp-kessanki
ERROR_CHECK

# 期を取得
cat $tmp-kessanki_master               |
awk '$2<='$ymonth' && $3>='$ymonth''  |
self 1                                 > $tmp-period
ERROR_CHECK

period=$(cat $tmp-period)

# 指定の検索条件のデータがあるかチェック
ls $lv3d/SIRE_HEAD  |
ugrep $ymonth       > $tmp-check_data.1
ERROR_CHECK

ls $lv1d/*/SIRE_HEAD_*  |
gyo                   > $tmp-check_data.2
ERROR_CHECK

# 仕入伝票ヘッダの取得
#  1:伝票番号 2:仕入日付    3:伝票種類    4:取引先コード
#  5:発注日   6:小計        7:消費税額    8:合計金額    
#  9:支払先   10:支払予定日 11:先方担当者 12:摘要       
#  13:顛末    14:削除フラグ 15:更新日時  

# L3取得
if [ -s $tmp-check_data.1 ] ; then
	cat $lv3d/SIRE_HEAD/SIRE_HEAD.$ymonth    |
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@NF@NF-1r                     > $tmp-sire_header_l3
	ERROR_CHECK
else
	:> $tmp-sire_header_l3
	ERROR_CHECK
fi

# INPUT(L1)取得
if [ -s $tmp-check_data.2 ] ; then
	cat $lv1d/*/SIRE_HEAD_*                             |
	#dayslash --input yyyy/mm/dd --output yyyymmdd 2 -  |
	# 指定の日付の範囲内のデータを抽出
	awk '$2>='$range_from' && $2<='$range_to''         |
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@NF@NF-1r                                > $tmp-sire_header_in
	ERROR_CHECK
else
	:> $tmp-sire-header_in
	ERROR_CHECK
fi

# L1とL3をマージ
# 同じ伝票番号の中で最も新しいもののみを残す
upl key=1 $tmp-sire_header_l3 $tmp-sire_header_in  |
# 削除フラグの立っている伝票を削除
delr NF-1 1                                        |
# join用self
self 4 1 2                                         |
# 1:取引先コード 2:伝票番号 3:仕入日付
msort key=1                                        |
# 仕入先名を結合
cjoin2 key=1 $tmp-siresaki_master -                |
# 1:取引先コード 2:取引先名 3:伝票番号 4:仕入日付
self 3 4 2                                         |
msort key=1                                        > $tmp-sire_num
# 1:伝票番号 2:仕入日付 3:取引先
# $sire_numは指定の明細の抽出に利用
ERROR_CHECK


# 仕入伝票明細の取得
#  1:伝票番号  2:伝票明細番号 3:商品コード  4:商品名   
#  5:数量      6:単価         7:単位        8:入数     
#  9:値引      10:金額        11:消費税率   12:消費税額
#  13:合計金額 14:摘要        15:削除フラグ 16:更新日時

# L3取得
if [ -s $tmp-check_data.1 ] ; then 
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@2@NF@NF-1r                       > $tmp-sire_meisai_l3
	ERROR_CHECK
else                          
        :> $tmp-sire_meisai_l3 
        ERROR_CHECK           
fi                            

# INPUT(L1)取得
if [ -s $tmp-check_data.2 ] ; then
	cat $lv1d/*/SIRE_MEISAI_*  |
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@2@NF@NF-1r   > $tmp-sire_meisai_in
	ERROR_CHECK
else                         
        :> $tmp-sire_meisai_in
        ERROR_CHECK          
fi                           

# 仕入商品マスタを取得                                  
# cat $lv3d/SIRE_SHOHIN_MASTER  |                          
# self 1 2                 > $tmp-shohin_master       
cat $lv3d/SYOUHIN/SYOUHIN                    |
tagself 商品ID 部門ID                        |
tail -n +2                                   > $tmp-shohin_master
ERROR_CHECK                                         

# L1とL3をマージ
# 同じ伝票番号の中で最も新しいもののみを残す
upl key=1/2 $tmp-sire_meisai_l3 $tmp-sire_meisai_in  |
# 削除フラグの立っている明細を削除
delr NF-1 1                                          |
# ヘッダ情報と照らし合わせ、取引先名を結合
join1 key=1 $tmp-sire_num -                          |
cjoin1 key=5 $tmp-shohin_master -                    |
# 1:伝票番号   2:仕入日付  3:取引先名 4:伝票明細番号 5:商品コード
# 6:部門コード 7:商品名    8:入数     9:箱数         10:数量
# 11:単位      12:標準価格 13:値引    14:金額        15:消費税率
# 16:消費税額  17:合計金額 18:摘要    19:削除フラグ  20:更新日時
self 2 3 5 6 7 8 10 11 12 17 18                       |
# 日付にスラッシュを入れる
dayslash --output yyyy/mm/dd 1                       > $tmp-sire_meisai
ERROR_CHECK

# 合計仕入金額を計算
cat $tmp-sire_meisai                  |
# 不要フィールド削除
delf NF                               |
#  1:仕入日付 2:取引先 3:部門コード 4:商品コード
#  5:商品名   6:入数   7:単位       8:数量
#  9:単価     10:金額
# 1~9フィールドを無視し10フィールドの合計のみを求める
sm5 dummy=1/9 val=10                  |
# 合計値の入ったレコードのみを取得
tail -1                               |
# 合計値の部分を取得
self NF                               |
# 1:金額
awk '{print '$period','$month',$1}'  > $tmp-gokei_kingaku
#  1:期 2:月 3:金額
ERROR_CHECK

# formhame用
echo PERIOD $period          |              
cat - <(echo CMONTH $month)  > $tmp-formhame
ERROR_CHECK                                 

# 現在時刻の設定
curtime="$(dayslash -d $todayhms --output 'yyyy年 mm月 dd日 HH:MM:SS')"

# HTML作成
cat $htmd/REPORT_SIRE_ITIRAN.HTML                |
calsed '###LOGIN_ID###' "$loginid" |
calsed '###CURRENT_TIME###' "$curtime" |
mojihame -lSIRE_RECORDS - $tmp-sire_meisai       |
mojihame -lPERIOD_LIST - $tmp-kessanki           |
mojihame -lSEARCH_DATE - <(echo $period $month)  |
mojihame -lTOTAL_RECORDS - $tmp-gokei_kingaku    |
formhame -n_ - $tmp-formhame                         |
calsed '###CURRENT_TIME###' "$curtime"           |
cat                                              > $tmp-html
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
