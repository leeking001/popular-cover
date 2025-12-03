import streamlit as st
import requests

# --- 0. 核心配置 ---
# 建议填入 Key，实现真正的一键生成
INTERNAL_API_KEY = "fk10575412.5JSLUZXFqFJ_qzxvMVOjuP6i9asC6LOHab8b61ec" 
INTERNAL_MODEL = "openai/gpt-5.1"
API_URL = "https://api.360.cn/v1/chat/completions"

# --- 1. 页面样式 ---
st.set_page_config(page_title="爆款封面一键生成", page_icon="⚡", layout="centered")
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stTextInput>div>div>input {font-size: 1.2rem; text-align: center;}
    .stButton>button {width: 100%; font-size: 1.2rem; padding: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# --- 2. 逻辑处理 ---
def parse_input(text):
    if not text: return "", ""
    parts = text.strip().split(' ', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], ""

def generate_cover(api_key, raw_text, size_opt, audience):
    m_title, s_title = parse_input(raw_text)
    if not s_title: s_title = " "
    
    size_map = {
        "16:9 (视频)": "1024x576",
        "3:4 (笔记)": "768x1024",
        "4:3 (文章)": "1024x768"
    }
    size_str = size_map[size_opt]
    ratio_desc = size_opt.split(' ')[0]

    prompt = f"""
    为主标题是<{m_title}>副标题是<{s_title}>的内容设计一张封面图，
    尺寸为<{ratio_desc}>，
    根据主题的受众（当前倾向：{audience}）生成一个写实风格人物特写形象，
    例如男性受众就放女性人物，表情要对应主题，
    人物形象跟文字穿插显示，整体风格要有高级感，
    文字要有设计和排版，不要翻译或更改文字，
    参考著名YouTube博主小lin说、影视飓风、MrBeast的视频封面
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": INTERNAL_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": size_str
    }

    try:
        # 🔥 关键修改：timeout 改为 120 秒 (2分钟)
        # AI 画图很慢，必须给它足够的时间
        res = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and data['data']:
                return data['data'][0]['url'], None
            return None, "生成成功但无图片返回"
        else:
            return None, f"API报错: {res.status_code} - {res.text}"
    except Exception as e:
        return None, f"网络错误或超时: {str(e)}"

# --- 3. 极简界面 ---
st.title("⚡ 爆款封面一键生成")

user_input = st.text_input("输入标题 (主标题 空格 副标题)", placeholder="例如：月入过万 AI实战教程")

c1, c2 = st.columns(2)
with c1:
    size_opt = st.selectbox("尺寸", ["16:9 (视频)", "3:4 (笔记)", "4:3 (文章)"])
with c2:
    audience = st.selectbox("受众", ["大众通用", "男性向", "女性向"])

final_key = INTERNAL_API_KEY
if not final_key:
    final_key = st.text_input("API Key", type="password")

if st.button("🚀 立即生成", type="primary"):
    if not user_input:
        st.toast("⚠️ 请输入标题")
    elif not final_key:
        st.toast("⚠️ 请输入 API Key")
    else:
        # 提示语改得更有耐心一点
        with st.spinner("AI 正在精心绘制中，通常需要 1 分钟，请耐心等待..."):
            aud_map = {"大众通用": "通用受众", "男性向": "男性受众", "女性向": "女性受众"}
            url, err = generate_cover(final_key, user_input, size_opt, aud_map[audience])
            
            if url:
                st.image(url, use_column_width=True)
                st.markdown(f"""
                    <a href="{url}" target="_blank" style="
                        display: block; margin: 10px auto; text-align: center;
                        background-color: #FF4B4B; color: white; 
                        padding: 10px 20px; border-radius: 8px; 
                        text-decoration: none; font-weight: bold;">
                        📥 下载高清原图
                    </a>
                """, unsafe_allow_html=True)
            else:
                st.error(f"生成失败: {err}")
