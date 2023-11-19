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

plt.rcParams['font.family'] = 'MS Gothic'
st.set_page_config(layout="wide")

#--------------------------------------------------------------------------------------------
# メイン処理
#--------------------------------------------------------------------------------------------
def main():
    # 画面表示
    rendering()

#--------------------------------------------------------------------------------------------
# 画面表示
#--------------------------------------------------------------------------------------------
def rendering():
    st.title('チューニング結果確認')

    # 概要説明
    st.markdown("""
    <div style="border:2px solid #7F7F7F; padding:15px; margin-top: 10px; margin-bottom: 30px; border-radius: 15px;">
        選択したAIモデルのチューニング結果確認と開発/本番環境の更新を行います。<br>
        チューニング結果を確認する場合は、AIモデルを選択して『チューニング結果を確認する』ボタンを押してください。<br>
        AIモデルを更新する場合は、AIモデルを選択して『開発/本番環境を確認する』ボタンを選択してください。
    </div>
    """, unsafe_allow_html=True)

    custom_css = """
    <style>
        .stRadio label {
            padding: 2px 0px;
            margin-bottom: 5px;
        }
    </style>
    """

    # モデル一覧（＋チューニング結果概要）表示
    st.markdown(custom_css, unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)
    labels = [f"Bert {i}／SetFit 9  ：  見逃し率0%(137件中0件見逃し)" for i in range(1, 6)]
    choice = st.radio("AIモデル一覧：", labels)
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    # 各種ボタン表示
    col1, col2, col3, _ = st.columns([3,2,2,6])  # 最後の数字は残りのスペースを確保するためのものです。
    with col1:
        if st.button('チューニング結果を確認する'):
            st.write(f'{choice}のチューニング結果を表示します。')
    with col2:
        if st.button('開発環境を更新する'):
            st.write(f'{choice}を開発環境に更新しました。')
    with col3:
        if st.button('本番環境を更新する'):
            st.write(f'{choice}を本番環境に更新しました。')

if __name__ == "__main__":
    main()