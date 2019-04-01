#!/bin/bash -vx
#
# REPORT_SIRE_ITIRAN_KENSAKU.CGI
# 仕入一覧検索CGI
#
# K.Bando () 2018/12/18
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

####################################################################
# ディレクトリと変数の定義
####################################################################
# homeディレクトリ
homd=/home/$(whoami)
# アプリケーションディレクトリ
apld=$homd/SCM/SIRE
# HTMLディレクトリ
htmd=$apld/HTML
# LV1ディレクトリ
lv1d=$homd/SCM/LV1
# LV3ディレクトリ
lv3d=$homd/SCM/LV3

# 本日日付
today=$(date +%Y%m%d)
# 現在の日時
todayhms=$(date +%Y%m%d%H%M%S)

####################################################################
# POSTデータの取得
####################################################################
period=$(nameread PERIOD $tmp-name)                ; ERROR_CHECK
month=$(nameread CMONTH $tmp-name | maezero 1.2 -) ; ERROR_CHECK

####################################################################
# メイン処理
####################################################################
# 仕入先マスタを取得

# 省略
loginid=""
loginname=""
companycode=""





cat $lv3d/SIRESAKI/SIRESAKI                   |
tagself 仕入先コード 仕入先名                 |
tail -n +2                                    > $tmp-siresaki_master
ERROR_CHECK

# 仕入商品マスタを取得
cat $lv3d/SYOUHIN/SYOUHIN                    |
tagself 商品ID 部門ID                        |
tail -n +2                                   > $tmp-shohin_master
ERROR_CHECK

#決算期マスタを取得
#  1:期 2:開始年月 3:終了年月
cat $lv3d/KESSANKI_MASTER/KESSANKI_MASTER    |
# マスタ全体と期のみのデータに分ける
tee $tmp-kessanki_master                     |
# セレクト用の期フィールド
self 1                                       > $tmp-kessanki
ERROR_CHECK

# 決算期マスタから決算期と月で検索して暦年を取得(第21期12月 ==> 2018年)
cat $tmp-kessanki_master  |
selr 1 $period            |
if [ ${month} -ge "1" -a ${month} -le $(selr 1 $period $tmp-kessanki_master | self 3.5.2 | 1bai 1) ] ; then
	self 3.1.4
else
	self 2.1.4
fi                        > $tmp-sel_year
ERROR_CHECK

year=$(cat $tmp-sel_year)  ; ERROR_CHECK
ymonth=$(echo $year$month) ; ERROR_CHECK

# 指定範囲の日付を取得
range_from=$(mdate -d ${ymonth}m | self 1 ) ; ERROR_CHECK
range_to=$(mdate -d ${ymonth}m | self NF )  ; ERROR_CHECK

# 仕入伝票ヘッダのLV3データの取得
# 指定の検索条件のLV3データがあるかチェック
ls $lv3d/SIRE_HEAD  |
ugrep $ymonth       > $tmp-check_data.lv3
ERROR_CHECK

if [ -s $tmp-check_data.lv3 ] ; then
	#  1:伝票番号 2:伝票日付    3:伝票種類    4:取引先コード
	#  5:発注日   6:小計        7:消費税額    8:合計金額
	#  9:支払先   10:支払予定日 11:先方担当者 12:摘要
	#  13:顛末    14:削除フラグ 15:更新日時
	cat $lv3d/SIRE_HEAD/SIRE_HEAD.$ymonth          |
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@NF@NF-1r                           > $tmp-sire_header_lv3
	ERROR_CHECK
else
	:> $tmp-sire_header_lv3
	ERROR_CHECK
fi

# 仕入伝票ヘッダのLV1データの取得
# 指定の検索条件のLV1データがあるかチェック
ls $lv1d/*/SIRE_HEAD_*  |
gyo                     > $tmp-check_data.lv1
ERROR_CHECK

if [ -s $tmp-check_data.lv1 ] ; then
	# レイアウトはLV3データと同じ
	cat $lv1d/*/SIRE_HEAD_*                       |
	# 伝票日付の範囲内のデータを抽出
	awk '$2>='$range_from' && $2<='$range_to''    |
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@NF@NF-1r                           > $tmp-sire_header_lv1
	ERROR_CHECK
else
	:> $tmp-sire-header_in
	ERROR_CHECK
fi

