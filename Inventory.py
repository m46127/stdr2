import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
import chardet

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """ダウンロードリンクを生成するHTMLを返します。"""
    bin_str = base64.b64encode(bin_file).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">Download {file_label}</a>'
    return href

def main():
    st.title("Inventory Management System")
    uploaded_file_csv = st.file_uploader("CSVファイル（ピッキングリスト）を選択", type="csv")
    uploaded_file_excel = st.file_uploader("Excelファイル（在庫表）を選択", type="xlsx")
    
    if uploaded_file_csv is not None and uploaded_file_excel is not None:
        # --- CSV(ピッキングリスト)の読み込み ---
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

        # CSVファイルの列名を確認し、統一する
        if 'コード' in picking_df.columns:
            code_col_csv = 'コード'
        elif '商品コード' in picking_df.columns:
            code_col_csv = '商品コード'
        else:
            st.error(f"CSVに「コード」または「商品コード」列が見つかりません。実際の列: {list(picking_df.columns)}")
            return
            
        if '数量' not in picking_df.columns:
            st.error(f"CSVに「数量」列が見つかりません。実際の列: {list(picking_df.columns)}")
            return

        # 数量を数値化して集計
        picking_df['数量'] = pd.to_numeric(picking_df['数量'], errors='coerce').fillna(0)
        picking_df = picking_df.groupby(code_col_csv, as_index=False)['数量'].sum()
        picking_df[code_col_csv] = picking_df[code_col_csv].astype(str).str.strip().str.upper()
        
        # マージ用にCSVの列名を「コード」に統一
        picking_df.rename(columns={code_col_csv: 'コード'}, inplace=True)

        # --- Excel(在庫表)の読み込み：元のレイアウトを維持 ---
        try:
            # Excelの6行目（Pythonではインデックス5）をヘッダーとして読み込む
            inventory_df = pd.read_excel(uploaded_file_excel, header=5)
        except Exception as e:
            st.error(f"Excelの読み込みに失敗しました: {e}")
            return
        
        # 'コード'または'商品コード'列を確実に取得
        if 'コード' in inventory_df.columns:
            code_col_excel = 'コード'
        elif '商品コード' in inventory_df.columns:
            code_col_excel = '商品コード'
        else:
            st.error("Excelの6行目に「コード」または「商品コード」列が見つかりません。レイアウトを確認してください。")
            return
        
        # 列名を「コード」に統一
        if code_col_excel != 'コード':
            inventory_df.rename(columns={code_col_excel: 'コード'}, inplace=True)
        
        # 'コード'列を文字列に変換し、空白を削除して大文字に統一
        inventory_df['コード'] = inventory_df['コード'].astype(str).str.strip().str.upper()
        
        # --- マージ処理 ---
        # `how='left'`でExcelの全行を保持しながら、数量を結合
        merged_df = pd.merge(inventory_df, picking_df, on='コード', how='left')
        
        # 数量がNaN（結合できなかった部分）を空白に置換
        merged_df['数量'] = merged_df['数量'].fillna('')

        # --- ダウンロード用Excelの生成 ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 元のシート名（'Sheet1'）に出力
            merged_df.to_excel(writer, sheet_name='Sheet1', index=False)

        st.markdown(get_binary_file_downloader_html(output.getvalue(), 'Merged_Inventory.xlsx'),
                    unsafe_allow_html=True)

if __name__ == "__main__":
    main()