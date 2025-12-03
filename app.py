import streamlit as st
from openai import OpenAI

# --- 页面配置 ---
st.set_page_config(page_title="Pro级封面生成器", page_icon="💎", layout="wide")

# --- CSS 样式优化 (让界面更好看) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-size: 20px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏 ---
with st.sidebar:
    st.title("💎 设置 (Pro版)")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    st.markdown("---")
    st.success("已启用模型：**FLUX.1-dev**\n\n这是目前最强的开源画质模型，擅长生成超写实人像和复杂构图。")

# --- 主界面 ---
st.title("💎 自媒体封面生成器 (电影级画质)")
st.markdown("生成媲美 MrBeast / 影视飓风 的 4K 级封面底图")

col1, col2 = st.columns([1, 1])
with col1:
    main_title = st.text_input("封面主题/标题", "月入过万")
    audience = st.selectbox("目标受众", ["男性受众 (生成美女)", "女性受众 (生成帅哥)", "通用 (生成极客)"])
    emotion = st.selectbox("人物表情", ["惊讶/震撼 (高点击)", "自信/微笑 (专业感)", "思考/严肃 (干货感)"])

with col2:
    ratio_opt = st.selectbox("封面比例", ["16:9 (横屏视频)", "3:4 (小红书)", "9:16 (抖音)"])
    # 高级选项
    style = st.selectbox("视觉风格", ["写实摄影 (Realism)", "3D 渲染 (C4D Style)", "赛博朋克 (Cyberpunk)"])

# --- 核心逻辑 ---
def generate_image_flux_pro(prompt, size_str):
    # 必须检查 Key
    if not api_key:
        return None, "请先输入 API Key"

    client = OpenAI(
        api_key=api_key, # 使用侧边栏输入的变量
        base_url="https://api.siliconflow.cn/v1" 
    )
    
    try:
        response = client.images.generate(
            # 🔥 关键升级：使用 dev 版本，画质极高
            model="black-forest-labs/FLUX.1-dev", 
            prompt=prompt,
            size=size_str,
            n=1,
        )
        return response.data[0].url, None
    except Exception as e:
        return None, str(e)

# --- 咒语构建 (电影级 Prompt) ---
def build_pro_prompt(topic, aud, emo, ratio, style_choice):
    # 1. 人物设定 (增加细节描述)
    if aud.startswith("男性"):
        person = "a stunningly beautiful female influencer, detailed skin texture, natural makeup"
    elif aud.startswith("女性"):
        person = "a charismatic handsome male creator, sharp jawline, stubble, detailed eyes"
    else:
        person = "a cool tech geek with glasses, futuristic vibe"

    # 2. 表情设定
    if "惊讶" in emo:
        face = "shocked expression, mouth open, eyes wide, hands on head, extreme emotion"
    elif "自信" in emo:
        face = "confident smirk, pointing at camera, engaging eye contact"
    else:
        face = "deep in thought, analytical look, serious professional expression"

    # 3. 风格与光影 (这是高级感的来源)
    if "写实" in style_choice:
        visuals = "Shot on Sony A7R IV, 85mm lens, f/1.8, depth of field, bokeh, studio lighting, rim light, 8k resolution, hyper-realistic, raw photo"
    elif "3D" in style_choice:
        visuals = "C4D render, Octane render, clay material, 3D illustration, bright candy colors, high gloss, masterpiece"
    else:
        visuals = "Neon lights, cyberpunk city background, blue and pink color palette, high contrast, cinematic fog"

    # 4. 尺寸逻辑
    ar = "16:9" if "16:9" in ratio else ("3:4" if "3:4" in ratio else "9:16")

    # 5. 最终拼接
    # FLUX Dev 喜欢自然语言，但也吃关键词堆叠
    prompt = f"""
    High quality YouTube thumbnail background.
    Subject: {person}, {face}.
    Theme: {topic}.
    Composition: Center composition, subject slightly to the side to leave space for text.
    Visuals: {visuals}.
    Quality: Masterpiece, best quality, ultra-detailed, sharp focus, professional color grading.
    Aspect Ratio: {ar}.
    (No text, clean background).
    """
    return prompt

# --- 尺寸映射 ---
size_map = {
    "16:9 (横屏视频)": "1024x576",
    "3:4 (小红书)": "768x1024",
    "9:16 (抖音)": "576x1024"
}

# --- 执行按钮 ---
if st.button("🚀 生成大师级封面", type="primary"):
    if not api_key:
        st.error("❌ 也就是没填 API Key，去侧边栏填一下！")
    else:
        final_prompt = build_pro_prompt(main_title, audience, emotion, ratio_opt, style)
        
        # 显示 Prompt 让你知道 AI 到底在画什么
        with st.expander("查看生成的咒语"):
            st.code(final_prompt)

        with st.spinner('正在调用 FLUX.1-dev 进行 4K 渲染 (约需 10-20 秒)...'):
            img_url, error_msg = generate_image_flux_pro(final_prompt, size_map[ratio_opt])
            
        if error_msg:
            st.error(f"出错啦: {error_msg}")
        elif img_url:
            st.success("✅ 生成成功！")
            st.image(img_url, use_column_width=True)
            st.markdown(f"### [📥 点击下载高清原图]({img_url})")
            st.info("💡 建议：把这张图放进 PPT 或 醒图，加上大大的标题，就是一张百万爆款封面！")
