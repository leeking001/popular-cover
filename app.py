import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import zipfile

# --- 0. 核心配置 ---
INTERNAL_API_KEY = "fk10575412.5JSLUZXFqFJ_qzxvMVOjuP6i9asC6LOHab8b61ec"  # 🔴 必填：在此填入 Key
INTERNAL_MODEL = "google/gemini-3-pro-image-preview" # 或 black-forest-labs/FLUX.1-schnell
API_URL = "https://api.360.cn/v1/images/generations" # 或 https://api.siliconflow.cn/v1/images/generations

# --- 1. 页面配置与中文极客风 UI ---
st.set_page_config(page_title="爆款封面一键生成", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* 标题样式 - 霓虹发光中文 */
    .neon-title {
        font-family: "Microsoft YaHei", sans-serif;
        font-size: 3rem;
        font-weight: 900;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF9068);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
        text-shadow: 0 0 20px rgba(255, 75, 75, 0.3);
    }
    
    /* 副标题 */
    .sub-title {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 30px;
        letter-spacing: 1px;
    }

    /* 输入框美化 */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E2329 !important;
        color: #fff !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    
    /* 按钮美化 */
    .stButton>button {
        width: 100%;
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.8rem;
        border-radius: 8px;
        border: none;
        background: linear-gradient(90deg, #D4145A, #FBB03B);
        color: white;
        box-shadow: 0 4px 15px rgba(212, 20, 90, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(212, 20, 90, 0.6);
    }
    
    /* 隐藏默认元素 */
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 状态管理 (保证下载不消失) ---
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = None
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None

# --- 3. 核心逻辑 ---
def process_image_data(image_url):
    """切图逻辑：将 2x2 的大图切成 4 张小图"""
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
    """打包下载"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for img, name in zip(images, filenames):
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            zf.writestr(name, img_byte_arr.getvalue())
    return zip_buffer.getvalue()

def generate_covers(api_key, raw_input, ratio_opt, audience_type):
    # 1. 解析输入
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    # 智能分配：如果只有1行标题，生成4种变体；如果有4行，各生成1张
    if len(lines) == 1:
        # 解析主副标题
        parts = lines[0].split(' ', 1)
        m_title = parts[0]
        s_title = parts[1] if len(parts) > 1 else ""
        
        # 准备 4 组数据 (内容一样，风格微调)
        items = [{"m": m_title, "s": s_title, "style": "High Impact"}] * 4
    else:
        # 取前4行
        items = []
        for line in (lines + lines)[:4]:
            parts = line.split(' ', 1)
            items.append({"m": parts[0], "s": parts[1] if len(parts) > 1 else "", "style": "Viral"})

    # 2. 尺寸 Prompt
    ratio_prompt = "16:9 aspect ratio composition"
    if "3:4" in ratio_opt: ratio_prompt = "3:4 vertical composition"
    elif "1:1" in ratio_opt: ratio_prompt = "Square composition"

    # 3. 受众逻辑 (你的核心咒语逻辑)
    # 这里将中文选项映射回 Prompt 逻辑
    char_prompt = "an expressive content creator"
    if "男性" in audience_type: char_prompt = "an attractive female host (appealing to male audience)"
    elif "女性" in audience_type: char_prompt = "a handsome male host (appealing to female audience)"

    # 4. 🔥 核心咒语构建 (严格恢复你的要求) 🔥
    # 我们告诉 AI：这是一个 2x2 的网格，但每一格都要严格遵守你的“爆款逻辑”
    prompt = f"""
    Create a 2x2 GRID image containing 4 distinct YouTube/Social Media thumbnails.
    Total Resolution: 8k.
    
    CORE RULES FOR EACH THUMBNAIL:
    1. Subject: Photorealistic close-up of {char_prompt}. Expression matches the theme.
    2. Layout: Character interwoven with text (depth effect). High-end design.
    3. Style Reference: MrBeast, MediaStorm (影视飓风), XiaoLinShuo (小lin说).
    4. Text: Must include Main Title & Subtitle. Typography must be designed, not just plain text.
    5. {ratio_prompt}.
    
    [Quadrant 1 - Top Left]: Main Title: "{items[0]['m']}", Sub: "{items[0]['s']}".
    [Quadrant 2 - Top Right]: Main Title: "{items[1]['m']}", Sub: "{items[1]['s']}".
    [Quadrant 3 - Bottom Left]: Main Title: "{items[2]['m']}", Sub: "{items[2]['s']}".
    [Quadrant 4 - Bottom Right]: Main Title: "{items[3]['m']}", Sub: "{items[3]['s']}".
    
    IMPORTANT: Distinct borders between quadrants. Do not mix text between quadrants.
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
st.markdown('<div class="neon-title">爆款封面一键生成</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI 智能设计 · 自动排版 · 批量出图</div>', unsafe_allow_html=True)

# 主控区
c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("##### 📝 输入指令")
    user_input = st.text_area(
        "输入标题", 
        height=180, 
        placeholder="模式一：输入 1 行标题 -> 生成 4 种风格方案\n模式二：输入 4 行标题 -> 批量生成 4 张封面\n\n示例：\n月入过万 AI实战教程\n(主标题与副标题之间请用空格隔开)",
        label_visibility="collapsed"
    )

with c2:
    st.markdown("##### ⚙️ 参数设置")
    ratio = st.selectbox("封面比例", ["16:9 (横屏视频)", "3:4 (小红书/笔记)", "1:1 (通用方形)"])
    audience = st.selectbox("目标受众", ["大众/通用", "男性向 (科技/游戏)", "女性向 (美妆/情感)"])
    
    final_key = INTERNAL_API_KEY
    if not final_key:
        final_key = st.text_input("API Key", type="password")
    
    st.markdown("<br>", unsafe_allow_html=True) 
    generate_btn = st.button("🚀 立即生成 (一次出4张)")

# --- 5. 执行逻辑 ---

if generate_btn:
    if not user_input.strip():
        st.toast("⚠️ 请输入标题")
    elif not final_key:
        st.toast("⚠️ 请输入 API Key")
    else:
        with st.spinner("AI 正在执行爆款逻辑：分析受众 -> 匹配人物 -> 穿插排版..."):
            # 清空旧数据
            st.session_state.generated_images = None
            st.session_state.zip_data = None
            
            big_url, err = generate_covers(final_key, user_input, ratio, audience)
            
            if big_url:
                images = process_image_data(big_url)
                if len(images) == 4:
                    # 存入 Session State
                    st.session_state.generated_images = images
                    file_names = [f"cover_v{i+1}.png" for i in range(4)]
                    st.session_state.zip_data = create_zip(images, file_names)
                    st.rerun()
                else:
                    st.error("图像处理异常")
            else:
                st.error(f"生成失败: {err}")

# --- 6. 结果展示区 ---

if st.session_state.generated_images:
    st.markdown("---")
    st.markdown("##### ✅ 生成结果")
    
    with st.container():
        images = st.session_state.generated_images
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.image(images[0], use_column_width=True, caption="方案 01")
            st.image(images[2], use_column_width=True, caption="方案 03")
        with col_b:
            st.image(images[1], use_column_width=True, caption="方案 02")
            st.image(images[3], use_column_width=True, caption="方案 04")

    # 下载区
    st.markdown("---")
    d1, d2, d3 = st.columns([1, 2, 1])
    with d2:
        if st.session_state.zip_data:
            st.download_button(
                label="📦 一键打包下载全部 (.ZIP)",
                data=st.session_state.zip_data,
                file_name="covers_pack.zip",
                mime="application/zip",
                use_container_width=True
            )
