# main.py
import streamlit as st
from streamlit_option_menu import option_menu

# メニューの選択肢を定義
menu_options = ["トップページ", "在庫", "同梱物集計"]

# サイドバーでオプションメニューを表示
selected_option = option_menu("メインメニュー", menu_options, icons=['house', 'layers', 'box'], menu_icon="cast", default_index=0)


# 選択肢に応じて表示するページを変更
if selected_option == "トップページ":
    # トップページの内容
    st.title("トップページ")
    st.write("ようこそ！")


elif selected_option == "在庫":
    # Inventory.py の内容をインポートして実行
    from Inventory import main as Inventory_main
    Inventory_main()

elif selected_option == "同梱物集計":
    # Include.py の内容をインポートして実行
    from Include import main as Include_main
    Include_main()