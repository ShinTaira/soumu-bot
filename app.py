import streamlit as st
import requests
import json
import streamlit.components.v1 as components
import pandas as pd
import pypdf
import datetime
import os

# ==========================================
# 設定エリア
# ==========================================
GAS_API_URL = "https://script.google.com/macros/s/AKfycbysmoIjjc4ka6l5T4zeaWZOc4Dd-hIwC-p7eifHBlWWeh3JXF9hwY6BmriOLqUxWwRnsQ/exec"
LOG_FILE = "user_logs.csv"

def log_user_action(action, detail):
    """ユーザーの操作をログファイルに記録する"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = st.session_state.get("user_name", "Unknown")
    
    # データフレーム作成
    new_data = pd.DataFrame({
        "timestamp": [now],
        "user": [user],
        "action": [action],
        "detail": [detail]
    })
    
    # ファイル追記 (ヘッダーは初回のみ)
    if not os.path.exists(LOG_FILE):
        new_data.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    else:
        new_data.to_csv(LOG_FILE, mode='a', header=False, index=False, encoding="utf-8-sig")
BOT_NAME = "総務Bot"
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
            if isinstance(data, list):
                return data, [] 
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
            if keyword.strip() and keyword.strip() in query_lower:
                return f"{item['answer']}\n\n---\n**関連キーワード:** {item['keywords']}"
    return None

# ==========================================
# UI設定
# ==========================================
st.set_page_config(page_title="🏢 SPIN 総務Bot", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    /* 全体のフォントと背景 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
        color: #334155;
    }
    
    .stApp {
        background-color: #f0f4f8; /* 薄いブルーグレーの背景で清潔感を演出 */
        background-image: linear-gradient(135deg, #f0f4f8 0%, #dbeafe 100%);
    }

    /* ヘッダーエリア */
    .main-header {
        background: linear-gradient(135deg, #0066cc 0%, #004c99 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 51, 102, 0.2);
    }
    .main-header h1 {
        color: white;
        font-weight: 700;
        margin: 0;
        font-size: 1.8rem;
        letter-spacing: 0.05em;
    }
    .main-header p {
        color: #e0f2fe;
        margin-top: 0.5rem;
        font-size: 0.95rem;
    }

    /* ボタン共通スタイル */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: auto;
        min-height: 54px;
        white-space: normal;
        text-align: left;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid transparent;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Primary Button (送信など) */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #0066cc 0%, #005bb5 100%);
        border: none;
        color: white;
        justify-content: center;
        text-align: center;
        font-weight: 700;
    }

    /* Secondary Button (キャンセル、戻るなど) */
    div[data-testid="stButton"] > button[kind="secondary"] {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        color: #334155;
        justify-content: center;
        text-align: center;
    }

    /* 概要選択ボタン (通常のボタンを使用している箇所) */
    /* 特定のクラス付与は難しいが、デフォルトのsecondaryボタンをカード風にする */

    /* エラーメッセージ */
    .error-message {
        color: #d32f2f;
        font-weight: 600;
        padding: 16px;
        background-color: #fde8e8;
        border-left: 5px solid #d32f2f;
        border-radius: 8px;
        margin-bottom: 16px;
    }

    /* チャットメッセージ */
    [data-testid="stChatMessage"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        margin-bottom: 0.5rem;
    }

    /* カード風装飾（Markdownで直接divを書く場合に使用） */
    .info-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border-top: 4px solid #0066cc;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# ステート管理
# ==========================================
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "こんにちは！下のカテゴリから知りたい内容を選んでください。"}]
if "selected_summary" not in st.session_state:
    st.session_state.selected_summary = None
if "escalation_mode" not in st.session_state:
    st.session_state.escalation_mode = False
if "escalation_context" not in st.session_state:
    st.session_state.escalation_context = ""

faq_data, employee_list = fetch_all_data()

# ==========================================
# サイドバー (常時表示)
# ==========================================
with st.sidebar:
    st.markdown("### 👤 ユーザー情報")
    if st.session_state.user_name:
        if st.session_state.get("is_admin_authenticated", False):
             st.write(f"**{st.session_state.user_name} (管理者)** 🔓")
        else:
             st.write(f"**{st.session_state.user_name}** さん")
    else:
        st.write("未ログイン")
    
    st.markdown("---")
    st.markdown("### 🤖 Botステータス")
    st.success("🟢 稼働中")
    
    st.markdown("---")
    st.markdown("### 💡 クイックヘルプ")
    st.info("困ったときは検索バーか、メニューから質問を選んでください。")

    st.markdown("---")
    # モード切り替え (管理者のみ表示)
    if st.session_state.get("is_admin_authenticated", False):
        app_mode = st.radio("機能モード", ["🤖 チャットBot", "📄 書類検索"])
    else:
        app_mode = "🤖 チャットBot"
    
    st.markdown("---")
    st.caption("Ver 2.0.1")

    # 管理者メニュー
    with st.expander("🔒 管理者メニュー"):
        password = st.text_input("Password", type="password", key="admin_pwd")
        if password == "admin123":
            if not st.session_state.get("is_admin_authenticated", False):
                st.toast("管理者としてログインしました！機能制限が解除されました。", icon="🔓")
            st.session_state.is_admin_authenticated = True
            st.success("Access Granted")
            if os.path.exists(LOG_FILE):
                df_log = pd.read_csv(LOG_FILE)
                
                # KPI
                total_access = len(df_log)
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                today_access = len(df_log[df_log['timestamp'].str.contains(today_str)])
                
                # 単純化のため、解決数などは正確なログが必要だが、ここでは仮にアクション数で代用
                st.metric("総アクション数", total_access)
                st.metric("本日のアクション", today_access)
                
                # トレンド
                st.write("📊 人気キーワード")
                search_logs = df_log[df_log['action'].str.contains("Search|Menu", case=False)]
                if not search_logs.empty:
                    top_keywords = search_logs['detail'].value_counts().head(5)
                    st.bar_chart(top_keywords)

                # データ
                st.write("📋 ログデータ")
                st.dataframe(df_log)
                
                csv = df_log.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "CSVダウンロード",
                    csv,
                    "user_logs.csv",
                    "text/csv"
                )
            else:
                st.info("ログデータはまだありません。")
        elif password:
            st.error("Invalid Password")

# ==========================================
# 画面1: 名前入力
# ==========================================
if not st.session_state.user_name:
    st.markdown(f"""
        <div class="main-header">
            <h1>🏢 SPIN 総務Bot</h1>
            <p>あなたの社内業務をスマートにサポートします</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="info-card"><h5>👋 ようこそ！</h5><p>利用を開始するには、社員名簿に登録されている<strong>フルネーム</strong>を入力してください。</p></div>', unsafe_allow_html=True)

    name_input = st.text_input("お名前", placeholder="例: スピン 太郎")
    
    if st.button("利用を開始する", type="primary"):
        if name_input:
            # ★修正: 入力された名前からスペースを全削除して比較用にする
            input_nospace = name_input.replace(" ", "").replace("　", "")
            
            # ★修正: 社員リスト側もスペースを全削除したリストを作る
            employee_list_nospace = [str(name).replace(" ", "").replace("　", "") for name in employee_list]
            
            # 比較（リストが取得できている場合のみチェック）
            if employee_list and input_nospace not in employee_list_nospace:
                st.markdown(f'<div class="error-message">⚠️ エラー: 「{name_input}」さんは社員名簿に見つかりませんでした。<br>正しいフルネームを再度入力してください。</div>', unsafe_allow_html=True)
            else:
                st.session_state.user_name = name_input
                st.rerun()
        else:
            st.warning("お名前を入力してください。")

