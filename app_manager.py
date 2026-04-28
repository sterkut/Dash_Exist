import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="Мій AI-Тренер | EXIST.UA", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; color: #1E293B; }
    h1, h2, h3 { font-weight: 800; color: #0F172A; }
    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; color: #0EA5E9; }
    [data-testid="stMetricLabel"] { font-weight: 600; color: #64748B; text-transform: uppercase; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { padding-top: 10px; padding-bottom: 10px; font-size: 1.2rem; font-weight: 600; }
    .card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .check-item { color: #166534; background: #F0FDF4; padding: 8px; border-radius: 6px; margin-bottom: 5px; display: flex; align-items: center; gap: 8px; font-weight: 500; }
    .cross-item { color: #991B1B; background: #FEF2F2; padding: 8px; border-radius: 6px; margin-bottom: 5px; display: flex; align-items: center; gap: 8px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- 2. БАЗА PIN-КОДІВ ---
MANAGER_PINS = {
    "1365": "Kobernyk",
    "2563": "Gardaman",
    "9586": "Nikolaychuk",
    "7562": "Bezdukhyi",
    "4216": "Chumakevych",
    "7381": "Gaskov",
    "5536": "Bezushkevych",
    "9743": "Palanichko",
    "9832": "Tovarianskyi",
    "9586": "Protsiv",
    "3632": "Sobeiko",
    "5587": "Yakubovskyi",
    "2534": "Melnyk",
    "8472": "Verner",
    "5741": "Zabrodskyi"
}

# --- 3. ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data(ttl=600)
def load_data():
    df = pd.DataFrame()
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        url = "https://docs.google.com/spreadsheets/d/1a1JlK5D4MoRjiHBLOuUN9ScVkKzGPLE6zL1LvXj3Ezw/edit?gid=0#gid=0"
        df = conn.read(spreadsheet=url)
    except: pass
    
    if df.empty:
        try: df = pd.read_excel(r"D:\виход\REPORT_EXIST_CEO.xlsx")
        except: pass

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if "Дата" in df.columns:
            df["Дата"] = pd.to_datetime(df["Дата"], errors='coerce').dt.date
        
        # Перетворення числових значень
        cols_to_fix = ['Hard_Бал', 'Soft_Бал', 'Крос_сел', 'Екосистема']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df_full = load_data()

# --- 4. АВТОРИЗАЦІЯ ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://www.exist.ua/assets/images/logo.svg", width=200)
        st.subheader("Вхід для менеджерів")
        pin = st.text_input("Введіть свій PIN-код", type="password")
        if st.button("Увійти", use_container_width=True):
            if pin in MANAGER_PINS:
                st.session_state["authenticated"] = True
                st.session_state["manager_name"] = MANAGER_PINS[pin]
                st.rerun()
            else:
                st.error("Невірний PIN-код")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. ФІЛЬТРАЦІЯ ДАНИХ (ПЕРСОНАЛІЗАЦІЯ) ---
manager_name = st.session_state["manager_name"]
df_personal = df_full[df_full["Менеджер"] == manager_name].copy()

# --- 6. ГОЛОВНИЙ ІНТЕРФЕЙС ---
with st.sidebar:
    st.markdown(f"### Вітаємо, {manager_name}! 👋")
    st.write("Твій AI-тренер готовий до розбору.")
    if st.button("🚪 Вийти"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")
    st.info("Поради формуються на основі твоїх останніх розмов.")

st.title("🚀 Мій AI-Тренер")

tab_analytics, tab_history, tab_trends = st.tabs(["🎯 Дашборд Ефективності", "🎧 Мої дзвінки та розбір", "📈 Моя динаміка"])

# ==========================================
# ВКЛАДКА 1: ДАШБОРД ЕФЕКТИВНОСТІ (ДУБЛІКАТ)
# ==========================================
with tab_analytics:
    st.markdown("### 📊 Загальні показники відділу та твій рейтинг")
    
    c1, c2 = st.columns(2)
    with c1:
        # Діаграма результатів (по всьому відділу для порівняння)
        res_col = 'Результат_Розмови_Заголовок' if 'Результат_Розмови_Заголовок' in df_full.columns else 'Результат_Розмови'
        if res_col in df_full.columns:
            res_counts = df_full[res_col].value_counts().reset_index()
            res_counts.columns = ['Результат', 'Кількість']
            fig_res = px.pie(res_counts, values='Кількість', names='Результат', hole=0.4, title="Структура результатів (Весь відділ)")
            st.plotly_chart(fig_res, use_container_width=True)
            
    with c2:
        # Конверсія (Весь відділ)
        conv_data = df_full['ROOT_PROBLEM'].apply(lambda x: 'Успіх' if x == 'Немає' else 'Втрачено').value_counts().reset_index()
        conv_data.columns = ['Статус', 'Кількість']
        fig_conv = px.bar(conv_data, x='Статус', y='Кількість', title="Конверсія відділу", color='Статус', color_discrete_map={'Успіх': '#16A34A', 'Втрачено': '#DC2626'})
        st.plotly_chart(fig_conv, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏆 Таблиця лідерів (Твоє місце)")
    
    # Розрахунок рейтингу
    leaderboard = df_full.groupby("Менеджер").agg(
        Дзвінків=('Дзвінок', 'count'),
        Сер_Хард=('Hard_Бал', 'mean'),
        Продажів=('ROOT_PROBLEM', lambda x: (x == 'Немає').sum())
    ).reset_index()
    leaderboard['Конверсія_%'] = (leaderboard['Продажів'] / leaderboard['Дзвінків'] * 100).round(1)
    leaderboard = leaderboard.sort_values(by="Сер_Hard", ascending=False)
    
    # Підсвітка самого себе в таблиці
    def highlight_self(s):
        return ['background-color: #E0F2FE; font-weight: bold' if s.Менеджер == manager_name else '' for _ in s]

    st.dataframe(leaderboard.style.apply(highlight_self, axis=1).format({'Сер_Hard': '{:.1f}', 'Конверсія_%': '{:.1f}%'}), use_container_width=True, hide_index=True)

# ==========================================
# ВКЛАДКА 2: МОЇ ДЗВІНКИ ТА РОЗБІР (ПЕРСОНАЛЬНО)
# ==========================================
with tab_history:
    st.markdown(f"### 🎧 Твої останні розмови")
    
    if df_personal.empty:
        st.info("Твої дзвінки ще не пройшли ШІ-аналіз.")
    else:
        # Список тільки своїх дзвінків
        cols_to_show = ["Дата", "Дзвінок", "Результат_Розмови_Заголовок", "Hard_Бал", "Готовність"]
        cols_to_show = [c for c in cols_to_show if c in df_personal.columns]
        
        event = st.dataframe(df_personal[cols_to_show], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        
        selected_indices = event.selection.rows
        if selected_indices:
            row = df_personal.iloc[selected_indices[0]]
            st.markdown("---")
            
            # --- Дизайн картки (як у СЕО) ---
            t1, t2, t3 = st.columns(3)
            with t1:
                score = int(row.get('Hard_Бал', 0))
                st.markdown(f"""<div class="card" style="text-align: center;">
                    <p style="color: #64748B; font-size: 13px; font-weight: 600;">ТВІЙ БАЛ</p>
                    <h1 style="font-size: 48px; color: #0EA5E9; margin: 5px 0;">{score}<span style="font-size: 18px; color: #64748B;">/12</span></h1>
                </div>""", unsafe_allow_html=True)
            with t2:
                intent = row.get('Готовність', 'N/A')
                st.markdown(f"""<div class="card" style="text-align: center;">
                    <p style="color: #64748B; font-size: 13px; font-weight: 600;">ГОТОВНІСТЬ КЛІЄНТА</p>
                    <h1 style="color: #0EA5E9; margin: 10px 0; font-size: 32px;">{intent}</h1>
                </div>""", unsafe_allow_html=True)
            with t3:
                soft = int(row.get('Soft_Бал', 0))
                st.markdown(f"""<div class="card" style="text-align: center;">
                    <p style="color: #64748B; font-size: 13px; font-weight: 600;">SOFT SKILLS</p>
                    <h1 style="color: #0EA5E9; margin: 10px 0; font-size: 32px;">{soft}/8</h1>
                </div>""", unsafe_allow_html=True)

            # Жовтий блок результату
            res_title = row.get('Результат_Розмови_Заголовок', 'Результат')
            res_desc = row.get('Результат_Розмови_Опис', '-')
            st.markdown(f"""
            <div style="background-color: #FEFCE8; border: 1px solid #FEF08A; border-radius: 12px; padding: 20px; margin: 20px 0;">
                <h4 style="margin: 0 0 8px 0; color: #B45309;">💡 Результат: {res_title}</h4>
                <p style="margin: 0; color: #475569;">{res_desc}</p>
            </div>
            """, unsafe_allow_html=True)

            # Сильні та слабкі сторони
            sc1, sc2 = st.columns(2)
            with sc1:
                st.write("👍 **Твої сильні сторони**")
                for item in str(row.get('Сильні_Сторони', '')).split('\n'):
                    if item.strip() and item.strip() != "-":
                        st.markdown(f"<div class='check-item'>✓ {item.strip()}</div>", unsafe_allow_html=True)
            with sc2:
                st.write("🚩 **Зони для росту**")
                for item in str(row.get('Слабкі_Сторони', '')).split('\n'):
                    if item.strip() and item.strip() != "-" and item.strip().lower() != "немає":
                        st.markdown(f"<div class='cross-item'>✕ {item.strip()}</div>", unsafe_allow_html=True)

            st.info(f"**📢 Порада від ШІ:** {row.get('Порада_для_менеджера', 'Продовжуй в тому ж дусі!')}")

# ==========================================
# ВКЛАДКА 3: МОЯ ДИНАМІКА
# ==========================================
with tab_trends:
    st.markdown("### 📈 Твоя динаміка розвитку")
    if not df_personal.empty and "Дата" in df_personal.columns:
        trend_data = df_personal.groupby("Дата").agg({"Hard_Бал": "mean", "Крос_сел": "mean"}).reset_index()
        fig_personal = px.line(trend_data, x="Дата", y="Hard_Бал", markers=True, title="Мій прогрес (Hard Бал)")
        st.plotly_chart(fig_personal, use_container_width=True)
    else:
        st.info("Потрібно більше закритих днів, щоб побудувати графік прогресу.")
