import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

# --- 页面配置 ---
st.set_page_config(page_title="全自动封面生成器", page_icon="🎨", layout="wide")

# --- 1. 字体管理 (关键：解决云端无中文字体问题) ---
FONT_URL = "https://github.com/StellarCN/scp_zh/raw/master/fonts/SimHei.ttf" # 使用黑体作为备选，稳定
FONT_PATH = "SimHei.ttf"

def load_font(size):
    """加载字体，如果本地没有则自动下载"""
    if not os.path.exists(FONT_PATH):
        with st.spinner("正在下载中文字体文件 (首次运行需要)..."):
            try:
                r = requests.get(FONT_URL)
                with open(FONT_PATH, "wb") as f:
                    f.write(r.content)
            except:
                st.error("字体下载失败，文字可能无法显示。")
                return None
    return ImageFont.truetype(FONT_PATH, size)

# --- 2. 图片处理逻辑 (加字) ---
def add_text_overlay(image_url, main_text, sub_text, layout="居中"):
    # 下载图片到内存
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # --- 主标题设置 ---
    # 动态计算字号：大约占图片宽度的 1/8 到 1/5
    main_font_size = int(W / 8) 
    main_font = load_font(main_font_size)
    
    # --- 副标题设置 ---
    sub_font_size = int(main_font_size * 0.5)
    sub_font = load_font(sub_font_size)

    if not main_font: return img # 字体加载失败直接返回原图

    # --- 颜色配置 (爆款风格：黄字+黑边，或白字+黑边) ---
    text_color = "#FFFFFF" # 白色
    stroke_color = "#000000" # 黑色描边
    stroke_width = int(main_font_size / 15) # 描边粗细

    # --- 计算文字位置 ---
    # 获取主标题宽高
    bbox = draw.textbbox((0, 0), main_text, font=main_font)
    w_text, h_text = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # 获取副标题宽高
    bbox_sub = draw.textbbox((0, 0), sub_text, font=sub_font)
    w_sub, h_sub = bbox_sub[2] - bbox_sub[0], bbox_sub[3] - bbox_sub[1]

    # 布局逻辑
    if layout == "居中":
        x_main = (W - w_text) / 2
        y_main = (H - h_text) / 2 - h_sub # 稍微偏上
        x_sub = (W - w_sub) / 2
        y_sub = y_main + h_text + 20
    elif layout == "底部":
        x_main = (W - w_text) / 2
        y_main = H - h_text - h_sub - 100
        x_sub = (W - w_sub) / 2
        y_sub = y_main + h_text + 20
    elif layout == "左侧":
        x_main = 50
        y_main = (H - h_text) / 2
        x_sub = 50
        y_sub = y_main + h_text + 20

    # --- 绘制主标题 (带描边) ---
    # 描边原理：在上下左右偏移位置画黑字，最后在中间画白字
    draw.text((x_main, y_main), main_text, font=main_font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)
    
    # --- 绘制副标题 (带背景框) ---
    # 画一个半透明背景框给副标题
    padding = 10
    if sub_text:
        # 绘制副标题文字 (带细描边)
        draw.text((x_sub, y_sub), sub_text, font=sub_font, fill="#FFD700", stroke_width=3, stroke_fill="black") # 金色字

    return img

# --- 3. AI 生成逻辑 ---
def generate_image_flux(api_key, prompt, size_str):
    client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
    try:
        response = client.images.generate(
            model="black-forest-labs/FLUX.1-dev", # 使用高画质版
            prompt=prompt,
            size=size_str,
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"AI生成出错: {e}")
        return None

# --- 4. 界面 UI ---
with st.sidebar:
    st.title("🎨 设置")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    st.info("提示：程序会自动下载中文字体，合成到图片上。")

st.title("🎨 全自动封面生成器 (AI绘图 + 自动排版)")

col1, col2 = st.columns([1, 1])
with col1:
    main_title = st.text_input("主标题 (大字)", "月入过万")
    sub_title = st.text_input("副标题 (小字)", "AI实战教程")
    layout_mode = st.selectbox("文字位置", ["居中", "底部", "左侧"])
    
with col2:
    audience = st.selectbox("画面主体", ["美女主持", "帅哥主持", "极客/程序员", "无人物/纯背景"])
    ratio_opt = st.selectbox("比例", ["16:9 (横屏)", "3:4 (竖屏)"])

# --- 执行逻辑 ---
if st.button("🚀 生成封面", type="primary"):
    if not api_key:
        st.warning("请填写 API Key")
    else:
        # 1. 构建 Prompt (强制要求留白，不要AI写字)
        size_map = {"16:9 (横屏)": "1024x576", "3:4 (竖屏)": "768x1024"}
        
        if audience == "美女主持":
            subject = "beautiful asian female host, professional, smiling"
        elif audience == "帅哥主持":
            subject = "handsome male host, confident"
        elif audience == "极客/程序员":
            subject = "tech geek with glasses, coding atmosphere"
        else:
            subject = "clean 3d abstract background, high tech"

        # 关键 Prompt：Negative space (留白)
        prompt = f"""
        YouTube thumbnail. {subject}.
        Composition: Subject on the side, large negative space in the {layout_mode.replace('左侧','right').replace('居中','center').replace('底部','top')} for text overlay.
        Style: High quality, 8k, studio lighting, depth of field.
        (No text, no watermark, clean background).
        """
        
        with st.spinner("1. AI 正在绘制底图 (FLUX.1-dev)..."):
            img_url = generate_image_flux(api_key, prompt, size_map[ratio_opt])
        
        if img_url:
            with st.spinner("2. Python 正在进行排版合成..."):
                # 调用合成函数
                final_img = add_text_overlay(img_url, main_title, sub_title, layout_mode)
                
                # 展示结果
                st.success("✅ 生成完成！")
                st.image(final_img, caption="最终效果图", use_column_width=True)
                
                # 提供下载
                buf = BytesIO()
                final_img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                st.download_button(
                    label="📥 下载最终封面",
                    data=byte_im,
                    file_name="cover.png",
                    mime="image/png"
                )
