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
    uploaded_file_csv = st.file_uploader("Choose a CSV file (Picking List)", type="csv")
    uploaded_file_excel = st.file_uploader("Choose an Excel file (Inventory Sheet)", type="xlsx")
    
    if uploaded_file_csv is not None and uploaded_file_excel is not None:
        # --- CSV(ピッキング)読み込み ---
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

        if not {'コード', '数量'}.issubset(picking_df.columns):
            st.error(f"CSVに「コード」「数量」列が見つかりません。実際の列: {list(picking_df.columns)}")
            return

        picking_df['数量'] = pd.to_numeric(picking_df['数量'], errors='coerce').fillna(0)
        picking_df = picking_df.groupby('コード', as_index=False)['数量'].sum()
        picking_df['コード'] = picking_df['コード'].astype(str).str.strip().str.upper()

        # --- Excel(在庫表)読み込み：元のレイアウトを維持 ---
        try:
            # header=5で6行目をヘッダーとして読み込む
            inventory_df = pd.read_excel(uploaded_file_excel, header=5, dtype=str)
        except Exception as e:
            st.error(f"Excelの読み込みに失敗しました: {e}")
            return
        
        # 'コード'列を確実に取得
        if 'コード' not in inventory_df.columns:
            st.error("Excelの6行目に「コード」列が見つかりません。レイアウトを確認してください。")
            return
        
        # 'コード'列の処理
        inventory_df['コード'] = inventory_df['コード'].astype(str).str.strip().str.upper()
        
        # --- マージ処理 ---
        # picking_dfの「数量」列をinventory_dfに左結合で追加
        merged_df = pd.merge(inventory_df, picking_df, on='コード', how='left')
        
        # 0 → NaN → 空白（見た目を空に）
        merged_df['数量'] = merged_df['数量'].replace(0, np.nan)
        merged_df['数量'] = merged_df['数量'].astype(object).where(merged_df['数量'].notna(), '')

        # --- ダウンロード用Excel生成 ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            merged_df.to_excel(writer, sheet_name='Sheet1', index=False)

        st.markdown(get_binary_file_downloader_html(output.getvalue(), 'Merged_Inventory.xlsx'),
                    unsafe_allow_html=True)

if __name__ == "__main__":
    main()