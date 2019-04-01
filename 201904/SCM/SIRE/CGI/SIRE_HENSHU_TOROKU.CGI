#!/bin/bash -vx
#
# SIRE_HENSHU_TOROKU.CGI
#
# 仕入伝票編集登録
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

# POSTパラメータ無しでの起動防止
if [ ! -s $tmp-name ] ; then
	rm -f $tmp-*
	echo "Content-type: text/html charset=utf-8"
	echo "" 
	echo "システムエラー"
	exit 1
fi

# エラーチェック 
ERROR_CHECK(){
	[ $(plus ${PIPESTATUS[@]}) -eq 0 ] && return
	rm -f $tmp-*
	echo "Content-type: text/html charset=utf-8"
	echo "" 
	echo "システムエラー"
	exit 1
}

# ディレクトリ定義
# homeディレクトリ  
homd=/home/$(whoami)
# アプリケーションディレクトリ
apld=$homd/SCM/SIRE
# HTMLディレクトリ
htmd=$apld/HTML
# INPUTディレクトリ
lv1d=$homd/SCM/LV1
# POMPAディレクトリ
pomd=$apld/POMPA
# LV3ディレクトリ
lv3d=$homd/SCM/LV3
# 採番ディレクトリ
said=$lv3d/SAIBAN

####################################################################
# ログインチェック
####################################################################

# 省略
loginid=""
loginname=""
companycode=""










####################################################################
# -メイン処理 
####################################################################

# POSTデータ取得
####################################################################

# ヘッダ情報取得
# 伝票番号
denno=$(nameread 伝票番号＿hidden $tmp-name)
ERROR_CHECK
#伝票種類
denpyousyu=$(nameread 伝票種類 $tmp-name)
ERROR_CHECK
denpyohiduke=$(nameread 伝票日付 $tmp-name)
ERROR_CHECK
#取引先
torihikisaki=$(nameread 取引先 $tmp-name)
ERROR_CHECK
#発注日
hattyubi=$(nameread 発注日 $tmp-name | calsed '/' @) 
ERROR_CHECK
#小計
syokei=$(nameread 小計 $tmp-name)
ERROR_CHECK
#消費税額
syohizeigaku=$(nameread 消費税額 $tmp-name)
ERROR_CHECK
#合計金額
gokeikingaku=$(nameread 合計金額 $tmp-name)
ERROR_CHECK
#支払先
siharaisaki=$(nameread 支払先 $tmp-name)
ERROR_CHECK
#支払予定日
siharaiyoteibi=$(nameread 支払予定日 $tmp-name)
ERROR_CHECK
#先方担当者
senpotantosya=$(nameread 先方担当者 $tmp-name)
ERROR_CHECK
#摘要
tekiyo=$(nameread 摘要 $tmp-name)
ERROR_CHECK
#顛末
tenmatu=$(nameread 顛末 $tmp-name)
ERROR_CHECK

echo "0" $(date +%Y%m%d%H%M%S )   |
# 1:削除フラグ 2:更新日時
cat                              >$tmp-fileinfo
ERROR_CHECK



# 仕入伝票番号採番
#denno=$(getno 1 $said/SIRE.SAIBAN)
#ERROR_CHECK

# ヘッダ情報作成
echo $denno $denpyohiduke $denpyousyu $torihikisaki $hattyubi $syokei  $syohizeigaku $gokeikingaku $siharaisaki $siharaiyoteibi $senpotantosya $tekiyo $tenmatu     |
#  1:伝票番号    2:伝票日付 3:伝票種類 4:取引先 5:発注日     
#  6:小計        7:消費税額 8:合計金額 9:仕入先 10:支払予定日
#  11:先方担当者 12:摘要    13:顛末   
joinx - $tmp-fileinfo   |
cat                     >$tmp-head
ERROR_CHECK 
#  1:伝票番号    2:伝票日付 3:伝票種類 4:取引先      5:発注日     
#  6:小計        7:消費税額 8:合計金額 9:仕入先      10:支払予定日
#  11:先方担当者 12:摘要    13:顛末    14:削除フラグ 15:更新日    


# 明細情報作成
nameread -e '商品コード_*|商品名_*|入数_*|箱数_*|数量_*|単位_*|単価_*|値引_*|^金額_*|消費税区分_*|消費税額_[0-9].*|合計金額_[0-9].*|^備考_*' $tmp-name |
yarr -13 |
#  1:商品コード 2:商品名    3:入数    4:箱数       5:数量 
#  6:単位       7:単価      8:値引    9:消費税区分 10:金額
#  11:消費税額  12:合計金額 13:備考
self 1/8 10 9 11/NF               |
#  1:商品コード 2:商品名    3:入数    4:箱数 5:数量       
#  6:単位       7:単価      8:値引    9:金額 10:消費税区分
#  11:消費税額  12:合計金額 13:備考

# 入力されていない行は削除
awk '($1 != "_")'                 |
# 明細番号を付与
juni                               |
#  1:伝票明細番号 2:商品コード 3:商品名    4:入数    5:箱数 
#  6:数量         7:単位       8:単価      9:値引    10:金額
#  11:消費税区分  12:消費税額  13:合計金額 14:備考
joinx <(echo $denno) -             |
#  1:伝票番号 2:伝票明細番号 3:商品コード 4:商品名    5:入数   
#  6:箱数     7:数量         8:単位       9:単価      10:値引  
#  11:金額    12:消費税区分  13:消費税額  14:合計金額 15:備考
joinx - $tmp-fileinfo              |
#  1:伝票番号    2:伝票明細番号 3:商品コード 4:商品名    5:入数   
#  6:箱数        7:数量         8:単位       9:単価      10:値引  
#  11:金額       12:消費税区分  13:消費税額  14:合計金額 15:備考
#  16:削除フラグ 17:更新日時   
cat                                >$tmp-meisai
ERROR_CHECK

# ファイル移動
mkdir -p $lv1d/$today
mv $tmp-head $lv1d/$today/SIRE_HEAD_$$
ERROR_CHECK
mv $tmp-meisai $lv1d/$today/SIRE_MEISAI_$$
ERROR_CHECK

# 出力用HTML
cat $htmd/SIRE_TOROKU_KANRYO.HTML                       |
calsed '###LOGIN_ID###' "$loginid" |
calsed '###CURRENT_TIME###' "$curtime" |
#cat $htmd/SIRE_TOROKU.HTML                       |
calsed '###LOGIN_ID###' "$loginid" |
calsed '###CURRENT_TIME###' "$curtime" |
calsed '###DEN_NO###' $denno                     |
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
