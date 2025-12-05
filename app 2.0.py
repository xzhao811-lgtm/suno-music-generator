import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import re
import time
from datetime import datetime
from PIL import Image # 引入 PIL 用于处理图片保存

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="Maestro：你的AI写歌助手", 
    page_icon="🎹", 
    layout="centered",
    initial_sidebar_state="expanded" # 默认展开侧边栏以便看到历史
)

# --- 初始化 Session State (用于存储历史记录) ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- CSS 样式优化 ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; }
        div.stButton > button {
            font-size: 1.2rem !important;
            font-weight: bold !important;
            padding: 0.6rem 2rem !important;
            width: 100%;
            border-radius: 10px;
        }
        /* 侧边栏样式微调 */
        [data-testid="stSidebar"] {
            background-color: #f9f9f9;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🎹 Maestro：你的AI写歌助手")
st.caption("COPY RIGHT@ZHAO Xinyi,HE Jingjing,ZHAO Zhenran")

# --- 2. 侧边栏 (API 设置 + 历史记录) ---
with st.sidebar:
    st.header("⚙️ API 设置")
    default_key = "app-QbS2Fs0LQ0klcni6nCfjchOS"
    DIFY_API_KEY = st.text_input("Dify API Key", value=default_key, type="password", disabled=True)
    base_url_input = st.text_input("Dify Base URL", value="https://api.dify.ai/v1")
    DIFY_BASE_URL = base_url_input.rstrip("/")
    
    st.divider() # 分割线
    
    # 【新增功能 3】：侧边栏历史记录
    st.header("📜 生成历史")
    if not st.session_state.history:
        st.caption("暂无历史记录，快去生成一首吧！")
    else:
        # 倒序遍历，最新的显示在最上面
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"🎵 {item['time']} - {item['prompt'][:10]}..."):
                st.image(item['image'], caption="参考图片", use_container_width=True)
                st.caption(f"提示词: {item['prompt']}")
                if item['links']:
                    for link in item['links']:
                        st.audio(link, format="audio/mp3")
                else:
                    st.warning("无音频链接")

# --- 3. 核心函数 ---

def upload_file(file_obj, user_id="user-123"):
    """上传文件"""
    # 这一步很关键：因为 file_obj 可能被读取过，上传前要重置指针
    file_obj.seek(0) 
    
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
    """提取链接并去重"""
    if not isinstance(text, str): return []
    links = re.findall(r'(https?://[^\s)]+\.mp3)', text)
    unique_links = list(dict.fromkeys(links))
    return unique_links[:2]

# --- 4. 小游戏组件 (代码保持不变) ---
def render_game():
    game_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Segoe UI', sans-serif; }
        .game-container {
            width: 100%; height: 270px; background-color: #F9FAFB; 
            border: 2px solid #E5E7EB; border-radius: 12px; position: relative; 
            overflow: hidden; text-align: center; box-sizing: border-box;
        }
        h4 { margin-top: 20px; color: #1F2937; font-size: 16px; font-weight: 500; letter-spacing: 0.5px; }
        #score { font-size: 28px; font-weight: 800; color: #000000; margin-bottom: 5px; }
        .note {
            position: absolute; font-size: 38px; cursor: pointer; user-select: none;
            opacity: 1 !important; filter: drop-shadow(0px 2px 2px rgba(0,0,0,0.1));
            animation: floatUp 5s linear infinite; z-index: 10;
        }
        .note:active { transform: scale(0.9); }
        .popped { display: none; }
        @keyframes floatUp {
            0% { transform: translateY(280px) rotate(0deg); }
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
        const colors = ['#E74C3C', '#2ECC71', '#3498DB', '#9B59B6', '#F1C40F', '#E67E22', '#16A085'];
        function createNote() {
            let note = document.createElement('div');
            note.className = 'note';
            note.innerText = notes[Math.floor(Math.random() * notes.length)];
            note.style.color = colors[Math.floor(Math.random() * colors.length)];
            note.style.left = (5 + Math.random() * 85) + '%'; 
            note.style.animationDuration = (3.5 + Math.random() * 3) + 's'; 
            note.onclick = function() {
                score++; scoreDisplay.innerText = '收集灵感: ' + score;
                this.classList.add('popped');
                setTimeout(createNote, 200); setTimeout(() => { note.remove(); }, 200);
            };
            note.addEventListener('animationend', () => { note.remove(); createNote(); });
            area.appendChild(note);
        }
        for(let i=0; i<8; i++) { setTimeout(createNote, i * 600); }
    </script>
    </body>
    </html>
    """
    components.html(game_html, height=280)

# --- 主界面逻辑 ---

st.markdown("### 📸 上传一张图片")
uploaded_file = st.file_uploader("label_hidden", label_visibility="collapsed", type=['png', 'jpg', 'jpeg', 'webp'])

# 【新增功能 1】：图片上传后立即预览
if uploaded_file is not None:
    st.image(uploaded_file, caption="🖼️ 图片预览", use_container_width=True)

st.markdown("### ✍️ 额外提示词 (可选)")
# 【新增功能 2】：添加灰色提示小字
st.caption("提示：提示词中请不要包含人名")

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
        
        # 准备 API 请求
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
            response = requests.post(url, headers=headers, json=payload, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    elapsed = int(time.time() - start_time)
                    timer_text.info(f"⏱️ **预计运行时间约 3 分钟** | 已运行: **{elapsed} 秒**")
                    current_progress = min(elapsed / 160.0, 0.99)
                    progress_bar.progress(current_progress)

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
            
            # --- 结果解析与展示 ---
            st.divider()
            st.markdown("### 🎧 生成结果")
            
            links = extract_audio_links(full_response)
            
            # 显示音频
            if links:
                for i, link in enumerate(links):
                    col1, col2 = st.columns([1, 4])
                    with col1: st.markdown(f"**Track {i+1}**")
                    with col2: st.audio(link, format="audio/mp3")
            else:
                if not full_response:
                    st.warning("⚠️ 流程结束但无文本返回。")
                else:
                    with st.expander("查看生成报告"):
                        st.markdown(full_response)
                    st.info("提示：未提取到音频链接，请查看上方报告。")

            # 【新增功能 3 保存逻辑】：成功后保存到 Session State 历史记录
            # 注意：必须将图片转换为 PIL Image 对象保存，因为 uploaded_file 指针在下一轮可能会失效
            try:
                uploaded_file.seek(0) # 重置指针以读取图片
                img_data = Image.open(uploaded_file)
                
                st.session_state.history.append({
                    "time": datetime.now().strftime("%H:%M"),
                    "prompt": user_prompt if user_prompt else "默认提示词",
                    "image": img_data,
                    "links": links
                })
                # 强制刷新一下侧边栏显示新历史（可选，Steamlit通常会自动更新UI）
            except Exception as e:
                print(f"历史记录保存失败: {e}")

        except Exception as e:
            st.error(f"❌ 连接中断: {e}")