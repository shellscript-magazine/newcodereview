#!/bin/bash -xv
#
# BUMON_DELETE_DEMO.CGI : 部門マスタ削除画面 
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
# 日時
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


# LV1データ作成
# 適用フラグ 登録日時を作成
echo "2 ${todayhms}" > ${tmp}-lv1_del_flg
ERROR_CHECK

# 登録画面から移動してきたことを考え、TOROKUのレコードを除外
# 1:id名 2:チェックフラグ
cat ${tmp}-name   |
# TOROKUが入っているレコードを除外
ugrep -v "TOROKU" > ${tmp}-name_del
ERROR_CHECK

# POSTされたデータが0バイトより大きいときに処理
if [ -s ${tmp}-name_del ] ; then
	# 1:BUMON_部門コード 2:チェックフラグ(on)
	cat ${tmp}-name                  |
	# 画面でチェックされたものを取得
	selr 2 on                        |
	# 第1フィールドを取得
	self 1                           |
	# 1:BUMON_部門コード
	# 余分な文字列を削除
	sed 's/BUMON_//g'                |
	# 1:部門コード
	# 部門コードを5桁にする
	maezero 1.5                      |
	# 部門コードでソート
	msort key=1                      |
	# LV3ファイルから削除対象のレコードを抽出
	cjoin0 key=1 - ${lv3d}/BUMON_MST |
	# 1:部門コード 2:部門名称                        3:担当者   4:適用開始日 5
	# :適用終了日  6:適用フラグ（1:適用中 2:適用外） 7:登録日時
	# 適用フラグと登録日時を入れ替える
	# 適用フラグと登録日時を入れ替える為に適用フラグと登録日時を削除
	delf NF-1 NF                     |
	# 1:部門コード 2:部門名称                        3:担当者   4:適用開始日 5
	# :適用終了日  
	# 新しい適用フラグ、登録日時をつける
	joinx - ${tmp}-lv1_del_flg       |
	# 後ほどデータをマージする為部門コードでソート
	msort key=1                      > ${tmp}-del_bumon
	# 1:部門コード  2:部門名称                        3:担当者   4:適用開始日
	# 5:適用終了日  6:適用フラグ（1:適用中 2:適用外） 7:登録日時
	ERROR_CHECK
	
	# LV1ディレクトリへコピー
	cp -p ${tmp}-del_bumon ${lv1d}/BUMON_DELETE_${todayhms}
	ERROR_CHECK
else
	# POSTされたデータが存在しない場合の処理
	echo "_ _ _ _ _ _ _" > ${tmp}-del_bumon
	ERROR_CHECK
fi

# 表示データ取得
# 1:部門コード  2:部門名称                        3:担当者   4:適用開始日
# 5:適用終了日  6:適用フラグ（1:適用中 2:適用外） 7:登録日時
cat ${lv3d}/BUMON_MST      |
# 削除用データとマージ
up3 key=1 ${tmp}-del_bumon |
# 部門コードが"_"のレコードを除外
delr 1 _                   |
# LV3データ更新用に保存 
tee ${tmp}-bumon_data      |
# 部門コード、適用日、登録日時でソート
msort key=1@4@7            |
# 現在適用中のレコードを抽出
awk '$4<="'${today}'"'     |
awk '$5>="'${today}'"'     |
# 重複を削除
getlast 1 1                |
# 適用フラグで判断
delr 6 2                   > ${tmp}-bumon_data_sansho
ERROR_CHECK

# HTML加工
cat ${htmd}/BUMON_DEMO_DELETE.HTML                    |
# ###DATE###を変換
calsed "###DATE###" ${today}                          |
# 文字をはめ込む
mojihame -l###BUMON_MST### - ${tmp}-bumon_data_sansho > ${tmp}-html
ERROR_CHECK

# LV3データ更新
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
