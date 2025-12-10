import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import zipfile
import json
import os
import time
import random
import string
import pandas as pd # 用于展示数据表格

# --- 0. 核心配置 ---
INTERNAL_API_KEY = ""  # 🔴 必填：你的 360 Key
INTERNAL_MODEL = "google/gemini-3-pro-image-preview"
API_URL = "https://api.360.cn/v1/images/generations"

# 数据库文件
USER_DB = "users.json"
CARD_DB = "cdkeys.json"
FREE_QUOTA = 3

# 🔴 管理员账号 (隐形后门)
ADMIN_USER = "admin"
ADMIN_PASS = "admin888" # 上线前记得改这个密码！

# --- 1. 数据库系统 ---
def load_json(file_path, default={}):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f: json.dump(default, f)
        return default
    try:
        with open(file_path, 'r') as f: return json.load(f)
    except: return default

def save_json(file_path, data):
    with open(file_path, 'w') as f: json.dump(data, f, indent=4)

def register_user(username, password):
    if username == ADMIN_USER: return False, "该用户名不可用" # 防止有人注册管理员号
    users = load_json(USER_DB)
    if username in users: return False, "用户已存在"
    users[username] = {"password": password, "balance": FREE_QUOTA}
    save_json(USER_DB, users)
    return True, "注册成功"

def login_check(username, password):
    # 1. 先检查是不是管理员
    if username == ADMIN_USER and password == ADMIN_PASS:
        return True, "admin"
    
    # 2. 再检查普通用户
    users = load_json(USER_DB)
    if username in users and users[username]["password"] == password:
        return True, "user"
    
    return False, None

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

def generate_cards(count, value):
    cards = load_json(CARD_DB)
    new_list = []
    for _ in range(count):
        code = "VIP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        cards[code] = {"value": value, "status": "unused", "create_time": time.strftime("%Y-%m-%d %H:%M")}
        new_list.append(code)
    save_json(CARD_DB, cards)
    return new_list

