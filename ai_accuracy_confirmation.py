import pandas as pd
import glob
import base64
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime
from pandas.tseries.offsets import MonthBegin
from dateutil.relativedelta import relativedelta

#############################################################################################
#
# Overview
# ・AI診断の精度確認処理
#
# Description
# ・入力された期間のAI精度（※）確認と確認結果のJupyterNoteBook表示を行う
#   また、見逃した法情連データが確認できるよう該当データのダウンロード機能も実装する
#   1. 確認期間を取得する
#   2. キャビネットデータデータを確認期間で絞り込む
#   3. 見逃しデータのダウンロード導線を表示する　
#   4. 確認データを元に精度確認とJupyterNoteBook表示を行う
#   ※キャビネットデータを元に、AIによる法情連データの見極めが想定通り行われているか
#
#############################################################################################

plt.rcParams['font.family'] = 'MS Gothic'
st.set_page_config(layout="wide")

#--------------------------------------------------------------------------------------------
# メイン処理
#--------------------------------------------------------------------------------------------
def main():

    # 画面表示
    rendering()

    # 確認ボタン選択
    if st.button('確認'):
        # キャビネットデータデータを確認期間で絞り込み
        filtered_data = get_analysis_data()
        # 見逃しデータのダウンロード導線表示
        generate_download_function(filtered_data)
        # AIの精度確認
        ai_accuracy_confirmation(filtered_data)

#--------------------------------------------------------------------------------------------
# 画面表示
#--------------------------------------------------------------------------------------------
def rendering():
    st.title('AI診断の精度確認')

    # 補足情報の表示
    st.markdown("""
    <div style="border:2px solid #7F7F7F; padding:15px; margin-top: 10px; margin-bottom: 30px; border-radius: 15px;">
        選択した期間のAI診断精度を確認します。<br>
        期間を選択して『確認』ボタンを押してください。<br>
        なお、確認期間に当月は含まれません。また『指定なし』を選択した場合はすべての期間が対象になります。<br>
    </div>
    """, unsafe_allow_html=True)

    # セレクトボックスのオプション
    options = [
        "指定なし",
        "直近1ヵ月",
        "直近3ヵ月",
        "直近半年",
        "直近1年"
    ]
    st.selectbox("期間:", options)


#--------------------------------------------------------------------------------------------
# 確認期間を使用したキャビネットデータの絞り込み
#--------------------------------------------------------------------------------------------
def get_analysis_data():

    # CSVファイルからデータを読み込む
    folders = ['./cabinet']
    
    # フォルダ内の全キャビネットデータをマージ
    all_files = []
    for folder in folders:
        all_files.extend(glob.glob(folder + "/*.csv"))
    li = []
    for filename in all_files:
        df = pd.read_csv(filename, encoding='sjis', index_col=None, header=0)
        li.append(df)

    # 重複データを除外
    data = pd.concat(li, axis=0, ignore_index=True)
    data = data.drop_duplicates()
    data['登録日時'] = pd.to_datetime(data['登録日時'])
    data['登録月'] = data['登録日時'].dt.to_period('M')
    end_month = datetime.now() - relativedelta(months=1)
    end_period = pd.Timestamp(end_month.strftime('%Y-%m') + '-01').to_period('M')
    filtered_data = data[data['登録月'] <= end_period]

    # 精度確認前のデータチェック
    if filtered_data.shape[0] == 0:
        st.error(f"確認期間のデータが0件です。データをアップロードしてください。")
        return pd.DataFrame()

    return filtered_data


#--------------------------------------------------------------------------------------------
# 見逃しデータのダウンロード導線表示
#--------------------------------------------------------------------------------------------
def generate_download_function(filtered_data):

    # 見逃しデータの取得
    # 取得条件はカラム名に'２次_判断理由' データに〇が含まれているもの、かつ、'AI_判断理由'には×が含まれているデータ
    judgment_columns = filtered_data.columns[filtered_data.columns.str.contains('２次_判断理由', case=False)]
    judgment_rows = (filtered_data[judgment_columns].apply(lambda col: col.str.contains('〇'))).any(axis=1)
    ai_rows = filtered_data['AI_判断理由'].str.contains('×')
    download_data = filtered_data[judgment_rows & ai_rows]
    download_data = download_data.drop('登録月', axis=1)  # ここは登録日を登録月に変更

    # 1件以上ある場合だけ表示する
    if len(download_data) >= 1:
        csv_string = download_data.to_csv(index=False, encoding='shift_jis', errors='replace')
        b64 = base64.b64encode(csv_string.encode('shift_jis')).decode()  
        href = f'''<a download="missed-data.csv" href="data:text/csv;charset=shift_jis;base64,{b64}" target="_blank">見逃しデータをダウンロードする</a>'''
        st.markdown(href, unsafe_allow_html=True)


