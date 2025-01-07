import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
import chardet  # chardetをインポート

def get_binary_file_downloader_html(bin_file, file_label='File'):
    bin_str = base64.b64encode(bin_file).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">Download {file_label}</a>'
    return href

def main():
    st.title("Inventory Management System")
    uploaded_file_csv = st.file_uploader("Choose a CSV file", type="csv")
    uploaded_file_excel = st.file_uploader("Choose an Excel file", type="xlsx")
    
    if uploaded_file_csv is not None and uploaded_file_excel is not None:
        # CSVファイルのエンコーディングを検出
        uploaded_file_csv.seek(0)  # ストリームの先頭に移動
        raw_data = uploaded_file_csv.read()
        result = chardet.detect(raw_data)
        detected_encoding = result['encoding']
        uploaded_file_csv.seek(0)  # ストリームの先頭に再度移動
        
        # 検出されたエンコーディングでCSVファイルを読み込む
        picking_df = pd.read_csv(uploaded_file_csv, encoding=detected_encoding)
        
        # 'コード'と'数量'の列が存在するか確認
        if 'コード' in picking_df.columns and '数量' in picking_df.columns:
            # 'コード'でグループ化して'数量'の合計を計算
            picking_df = picking_df.groupby('コード')['数量'].sum().reset_index()
            picking_df['コード'] = picking_df['コード'].astype(str).str.strip().str.upper()
        else:
            # 'コード'または'数量'列が存在しない場合の処理
            st.error('CSVファイルに「コード」または「数量」列が存在しません。')
            return
        
        # 在庫表のExcelファイルを読み込む
        inventory_df = pd.read_excel(uploaded_file_excel, usecols='D')
        inventory_df.columns = ['コード']
        inventory_df['コード'] = inventory_df['コード'].astype(str).str.strip().str.upper()
        
        # 在庫表とピッキングリストをマージ
        merged_df = pd.merge(inventory_df, picking_df, on='コード', how='left')
        
        # 0の値をNaNに置き換えて空白にする
        merged_df['数量'].replace(0, np.nan, inplace=True)
        
        # ファイルをダウンロードするためのリンクを作成
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            merged_df.to_excel(writer, sheet_name='Sheet1', index=False)

        binary_excel = output.getvalue()
        st.markdown(get_binary_file_downloader_html(binary_excel, 'Merged_Inventory.xlsx'), unsafe_allow_html=True)

if __name__ == "__main__":
    main()