# ==========================================
# 画面2: メインチャット
# ==========================================
else:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        
        # --- モード分岐 ---
        if app_mode == "📄 書類検索":
            st.markdown("## 📄 書類検索モード")
            st.markdown('<div class="info-card"><p>就業規則やマニュアルなどのPDFファイルをアップロードして、内容を直接検索できます。</p></div>', unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("PDFファイルを選択", type="pdf")
            
            if uploaded_file:
                try:
                    # PDF読み込み
                    pdf_reader = pypdf.PdfReader(uploaded_file)
                    num_pages = len(pdf_reader.pages)
                    st.success(f"✅ {uploaded_file.name} (全{num_pages}ページ) を読み込みました")
                    
                    st.markdown("---")
                    search_kw = st.text_input("検索するキーワードを入力してください", placeholder="例: 残業代、有給休暇...")
                    
                    if st.button("検索実行", type="primary"):
                        if search_kw:
                            log_user_action("PDF Search", f"File: {uploaded_file.name}, KW: {search_kw}")
                            results = []
                            
                            # 全ページ探索
                            for pg_num, page in enumerate(pdf_reader.pages, 1):
                                text = page.extract_text()
                                if text:
                                    # キーワードが含まれるかチェック
                                    if search_kw in text:
                                        # 見つかった箇所の前後を抽出（コンテキスト）
                                        idx = text.find(search_kw)
                                        # 前後40文字
                                        start_idx = max(0, idx - 40)
                                        end_idx = min(len(text), idx + len(search_kw) + 40)
                                        snippet = text[start_idx:end_idx].replace("\n", "")
                                        
                                        # ハイライト
                                        snippet = snippet.replace(search_kw, f"**`{search_kw}`**")
                                        results.append((pg_num, snippet))
                            
                            if results:
                                st.write(f"🔍 **{len(results)}箇所** で見つかりました:")
                                for pg, snip in results:
                                    st.markdown(f"- **P.{pg}**: ...{snip}...")
                            else:
                                st.warning(f"「{search_kw}」は見つかりませんでした。")
                        else:
                            st.error("キーワードを入力してください。")
                
                except Exception as e:
                    st.error(f"PDFの読み込みエラー: {e}")

        else:
            # --- 通常: チャットBotモード ---
            st.markdown(f"""
                <div class="main-header">
                    <h1>🏢 SPIN 総務Bot</h1>
                    <p>Logged in as: <strong>{st.session_state.user_name}</strong></p>
                </div>
            """, unsafe_allow_html=True)
    
        # --- ロジック ---
        def process_text_input(user_input):
            log_user_action("Search/Chat", user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})
            if "担当者へ連絡" in user_input:
                st.session_state.escalation_mode = True
                st.session_state.escalation_context = "テキスト入力からの連絡"
                st.rerun()
            else:
                result = search_faq(user_input, faq_data)
                reply_text = result if result else "申し訳ありません。回答が見つかりませんでした。\n\n解決しない場合は、下の**「担当者へ連絡」**ボタンを押してください。"
                st.session_state.messages.append({"role": "assistant", "content": reply_text, "feedback": True})
    
        def global_search(query, data):
            """全体のデータを検索してリストで返す"""
            if not query: return []
            query_lower = query.lower().strip()
            results = []
            for item in data:
                # マッチング対象: カテゴリ、概要、詳細、キーワード
                target_text = f"{item.get('category', '')} {item.get('summary', '')} {item.get('answer', '')} {item.get('keywords', '')}".lower()
                if query_lower in target_text:
                    results.append(item)
            return results
    
        def process_keyword_click(keyword, answer, category, full_keywords):
            log_user_action("Menu Select", f"{category} > {keyword}")
            st.session_state.messages.append({"role": "user", "content": keyword})
            reply_content = f"{answer}\n\n---\n**関連キーワード:** {full_keywords}"
            # フィードバックフラグを追加
            st.session_state.messages.append({"role": "assistant", "content": reply_content, "feedback": True})
            st.session_state.selected_summary = None
    
        @st.dialog("お問い合わせ")
        def open_inquiry_modal(context):
            st.write("解決できず申し訳ありません。担当者へ問い合わせますか？")
            
            # フォーム初期値
            default_subject = f"【未解決】{context}"
            
            with st.form("modal_inquiry_form"):
                st.text_input("件名", value=default_subject, disabled=True)
                detail = st.text_area("詳細内容", placeholder="具体的な不明点や、聞きたい内容を入力してください")
                
                submitted = st.form_submit_button("送信する", type="primary")
                if submitted:
                    if detail:
                        # 送信処理 (ログ出力等)
                        log_msg = f"担当者へ連絡 (カテゴリ: {context})\n詳細: {detail}"
                        # Bot返信はチャットには追加せず、Modal内で完結させる表現にするか？
                        # 要件: "モーダル内で「送信完了しました」と表示... 「終了してトップへ戻る」ボタンを表示"
                        send_log_to_gas(log_msg, "（Bot: Modal Inquiry Sent）", st.session_state.user_name)
                        st.session_state.modal_success = True
                        st.rerun()
                    else:
                        st.error("詳細内容を入力してください。")
    
            # 送信成功後の表示
            if st.session_state.get("modal_success", False):
                st.success("お問い合わせを送信しました。担当者（木村）よりご連絡いたします。")
                if st.button("🏁 終了してトップへ戻る", type="primary"):
                    st.session_state.modal_success = False
                    st.session_state.search_query = ""
                    st.session_state.current_category = "(選択してください)"
                    st.session_state.selected_summary = None
                    st.rerun()
    
        def trigger_escalation_form(context):
            # レガシー互換のため残すが、実際はModalを呼ぶ形に変えるか、
            # show_feedback_ui 側で open_inquiry_modal を呼ぶようにする。
            # ここでは何もしないか、open_inquiry_modal(context) を呼びたいが、dialog関数は直接呼ぶもの。
            open_inquiry_modal(context)
    
        def show_feedback_ui(key_suffix, context_text):
            st.write("この回答で解決しましたか？")
            col_yes, col_no = st.columns([1, 4])
            with col_yes:
                if st.button("👍 はい", key=f"fb_yes_{key_suffix}", type="secondary"):
                    st.toast("フィードバックありがとうございます！", icon="🎉")
            with col_no:
                if st.button("👎 いいえ", key=f"fb_no_{key_suffix}", type="secondary"):
                    trigger_escalation_form(context_text)
    
        def submit_escalation(detail_text):
            context = st.session_state.escalation_context
            log_msg = f"担当者へ連絡 (カテゴリ: {context})\n詳細: {detail_text}"
            reply_text = "承知いたしました。人事部の木村にエスカレーション通知を送ります。\n木村が確認次第、別途ご連絡いたします。"
            st.session_state.messages.append({"role": "assistant", "content": reply_text})
            send_log_to_gas(log_msg, reply_text, st.session_state.user_name)
            st.session_state.show_inquiry = False
            st.success("お問い合わせを受け付けました。担当者（木村）よりご連絡いたします。")
    
        # --- 履歴表示 ---
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # フィードバック表示（assistantかつfeedbackフラグがある場合）
                if message.get("feedback"):
                    show_feedback_ui(f"chat_{i}", f"【未解決】チャット履歴: {i}")
    
        # --- エスカレーションフォーム ---
        # お知らせ掲示板
        st.info("📢 【重要】年末調整の提出期限は12/10までです。お早めに対応をお願いします。", icon="ℹ️")
    
        # 検索バーの設置 (keyを使ってステートと同期)
        if "search_query" not in st.session_state:
            st.session_state.search_query = ""
            
        def set_search_query(term):
            st.session_state.search_query = term
    
        search_query = st.text_input("🔍 キーワード検索", placeholder="キーワードで探す（例：交通費、有給、年末調整...）", key="search_query")
        
        # クイック検索タグ
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True) # スペーサー
        quick_tags = ["有給", "交通費", "年末調整", "住所変更"]
        q_cols = st.columns(len(quick_tags))
        for i, tag in enumerate(quick_tags):
            # クイックタグは押すと検索バーに入力される
            q_cols[i].button(tag, key=f"qtag_{i}", on_click=set_search_query, args=(tag,), use_container_width=True)
        
        # 検索テキストがある場合は検索結果を表示
        if search_query:
            st.markdown(f"### 🔎 「{search_query}」の検索結果")
            search_results = global_search(search_query, faq_data)
            
            if search_results:
                for i, item in enumerate(search_results):
                    # カード表示
                    title = f"{item.get('category', 'その他')} > {item.get('summary', '概要なし')}"
                    answer = item.get('answer', '回答がありません')
                    
                    st.markdown(f"""
                        <div class="info-card">
                            <h4 style="margin:0; color:#0066cc;">{title}</h4>
                            <p style="margin-top:0.5rem; white-space: pre-wrap;">{answer}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # フィードバックセクション
                    # フィードバックセクション
                    show_feedback_ui(f"search_{i}", f"【未解決】検索: {search_query} > {title}")
                    st.markdown("---")
            else:
                st.info("該当する項目は見つかりませんでした。別のキーワードで試すか、下のメニューから探してください。")
    
        # 検索テキストがない場合は通常のカテゴリメニューを表示
        else:
            st.markdown("### 🔍 質問メニュー")
            
            if faq_data:
                categories = sorted(list(set([item['category'] for item in faq_data if item.get('category')])))
                
                # セッションステートでカテゴリ選択を管理するためのキーを設定
                if "current_category" not in st.session_state:
                    st.session_state.current_category = "(選択してください)"
    
                def on_category_change():
                    st.session_state.selected_summary = None
    
                # key="current_category" を追加してステートと同期させる
                selected_category = st.selectbox(
                    "カテゴリを選択してください", 
                    ["(選択してください)"] + categories, 
                    on_change=on_category_change,
                    key="current_category"  
                )
    
                if selected_category != "(選択してください)":
                # ▼▼▼ トップに戻るボタンの追加 ▼▼▼
                    def go_to_top():
                        st.session_state.current_category = "(選択してください)"
                        st.session_state.selected_summary = None
    
                    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
                    col_top_back, _ = st.columns([1, 3])
                    with col_top_back:
                        st.button("↩️ トップメニューに戻る", type="secondary", key="back_to_top_main", on_click=go_to_top)
                # ▲▲▲ 追加終わり ▲▲▲
    
    
                    # カテゴリ内の全データを取得
                    category_items = [item for item in faq_data if item['category'] == selected_category]
    
                    if st.session_state.selected_summary is None:
                        st.markdown(f"""
                            <div class="info-card">
                                <h3 style="margin:0; color:#0066cc;">📂 {selected_category}</h3>
                                <p style="margin:0.5rem 0 0 0; color:#64748b;">知りたい内容の概要を選択してください。</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 概要ラベルの重複を排除してリスト化
                        unique_summaries = []
                        seen = set()
                        for item in category_items:
                            label = item.get('summary')
                            if not label:
                                label = str(item['keywords']).split(',')[0]
                            if label not in seen:
                                unique_summaries.append(label)
                                seen.add(label)
    
                        cols = st.columns(2)
                        for i, label in enumerate(unique_summaries):
                            if cols[i % 2].button(label, key=f"topic_btn_{i}"):
                                st.session_state.selected_summary = label
                                st.rerun()
                    else:
                        target_summary = st.session_state.selected_summary
                        
                        st.markdown(f"""
                            <div class="info-card">
                                <h3 style="margin:0; color:#0066cc;">📄 {target_summary}</h3>
                                <p style="margin:0.5rem 0 0 0; color:#64748b;">さらに具体的なキーワードを選択してください。</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 戻るボタン
                        col_back1, col_back2 = st.columns([1, 2])
                        with col_back1:
                            if st.button("↩️ 概要選択に戻る", key="back_btn", type="secondary"):
                                st.session_state.selected_summary = None
                                st.rerun()
                        
                        # 選択された概要名に一致する全アイテムを抽出
                        matched_items = [
                            item for item in category_items 
                            if (item.get('summary') or str(item['keywords']).split(',')[0]) == target_summary
                        ]
                        
                        # 全アイテムのキーワードを集約
                        kw_cols = st.columns(2)
                        idx = 0
                        for item in matched_items:
                            keywords_list = str(item['keywords']).split(',')
                            for kw in keywords_list:
                                clean_kw = kw.strip()
                                if clean_kw:
                                    if kw_cols[idx % 2].button(clean_kw, key=f"kw_btn_{idx}"):
                                        process_keyword_click(clean_kw, item['answer'], selected_category, item['keywords'])
                                        st.rerun()
                                    idx += 1
    
            else:
                st.error("データの読み込みに失敗しました。")
    
            # --- グローバルナビゲーション: トップに戻る ---
            # 検索中、またはカテゴリ選択中のみ表示
            is_searching = bool(st.session_state.get("search_query"))
            is_category_selected = st.session_state.get("current_category", "(選択してください)") != "(選択してください)"
            
            if is_searching or is_category_selected:
                st.markdown("---")
                if st.button("↩️ トップメニューに戻る", key="global_back_to_top_footer", use_container_width=True):
                    st.session_state.current_category = "(選択してください)"
                    st.session_state.selected_summary = None
                    st.session_state.search_query = ""
                    st.rerun()
    
            # --- フッター: お問い合わせフォーム（共通） ---
            st.markdown("---")
            
            # フォーム未表示時は「開く」ボタンを表示
            if not st.session_state.get("show_inquiry", False):
                st.write("解決しない場合はこちら")
                if st.button("✉️ お問い合わせフォームを開く", type="primary"):
                    st.session_state.show_inquiry = True
                    # コンテキストの決定
                    if st.session_state.get("search_query"):
                        ctx = f"検索: {st.session_state.search_query}"
                    elif st.session_state.get("current_category", "(選択してください)") != "(選択してください)":
                        ctx = st.session_state.current_category
                    else:
                        ctx = "その他"
                    st.session_state.escalation_context = ctx
                    st.rerun()
    
            # フォーム表示
            if st.session_state.get("show_inquiry", False):
                # アンカーと自動スクロール
                st.markdown("<div id='contact-form'></div>", unsafe_allow_html=True)
                if st.session_state.get("scroll_to_form"):
                    components.html(
                        """
                        <script>
                            // 画面の一番下へスクロール（親ウィンドウを対象）
                            var doc = window.parent.document;
                            window.parent.scrollTo({top: doc.body.scrollHeight, behavior: 'smooth'});
                        </script>
                        """,
                        height=0
                    )
                    st.session_state.scroll_to_form = False
    
                # 案内メッセージ（自動展開時用）
                if "【未解決】" in st.session_state.get("escalation_context", ""):
                    st.warning("承知いたしました。詳細をお問い合わせフォームよりご連絡ください。")
    
                # フォームヘッダー（カードデザイン）
                st.markdown(f"""
                    <div class="info-card">
                        <h4 style="margin:0; color:#0066cc;">📝 お問い合わせフォーム</h4>
                        <p style="margin:0.5rem 0 0 0;">件名: <strong>【Bot問い合わせ】{st.session_state.get('escalation_context', 'その他')}</strong></p>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.form("inquiry_form_footer"):
                    st.write("具体的な不明点や、聞きたい内容を入力してください")
                    detail = st.text_area("詳細内容", label_visibility="collapsed")
                    col_sub, col_cls = st.columns([1, 1])
                    with col_sub:
                        submitted = st.form_submit_button("送信する", type="primary")
                    with col_cls:
                        closed = st.form_submit_button("閉じる", type="secondary")
                    
                    if submitted:
                        if detail:
                            submit_escalation(detail)
                            st.rerun()
                        else:
                            st.error("内容を入力してください。")
                    
                    if closed:
                        st.session_state.show_inquiry = False
                        st.rerun()
    
        if prompt := st.chat_input("質問を直接入力することもできます..."):
            process_text_input(prompt)
            st.rerun()