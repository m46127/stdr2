# Include.py
import streamlit as st
import pandas as pd

def main():
    # Streamlitアプリのタイトルを設定
    st.title('同梱物の追加数量集計')

    # ファイルアップロードのウィジェット
    uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=['csv'])

    # アップロードされたファイルがあるかどうかを確認
    if uploaded_file is not None:
        # CSVファイルを読み込む（エンコーディングを指定）
        df = pd.read_csv(uploaded_file, encoding='cp932')

        # 合計数量と追加数量の初期化
        total_count = 0
        additional_count = 0

        # 各行ごとに商品タイプと数量をチェック
        for index, row in df.iterrows():
            row_count = 0  # その行の同梱物数量
            # 30種類の商品タイプをチェック
            for i in range(1, 31):
                # 商品タイプ列と数量列が存在するか確認
                if f'商品タイプ{i}' in df.columns and f'商品数量{i}' in df.columns:
                    # 商品タイプが'同梱物'の場合、その行の数量をカウント
                    if row[f'商品タイプ{i}'] == '同梱物':
                        row_count += row[f'商品数量{i}']

            # その行の同梱物数量が5を超える場合、追加数量を加算
            if row_count > 5:
                additional_count += row_count - 5
            total_count += row_count

        # 結果を整数に変換して表示
        total_count = int(total_count)
        additional_count = int(additional_count)
        st.write(f"同梱物の合計数量: {total_count}, 追加数量: {additional_count}")

    else:
        # ファイルがアップロードされていない場合のメッセージを表示
        st.write("CSVファイルをアップロードしてください。")

if __name__ == "__main__":
    main()