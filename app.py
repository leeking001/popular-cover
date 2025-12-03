import streamlit as st
import requests
import random

# --- 0. 全局配置 (隐藏在代码里，不给用户看) ---
# 建议将 API Key 放入 Streamlit Secrets 中，或者在此处临时填入
# 如果你想让用户自己填，可以把这里留空，代码会自动处理
INTERNAL_API_KEY = "fk10575412.NkbUIIJ-cNkQfnnp14Te3aGCmjxdzVRhc575e1a1"  # 🔴 只有你自己知道的 Key (如果部署给别人用，填在这里)
INTERNAL_MODEL = "google/gemini-3-pro-image-preview" # 🔴 只有你自己知道的模型

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="AI封面一键生成", page_icon="⚡", layout="centered") # 使用 centered 布局，更像个 App

# 隐藏右上角菜单和底部的 Streamlit 水印，让应用看起来更原生
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stTextInput > label {font-size: 1.1rem; font-weight: bold;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. 核心生成逻辑 (黑盒) ---
def run_magic_generation(user_key, m_title, s_title, orientation, audience_type):
    url = "https://api.360.cn/v1/images/generations"
    
    # 自动匹配尺寸 (标准尺寸，够用且快)
    if orientation == "横屏 (视频/文章)":
        size_str = "1024x576" # 标准 16:9
        ratio_desc = "16:9"
    else:
        size_str = "768x1024" # 标准 3:4
        ratio_desc = "3:4"

    # 🔴 你的秘密咒语模板 (用户看不见)
    # 我们在后台默默把用户的输入填进去
    secret_prompt = f"""
    为主标题是<{m_title}>副标题是<{s_title}>的内容设计一张封面图，
    尺寸为<{ratio_desc}>，
    根据主题的受众（当前倾向：{audience_type}）生成一个写实风格人物特写形象，
    例如男性受众就放女性人物，表情要对应主题，
    人物形象跟文字穿插显示，整体风格要有高级感，
    文字要有设计和排版，
    参考著名YouTube博主小lin说、影视飓风、MrBeast的视频封面
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_key}"
    }
    
    payload = {
        "model": INTERNAL_MODEL,
        "prompt": secret_prompt,
        "n": 1,
        "size": size_str
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['url']
    except:
        pass
    return None

# --- 3. 极简 UI 界面 ---

st.title("⚡ 爆款封面一键生成")
st.caption("输入标题，AI 自动搞定排版、配图与设计。")

# 容器化布局，显得更整洁
with st.container():
    # 标题输入
    main_title = st.text_input("主标题", placeholder="例如：月入过万")
    sub_title = st.text_input("副标题", placeholder="例如：普通人翻身实战")
    
    # 选项一行排开
    c1, c2 = st.columns(2)
    with c1:
        orientation = st.selectbox("封面类型", ["横屏 (视频/文章)", "竖屏 (小红书/抖音)"])
    with c2:
        # 把复杂的受众选择简化为“内容调性”
        audience = st.selectbox("内容受众", ["大众/通用", "男性向 (科技/游戏)", "女性向 (美妆/情感)"])

    # API Key 处理逻辑：
    # 1. 优先读取代码里的 INTERNAL_API_KEY
    # 2. 其次读取 Streamlit Secrets
    # 3. 如果都没有，才显示输入框让用户填
    final_key = INTERNAL_API_KEY
    if not final_key and "360_API_KEY" in st.secrets:
        final_key = st.secrets["360_API_KEY"]
    
    if not final_key:
        final_key = st.text_input("请输入访问密钥 (API Key)", type="password")

    st.markdown("---")
    
    # 大大的生成按钮
    if st.button("✨ 立即生成封面", type="primary", use_container_width=True):
        if not main_title:
            st.toast("⚠️ 请至少输入主标题")
        elif not final_key:
            st.toast("⚠️ 缺少 API Key")
        else:
            with st.spinner("正在设计排版中..."):
                # 映射受众选项到 Prompt 逻辑
                aud_map = {
                    "大众/通用": "通用受众",
                    "男性向 (科技/游戏)": "男性受众",
                    "女性向 (美妆/情感)": "女性受众"
                }
                
                img_url = run_magic_generation(final_key, main_title, sub_title, orientation, aud_map[audience])
                
                if img_url:
                    st.success("生成完成！")
                    st.image(img_url, use_column_width=True)
                    st.markdown(f"<a href='{img_url}' target='_blank' style='display:block; text-align:center; background:#FF4B4B; color:white; padding:10px; border-radius:5px; text-decoration:none;'>📥 点击下载高清原图</a>", unsafe_allow_html=True)
                else:
                    st.error("生成失败，请稍后重试。")

