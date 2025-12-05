import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import zipfile
import time

# --- 0. 核心配置 (绝密区域) ---
# 🔴 必填：在此填入 360 的 Key
INTERNAL_API_KEY = "fk10575412.5JSLUZXFqFJ_qzxvMVOjuP6i9asC6LOHab8b61ec"  
# 🔴 核心模型 (后台锁定，用户不可见)
INTERNAL_MODEL = "google/gemini-3-pro-image-preview" 
# 🔴 接口地址
API_URL = "https://api.360.cn/v1/images/generations" 

# --- 1. 页面配置与中文极客风 UI ---
st.set_page_config(page_title="爆款封面一键生成", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* 标题样式 - 霓虹发光 */
    .neon-title {
        font-family: "Microsoft YaHei", sans-serif;
        font-size: 3rem;
        font-weight: 900;
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
        text-shadow: 0 0 20px rgba(0, 201, 255, 0.3);
    }
    
    .sub-title {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 30px;
        letter-spacing: 1px;
    }

    /* 输入框与按钮美化 */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E2329 !important;
        color: #fff !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    
    .stButton>button {
        width: 100%;
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.8rem;
        border-radius: 8px;
        border: none;
        background: linear-gradient(90deg, #0061ff, #60efff);
        color: white;
        box-shadow: 0 4px 15px rgba(0, 97, 255, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 97, 255, 0.6);
    }
    
    /* 隐藏所有干扰元素 */
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 状态管理 ---
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = None
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None

# --- 3. 核心逻辑 (黑盒处理) ---
def process_hidden_logic(image_url):
    """后台静默切图"""
    try:
        response = requests.get(image_url, timeout=60)
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        mid_w, mid_h = width // 2, height // 2
        
        # 无论画布是什么形状，都从中间切十字
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

def generate_covers(api_key, raw_input, ratio_opt, audience_type):
    # 1. 解析输入
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if len(lines) == 1:
        parts = lines[0].split(' ', 1)
        m_title = parts[0]
        s_title = parts[1] if len(parts) > 1 else ""
        items = [{"m": m_title, "s": s_title}] * 4
    else:
        items = []
        for line in (lines + lines)[:4]:
            parts = line.split(' ', 1)
            items.append({"m": parts[0], "s": parts[1] if len(parts) > 1 else ""})

    # 2. 动态画布尺寸 (解决比例不对的核心逻辑)
    # 360/Gemini 接口通常支持宽屏和竖屏分辨率
    if "16:9" in ratio_opt:
        canvas_size = "1792x1024" # 宽屏画布 -> 切出 16:9
        ratio_desc = "Wide 16:9 aspect ratio"
    elif "3:4" in ratio_opt:
        canvas_size = "1024x1792" # 竖屏画布 -> 切出 9:16/3:4
        ratio_desc = "Vertical 9:16 aspect ratio"
    else:
        canvas_size = "1024x1024" # 正方形
        ratio_desc = "Square 1:1 aspect ratio"

    # 3. 受众逻辑 (你的核心咒语：性别反转)
    char_prompt = "an expressive content creator"
    if "男性" in audience_type: 
        char_prompt = "an attractive female host (appealing to male audience)"
    elif "女性" in audience_type: 
        char_prompt = "a handsome male host (appealing to female audience)"

    # 4. 🔥 核心咒语 (完整保留，含安全补丁) 🔥
    prompt = f"""
    Generate a single image that is a 2x2 GRID containing 4 distinct thumbnails.
    
    CORE RULES (Strictly Followed):
    1. Subject: Photorealistic close-up of {char_prompt}. Expression matches the theme.
    2. Layout: Character interwoven with text (depth effect). High-end design.
    3. Style Reference: MrBeast, MediaStorm (影视飓风), XiaoLinShuo (小lin说).
    4. Text: Must include Main Title & Subtitle. Typography must be designed.
    5. Content Aspect Ratio: {ratio_desc}.
    
    [Quadrant 1]: Title: "{items[0]['m']}", Sub: "{items[0]['s']}".
    [Quadrant 2]: Title: "{items[1]['m']}", Sub: "{items[1]['s']}".
    [Quadrant 3]: Title: "{items[2]['m']}", Sub: "{items[2]['s']}".
    [Quadrant 4]: Title: "{items[3]['m']}", Sub: "{items[3]['s']}".
    
    CRITICAL VISUAL RULES: 
    - SEAMLESS composition within each quadrant.
    - NO visible borders, NO frames, NO white lines between images.
    - Images should touch each other directly (Full Bleed).
    
    ⛔ SAFETY: DO NOT generate maps, globes, flags or political symbols. Use abstract backgrounds.
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    # 初始 Payload
    payload = {
        "model": INTERNAL_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": canvas_size # 🔥 尝试申请对应比例的画布
    }

    # 智能重试逻辑 (含尺寸回退)
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            
            if res.status_code == 200:
                data = res.json()
                if 'data' in data and data['data']:
                    return data['data'][0]['url'], None
            
            # 处理 429 (拥堵)
            elif res.status_code == 429:
                time.sleep(2)
                continue
            
            # 处理 400 (通常是尺寸不支持)
            elif res.status_code == 400 and "size" in res.text.lower():
                # 如果宽屏/竖屏不支持，自动回退到正方形，保证能出图
                payload["size"] = "1024x1024"
                continue
                
            else:
                return None, f"API错误 ({res.status_code}): {res.text}"
                
        except Exception as e:
            return None, str(e)
            
    return None, "服务器繁忙，请稍后重试"

# --- 4. 界面布局 ---

st.markdown('<div class="neon-title">爆款封面一键生成</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI 智能设计 · 自动排版 · 批量出图</div>', unsafe_allow_html=True)

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
    generate_btn = st.button("🚀 立即生成 (智能引擎)")

# --- 5. 执行逻辑 ---

if generate_btn:
    if not user_input.strip():
        st.toast("⚠️ 请输入标题")
    elif not final_key:
        st.toast("⚠️ 请输入 API Key")
    else:
        with st.spinner("AI 正在设计 4 套爆款方案..."):
            st.session_state.generated_images = None
            st.session_state.zip_data = None
            
            big_url, err = generate_covers(final_key, user_input, ratio, audience)
            
            if big_url:
                images = process_hidden_logic(big_url)
                if len(images) == 4:
                    st.session_state.generated_images = images
                    file_names = [f"cover_v{i+1}.png" for i in range(4)]
                    st.session_state.zip_data = create_zip(images, file_names)
                    st.rerun()
                else:
                    st.error("图像处理异常")
            else:
                st.error(f"生成失败: {err}")
                if "12020" in str(err):
                    st.warning("⚠️ 提示：触发了敏感词风控，请修改标题重试。")

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
