import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
import chardet

def get_binary_file_downloader_html(bin_file, file_label='File'):
    bin_str = base64.b64encode(bin_file).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">Download {file_label}</a>'
    return href

def main():
    st.title("Inventory Management System")
    uploaded_file_csv = st.file_uploader("Choose a CSV file", type="csv")
    uploaded_file_excel = st.file_uploader("Choose an Excel file", type="xlsx")
    
    if uploaded_file_csv is not None and uploaded_file_excel is not None:
        # --- CSV 読み込み（文字列で） ---
        uploaded_file_csv.seek(0)
        raw = uploaded_file_csv.read()
        enc = (chardet.detect(raw) or {}).get('encoding') or 'utf-8-sig'
        uploaded_file_csv.seek(0)

        # 先頭ゼロ保全のため dtype=str
        picking_df = pd.read_csv(uploaded_file_csv, encoding=enc, dtype=str)

        # 必要列チェック
        if not {'コード','数量'}.issubset(picking_df.columns):
            st.error(f"CSVに「コード」「数量」列がありません。実際の列: {list(picking_df.columns)}")
            return

        # 数量を数値化→集計
        picking_df['数量'] = pd.to_numeric(picking_df['数量'], errors='coerce').fillna(0)
        picking_df = picking_df.groupby('コード', as_index=False)['数量'].sum()
        picking_df['コード'] = picking_df['コード'].str.strip().str.upper()

        # --- Excel 読み込み（文字列で） ---
        # 見出し行がズレている場合は header=0 を変更（例: header=1 など）
        inventory_df = pd.read_excel(uploaded_file_excel, dtype=str, header=0)

        # 列名の正規化（不可視・全角スペース除去、前後空白除去）
        norm_cols = (pd.Series(inventory_df.columns.astype(str))
                        .str.replace('\u3000','', regex=False)   # 全角スペース
                        .str.replace('\xa0','', regex=False)     # 不可視スペース
                        .str.strip())
        inventory_df.columns = norm_cols

        # 候補列（コード系）を推定
        candidates = [c for c in inventory_df.columns if any(k in c for k in ['コード','品番','SKU','Jan','JAN','商品番号','品コード'])]
        if not candidates:
            st.error(f"Excelにコード列が見つかりません。列名の一例：商品コード/コード/品番/SKU/JAN。実際の列: {list(inventory_df.columns)}")
            return

        # ユーザーに選ばせる（自動で一番それっぽいのを先頭に）
        selected_col = st.selectbox("在庫表のコード列を選択してください", candidates, index=0)
        inventory_df = inventory_df[[selected_col]].rename(columns={selected_col: 'コード'})
        inventory_df['コード'] = inventory_df['コード'].str.strip().str.upper()

        # --- マージ ---
        merged_df = pd.merge(inventory_df, picking_df, on='コード', how='left')

        # 0 → NaN → 空文字（見た目空白）
        merged_df['数量'] = merged_df['数量'].replace(0, np.nan)
        merged_df['数量'] = merged_df['数量'].astype(object).where(merged_df['数量'].notna(), '')

        # --- ダウンロード ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            merged_df.to_excel(writer, sheet_name='Sheet1', index=False)
        st.markdown(get_binary_file_downloader_html(output.getvalue(), 'Merged_Inventory.xlsx'), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
