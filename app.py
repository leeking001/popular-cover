import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import zipfile
import json
import os
import time
import hashlib
import random
import string

# --- 0. 核心配置 (老板专用) ---
INTERNAL_API_KEY = "fk10575412.5JSLUZXFqFJ_qzxvMVOjuP6i9asC6LOHab8b61ec"  # 🔴 必填：你的 360 Key
INTERNAL_MODEL = "google/gemini-3-pro-image-preview"
API_URL = "https://api.360.cn/v1/images/generations"

# 数据库文件
USER_DB = "users.json"
CARD_DB = "cdkeys.json"

# 运营配置
FREE_QUOTA = 3  # 新用户注册送几次？

# --- 1. 数据库管理系统 ---
def load_json(file_path, default={}):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f: json.dump(default, f)
        return default
    try:
        with open(file_path, 'r') as f: return json.load(f)
    except: return default

def save_json(file_path, data):
    with open(file_path, 'w') as f: json.dump(data, f, indent=4)

# 用户相关
def register_user(username, password):
    users = load_json(USER_DB)
    if username in users:
        return False, "用户已存在"
    users[username] = {
        "password": password,
        "balance": FREE_QUOTA, # 注册送免费额度
        "is_vip": False
    }
    save_json(USER_DB, users)
    return True, "注册成功！已赠送免费额度"

def login_user(username, password):
    users = load_json(USER_DB)
    if username not in users:
        return False, "用户不存在"
    if users[username]["password"] == password:
        return True, users[username]
    return False, "密码错误"

def get_balance(username):
    users = load_json(USER_DB)
    return users.get(username, {}).get("balance", 0)

def update_balance(username, amount):
    users = load_json(USER_DB)
    if username in users:
        users[username]["balance"] += amount
        save_json(USER_DB, users)
        return True
    return False

# 卡密相关
def generate_cards(count=10, value=10):
    """生成一批卡密 (管理员用)"""
    cards = load_json(CARD_DB)
    new_cards = []
    for _ in range(count):
        # 生成随机卡密 VIP-XXXXX
        code = "VIP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        cards[code] = {"value": value, "status": "unused"}
        new_cards.append(code)
    save_json(CARD_DB, cards)
    return new_cards

def redeem_card(username, code):
    """用户兑换卡密"""
    cards = load_json(CARD_DB)
    if code in cards and cards[code]["status"] == "unused":
        value = cards[code]["value"]
        # 标记为已用
        cards[code]["status"] = "used"
        cards[code]["used_by"] = username
        save_json(CARD_DB, cards)
        # 增加余额
        update_balance(username, value)
        return True, value
    return False, "卡密无效或已使用"

