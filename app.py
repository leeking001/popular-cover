import streamlit as st
from openai import OpenAI

# --- 页面基础设置 ---
st.set_page_config(page_title="爆款封面生成器", page_icon="🔥", layout="wide")

# --- 侧边栏配置 ---
with st.sidebar:
    st.title("⚙️ 设置")
    api_key = st.text_input("OpenAI API Key", type="password", help="需要填入你的 Key 才能运行")
    st.markdown("---")
    st.info("💡 **设计风格参考**：\n- MrBeast (夸张表情/高饱和)\n- 影视飓风 (科技感/高画质)\n- 小Lin说 (专业/财经风)")

# --- 主界面 ---
st.title("🔥 自媒体爆款封面生成器")
st.markdown("根据你的咒语逻辑：自动匹配受众性别，生成写实风格、人物与文字穿插的高级感封面。")

# --- 输入区域 ---
col1, col2 = st.columns([1, 1])

with col1:
    main_title = st.text_input("主标题 (建议简短)", "月入过万")
    sub_title = st.text_input("副标题", "AI副业实战教程")
    audience = st.selectbox("目标受众是谁？", ["男性受众", "女性受众", "通用/中性"])

with col2:
    ratio_opt = st.selectbox("封面比例", ["16:9 (B站/西瓜/YouTube)", "3:4 (小红书)", "9:16 (抖音/TikTok)"])
    style_intensity = st.slider("表情夸张程度 (MrBeast指数)", 1, 10, 5)
    text_mode = st.radio("文字生成模式", ["仅生成无字底图 (推荐，后期加字)", "尝试让AI直接写字 (不稳定)"])

# --- 核心逻辑函数 ---
def build_prompt(m_title, s_title, aud, ratio, intensity, mode):
    # 1. 逻辑判断：根据受众决定人物形象
    if aud == "男性受众":
        character = "an attractive, professional female host, friendly yet authoritative"
        gender_note = "Female character for male audience appeal"
    elif aud == "女性受众":
        character = "a handsome, charismatic male host, warm smile"
        gender_note = "Male character for female audience appeal"
    else:
        character = "an expressive content creator"
        gender_note = "Neutral appeal"

    # 2. 表情控制
    if intensity > 7:
        expression = "shocked face, mouth open, wide eyes, extreme emotion (MrBeast style)"
    elif intensity > 4:
        expression = "confident smile, engaging eye contact, pointing at the text"
    else:
        expression = "serious, professional, analytical look (financial/news style)"

    # 3. 文字处理逻辑
    if "无字" in mode:
        text_instruction = "Do NOT include any text. Leave negative space in the center or side for overlaying text later. Clean composition."
    else:
        text_instruction = f"The image MUST include the text: '{m_title}' in huge, bold, 3D typography, and '{s_title}' in smaller subtitle font. The character should be interwoven with the text (depth of field effect)."

    # 4. 最终咒语拼接 (Prompt Engineering)
    # 我们将你的中文需求翻译成 DALL-E 更易理解的英文结构，并保留核心风格
    prompt = f"""
    Create a high-end YouTube/Social Media thumbnail.
    Aspect Ratio: {ratio}.
    
    [Subject]
    A photorealistic close-up of {character}. 
    Expression: {expression}.
    Lighting: Studio lighting, rim light, high contrast, 8k resolution.
    
    [Composition & Style]
    Style references: MrBeast (vibrant colors), MediaStorm (high tech quality).
    The character is positioned to interact with the background elements.
    Background: Abstract, high-quality gradient or blurred studio background, matching the theme of '{m_title}'.
    Visuals: High saturation, pop-culture aesthetic.
    
    [Text & Layout]
    {text_instruction}
    
    [Logic Note]
    {gender_note}. The overall vibe should be premium and click-worthy.
    """
    return prompt

def generate_image(prompt, size_str):
    client = OpenAI(api_key=api_key)
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size_str,
            quality="hd", # 使用 HD 模式以获得更好的细节
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"生成失败: {e}")
        return None

# --- 尺寸映射 ---
size_map = {
    "16:9 (B站/西瓜/YouTube)": "1792x1024",
    "3:4 (小红书)": "1024x1792", # DALL-E 3 竖屏标准
    "9:16 (抖音/TikTok)": "1024x1792"
}

# --- 生成按钮 ---
if st.button("🚀 开始生成封面", type="primary"):
    if not api_key:
        st.warning("请先在左侧填入 API Key")
    else:
        # 1. 构建咒语
        final_prompt = build_prompt(main_title, sub_title, audience, ratio_opt, style_intensity, text_mode)
        
        # 2. 显示实际发送给 AI 的咒语 (方便调试)
        with st.expander("查看生成的魔法咒语 (Prompt)"):
            st.code(final_prompt)
            
        # 3. 调用接口
        with st.spinner('正在渲染人物、调整灯光、排版构图...'):
            image_url = generate_image(final_prompt, size_map[ratio_opt])
            
        # 4. 展示结果
        if image_url:
            st.success("生成成功！")
            st.image(image_url, use_column_width=True)
            st.markdown(f"**[点击下载高清原图]({image_url})**")
            
            if "无字" in text_mode:
                st.info("💡 提示：你选择了无字模式。现在把这张图放入 Canva/醒图，加上大大的标题，效果最好！")
