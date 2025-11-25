import streamlit as st
import requests
import json

# ==========================================
# 設定エリア
# ==========================================
# ★GASのURL (変更なし)
GAS_API_URL = "https://script.google.com/macros/s/AKfycbysmoIjjc4ka6l5T4zeaWZOc4Dd-hIwC-p7eifHBlWWeh3JXF9hwY6BmriOLqUxWwRnsQ/exec"
BOT_NAME = "総務サポートBot"
THEME_COLOR = "#003366"

# ==========================================
# 関数定義
# ==========================================

# キャッシュ無効化
# @st.cache_data
def fetch_faq_data():
    try:
        response = requests.get(GAS_API_URL)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def send_log_to_gas(message, reply, user_name, log_type="🚨エスカレーション"):
    try:
        payload = {
            "message": message,
            "reply": reply,
            "type": log_type,
            "userName": user_name
        }
        requests.post(GAS_API_URL, json=payload)
    except:
        pass

def search_faq(query, faq_data):
    if not query: return None
    query_lower = query.lower().strip()
    
    for item in faq_data:
        keywords = str(item['keywords']).lower().split(',')
        for keyword in keywords:
            if keyword.strip() in query_lower:
                # 検索時もキーワードを併記して返す
                return f"{item['answer']}\n\n---\n**関連キーワード:** {item['keywords']}"
    return None

# ==========================================
# UI設定
# ==========================================
st.set_page_config(page_title=BOT_NAME, page_icon="🤖", layout="centered")

st.markdown(f"""
    <style>
    .main-header {{
        background-color: {THEME_COLOR}; padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;
    }}
    .stButton > button {{
        width: 100%; border-radius: 8px; height: auto; min-height: 50px; white-space: normal; text-align: left; padding: 10px 15px; display: flex; align-items: center;
    }}
    div[data-testid="stButton"] > button[kind="primary"] {{
        background-color: #ff4b4b; border-color: #ff4b4b; color: white; justify-content: center; text-align: center;
    }}
    div[data-testid="stButton"] > button[kind="secondary"] {{
        background-color: #f0f2f6; border-color: #d6d6d6; color: #31333F; justify-content: center; text-align: center; height: 40px;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ステート管理
# ==========================================
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "こんにちは！下のカテゴリから知りたい内容を選んでください。"}]
if "selected_topic_item" not in st.session_state:
    st.session_state.selected_topic_item = None

# ==========================================
# 画面1: 名前入力
# ==========================================
if not st.session_state.user_name:
    st.markdown(f'<div class="main-header"><h1>🤖 {BOT_NAME}</h1></div>', unsafe_allow_html=True)
    st.write("利用を開始するにはお名前を入力してください。")
    name_input = st.text_input("お名前", placeholder="例: スピン 太郎")
    
    if st.button("利用を開始する", type="primary"):
        if name_input:
            st.session_state.user_name = name_input
            st.rerun()
        else:
            st.warning("お名前を入力してください。")

# ==========================================
# 画面2: メインチャット
# ==========================================
else:
    st.markdown(f'<div class="main-header"><h1>🤖 {BOT_NAME}</h1><p>利用中: {st.session_state.user_name} さん</p></div>', unsafe_allow_html=True)

    faq_data = fetch_faq_data()

    # --- ロジック ---
    def process_text_input(user_input):
        st.session_state.messages.append({"role": "user", "content": user_input})
        if "担当者へ連絡" in user_input:
            reply_text = "承知いたしました。人事部の木村にエスカレーション通知を送ります。\n木村が確認次第、別途ご連絡いたします。"
            send_log_to_gas(user_input, reply_text, st.session_state.user_name)
        else:
            result = search_faq(user_input, faq_data)
            reply_text = result if result else "申し訳ありません。回答が見つかりませんでした。\n\n直接担当者に聞きたい場合は、**「担当者へ連絡」**ボタンを押してください。"
        st.session_state.messages.append({"role": "assistant", "content": reply_text})

    def select_topic(item):
        st.session_state.selected_topic_item = item

    # ★修正点: 回答にキーワードも併記する
    def process_keyword_click(keyword, answer, category, full_keywords):
        st.session_state.messages.append({"role": "user", "content": keyword})
        # 回答＋キーワードの形にする
        reply_content = f"{answer}\n\n---\n**関連キーワード:** {full_keywords}"
        st.session_state.messages.append({"role": "assistant", "content": reply_content})
        st.session_state.selected_topic_item = None

    def process_escalation(category_context):
        msg = "担当者へ連絡"
        reply_text = "承知いたしました。人事部の木村にエスカレーション通知を送ります。\n木村が確認次第、別途ご連絡いたします。"
        st.session_state.messages.append({"role": "user", "content": msg})
        st.session_state.messages.append({"role": "assistant", "content": reply_text})
        log_msg = f"{msg} (閲覧中カテゴリ: {category_context})"
        send_log_to_gas(log_msg, reply_text, st.session_state.user_name)

    # --- 履歴表示 ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- メニュー表示 ---
    st.markdown("### 🔍 質問メニュー")
    
    if faq_data:
        categories = sorted(list(set([item['category'] for item in faq_data if item.get('category')])))
        
        def on_category_change():
            st.session_state.selected_topic_item = None

        selected_category = st.selectbox("カテゴリを選択してください", ["(選択してください)"] + categories, on_change=on_category_change)

        if selected_category != "(選択してください)":
            
            # ▼ 概要選択モード
            if st.session_state.selected_topic_item is None:
                st.markdown(f"**{selected_category}** の中から、知りたい概要を選んでください:")
                category_items = [item for item in faq_data if item['category'] == selected_category]
                
                cols = st.columns(2)
                for i, item in enumerate(category_items):
                    label = item.get('summary')
                    if not label:
                        label = str(item['keywords']).split(',')[0]
                    
                    if cols[i % 2].button(label, key=f"topic_btn_{i}"):
                        select_topic(item)
                        st.rerun()

            # ▼ 詳細キーワード選択モード
            else:
                target_item = st.session_state.selected_topic_item
                summary_title = target_item.get('summary')
                if not summary_title:
                     summary_title = str(target_item['keywords']).split(',')[0]

                st.info(f"**「{summary_title}」** について、具体的にどれに当てはまりますか？")
                
                if st.button("↩️ 概要選択に戻る", key="back_btn", type="secondary"):
                    st.session_state.selected_topic_item = None
                    st.rerun()

                keywords_list = str(target_item['keywords']).split(',')
                kw_cols = st.columns(2)
                for j, kw in enumerate(keywords_list):
                    clean_kw = kw.strip()
                    if clean_kw:
                        if kw_cols[j % 2].button(clean_kw, key=f"kw_btn_{j}"):
                            # ★修正点: キーワード全体(target_item['keywords'])も渡す
                            process_keyword_click(clean_kw, target_item['answer'], selected_category, target_item['keywords'])
                            st.rerun()

        st.markdown("---")
        st.write("解決しない場合はこちら")
        current_context = selected_category if selected_category != "(選択してください)" else "未選択"
        if st.button("🙋‍♀️ 担当者（人事部木村）へ連絡する", type="primary"):
            process_escalation(current_context)
            st.rerun()
    else:
        st.error("データの読み込みに失敗しました。")

    if prompt := st.chat_input("質問を直接入力することもできます..."):
        process_text_input(prompt)
        st.rerun()