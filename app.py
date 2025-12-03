import streamlit as st
import requests
import json
from io import BytesIO

# --- 页面配置 ---
st.set_page_config(page_title="Gemini 3 Pro 封面生成器 (严格模式)", page_icon="🎯", layout="wide")

# --- 核心：调用 360 接口 ---
def generate_image_360(api_key, prompt, size_str):
    # 接口地址
    url = "https://api.360.cn/v1/images/generations"
    # 模型名称
    model_name = "google/gemini-3-pro-image-preview"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 构造请求体
    payload = {
        "model": model_name,
        "prompt": prompt,
        "n": 1,
        "size": size_str
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            # 尝试获取图片链接，兼容不同的返回结构
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['url']
            else:
                st.error(f"API返回数据格式异常: {data}")
                return None
        else:
            st.error(f"接口报错 ({response.status_code}): {response.text}")
            return None
            
    except Exception as e:
        st.error(f"请求发送失败: {e}")
        return None

# --- 界面 UI ---
with st.sidebar:
    st.title("🎯 设置")
    api_key = st.text_input("360 API Key", type="password", help="请输入 api.360.cn 的密钥")
    
    st.markdown("---")
    st.info(f"当前模型：\n`google/gemini-3-pro-image-preview`")
    st.warning("⚠️ 注意：此模式下，文字由 AI 直接生成。如果出现错别字，请多试几次。")

st.title("🎯 爆款封面生成器 (严格指令版)")
st.caption("严格执行指定提示词模板，生成包含文字设计的封面")

col1, col2 = st.columns([1, 1])
with col1:
    main_title = st.text_input("主标题", "月入过万")
    sub_title = st.text_input("副标题", "Gemini实战")
    # 增加受众选择，因为你的提示词里有“根据主题的受众”这一逻辑
    audience = st.selectbox("目标受众 (影响人物性别)", ["男性受众", "女性受众", "通用受众"])

with col2:
    ratio_opt = st.selectbox("封面比例", ["16:9", "3:4", "1:1"])
    # 增加一个补充描述，防止AI不知道主题是什么
    theme_desc = st.text_input("主题补充 (可选)", "科技感，赚钱，极客")

if st.button("🚀 严格执行生成", type="primary"):
    if not api_key:
        st.warning("请先在侧边栏填写 API Key")
    else:
        # 1. 尺寸映射
        size_map = {
            "16:9": "1024x576",
            "3:4": "768x1024",
            "1:1": "1024x1024"
        }
        
        # 2. 构建严格的 Prompt
        # 注意：我把 audience 拼接到“主题”里，帮助 AI 更好地理解“根据主题的受众”
        # 模板严格按照你提供的要求拼接
        
        final_prompt = f"""
        为主标题是<{main_title}>副标题是<{sub_title}>的内容设计一张封面图，
        尺寸为<{ratio_opt}>，
        根据主题的受众（当前受众为：{audience}，主题关键词：{theme_desc}）生成一个写实风格人物特写形象，
        例如男性受众就放女性人物，表情要对应主题，
        人物形象跟文字穿插显示，整体风格要有高级感，
        文字要有设计和排版，不要翻译或更改文字，
        参考著名YouTube博主小lin说、影视飓风、MrBeast的视频封面
        """
        
        # 显示实际发送的 Prompt 供检查
        with st.expander("查看发送给 AI 的完整指令"):
            st.text(final_prompt)
        
        # 3. 调用接口
        with st.spinner(f"正在请求 Gemini 3 Pro Image 进行设计与绘制..."):
            img_url = generate_image_360(api_key, final_prompt, size_map[ratio_opt])
            
        # 4. 展示结果
        if img_url:
            st.success("✅ 生成成功！")
            st.image(img_url, use_column_width=True)
            st.markdown(f"**[📥 点击下载原图]({img_url})**")
