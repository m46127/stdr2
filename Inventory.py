import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
import chardet  # 文字コード検出

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """ダウンロードリンクを生成"""
    bin_str = base64.b64encode(bin_file).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">{file_label} をダウンロード</a>'
    return href

def main():
    st.title("Inventory Management System")
    uploaded_file_csv = st.file_uploader("CSVファイルを選択", type="csv")
    uploaded_file_excel = st.file_uploader("Excelファイルを選択", type="xlsx")
    
    if uploaded_file_csv is not None and uploaded_file_excel is not None:
        # --- CSV(ピッキングリスト)読み込み ---
        uploaded_file_csv.seek(0)
        raw_data = uploaded_file_csv.read()
        detected = chardet.detect(raw_data) or {}
        enc = detected.get('encoding') or 'utf-8-sig'
        uploaded_file_csv.seek(0)

        try:
            picking_df = pd.read_csv(uploaded_file_csv, encoding=enc, dtype=str)
        except Exception as e:
            st.error(f"CSVの読み込みに失敗しました: {e}")
            return

        # 必須列チェック
        if not {'コード', '数量'}.issubset(picking_df.columns):
            st.error(f"CSVに「コード」「数量」列が見つかりません。 実際の列: {list(picking_df.columns)}")
            return

        # 数量を数値化して集計（同じコードをまとめる）
        picking_df['数量'] = pd.to_numeric(picking_df['数量'], errors='coerce').fillna(0)
        picking_df = picking_df.groupby('コード', as_index=False)['数量'].sum()
        picking_df['コード'] = picking_df['コード'].astype(str).str.strip().str.upper()

        # --- Excel(在庫表)読み込み：F列の6行目以降 ---
        try:
            df_f = pd.read_excel(uploaded_file_excel, usecols="F", header=None, dtype=str)
        except Exception as e:
            st.error(f"Excelの読み込みに失敗しました: {e}")
            return

        # F6以降を取り出す（0始まりなので5以降）
        inventory_df = df_f.iloc[5:].copy()
        inventory_df.columns = ['コード']

        # コード列を整形（空セルは残す！削除しない）
        inventory_df['コード'] = inventory_df['コード'].fillna('')
        inventory_df['コード'] = inventory_df['コード'].astype(str).str.strip().str.upper()

        # 元のExcel行番号を保持（後でズレ確認しやすい）
        inventory_df = inventory_df.reset_index().rename(columns={'index': '元行番号'})

        # --- マージ ---
        merged_df = pd.merge(
            inventory_df, picking_df, on='コード', how='left'
        )

        # 数量列を整形（0やNaNは空白に）
        merged_df['数量'] = merged_df['数量'].replace(0, np.nan)
        merged_df['数量'] = merged_df['数量'].fillna('')

        # 出力時は「元行番号」を落とす
        final_df = merged_df.drop(columns=['元行番号'])

        # --- ダウンロード用Excel生成 ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_df.to_excel(writer, sheet_name='Sheet1', index=False)

        st.markdown(get_binary_file_downloader_html(output.getvalue(), 'Merged_Inventory.xlsx'),
                    unsafe_allow_html=True)

if __name__ == "__main__":
    main()
