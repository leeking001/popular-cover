import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import zipfile

# --- 0. 核心配置 (后台配置，用户不可见) ---
INTERNAL_API_KEY = "fk10575412.5JSLUZXFqFJ_qzxvMVOjuP6i9asC6LOHab8b61ec"  # 🔴 请在此填入 Key，实现真正的“一键”
INTERNAL_MODEL = "google/gemini-3-pro-image-preview" # 或 black-forest-labs/FLUX.1-schnell
API_URL = "https://api.360.cn/v1/images/generations" # 或 https://api.siliconflow.cn/v1/images/generations

# --- 1. 页面样式优化 ---
st.set_page_config(page_title="爆款封面一键生成", page_icon="🔥", layout="wide")
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stButton>button {
        width: 100%; 
        font-size: 1.3rem; 
        padding: 1rem; 
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9068 100%); 
        color: white; 
        border: none;
        border-radius: 10px;
        font-weight: bold;
    }
    .case-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .input-hint {
        font-size: 0.9rem;
        color: #666;
        margin-top: -10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心逻辑 (隐蔽的拼图技术) ---
def process_image_data(image_url):
    """后台处理图像数据，返回图片对象列表"""
    try:
        response = requests.get(image_url, timeout=30)
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        mid_w, mid_h = width // 2, height // 2
        
        # 隐蔽切割：左上, 右上, 左下, 右下
        return [
            img.crop((0, 0, mid_w, mid_h)),
            img.crop((mid_w, 0, width, mid_h)),
            img.crop((0, mid_h, mid_w, height)),
            img.crop((mid_w, mid_h, width, height))
        ]
    except:
        return []

def create_zip(images, filenames):
    """将多张图片打包成 ZIP"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, false) as zf:
        for img, name in zip(images, filenames):
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            zf.writestr(name, img_byte_arr.getvalue())
    return zip_buffer.getvalue()

def generate_covers(api_key, raw_input, ratio_opt, audience):
    # 1. 解析输入：支持单行或多行
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    # 智能策略：
    # 如果用户只输了1行 -> 生成4张不同风格的变体 (A/B测试)
    # 如果用户输了4行 -> 每行生成1张
    if len(lines) == 1:
        titles = lines * 4
        styles = ["High Saturation (MrBeast Style)", "Minimalist & Clean", "Cinematic & Professional", "Close-up Emotion"]
    else:
        # 取前4个，不足的补齐
        titles = (lines + lines)[:4]
        styles = ["Viral Style"] * 4

    # 2. 尺寸 Prompt 修正
    # 虽然物理切割是正方形，但我们通过 Prompt 让构图适应目标比例
    ratio_prompt = ""
    if "16:9" in ratio_opt: ratio_prompt = "Composition suited for 16:9 video thumbnail"
    elif "3:4" in ratio_opt: ratio_prompt = "Composition suited for 3:4 vertical post"
    
    # 3. 构建隐蔽的 Grid Prompt
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

# --- 3. 界面 UI ---

# === 顶部：案例展示 ===
with st.expander("🔥 查看爆款封面案例 (点击展开)", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="case-card">💰<br><b>搞钱类</b><br>大字报+真人浮夸</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="case-card">💄<br><b>美妆类</b><br>前后对比+高清特写</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="case-card">💻<br><b>干货类</b><br>极简背景+核心关键词</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="case-card">🥗<br><b>生活类</b><br>温馨滤镜+生活场景</div>', unsafe_allow_html=True)

st.title("🔥 爆款封面一键生成")
st.markdown("AI 智能设计 | 自动排版 | 批量出图")

# === 中部：输入区 ===
col_input, col_setting = st.columns([2, 1])

with col_input:
    user_input = st.text_area("输入标题", height=150, placeholder="示例：\n月入过万 AI实战教程\n(主标题与副标题之间请用空格隔开)\n\n提示：输入1行将生成4种风格变体；输入4行将批量生成4张。")
    st.markdown('<p class="input-hint">💡 技巧：主标题与副标题之间用 <b>空格</b> 隔开，AI 会自动识别排版。</p>', unsafe_allow_html=True)

with col_setting:
    st.markdown("#### ⚙️ 封面设置")
    ratio = st.selectbox("封面比例", ["16:9 (横屏视频)", "3:4 (小红书/笔记)", "1:1 (通用方形)"])
    audience = st.selectbox("目标受众", ["大众/通用", "男性向 (科技/游戏)", "女性向 (美妆/情感)"])
    
    # Key 处理
    final_key = INTERNAL_API_KEY
    if not final_key:
        final_key = st.text_input("API Key", type="password")

# === 底部：操作区 ===
if st.button("🚀 立即生成 (一次出4张)"):
    if not user_input.strip():
        st.toast("⚠️ 请输入至少一个标题")
    elif not final_key:
        st.toast("⚠️ 请输入 API Key")
    else:
        with st.spinner("AI 正在设计 4 套爆款方案，请稍候..."):
            # 1. 调用生成
            big_url, err = generate_covers(final_key, user_input, ratio, audience)
            
            if big_url:
                # 2. 后台处理 (切图)
                images = process_image_data(big_url)
                
                if len(images) == 4:
                    st.success("✅ 生成完成！请选择方案：")
                    
                    # 3. 展示结果 (2x2 布局)
                    r1_c1, r1_c2 = st.columns(2)
                    r2_c1, r2_c2 = st.columns(2)
                    
                    # 准备文件名
                    file_names = [f"cover_option_{i+1}.png" for i in range(4)]
                    
                    # 展示图片
                    preview_cols = [r1_c1, r1_c2, r2_c1, r2_c2]
                    for idx, img in enumerate(images):
                        with preview_cols[idx]:
                            st.image(img, use_column_width=True)
                            st.caption(f"方案 {idx+1}")
                    
                    # 4. 下载区域
                    st.markdown("---")
                    dl_col1, dl_col2 = st.columns([1, 1])
                    
                    # 生成 ZIP
                    zip_data = create_zip(images, file_names)
                    
                    with dl_col1:
                        st.download_button(
                            label="📦 一键下载全部 (ZIP)",
                            data=zip_data,
                            file_name="all_covers.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    with dl_col2:
                        st.info("💡 提示：也可以右键点击上方图片单独保存")
                        
                else:
                    st.error("图像处理异常，请重试")
            else:
                st.error(f"生成失败: {err}")
