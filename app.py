import streamlit as st
import requests
import json

# ==========================================
# 設定エリア
# ==========================================
GAS_API_URL = "https://script.google.com/macros/s/AKfycbysmoIjjc4ka6l5T4zeaWZOc4Dd-hIwC-p7eifHBlWWeh3JXF9hwY6BmriOLqUxWwRnsQ/exec"
BOT_NAME = "総務サポートBot"
THEME_COLOR = "#003366"

# ==========================================
# 関数定義
# ==========================================

@st.cache_data
def fetch_all_data():
    try:
        response = requests.get(GAS_API_URL)
        if response.status_code == 200:
            data = response.json()
            # 古いGASの場合はリストが返ってくる可能性があるので対応
            if isinstance(data, list):
                return data, [] # FAQリスト, 空の社員リスト
            return data.get('faq', []), data.get('employees', [])
        return [], []
    except:
        return [], []

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
    /* エラーメッセージを目立たせる */
    .error-message {{
        color: #ff4b4b; font-weight: bold; padding: 10px; background-color: #ffe6e6; border-radius: 5px; margin-bottom: 10px;
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
if "escalation_mode" not in st.session_state:
    st.session_state.escalation_mode = False
if "escalation_context" not in st.session_state:
    st.session_state.escalation_context = ""

# データのロード (FAQと社員リストを一括取得)
faq_data, employee_list = fetch_all_data()

# ==========================================
# 画面1: 名前入力 (認証付き)
# ==========================================
if not st.session_state.user_name:
    st.markdown(f'<div class="main-header"><h1>🤖 {BOT_NAME}</h1></div>', unsafe_allow_html=True)
    
    st.info("利用を開始するには、フルネームを入力してください。")
    name_input = st.text_input("お名前", placeholder="例: 平良 慎")
    
    if st.button("利用を開始する", type="primary"):
        if name_input:
            # 入力された名前のスペースを削除して正規化（全角半角対応などは簡易的に）
            input_clean = name_input.strip()
            
            # 社員リストチェック
            if employee_list and input_clean not in employee_list:
                st.markdown(f'<div class="error-message">⚠️ エラー: 「{input_clean}」さんは社員名簿に見つかりませんでした。<br>正しいフルネームを再度入力してください。</div>', unsafe_allow_html=True)
            else:
                # リストにある、またはリスト取得失敗時(空)は通過させる(安全策)
                st.session_state.user_name = input_clean
                st.rerun()
        else:
            st.warning("お名前を入力してください。")

# ==========================================
# 画面2: メインチャット
# ==========================================
else:
    st.markdown(f'<div class="main-header"><h1>🤖 {BOT_NAME}</h1><p>利用中: {st.session_state.user_name} さん</p></div>', unsafe_allow_html=True)

    # --- ロジック ---
    def process_text_input(user_input):
        st.session_state.messages.append({"role": "user", "content": user_input})
        if "担当者へ連絡" in user_input:
            # テキスト入力で「担当者へ連絡」と打たれた場合もフォームモードへ
            st.session_state.escalation_mode = True
            st.session_state.escalation_context = "テキスト入力からの連絡"
            st.rerun()
        else:
            result = search_faq(user_input, faq_data)
            reply_text = result if result else "申し訳ありません。回答が見つかりませんでした。\n\n解決しない場合は、下の**「担当者へ連絡」**ボタンを押してください。"
            st.session_state.messages.append({"role": "assistant", "content": reply_text})

    def select_topic(item):
        st.session_state.selected_topic_item = item

    def process_keyword_click(keyword, answer, category, full_keywords):
        st.session_state.messages.append({"role": "user", "content": keyword})
        reply_content = f"{answer}\n\n---\n**関連キーワード:** {full_keywords}"
        st.session_state.messages.append({"role": "assistant", "content": reply_content})
        st.session_state.selected_topic_item = None

    # エスカレーションボタンが押された時の処理（モード切替）
    def trigger_escalation_form(context):
        st.session_state.escalation_mode = True
        st.session_state.escalation_context = context

    # フォーム送信処理
    def submit_escalation(detail_text):
        context = st.session_state.escalation_context
        
        # ログ用メッセージを作成
        log_msg = f"担当者へ連絡 (カテゴリ: {context})\n詳細: {detail_text}"
        
        # 通知用メッセージ（LINEワークスに飛ぶ）
        reply_text = "承知いたしました。人事部の木村にエスカレーション通知を送ります。\n木村が確認次第、別途ご連絡いたします。"
        
        st.session_state.messages.append({"role": "assistant", "content": reply_text})
        
        # GASへ送信（詳細も含めて送る）
        send_log_to_gas(log_msg, reply_text, st.session_state.user_name)
        
        # モードリセット
        st.session_state.escalation_mode = False
        st.success("担当者へ詳細を送信しました！")

    # --- 履歴表示 ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- エスカレーションフォーム表示中かどうかで分岐 ---
    if st.session_state.escalation_mode:
        st.markdown("---")
        st.warning("📝 **担当者へ連絡します**")
        st.write(f"現在のカテゴリ: **{st.session_state.escalation_context}**")
        
        with st.form("escalation_form"):
            detail = st.text_area("困っている内容や、わからない点を具体的に入力してください。", placeholder="例: 〇〇の申請画面でエラーが出て進めません。")
            
            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("キャンセル", type="secondary")
            with col2:
                submit = st.form_submit_button("この内容で送信する", type="primary")
            
            if submit:
                if detail:
                    submit_escalation(detail)
                    st.rerun()
                else:
                    st.error("内容を入力してください。")
            
            if cancel:
                st.session_state.escalation_mode = False
                st.rerun()

    # --- 通常メニュー表示 ---
    else:
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
                                process_keyword_click(clean_kw, target_item['answer'], selected_category, target_item['keywords'])
                                st.rerun()

            st.markdown("---")
            st.write("解決しない場合はこちら")
            current_context = selected_category if selected_category != "(選択してください)" else "未選択"
            
            # ★変更点: ボタンを押すと送信ではなく「フォームモード」にする
            if st.button("🙋‍♀️ 担当者（人事部木村）へ連絡する", type="primary"):
                trigger_escalation_form(current_context)
                st.rerun()
        else:
            st.error("データの読み込みに失敗しました。")

        if prompt := st.chat_input("質問を直接入力することもできます..."):
            process_text_input(prompt)
            st.rerun()