# LV1とLV3をマージし、同じ伝票番号で最も新しいものだけを残す
upl key=1 $tmp-sire_header_lv3 $tmp-sire_header_lv1 |
# 削除フラグの立っている伝票は削除
delr NF-1 1                                         |
# join用self
self 4 1 2                                          |
# 1:取引先コード 2:伝票番号 3:仕入日付
msort key=1                                         |
# 取引先名を結合
cjoin2 key=1 $tmp-siresaki_master -                 |
# 1:取引先コード 2:取引先名 3:伝票番号 4:仕入日付
self 3 4 2                                          |
msort key=1                                         > $tmp-sire_num
# 1:伝票番号 2:仕入日付 3:取引先
ERROR_CHECK


# 仕入伝票明細のLV3データの取得
if [ -s $tmp-check_data.lv3 ] ; then
	#  1:伝票番号  2:伝票明細番号 3:商品コード  4:商品名
	#  5:数量      6:単価         7:単位        8:入数
	#  9:値引      10:金額        11:消費税率   12:消費税額
	#  13:合計金額 14:摘要        15:削除フラグ 16:更新日時
	cat $lv3d/SIRE_MEISAI/SIRE_MEISAI.$ymonth    |
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@2@NF@NF-1r                       > $tmp-sire_meisai_lv3
	ERROR_CHECK
else
	:> $tmp-sire_meisai_lv3
	ERROR_CHECK
fi

# 仕入伝票明細のLV1データの取得
if [ -s $tmp-check_data.lv1 ] ; then
	#  レイアウトはLV3データと同じ
	cat $lv1d/*/SIRE_MEISAI_*                    |
	# 同じ伝票番号の情報を古い順にソート(最も新しいデータが一番下に来るように)
	msort key=1@2@NF@NF-1r                       > $tmp-sire_meisai_in
	ERROR_CHECK
else
	:> $tmp-sire_meisai_in
	ERROR_CHECK
fi

# LV1とLV3をマージし、同じ伝票番号で最も新しいものだけを残す
upl key=1/2 $tmp-sire_meisai_lv3 $tmp-sire_meisai_in |
# 削除フラグの立っている伝票は削除
delr NF-1 1                                          |
# ヘッダ情報と照らし合わせ、取引先名を結合
join1 key=1 $tmp-sire_num -                          |
cjoin1 key=5 $tmp-shohin_master -                    |
# 1:伝票番号   2:仕入日付  3:取引先名 4:伝票明細番号 5:商品コード
# 6:部門コード 7:商品名    8:入数     9:箱数         10:数量
# 11:単位      12:標準価格 13:値引    14:金額        15:消費税率
# 16:消費税額  17:合計金額 18:摘要    19:削除フラグ  20:更新日時
self 2 3 5 6 7 8 10 11 12 17 18                       |
# 1:日付  2:取引先 3:商品コード 4:部門コード 5:商品名
# 6:入数  7:数量   8:単位       9:単価       10:金額
# 11:摘要
# 日付書式変更 yyyymmdd => yyyy/mm/dd
dayslash --output yyyy/mm/dd 1                       > $tmp-sire_meisai
ERROR_CHECK

# 合計仕入金額を計算
cat $tmp-sire_meisai                  |
delf NF                               |
# 1:日付  2:取引先 3:商品コード 4:部門コード 5:商品名
# 6:入数  7:数量   8:単位       9:単価       10:金額
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
echo PERIOD $period                   |
cat - <(echo CMONTH $month)           > $tmp-formhame
ERROR_CHECK

# 現在時刻の設定
curtime="$(dayslash -d $todayhms --output 'yyyy年 mm月 dd日 HH:MM:SS')"

# HTML作成
cat $htmd/REPORT_SIRE_ITIRAN.HTML                  |
calsed '###LOGIN_ID###' "$loginid"                 |
calsed '###CURRENT_TIME###' "$curtime"             |
mojihame -lSIRE_RECORDS - $tmp-sire_meisai         |
mojihame -lPERIOD_LIST - $tmp-kessanki             |
mojihame -lSEARCH_DATE - <(echo $period $month)    |
mojihame -lTOTAL_RECORDS - $tmp-gokei_kingaku      |
formhame -n_ - $tmp-formhame                       |
cat                                                > $tmp-html
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
rm -f $tmp-*
ERROR_CHECK
exit 0
