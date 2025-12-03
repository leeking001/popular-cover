import streamlit as st
from openai import OpenAI

# --- 页面配置 ---
st.set_page_config(page_title="FLUX 爆款封面生成器", page_icon="⚡", layout="wide")

# --- 侧边栏 ---
with st.sidebar:
    st.title("⚡ 设置 (硅基流动版)")
    # 这里让用户输入硅基流动的 Key
    api_key = st.text_input("SiliconFlow API Key", type="password", help="去 cloud.siliconflow.cn 注册获取")
    st.markdown("---")
    st.info("💡 **模型说明**：\n本工具使用 FLUX.1-schnell 模型。\n它的写实感和光影效果目前是业界顶尖的。")

# --- 主界面 ---
st.title("⚡ 自媒体爆款封面生成器 (FLUX版)")
st.caption("使用 FLUX.1 模型，生成超写实、电影质感的封面图")

col1, col2 = st.columns([1, 1])
with col1:
    main_title = st.text_input("主标题", "月入过万")
    sub_title = st.text_input("副标题", "AI副业实战")
    audience = st.selectbox("目标受众", ["男性受众", "女性受众", "通用"])
with col2:
    ratio_opt = st.selectbox("封面比例", ["16:9 (横屏)", "3:4 (竖屏)", "9:16 (全屏)"])
    # FLUX 对文字支持较好，但中文依然建议后期加
    text_mode = st.radio("模式", ["生成无字底图 (推荐)", "尝试生成英文文字"])

# --- 核心逻辑 ---
def generate_image_flux(prompt, size_str):
    # 关键修改点 1: 配置 Base URL 为硅基流动地址
    client = OpenAI(
        api_key=sk-nytxinkfozqypfcmrdsoyjujxkvxgkdediprwjojvllofazq,
        base_url="https://api.siliconflow.cn/v1" 
    )
    
    try:
        response = client.images.generate(
            # 关键修改点 2: 使用 FLUX 模型
            model="black-forest-labs/FLUX.1-schnell", 
            prompt=prompt,
            size=size_str,
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"生成失败: {e}")
        return None

# --- 咒语构建 (针对 FLUX 优化) ---
def build_prompt(m_title, s_title, aud, ratio, mode):
    # 逻辑判断
    if aud == "男性受众":
        subject = "a gorgeous, professional female host, looking at camera, friendly smile"
    elif aud == "女性受众":
        subject = "a handsome, charismatic male host, looking at camera, confident"
    else:
        subject = "an expressive asian content creator"

    # 尺寸描述 (FLUX 对像素尺寸敏感)
    if "16:9" in ratio: size_desc = "16:9 aspect ratio"
    elif "3:4" in ratio: size_desc = "3:4 aspect ratio"
    else: size_desc = "9:16 aspect ratio"

    # 文字逻辑
    if "无字" in mode:
        text_prompt = "clean background, negative space for text overlay, no text in image"
    else:
        text_prompt = f"text '{m_title}' written in background, bold typography"

    # FLUX 喜欢的提示词风格：直接、堆叠关键词
    prompt = f"""
    {subject}, close up shot, high detail skin texture, realistic eyes.
    Background: abstract studio background, high tech, cinematic lighting, volumetric fog, 8k, masterpiece.
    Style: YouTube thumbnail style, high saturation, sharp focus.
    {text_prompt}, {size_desc}.
    """
    return prompt

# --- 尺寸映射 (FLUX 支持特定分辨率) ---
size_map = {
    "16:9 (横屏)": "1024x576", # FLUX Schnell 常用比例
    "3:4 (竖屏)": "768x1024",
    "9:16 (全屏)": "576x1024"
}

# --- 执行按钮 ---
if st.button("🚀 立即生成", type="primary"):
    if not api_key:
        st.warning("请先输入 SiliconFlow API Key")
    else:
        final_prompt = build_prompt(main_title, sub_title, audience, ratio_opt, text_mode)
        with st.spinner('FLUX 正在渲染超高清图片...'):
            # 注意：FLUX 生成速度极快
            img_url = generate_image_flux(final_prompt, size_map[ratio_opt])
            
        if img_url:
            st.success("生成成功！")
            st.image(img_url, use_column_width=True)
            st.markdown(f"[下载原图]({img_url})")
