import streamlit as st
import requests
import json
import re

# --- 页面设置 ---
st.set_page_config(page_title="Suno 音乐生成器", page_icon="🎵", layout="centered")
st.title("🎵 AI 音乐生成器 (流式抗超时版)")
st.caption("模式: Advanced Chat | 机制: Streaming (解决 504 超时)")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("API 设置")
    DIFY_API_KEY = st.text_input("Dify API Key", type="password", help="请使用 master-5.0 应用的 API Key")
    base_url_input = st.text_input("Dify Base URL", value="https://api.dify.ai/v1")
    DIFY_BASE_URL = base_url_input.rstrip("/")
    st.info("💡 此版本使用流式传输，可以长时间运行而不会断连。")

# --- 核心函数 ---

def upload_file(file_obj, user_id="user-123"):
    """步骤 1: 上传文件"""
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
    """提取 MP3 链接"""
    if not isinstance(text, str): return []
    return re.findall(r'(https?://[^\s)]+\.mp3)', text)

# --- 主界面 ---

uploaded_file = st.file_uploader("📸 上传图片", type=['png', 'jpg', 'jpeg', 'webp'])
user_prompt = st.text_input("✍️ 提示词", placeholder="例如：古典风格...")

if st.button("🚀 开始生成", type="primary"):
    if not DIFY_API_KEY or not uploaded_file:
        st.warning("⚠️ 请完善 API Key 和图片")
        st.stop()

    # 进度显示容器
    status_container = st.status("🤖 正在连接 AI...", expanded=True)
    
    with status_container:
        st.write("📤 上传图片中...")
        file_id = upload_file(uploaded_file)
        
        if file_id:
            st.write("✅ 图片上传成功，开始执行工作流...")
            st.write("⏳ 正在生成音乐（由于是流式传输，请耐心观察下方输出变化）...")
            
            # --- 核心修改：流式请求逻辑 ---
            url = f"{DIFY_BASE_URL}/chat-messages"
            headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
            
            image_payload = {"type": "image", "transfer_method": "local_file", "upload_file_id": file_id}
            inputs = {"pic": [image_payload]} # 必须传 pic 变量
            
            payload = {
                "inputs": inputs,
                "query": user_prompt if user_prompt else "生成音乐",
                "response_mode": "streaming", # ⚠️ 关键：改为流式模式
                "conversation_id": "",
                "user": "user-123",
                "files": [image_payload]
            }
            
            # 创建一个空占位符，用于实时打字机效果
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # 开启流式请求 (stream=True)
                response = requests.post(url, headers=headers, json=payload, stream=True)
                response.raise_for_status()
                
                # 逐行读取数据
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            try:
                                json_str = decoded_line[6:] # 去掉 'data: ' 前缀
                                data = json.loads(json_str)
                                event = data.get('event')
                                
                                # 处理不同类型的事件
                                if event == 'message' or event == 'agent_message' or event == 'text_chunk':
                                    # 累加回复内容
                                    chunk = data.get('answer', '')
                                    full_response += chunk
                                    # 实时刷新界面
                                    message_placeholder.markdown(full_response + "▌")
                                
                                elif event == 'node_started':
                                    # 可选：显示正在运行的节点（让你知道它没死机）
                                    node_title = data.get('data', {}).get('title', '未知节点')
                                    st.write(f"🔄 正在执行: {node_title}...")
                                    
                                elif event == 'error':
                                    st.error(f"流式错误: {data}")
                                    
                            except Exception:
                                pass # 忽略解析错误的行
                
                # 循环结束，任务完成
                message_placeholder.markdown(full_response) # 去掉光标
                status_container.update(label="✅ 生成完成！", state="complete", expanded=False)
                
                # 提取并播放
                st.divider()
                st.subheader("🎧 生成结果")
                links = extract_audio_links(full_response)
                
                if links:
                    for i, link in enumerate(links):
                        st.markdown(f"**Track {i+1}**")
                        st.audio(link, format="audio/mp3")
                else:
                    if not full_response:
                        st.warning("⚠️ 流程跑完了，但没有返回任何文字。请检查工作流的输出节点。")
                    else:
                        st.info("提示：未提取到音频链接，请阅读上方生成的文本报告。")

            except Exception as e:
                status_container.update(label="❌ 连接中断", state="error")
                st.error(f"请求发生错误: {e}")