import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import re
import time

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="Maestro：你的AI写歌助手", 
    page_icon="🎹", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS 样式优化 (针对按钮和整体布局) ---
st.markdown("""
    <style>
        /* 调整页面顶部边距，让标题更紧凑 */
        .block-container {
            padding-top: 2rem !important;
        }
        /* 优化开始按钮，使其更醒目 */
        div.stButton > button {
            font-size: 1.2rem !important;
            font-weight: bold !important;
            padding: 0.6rem 2rem !important;
            width: 100%;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🎹 Maestro：你的AI写歌助手")
st.caption("模式: Advanced Chat | 机制: Streaming | 自动去重")

# --- 2. 侧边栏 (自动配置) ---
with st.sidebar:
    st.header("API 设置")
    default_key = "app-QbS2Fs0LQ0klcni6nCfjchOS"
    DIFY_API_KEY = st.text_input("Dify API Key", value=default_key, type="password", disabled=True)
    
    base_url_input = st.text_input("Dify Base URL", value="https://api.dify.ai/v1")
    DIFY_BASE_URL = base_url_input.rstrip("/")
    st.info("已自动配置 API Key。")

# --- 3. 核心函数 ---

def upload_file(file_obj, user_id="user-123"):
    """上传文件"""
    url = f"{DIFY_BASE_URL}/files/upload"
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    files = {'file': (file_obj.name, file_obj, file_obj.type)}
    data = {'user': user_id}
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json().get('id')
    except Exception as e:
        st.error(f"❌ 图片上传失败: {e}")
        return None

def extract_audio_links(text):
    """提取链接并去重 (保留前2个)"""
    if not isinstance(text, str): return []
    links = re.findall(r'(https?://[^\s)]+\.mp3)', text)
    unique_links = list(dict.fromkeys(links))
    return unique_links[:2]

# --- 4. 简约风格小游戏 (HTML/JS) ---
def render_game():
    game_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Segoe UI', sans-serif; }
        .game-container {
            width: 100%;
            height: 270px;
            /* --- 风格：极简灰 --- */
            background-color: #F9FAFB; 
            border: 2px solid #E5E7EB; 
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            text-align: center;
            box-sizing: border-box;
        }
        h4 { 
            margin-top: 20px; 
            color: #1F2937; /* 近乎黑色 */
            font-size: 16px; 
            font-weight: 500;
            letter-spacing: 0.5px;
        }
        #score { 
            font-size: 28px; 
            font-weight: 800; 
            color: #000000; /* 纯黑 */
            margin-bottom: 5px; 
        }
        
        .note {
            position: absolute;
            font-size: 38px;
            cursor: pointer;
            user-select: none;
            /* --- 音符：完全不透明，鲜艳 --- */
            opacity: 1 !important; 
            filter: drop-shadow(0px 2px 2px rgba(0,0,0,0.1));
            animation: floatUp 5s linear infinite; 
            z-index: 10;
        }
        .note:active { transform: scale(0.9); }
        .popped { 
            display: none; /* 点击即消失 */
        }
        
        @keyframes floatUp {
            0% { transform: translateY(280px) rotate(0deg); }
            /* 一直保持不透明直到移出顶部 */
            100% { transform: translateY(-60px) rotate(360deg); }
        }
    </style>
    </head>
    <body>
    <div class="game-container">
        <h4>🎵 等待太枯燥？来捕捉灵感音符！</h4>
        <div id="score">收集灵感: 0</div>
        <div id="game-area"></div>
    </div>
    <script>
        let score = 0;
        const area = document.getElementById('game-area');
        const scoreDisplay = document.getElementById('score');
        const notes = ['♪', '♫', '♬', '♩', '♭', '♮', '♯'];
        // 高饱和度颜色
        const colors = ['#E74C3C', '#2ECC71', '#3498DB', '#9B59B6', '#F1C40F', '#E67E22', '#16A085'];

        function createNote() {
            let note = document.createElement('div');
            note.className = 'note';
            note.innerText = notes[Math.floor(Math.random() * notes.length)];
            note.style.color = colors[Math.floor(Math.random() * colors.length)];
            note.style.left = (5 + Math.random() * 85) + '%'; // 避免贴边
            note.style.animationDuration = (3.5 + Math.random() * 3) + 's'; 
            
            note.onclick = function() {
                score++;
                scoreDisplay.innerText = '收集灵感: ' + score;
                this.classList.add('popped');
                
                // 立即再生 (无限循环)
                setTimeout(createNote, 200);
                setTimeout(() => { note.remove(); }, 200);
            };
            
            // 动画结束后自动再生 (防止屏幕空了)
            note.addEventListener('animationend', () => {
                note.remove();
                createNote();
            });
            
            area.appendChild(note);
        }

        // 初始生成 8 个音符 (保持清爽)
        for(let i=0; i<8; i++) {
            setTimeout(createNote, i * 600);
        }
    </script>
    </body>
    </html>
    """
    components.html(game_html, height=280)

# --- 主界面逻辑 ---

# ⚠️ 关键修改：不再使用组件自带的 label，而是用 Markdown H3 标题
# 这样能保证字体绝对够大，和“生成结果”完全一致
st.markdown("### 📸 上传一张图片")
uploaded_file = st.file_uploader("label_hidden", label_visibility="collapsed", type=['png', 'jpg', 'jpeg', 'webp'])

st.markdown("### ✍️ 额外提示词 (可选)")
user_prompt = st.text_input("label_hidden", label_visibility="collapsed", placeholder="例如：生成古典风格...")

if st.button("🚀 开始生成音乐", type="primary"):
    if not DIFY_API_KEY or not uploaded_file:
        st.warning("⚠️ 请确保上传了图片")
        st.stop()

    # 1. 游戏区域
    render_game()

    # 2. 状态显示区域
    status_text = st.empty()
    timer_text = st.empty()
    progress_bar = st.progress(0)
    
    status_text.markdown("### 📤 正在上传图片...")
    file_id = upload_file(uploaded_file)
    
    if file_id:
        status_text.markdown("### 🤖 正在连接 Maestro 大脑...")
        
        # 准备请求
        url = f"{DIFY_BASE_URL}/chat-messages"
        headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
        
        image_payload = {"type": "image", "transfer_method": "local_file", "upload_file_id": file_id}
        inputs = {"pic": [image_payload]} 
        
        payload = {
            "inputs": inputs,
            "query": user_prompt if user_prompt else "生成音乐",
            "response_mode": "streaming", 
            "conversation_id": "",
            "user": "user-123",
            "files": [image_payload]
        }
        
        full_response = ""
        start_time = time.time()
        
        try:
            # 开启流式请求
            response = requests.post(url, headers=headers, json=payload, stream=True)
            response.raise_for_status()
            
            # --- 核心循环 ---
            for line in response.iter_lines():
                if line:
                    # 更新时间
                    elapsed = int(time.time() - start_time)
                    
                    # 1. 计时器显示
                    timer_text.info(f"⏱️ **预计运行时间约 3 分钟** | 已运行: **{elapsed} 秒**")
                    
                    # 2. 进度条逻辑 (160秒跑满)
                    current_progress = min(elapsed / 160.0, 0.99)
                    progress_bar.progress(current_progress)

                    # 解析数据
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        try:
                            json_str = decoded_line[6:]
                            data = json.loads(json_str)
                            event = data.get('event')
                            
                            if event in ['message', 'agent_message', 'text_chunk']:
                                chunk = data.get('answer', '')
                                full_response += chunk
                        except:
                            pass
            
            # --- 完成 ---
            progress_bar.progress(1.0)
            status_text.empty()
            timer_text.success(f"✅ 生成完成！总耗时: {int(time.time() - start_time)} 秒")
            
            # --- 结果展示 ---
            st.divider()
            st.markdown("### 🎧 生成结果")
            
            links = extract_audio_links(full_response)
            
            if links:
                for i, link in enumerate(links):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"**Track {i+1}**")
                    with col2:
                        st.audio(link, format="audio/mp3")
            else:
                if not full_response:
                    st.warning("⚠️ 流程结束但无文本返回。")
                else:
                    with st.expander("查看生成报告"):
                        st.markdown(full_response)
                    st.info("提示：未提取到音频链接，请查看上方报告。")

        except Exception as e:
            st.error(f"❌ 连接中断: {e}")