def redeem_card(username, code):
    cards = load_json(CARD_DB)
    if code in cards and cards[code]["status"] == "unused":
        cards[code]["status"] = "used"
        cards[code]["used_by"] = username
        cards[code]["use_time"] = time.strftime("%Y-%m-%d %H:%M")
        save_json(CARD_DB, cards)
        update_balance(username, cards[code]["value"])
        return True, cards[code]["value"]
    return False, "无效卡密"

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
    .login-box { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 10px; margin-top: 20px; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; border: none; background: linear-gradient(90deg, #0061ff, #60efff); color: white; height: 50px; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #333; }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. 核心逻辑 (生成部分) ---
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

def simulate_progress():
    progress_text = st.empty()
    my_bar = st.progress(0)
    steps = ["🧠 分析关键词...", "🎨 匹配配色...", "📐 计算构图...", "💡 调整灯光...", "✨ 4K渲染...", "🚀 打包中..."]
    for i in range(80):
        time.sleep(0.02)
        my_bar.progress(i + 1)
        if i % 15 == 0: progress_text.text(steps[(i // 15) % len(steps)])
    return my_bar, progress_text

# --- 4. 界面逻辑 ---

if 'user' not in st.session_state: st.session_state.user = None
if 'role' not in st.session_state: st.session_state.role = None # admin 或 user
if 'generated_images' not in st.session_state: st.session_state.generated_images = None
if 'zip_data' not in st.session_state: st.session_state.zip_data = None
if 'show_login' not in st.session_state: st.session_state.show_login = False

# ==========================================
# 🔴 场景 A：管理员后台 (只有登录 admin 才能见)
# ==========================================
if st.session_state.role == "admin":
    st.markdown("## 🔧 封面工厂·管理后台")
    st.info("👋 欢迎老板！这里是你的印钞机控制台。")
    
    tab1, tab2 = st.tabs(["💳 卡密生成 (进货)", "📊 数据统计"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            gen_count = st.number_input("生成数量", min_value=1, value=10)
        with c2:
            gen_value = st.number_input("面值 (次数)", min_value=1, value=10)
        
        if st.button("⚡ 一键生成卡密"):
            new_cards = generate_cards(gen_count, gen_value)
            st.success(f"成功生成 {len(new_cards)} 张卡密！请复制下方内容：")
            st.code("\n".join(new_cards))
            st.caption("提示：复制这些卡密，去发卡网或者闲鱼上架即可。")
            
        st.markdown("---")
        st.markdown("#### 📦 卡密库存状态")
        all_cards = load_json(CARD_DB)
        if all_cards:
            df = pd.DataFrame.from_dict(all_cards, orient='index')
            st.dataframe(df)
        else:
            st.write("暂无数据")

    with tab2:
        st.markdown("#### 👥 用户列表")
        all_users = load_json(USER_DB)
        if all_users:
            df_users = pd.DataFrame.from_dict(all_users, orient='index')
            st.dataframe(df_users)
        else:
            st.write("暂无用户")

    if st.button("退出管理后台"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

# ==========================================
# 🟢 场景 B：普通用户界面 (生成器)
# ==========================================
else:
    # 侧边栏
    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 👋 欢迎, {st.session_state.user}")
            balance = get_balance(st.session_state.user)
            st.metric("剩余次数", f"{balance} 次")
            st.markdown("---")
            st.markdown("#### 💎 充值中心")
            st.markdown("[👉 点击购买卡密](https://www.baidu.com)", unsafe_allow_html=True)
            code = st.text_input("输入卡密", placeholder="VIP-XXXX")
            if st.button("兑换"):
                succ, msg = redeem_card(st.session_state.user, code.strip())
                if succ: st.success(f"成功！余额 +{msg}"); time.sleep(1); st.rerun()
                else: st.error(msg)
            st.markdown("---")
            if st.button("退出登录"):
                st.session_state.user = None; st.session_state.role = None; st.session_state.show_login = False; st.rerun()
        else:
            st.info("👋 欢迎使用！\n\n新用户注册即送 3 次免费额度。")

    # 主界面
    st.markdown('<div class="neon-title">爆款封面工厂</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AI 智能设计 · 自动排版 · 批量出图</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        user_input = st.text_area("输入标题", height=180, placeholder="示例：\n月入过万 AI实战\n(主副标题空格隔开)")
    with c2:
        ratio = st.selectbox("比例", ["16:9 (视频)", "3:4 (笔记)", "1:1 (通用)"])
        audience = st.selectbox("受众", ["大众", "男性向", "女性向"])
        st.markdown("<br>", unsafe_allow_html=True)
        btn_text = "🚀 立即生成 (消耗1次)" if st.session_state.user else "🚀 立即生成 (需登录)"
        click_gen = st.button(btn_text)

    if click_gen:
        if not st.session_state.user:
            st.session_state.show_login = True
        else:
            balance = get_balance(st.session_state.user)
            if balance <= 0: st.error("⚠️ 您的免费额度已用完，请在左侧充值！")
            elif not user_input.strip(): st.toast("请输入标题")
            elif not INTERNAL_API_KEY: st.error("管理员未配置 API Key")
            else:
                my_bar, progress_txt = simulate_progress()
                progress_txt.text("⚡ 连接云端算力...")
                big_url, err = generate_covers(INTERNAL_API_KEY, user_input, ratio, audience)
                my_bar.progress(100); progress_txt.text("✅ 完成！"); time.sleep(0.5); my_bar.empty(); progress_txt.empty()

                if big_url:
                    update_balance(st.session_state.user, -1)
                    images = process_hidden_logic(big_url)
                    if len(images) == 4:
                        st.session_state.generated_images = images
                        fnames = [f"cover_{i}.png" for i in range(4)]
                        st.session_state.zip_data = create_zip(images, fnames)
                        st.rerun()
                else: st.error(f"失败: {err}")

    # 后置登录框
    if not st.session_state.user and st.session_state.show_login:
        st.markdown("---")
        st.markdown("##### 🔒 请先登录以保存您的作品")
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["登录", "注册 (送3次)"])
            with tab1:
                l_u = st.text_input("用户名", key="l_u")
                l_p = st.text_input("密码", type="password", key="l_p")
                if st.button("登录账号"):
                    succ, role = login_check(l_u, l_p)
                    if succ:
                        st.session_state.user = l_u
                        st.session_state.role = role
                        st.session_state.show_login = False
                        st.success("登录成功！")
                        time.sleep(0.5)
                        st.rerun()
                    else: st.error("账号或密码错误")
            with tab2:
                r_u = st.text_input("设置用户名", key="r_u")
                r_p = st.text_input("设置密码", type="password", key="r_p")
                if st.button("注册并领取福利"):
                    if len(r_u) < 3: st.warning("用户名太短")
                    else:
                        succ, msg = register_user(r_u, r_p)
                        if succ:
                            st.session_state.user = r_u
                            st.session_state.role = "user"
                            st.session_state.show_login = False
                            st.success("注册成功！")
                            time.sleep(0.5)
                            st.rerun()
                        else: st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

    # 结果展示
    if st.session_state.generated_images and st.session_state.role != "admin":
        st.markdown("---")
        st.markdown("##### ✅ 生成结果")
        imgs = st.session_state.generated_images
        c_a, c_b = st.columns(2)
        with c_a: st.image(imgs[0], use_column_width=True, caption="方案 A"); st.image(imgs[2], use_column_width=True, caption="方案 C")
        with c_b: st.image(imgs[1], use_column_width=True, caption="方案 B"); st.image(imgs[3], use_column_width=True, caption="方案 D")
        if st.session_state.zip_data: st.download_button("📦 下载全部 (.ZIP)", st.session_state.zip_data, "covers.zip", "application/zip")
