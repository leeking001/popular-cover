import streamlit as st
import requests
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# --- 页面配置 ---
st.set_page_config(page_title="Gemini 3 Pro 封面生成器", page_icon="🚀", layout="wide")

# --- 1. 字体加载 (保持不变，为了排版好看) ---
FONT_URL = "https://github.com/StellarCN/scp_zh/raw/master/fonts/SimHei.ttf"
FONT_PATH = "SimHei.ttf"

def load_font(size):
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL)
            with open(FONT_PATH, "wb") as f: f.write(r.content)
        except: return None
    return ImageFont.truetype(FONT_PATH, size)

# --- 2. 图片加字逻辑 (Python 矢量合成) ---
def add_text_overlay(image_url, main_text, sub_text, layout="居中"):
    try:
        # 下载图片
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
    except Exception as e:
        st.error(f"图片下载失败: {e}")
        return None
        
    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    # 动态字号
    main_size = int(W / 8)
    main_font = load_font(main_size)
    sub_font = load_font(int(main_size * 0.5))
    
    if not main_font: return img # 字体失败返回原图

    # 样式配置
    stroke_width = int(main_size / 15)
    
    # 计算位置
    bbox = draw.textbbox((0, 0), main_text, font=main_font)
    w_m, h_m = bbox[2]-bbox[0], bbox[3]-bbox[1]
    bbox_s = draw.textbbox((0, 0), sub_text, font=sub_font)
    w_s, h_s = bbox_s[2]-bbox_s[0], bbox_s[3]-bbox_s[1]

    if layout == "居中":
        x_m, y_m = (W-w_m)/2, (H-h_m)/2 - h_s
        x_s, y_s = (W-w_s)/2, y_m + h_m + 20
    elif layout == "底部":
        x_m, y_m = (W-w_m)/2, H - h_m - h_s - 100
        x_s, y_s = (W-w_s)/2, y_m + h_m + 20
    elif layout == "左侧":
        x_m, y_m = 50, (H-h_m)/2
        x_s, y_s = 50, y_m + h_m + 20

    # 绘制文字
    draw.text((x_m, y_m), main_text, font=main_font, fill="white", stroke_width=stroke_width, stroke_fill="black")
    if sub_text:
        draw.text((x_s, y_s), sub_text, font=sub_font, fill="#FFD700", stroke_width=3, stroke_fill="black")
    
    return img

# --- 3. 核心：调用你定义的 360 接口 ---
def generate_image_360(api_key, prompt, size_str):
    # 🔥 你指定的接口地址
    url = "https://api.360.cn/v1/images/generations"
    
    # 🔥 你指定的模型名称
    model_name = "google/gemini-3-pro-image-preview"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" # 假设是 Bearer Token 认证
    }
    
    # 构造请求体 (遵循 OpenAI 标准格式)
    payload = {
        "model": model_name,
        "prompt": prompt,
        "n": 1,
        "size": size_str
    }
    
    try:
        # 使用 requests 直接发送 POST 请求
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        # 解析响应
        if response.status_code == 200:
            data = response.json()
            # 通常图片链接在 data['data'][0]['url']
            return data['data'][0]['url']
        else:
            st.error(f"接口报错 ({response.status_code}): {response.text}")
            return None
            
    except Exception as e:
        st.error(f"请求发送失败: {e}")
        return None

# --- 4. 界面 UI ---
with st.sidebar:
    st.title("🚀 设置")
    # 这里需要填入 360 API 的 Key
    api_key = st.text_input("360 API Key", type="password", help="请输入 api.360.cn 的密钥")
    
    st.markdown("---")
    st.info(f"当前锁定模型：\n`google/gemini-3-pro-image-preview`")
    st.info(f"当前接口地址：\n`api.360.cn/v1/images/generations`")

st.title("🚀 Gemini 3 Pro 封面生成器")
st.caption("基于 360 AI 接口定制开发")

col1, col2 = st.columns([1, 1])
with col1:
    main_title = st.text_input("主标题", "月入过万")
    sub_title = st.text_input("副标题", "Gemini实战")
    layout = st.selectbox("文字位置", ["居中", "底部", "左侧"])
with col2:
    desc = st.text_input("画面描述", "一个极客风格的男生，背景是发光的代码，赛博朋克")
    ratio = st.selectbox("比例", ["16:9", "3:4", "1:1"])

if st.button("🚀 立即生成", type="primary"):
    if not api_key:
        st.warning("请先在侧边栏填写 API Key")
    else:
        # 尺寸映射 (根据模型支持情况，通常是这些标准尺寸)
        size_map = {
            "16:9": "1024x576",
            "3:4": "768x1024",
            "1:1": "1024x1024"
        }
        
        # 构建 Prompt
        final_prompt = f"""
        {desc}.
        Style: High quality, 8k, photorealistic, cinematic lighting.
        Composition: Clean background, negative space for text overlay.
        (No text, no watermark).
        """
        
        with st.spinner(f"正在请求 Gemini 3 Pro Image 模型..."):
            img_url = generate_image_360(api_key, final_prompt, size_map[ratio])
            
        if img_url:
            with st.spinner("正在进行排版合成..."):
                final_img = add_text_overlay(img_url, main_title, sub_title, layout)
                
                if final_img:
                    st.success("✅ 生成成功！")
                    st.image(final_img, use_column_width=True)
                    
                    # 下载
                    buf = BytesIO()
                    final_img.save(buf, format="PNG")
                    st.download_button("📥 下载封面", buf.getvalue(), "gemini3_cover.png", "image/png")
