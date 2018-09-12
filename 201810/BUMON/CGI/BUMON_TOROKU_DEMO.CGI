#!/bin/bash -xv
#
# BUMON_TOROKU_DEMO.CGI : 部門マスタ登録画面 
#
# 作成日：2018/08/20
# 作成者：t.muramoto

####################################################################
# 環境変数の設定
####################################################################
export PATH=/home/UTL:/home/TOOL:/usr/local/bin/:${PATH}
export LANG=ja_JP.UTF-8
####################################################################

####################################################################
# 実行ログの出力
####################################################################
exec 2> /LOG/LOG.$(basename $0).$(date +%Y%m%d%H%M%S)

####################################################################
# 変数設定
####################################################################
# 日付
today=$(mdate today)
# 時刻
todayhms=$(date +%Y%m%d%H%M%S)

# ホームディレクトリ
homd=/home/usp/WEB/BUMON
# LV1ディレクトリ
lv1d=${homd}/LV1
# LV3ディレクトリ
lv3d=${homd}/LV3
# HTMLディレクトリ
htmd=${homd}/HTML
# SEMAPHOREディレクトリ
semd=${homd}/SEMAPHORE
# tmp
tmp=/tmp/$$

####################################################################
# エラーチェック関数
####################################################################
# ERROR_CHECK
ERROR_CHECK(){
        [ $(plus ${PIPESTATUS[@]}) -eq 0 ] && return
        # エラーの場合
        rm -rf $tmp-*
        touch $semd/$(basename $0).$HOSTNAME.ERROR.$today
        exit 1
}

####################################################################
#  画面表示用データ作成
####################################################################
# POSTされたデータを取得
if [ $(echo ${CONTENT_LENGTH}) -ne 0 ]; then
  dd bs=${CONTENT_LENGTH}        |
  cgi-name -e_ -s_               > $tmp-name
  ERROR_CHECK
else
  # POSTの内容がない場合はファイルのみ作成
  :> $tmp-name
fi


# 適用フラグ、登録日時を作成
echo "1 ${todayhms}" > ${tmp}-flg
ERROR_CHECK
# 1:適用フラグ 2:登録日時

# LV1データ作成
# POSTデータが０バイトより大きい場合は処理
if [ -s ${tmp}-name ] ; then
	# 1:ID名 2:入力値
	cat ${tmp}-name    |
	# タグ形式に変換
	name-tag           |
	# 1:部門コード 2:部門名称 3:担当者 4:適用開始日 5:適用終了日
	# ヘッダを削除
	sed 1d             |
	# 適用フラグ、登録日時をつける
	joinx - ${tmp}-flg |
	# 1:部門コード 2:部門名称                        3:担当者   4:適用開始日 5
	# :適用終了日  6:適用フラグ（1:適用中 2:適用外） 7:登録日時
	# 部門コードを5桁に変換
	maezero 1.5        |
	# 部門コードでソート
	msort key=1        > ${tmp}-lv1
	ERROR_CHECK

	# LV1データを保存
	cp -p ${tmp}-lv1 ${lv1d}/BUMON_TOROKU_${todayhms}
	ERROR_CHECK
else
	# POSTデータが0バイトのときの処理
	echo "_ _ _ _ _ _ _" > ${tmp}-lv1
	ERROR_CHECK
fi

# 表示データ取得
# 1:部門コード  2:部門名称                        3:担当者   4:適用開始日
# 5:適用終了日  6:適用フラグ（1:適用中 2:適用外） 7:登録日時
cat ${lv3d}/BUMON_MST  |
# 部門コードをキーとして登録データをマージ
up3 key=1 - ${tmp}-lv1 |
# 部門コードが"_"は除外
delr 1 _               |
# LV3更新データとして保存
tee ${tmp}-bumon_data  |
# 現在適用中のレコードを抽出
awk '$4<="'${today}'"' |
awk '$5>="'${today}'"' |
# 部門コード、適用開始日、登録日時でソート
msort key=1@4@7        |
# 部門コードをキーとして重複を削除
getlast 1 1            |
# 適用フラグで判断
delr 6 2               > ${tmp}-bumon_data_sansho
ERROR_CHECK

# HTML加工
cat ${htmd}/BUMON_DEMO_TOROKU.HTML                    |
# ###DATE###を変換
calsed "###DATE###" ${today} -                        |
# 文字をはめ込む
mojihame -l###BUMON_MST### - ${tmp}-bumon_data_sansho > ${tmp}-html
ERROR_CHECK

# LV3データを更新
cp -p ${tmp}-bumon_data ${lv3d}/BUMON_MST
ERROR_CHECK

####################################################################
#  HTML表示
####################################################################
echo "Content-type:text/html"
echo ""
cat $tmp-html

####################################################################
# 終了処理
####################################################################
rm -f ${tmp}-*
exit 0
