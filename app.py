import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import zipfile

# --- 0. 核心配置 ---
INTERNAL_API_KEY = "fk10575412.5JSLUZXFqFJ_qzxvMVOjuP6i9asC6LOHab8b61ec"  # 🔴 必填：在此填入 Key
INTERNAL_MODEL = "google/gemini-3-pro-image-preview" # 或 black-forest-labs/FLUX.1-schnell
API_URL = "https://api.360.cn/v1/images/generations" # 或 https://api.siliconflow.cn/v1/images/generations

# --- 1. 页面配置与未来感 UI ---
st.set_page_config(page_title="AI Cover Lab", page_icon="⚡", layout="wide")

# 注入赛博朋克/未来感 CSS
st.markdown("""
<style>
    /* 全局深色背景微调 */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* 标题样式 - 霓虹发光 */
    .neon-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #00dc82, #36c4f0, #f72585);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 0 0 30px rgba(54, 196, 240, 0.3);
    }
    
    /* 副标题 */
    .sub-title {
        text-align: center;
        color: #888;
        font-size: 1.2rem;
        margin-bottom: 40px;
        letter-spacing: 2px;
    }

    /* 输入框美化 */
    .stTextArea textarea {
        background-color: #1E2329 !important;
        color: #fff !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
    }
    .stTextInput input {
        background-color: #1E2329 !important;
        color: #fff !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
    }
    
    /* 按钮美化 - 渐变流光 */
    .stButton>button {
        width: 100%;
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.8rem;
        border-radius: 12px;
        border: none;
        background: linear-gradient(90deg, #2196F3, #00BCD4);
        color: white;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(33, 150, 243, 0.6);
    }

    /* 结果卡片容器 */
    .result-container {
        background-color: #161B22;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #30363D;
        margin-top: 20px;
    }
    
    /* 隐藏默认元素 */
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 状态管理 (解决下载按钮失效的关键) ---
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = None
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None

# --- 3. 核心逻辑 ---
def process_image_data(image_url):
    try:
        response = requests.get(image_url, timeout=30)
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        mid_w, mid_h = width // 2, height // 2
        return [
            img.crop((0, 0, mid_w, mid_h)),
            img.crop((mid_w, 0, width, mid_h)),
            img.crop((0, mid_h, mid_w, height)),
            img.crop((mid_w, mid_h, width, height))
        ]
    except:
        return []

def create_zip(images, filenames):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for img, name in zip(images, filenames):
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            zf.writestr(name, img_byte_arr.getvalue())
    return zip_buffer.getvalue()

def generate_covers(api_key, raw_input, ratio_opt, audience):
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if len(lines) == 1:
        titles = lines * 4
        styles = ["High Saturation (Viral)", "Minimalist (Clean)", "Cinematic (Pro)", "Close-up (Emotion)"]
    else:
        titles = (lines + lines)[:4]
        styles = ["Viral Style"] * 4

    ratio_prompt = ""
    if "16:9" in ratio_opt: ratio_prompt = "Composition suited for 16:9 video thumbnail"
    elif "3:4" in ratio_opt: ratio_prompt = "Composition suited for 3:4 vertical post"
    
    prompt = f"""
    Create a 2x2 GRID image containing 4 distinct thumbnails. High Quality 8k.
    
    [Top-Left]: Title "{titles[0]}". Style: {styles[0]}. {ratio_prompt}.
    [Top-Right]: Title "{titles[1]}". Style: {styles[1]}. {ratio_prompt}.
    [Bottom-Left]: Title "{titles[2]}". Style: {styles[2]}. {ratio_prompt}.
    [Bottom-Right]: Title "{titles[3]}". Style: {styles[3]}. {ratio_prompt}.
    
    IMPORTANT: Distinct borders. No text bleeding. Each quadrant is a complete cover.
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": INTERNAL_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }

    try:
        res = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and data['data']:
                return data['data'][0]['url'], None
            return None, "生成成功但无数据"
        else:
            return None, f"API错误: {res.status_code}"
    except Exception as e:
        return None, str(e)

# --- 4. 界面布局 ---

# 标题区
st.markdown('<div class="neon-title">AI COVER LAB</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">NEXT GEN THUMBNAIL GENERATOR</div>', unsafe_allow_html=True)

# 主控区
c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("##### 🧠 输入指令 / INPUT")
    user_input = st.text_area(
        "输入标题", 
        height=180, 
        placeholder="模式一：输入 1 行标题 -> 生成 4 种风格方案\n模式二：输入 4 行标题 -> 批量生成 4 张封面\n\n示例：\n月入过万 AI实战教程",
        label_visibility="collapsed"
    )

with c2:
    st.markdown("##### ⚙️ 参数 / SETTINGS")
    ratio = st.selectbox("封面比例", ["16:9 (Video)", "3:4 (Social)", "1:1 (Square)"])
    audience = st.selectbox("目标受众", ["General (通用)", "Tech/Male (科技/男)", "Beauty/Female (美妆/女)"])
    
    final_key = INTERNAL_API_KEY
    if not final_key:
        final_key = st.text_input("API Key", type="password")
    
    st.markdown("<br>", unsafe_allow_html=True) # 占位
    generate_btn = st.button("⚡ ACTIVATE GENERATOR")

# --- 5. 执行逻辑 ---

if generate_btn:
    if not user_input.strip():
        st.toast("⚠️ 请输入标题 / Please input title")
    elif not final_key:
        st.toast("⚠️ 请输入 API Key")
    else:
        with st.spinner("SYSTEM PROCESSING..."):
            # 清空旧数据
            st.session_state.generated_images = None
            st.session_state.zip_data = None
            
            big_url, err = generate_covers(final_key, user_input, ratio, audience)
            
            if big_url:
                images = process_image_data(big_url)
                if len(images) == 4:
                    # 🔥 存入 Session State (关键步骤)
                    st.session_state.generated_images = images
                    file_names = [f"cover_v{i+1}.png" for i in range(4)]
                    st.session_state.zip_data = create_zip(images, file_names)
                    st.rerun() # 强制刷新以显示结果
                else:
                    st.error("Image Processing Error")
            else:
                st.error(f"Generation Failed: {err}")

# --- 6. 结果展示区 (从 Session State 读取) ---

if st.session_state.generated_images:
    st.markdown("---")
    st.markdown("##### ✅ 生成结果 / RESULTS")
    
    # 结果容器
    with st.container():
        images = st.session_state.generated_images
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.image(images[0], use_column_width=True, caption="OPTION 01")
            st.image(images[2], use_column_width=True, caption="OPTION 03")
        with col_b:
            st.image(images[1], use_column_width=True, caption="OPTION 02")
            st.image(images[3], use_column_width=True, caption="OPTION 04")

    # 下载区
    st.markdown("---")
    d1, d2, d3 = st.columns([1, 2, 1])
    with d2:
        if st.session_state.zip_data:
            st.download_button(
                label="📥 DOWNLOAD ALL ASSETS (.ZIP)",
                data=st.session_state.zip_data,
                file_name="ai_covers_pack.zip",
                mime="application/zip",
                use_container_width=True
            )
