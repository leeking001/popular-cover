import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import math

# --- 0. 核心配置 ---
INTERNAL_API_KEY = "fk10575412.5JSLUZXFqFJ_qzxvMVOjuP6i9asC6LOHab8b61ec" 
INTERNAL_MODEL = "google/gemini-3-pro-image-preview"
API_URL = "https://api.360.cn/v1/images/generations"

# --- 1. 页面样式 ---
st.set_page_config(page_title="爆款封面一键生成", page_icon="⚡", layout="wide")
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stButton>button {width: 100%; font-size: 1.2rem; padding: 0.8rem; background-color: #D50000; color: white;}
    .success-text {color: green; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- 2. 切图逻辑 (田字格切割) ---
def slice_image_quadrant(image_url):
    """
    下载大图，切成 2x2 (田字格) 4张图
    返回顺序：左上, 右上, 左下, 右下
    """
    try:
        response = requests.get(image_url, timeout=30)
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        
        mid_w = width // 2
        mid_h = height // 2
        
        # 切割 4 张
        # (left, top, right, bottom)
        img_tl = img.crop((0, 0, mid_w, mid_h))       # 左上
        img_tr = img.crop((mid_w, 0, width, mid_h))    # 右上
        img_bl = img.crop((0, mid_h, mid_w, height))   # 左下
        img_br = img.crop((mid_w, mid_h, width, height)) # 右下
        
        return [img_tl, img_tr, img_bl, img_br]
    except:
        return []

# --- 3. 生成逻辑 (1调4) ---
def generate_batch_quad(api_key, titles_chunk):
    """
    接收 1-4 个标题，生成一张拼图
    """
    # 补齐 4 个位置，如果不足 4 个，用 "Abstract background" 填充，避免 AI 乱画
    padded_titles = titles_chunk + ["Abstract geometric background"] * (4 - len(titles_chunk))
    
    t1, t2, t3, t4 = padded_titles[0], padded_titles[1], padded_titles[2], padded_titles[3]
    
    # 核心 Prompt：强制 2x2 网格布局
    prompt = f"""
    Create a 2x2 GRID split-screen image containing 4 distinct thumbnails.
    Total Resolution: Maximum Possible (High Detail).
    
    [Quadrant 1 - Top Left]: YouTube thumbnail for "{t1}". High saturation, close-up.
    [Quadrant 2 - Top Right]: YouTube thumbnail for "{t2}". Cinematic lighting.
    [Quadrant 3 - Bottom Left]: YouTube thumbnail for "{t3}". Minimalist design.
    [Quadrant 4 - Bottom Right]: YouTube thumbnail for "{t4}". Vivid colors.
    
    IMPORTANT: 
    - Strict distinct borders between quadrants. 
    - Do not bleed elements across borders.
    - Each quadrant must be a complete image.
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    # 🔥 尝试请求 2048x2048 以获得更高清的 4K 效果
    # 如果 API 不支持，它通常会自动降级或报错，如果报错改成 1024x1024
    payload = {
        "model": INTERNAL_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": "2048x2048" # 这里先保守填 1024，如果你确定支持 2048 可修改
    }

    try:
        res = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and data['data']:
                return data['data'][0]['url']
    except:
        pass
    return None

# --- 4. 界面 UI ---
st.title("⚡ 爆款封面一键生成 (批量工厂)")
st.caption("极速流水线：系统将在后台自动合并任务，最大化产出效率。")

# 批量输入
raw_text = st.text_area("请输入标题列表 (一行一个，建议一次输 4 的倍数)", height=200, 
                       placeholder="Python入门\n减肥食谱\n杭州旅游\nAI赚钱\n...")

final_key = INTERNAL_API_KEY
if not final_key:
    final_key = st.text_input("API Key", type="password")

if st.button("🚀 启动超级流水线", type="primary"):
    if not raw_text.strip():
        st.warning("请先输入标题")
    elif not final_key:
        st.warning("请输入 API Key")
    else:
        titles = [t.strip() for t in raw_text.split('\n') if t.strip()]
        total = len(titles)
        
        # 按 4 个一组进行切分
        # [A,B,C,D, E,F] -> [[A,B,C,D], [E,F]]
        chunks = [titles[i:i + 4] for i in range(0, len(titles), 4)]
        
        st.info(f"收到 {total} 个任务，打包为 {len(chunks)} 次生成请求...")
        
        progress_bar = st.progress(0)
        result_gallery = []
        
        for i, chunk in enumerate(chunks):
            with st.spinner(f"正在处理第 {i+1} 批次 (包含 {len(chunk)} 个封面)..."):
                # 调用接口
                big_url = generate_batch_quad(final_key, chunk)
                
                if big_url:
                    # 切割
                    imgs = slice_image_quadrant(big_url)
                    # 只取我们需要的前 n 张 (去掉补位的)
                    valid_imgs = imgs[:len(chunk)]
                    
                    for idx, img in enumerate(valid_imgs):
                        result_gallery.append((chunk[idx], img))
            
            progress_bar.progress((i + 1) / len(chunks))
            
        st.success(f"✅ 生产完成！共产出 {len(result_gallery)} 张封面")
        
        # 展示结果 (4列布局)
        cols = st.columns(4)
        for idx, (title, img) in enumerate(result_gallery):
            with cols[idx % 4]:
                st.image(img, use_column_width=True)
                st.caption(f"📄 {title}")
                
                # 下载
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.download_button(
                    label="📥",
                    data=buf.getvalue(),
                    file_name=f"cover_{idx}.png",
                    mime="image/png",
                    key=f"dl_{idx}"
                )