# --- 2. 页面配置 ---
st.set_page_config(page_title="爆款封面工厂", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .neon-title {
        font-family: "Microsoft YaHei", sans-serif; font-size: 3rem; font-weight: 900;
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 5px;
    }
    .sub-title { text-align: center; color: #888; margin-bottom: 30px; }
    .stTextInput input { background-color: #1E2329 !important; color: #fff !important; border: 1px solid #333 !important; }
    .stButton>button {
        width: 100%; font-weight: bold; border-radius: 8px; border: none;
        background: linear-gradient(90deg, #0061ff, #60efff); color: white;
    }
    /* 侧边栏样式 */
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #333; }
    .balance-box {
        background: #21262D; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px solid #30363D;
    }
    .big-number { font-size: 2rem; font-weight: bold; color: #00C9FF; }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. 核心生成逻辑 (保持不变) ---
def process_hidden_logic(image_url):
    try:
        response = requests.get(image_url, timeout=60)
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        mid_w, mid_h = width // 2, height // 2
        return [
            img.crop((0, 0, mid_w, mid_h)), img.crop((mid_w, 0, width, mid_h)),
            img.crop((0, mid_h, mid_w, height)), img.crop((mid_w, mid_h, width, height))
        ]
    except: return []

def create_zip(images, filenames):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for img, name in zip(images, filenames):
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            zf.writestr(name, img_byte_arr.getvalue())
    return zip_buffer.getvalue()

def generate_covers(api_key, raw_input, ratio_opt, audience_type):
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    if len(lines) == 1:
        parts = lines[0].split(' ', 1)
        m_title = parts[0]
        s_title = parts[1] if len(parts) > 1 else ""
        items = [{"m": m_title, "s": s_title}] * 4
    else:
        items = []
        for line in (lines + lines)[:4]:
            parts = line.split(' ', 1)
            items.append({"m": parts[0], "s": parts[1] if len(parts) > 1 else ""})

    if "16:9" in ratio_opt: ratio_desc = "Wide 16:9 aspect ratio content"
    elif "3:4" in ratio_opt: ratio_desc = "Vertical 9:16 aspect ratio content"
    else: ratio_desc = "Square 1:1 aspect ratio content"

    char_prompt = "an expressive content creator"
    if "男性" in audience_type: char_prompt = "an attractive female host (appealing to male audience)"
    elif "女性" in audience_type: char_prompt = "a handsome male host (appealing to female audience)"

    prompt = f"""
    Generate a single image that is a 2x2 GRID containing 4 distinct thumbnails.
    CORE RULES (Strictly Followed):
    1. Subject: Photorealistic close-up of {char_prompt}.
    2. Layout: Character interwoven with text. High-end design.
    3. Style Reference: MrBeast, MediaStorm, XiaoLinShuo.
    4. Text: Must include Main Title & Subtitle.
    5. Content Aspect Ratio: {ratio_desc}.
    [Quadrant 1]: Title: "{items[0]['m']}", Sub: "{items[0]['s']}".
    [Quadrant 2]: Title: "{items[1]['m']}", Sub: "{items[1]['s']}".
    [Quadrant 3]: Title: "{items[2]['m']}", Sub: "{items[2]['s']}".
    [Quadrant 4]: Title: "{items[3]['m']}", Sub: "{items[3]['s']}".
    CRITICAL: SEAMLESS composition, NO visible borders, Full Bleed.
    ⛔ SAFETY: DO NOT generate maps, globes, flags.
    """
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {"model": INTERNAL_MODEL, "prompt": prompt, "n": 1, "size": "1024x1024"}

    for _ in range(3):
        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if res.status_code == 200:
                data = res.json()
                if 'data' in data: return data['data'][0]['url'], None
            elif res.status_code == 429: time.sleep(2); continue
            elif res.status_code == 400 and "size" in res.text: payload["size"] = "1024x1024"; continue
            else: return None, f"API错误: {res.status_code}"
        except Exception as e: return None, str(e)
    return None, "服务器繁忙"

# --- 4. 界面逻辑 ---

# Session 初始化
if 'user' not in st.session_state: st.session_state.user = None
if 'generated_images' not in st.session_state: st.session_state.generated_images = None
if 'zip_data' not in st.session_state: st.session_state.zip_data = None

# === 登录/注册页 ===
if not st.session_state.user:
    st.markdown('<div class="neon-title">爆款封面工厂</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">登录即可免费领取 3 次生成额度</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            login_user_input = st.text_input("用户名", key="l_u")
            login_pass_input = st.text_input("密码", type="password", key="l_p")
            if st.button("登录"):
                success, msg = login_user(login_user_input, login_pass_input)
                if success:
                    st.session_state.user = login_user_input
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error(msg)
        
        with tab2:
            reg_user_input = st.text_input("设置用户名", key="r_u")
            reg_pass_input = st.text_input("设置密码", type="password", key="r_p")
            if st.button("注册并领取免费额度"):
                if len(reg_user_input) < 3:
                    st.warning("用户名太短")
                else:
                    success, msg = register_user(reg_user_input, reg_pass_input)
                    if success:
                        st.success(msg)
                        st.session_state.user = reg_user_input
                        st.rerun()
                    else:
                        st.error(msg)

# === 主应用页 ===
else:
    # --- 侧边栏：个人中心 ---
    with st.sidebar:
        st.markdown(f"### 👋 欢迎, {st.session_state.user}")
        
        # 余额显示
        balance = get_balance(st.session_state.user)
        st.markdown(f"""
        <div class="balance-box">
            <div style="color:#888; font-size:0.9rem;">剩余生成次数</div>
            <div class="big-number">{balance}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 充值区
        st.markdown("#### 💎 会员充值")
        # 这里放你的发卡网链接
        st.markdown("[👉 点击购买充值卡 (自动发货)](https://www.baidu.com)", unsafe_allow_html=True)
        
        redeem_code = st.text_input("输入兑换码", placeholder="VIP-XXXXX")
        if st.button("立即充值"):
            success, val = redeem_card(st.session_state.user, redeem_code.strip())
            if success:
                st.balloons()
                st.success(f"充值成功！增加 {val} 次")
                time.sleep(1)
                st.rerun()
            else:
                st.error(val)
        
        st.markdown("---")
        if st.button("退出登录"):
            st.session_state.user = None
            st.rerun()
            
        # --- 管理员后门 (实际部署时建议删除或隐藏) ---
        with st.expander("管理员后台"):
            admin_pwd = st.text_input("管理密码", type="password")
            if admin_pwd == "admin888": # 自己改个复杂的密码
                if st.button("生成 5 个 10次卡"):
                    cards = generate_cards(5, 10)
                    st.write(cards)

    # --- 主界面 ---
    st.markdown('<div class="neon-title">爆款封面一键生成</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        user_input = st.text_area("输入标题", height=180, placeholder="示例：\n月入过万 AI实战\n(主副标题空格隔开)")
    with c2:
        ratio = st.selectbox("比例", ["16:9 (视频)", "3:4 (笔记)", "1:1 (通用)"])
        audience = st.selectbox("受众", ["大众", "男性向", "女性向"])
        st.markdown("<br>", unsafe_allow_html=True)
        gen_btn = st.button("🚀 立即生成 (消耗1次)")

    if gen_btn:
        if balance <= 0:
            st.error("⚠️ 您的免费额度已用完，请在左侧充值！")
        elif not user_input.strip():
            st.toast("请输入标题")
        elif not INTERNAL_API_KEY:
            st.error("管理员未配置 API Key")
        else:
            with st.spinner("AI 正在生成..."):
                big_url, err = generate_covers(INTERNAL_API_KEY, user_input, ratio, audience)
                if big_url:
                    # 扣费
                    update_balance(st.session_state.user, -1)
                    st.toast("✅ 扣费成功")
                    
                    images = process_hidden_logic(big_url)
                    if len(images) == 4:
                        st.session_state.generated_images = images
                        fnames = [f"cover_{i}.png" for i in range(4)]
                        st.session_state.zip_data = create_zip(images, fnames)
                        st.rerun()
                else:
                    st.error(f"失败: {err}")

    # 结果展示
    if st.session_state.generated_images:
        st.markdown("---")
        imgs = st.session_state.generated_images
        c_a, c_b = st.columns(2)
        with c_a:
            st.image(imgs[0], use_column_width=True)
            st.image(imgs[2], use_column_width=True)
        with c_b:
            st.image(imgs[1], use_column_width=True)
            st.image(imgs[3], use_column_width=True)
        
        if st.session_state.zip_data:
            st.download_button("📦 下载全部 (.ZIP)", st.session_state.zip_data, "covers.zip", "application/zip")