#--------------------------------------------------------------------------------------------
# AIの精度確認とJupyterNoteBook表示
#--------------------------------------------------------------------------------------------
def ai_accuracy_confirmation(filtered_data):

    # 法情連データ件数を算出
    secondary_columns = [col for col in filtered_data.columns if '２次_判断理由' in col]
    total_secondary_condition = filtered_data[secondary_columns].apply(lambda row: row.str.contains("〇", na=False).any(), axis=1)
    total_secondary_count = filtered_data[total_secondary_condition].shape[0]
    
    # 見逃し率・見逃しデータ件数を算出
    missed_condition = (filtered_data[secondary_columns].apply(lambda row: row.str.contains("〇", na=False).any(), axis=1)) & (filtered_data['AI_判断理由'].str.contains("×", na=False))
    missed_count = filtered_data[missed_condition].shape[0]
    if total_secondary_count == 0:
        missed_rate = 0
    else:
        missed_rate = missed_count / total_secondary_count * 100
    labels = ['検出', '見逃し']
    values = [total_secondary_count - missed_count, missed_count]
    FONT_SIZE_TITLE = 16
    FONT_SIZE_LABEL = 14
    FONT_SIZE_TICK = 14
    col1, col2 = st.columns(2)

    # 円グラフで見逃し率を描画
    with col1:
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title('見逃し率', fontsize=FONT_SIZE_TITLE, y=1.05)
        plt.subplots_adjust(top=0.85)
        st.pyplot(fig)

    # 棒グラフで見逃しデータ件数を算出
    condition = filtered_data[filtered_data.columns[filtered_data.columns.str.contains('２次_判断理由')]].apply(lambda x: x.str.contains('〇')).any(axis=1) & \
                filtered_data[filtered_data.columns[filtered_data.columns.str.contains('AI_判断理由')]].apply(lambda x: x.str.contains('×')).any(axis=1)
    missed_data = filtered_data[condition].copy()
    grouped_data = missed_data.groupby('登録月').size()
    if grouped_data.empty:
        grouped_data = pd.Series([0], index=["None"])
    with col2:
        fig2, ax2 = plt.subplots(figsize=(10, 7))
        grouped_data.plot(kind='bar', ax=ax2)
        ax2.set_title(f"見逃し件数（{missed_count}/{total_secondary_count}件）", fontsize=FONT_SIZE_TITLE, y=1.05)
        ax2.yaxis.set_major_locator(plt.MultipleLocator(1))
        ax2.set_xlabel('登録月', fontsize=FONT_SIZE_LABEL)
        ax2.set_ylabel('見逃し件数', fontsize=FONT_SIZE_LABEL)
        ax2.tick_params(axis='both', which='major', labelsize=FONT_SIZE_TICK)
        st.pyplot(fig2)

    FONT_SIZE_TITLE = 10
    FONT_SIZE_LABEL = 8
    FONT_SIZE_TICK = 8

    # 棒グラフで要データ件数を算出
    condition = filtered_data[filtered_data.columns[filtered_data.columns.str.contains('２次_判断理由')]].apply(lambda x: x.str.contains('〇')).any(axis=1)
    need_data = filtered_data[condition].copy()
    need_data['AI出力値'] = (need_data['AI出力値'] * 100).astype(int) / 100
    grouped_data = need_data.groupby('AI出力値').size()

    all_ticks = np.arange(0, 1.05, 0.05) 
    grouped_data = grouped_data.reindex(all_ticks, fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4))
    grouped_data.plot(kind='bar', ax=ax, color='red')  
    ax.set_title('AI出力値単位のデータ件数（要データ）', fontsize=FONT_SIZE_TITLE)
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax.set_xlabel('AI出力値', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('件数', fontsize=FONT_SIZE_LABEL)
    ax.yaxis.set_major_locator(plt.FixedLocator(np.arange(0, max(grouped_data) + 1, 10)))
    ax.tick_params(axis='both', which='major', labelsize=FONT_SIZE_TICK)
    for spine in ax.spines.values():
        spine.set_edgecolor('#7F7F7F')
    ax.set_xticklabels([])
    ax.yaxis.set_ticks_position('none')
    ax.xaxis.set_ticks_position('none')
    ax.text(1, -0.05, '1', transform=ax.transAxes, fontsize=FONT_SIZE_LABEL)
    # 左からx軸何メモリ分かを指定する
    ax.axvline(x=3.5, color='red', linewidth=2, linestyle='-')
    ax.annotate('モデルの出力値: 0.00437\n足きりのデータの割合: 0.5\n見逃し率: 0.0\n見逃し個数: 0',
                xy=(3.5, 0), xytext=(4, 10),
                fontsize=10, color='black',
                bbox=dict(facecolor='white', edgecolor='#7F7F7F', boxstyle='round,pad=0.5'))
    plt.tight_layout()
    st.pyplot(fig)

    # 棒グラフで不要データ件数を算出
    relevant_columns = filtered_data.columns[filtered_data.columns.str.contains('２次_判断理由')]
    condition = ~filtered_data[relevant_columns].apply(lambda x: x.str.contains('〇')).any(axis=1)
    need_not_data = filtered_data[condition]
    grouped_data = need_not_data.groupby('AI出力値').size()

    print (grouped_data)
    all_ticks = np.arange(0, 1.05, 0.05) 
    grouped_data = grouped_data.reindex([0.00,0.05,0.10,0.15,0.20, 0.25, 0.30, 0.35, 0.40, 0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95,1.00], fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4))
    grouped_data.plot(kind='bar', ax=ax)
    ax.set_title('AI出力値単位のデータ件数（不要データ）', fontsize=FONT_SIZE_TITLE)
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax.set_xlabel('AI出力値', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('件数', fontsize=FONT_SIZE_LABEL)
    ax.yaxis.set_major_locator(plt.FixedLocator(np.arange(0, max(grouped_data) + 1, 10)))
    ax.tick_params(axis='both', which='major', labelsize=FONT_SIZE_TICK)
    for spine in ax.spines.values():
        spine.set_edgecolor('#7F7F7F')
    ax.invert_yaxis()

    ax.set_xticklabels([])
    ax.yaxis.set_ticks_position('none')
    ax.xaxis.set_ticks_position('none')
    ax.text(1, -0.05, '1', transform=ax.transAxes, fontsize=FONT_SIZE_LABEL)
    # 左からx軸何メモリ分かを指定する
    ax.axvline(x=3.5, color='red', linewidth=2, linestyle='-')
    plt.tight_layout()
    st.pyplot(fig)

    plt.show()
if __name__ == "__main__":
    main()
