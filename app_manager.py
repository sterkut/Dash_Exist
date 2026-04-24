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
</style>
""", unsafe_allow_html=True)

# --- 2. БАЗА PIN-КОДІВ МЕНЕДЖЕРІВ ---
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
    "2534": "Verner",
    "5741": "Zabrodskyi"
}

# --- 3. ЛОГІКА АВТОРИЗАЦІЇ ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.manager_name = ""

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;'>", unsafe_allow_html=True)
        st.title("🔐 Особистий кабінет")
        st.write("Введіть ваш персональний PIN-код для доступу до аналітики.")
        
        pin = st.text_input("PIN-код", type="password", placeholder="****")
        
        if st.button("Увійти", use_container_width=True):
            if pin in MANAGER_PINS:
                st.session_state.logged_in = True
                st.session_state.manager_name = MANAGER_PINS[pin]
                st.rerun()
            else:
                st.error("❌ Невірний PIN-код. Спробуйте ще раз.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data(ttl=60)
def load_data():
    df = pd.DataFrame()
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        url = "https://docs.google.com/spreadsheets/d/1a1JlK5D4MoRjiHBLOuUN9ScVkKzGPLE6zL1LvXj3Ezw/edit?gid=0#gid=0"
        df = conn.read(spreadsheet=url)
    except Exception:
        pass
    
    if df.empty:
        try:
            df = pd.read_excel(r"D:\виход\REPORT_EXIST_CEO.xlsx")
        except Exception:
            pass

    if not df.empty:
        rename_dict = {}
        for col in df.columns:
            if "OOT" in col and "PROBLEM" in col: rename_dict[col] = "ROOT_PROBLEM"
            if "Готовність" in col: rename_dict[col] = "Готовність"
            if "Крос_Сел" in col and "проба" in col: rename_dict[col] = "Спроба_Крос_Селу"
            if "Дотиснув" in col: rename_dict[col] = "Зафіксував_Наступний_Крок"
            if "Екосистема" in col: rename_dict[col] = "Екосистема"
        df.rename(columns=rename_dict, inplace=True)
        
        if "Менеджер" in df.columns:
            df["Менеджер"] = df["Менеджер"].astype(str)
        if "Дзвінок" in df.columns:
            df["Дзвінок"] = df["Дзвінок"].astype(str)
            
    return df

df_full = load_data()

if df_full.empty:
    st.error("❌ Не вдалося знайти дані.")
    st.stop()

# ВІДРІЗАЄМО ЧУЖІ ДАНІ (Тільки для персональних вкладок)
my_df = df_full[df_full["Менеджер"] == st.session_state.manager_name].copy()

if my_df.empty:
    st.warning(f"👋 Вітаємо, {st.session_state.manager_name}! У вас поки що немає проаналізованих дзвінків у базі.")
    st.stop()

# --- 5. САЙДБАР МЕНЕДЖЕРА ---
with st.sidebar:
    st.markdown(f"### 👤 Привіт, {st.session_state.manager_name}!")
    if st.button("🚪 Вийти з кабінету"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🎛 Фільтри дзвінків")
    
    intents_list = sorted(my_df["Готовність"].dropna().unique()) if "Готовність" in my_df.columns else []
    selected_intents = st.multiselect("🎯 Готовність клієнта", intents_list, default=intents_list)

    root_list = sorted(my_df["ROOT_PROBLEM"].dropna().unique()) if "ROOT_PROBLEM" in my_df.columns else []
    selected_roots = st.multiselect("🚨 Результат / Причина", root_list, default=root_list)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 💰 Базові параметри угод")
    avg_check = st.number_input("Середній чек (грн)", value=1500, step=100)
    avg_cross_check = st.number_input("Середній чек доп. товару (грн)", value=100, step=10)
    cross_conv = st.slider("Конверсія у доп. продаж (%)", 0, 100, 10)

my_df_filtered = my_df[
    (my_df["Готовність"].isin(selected_intents)) &
    (my_df["ROOT_PROBLEM"].isin(selected_roots))
].copy()

# --- МАТЕМАТИКА ВТРАТ (Справедлива для менеджера) ---
intent_weights = {"High": 1.0, "Medium": 0.5, "Low": 0.0}
SYSTEMIC_ISSUES = ["Наявність", "Ціна", "Термін поставки", "Процес"]

my_df_filtered['Потенціал_грн'] = my_df_filtered['Готовність'].map(intent_weights).fillna(0) * avg_check

# Втрата рахується тільки якщо причина в менеджері
my_df_filtered['Втрачено_Головна'] = my_df_filtered.apply(
    lambda x: x['Потенціал_грн'] if (x['ROOT_PROBLEM'] != 'Немає' and x['ROOT_PROBLEM'] not in SYSTEMIC_ISSUES) else 0, axis=1
)

my_df_filtered['Втрачено_Крос'] = my_df_filtered.apply(
    lambda x: (avg_cross_check * (cross_conv/100)) if (x['ROOT_PROBLEM'] == 'Немає' and x['Спроба_Крос_Селу'] == 'Ні') else 0, axis=1
)

my_df_filtered['Втрачено_грн'] = my_df_filtered['Втрачено_Головна'] + my_df_filtered['Втрачено_Крос']

# --- 6. ЗАГОЛОВОК І ВКЛАДКИ ---
st.title("🎯 Мій AI-Тренер з продажів")
# Додали нову вкладку "Рейтинг"
tab_stats, tab_coach, tab_call, tab_rating = st.tabs(["🏆 Моя Ефективність", "🧠 Поради Тренера", "🎧 Аналіз моєї розмови", "📊 Рейтинг"])

# ==========================================
# ПАНЕЛЬ 1: ОСОБИСТА ЕФЕКТИВНІСТЬ
# ==========================================
with tab_stats:
    st.markdown("""
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <h3 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; border-bottom: 2px solid #F1F5F9; padding-bottom: 10px;">📈 Твої показники</h3>
        </div>
    """, unsafe_allow_html=True)

    total_calls = len(my_df_filtered)
    lost_main = my_df_filtered['Втрачено_Головна'].sum()
    lost_cross = my_df_filtered['Втрачено_Крос'].sum()

    success_deals = my_df_filtered[my_df_filtered['ROOT_PROBLEM'] == 'Немає']
    win_rate = (len(success_deals) / total_calls * 100) if total_calls > 0 else 0
    
    made_cross_count = len(success_deals[success_deals['Спроба_Крос_Селу'] == 'Так'])
    cross_rate = (made_cross_count / len(success_deals) * 100) if len(success_deals) > 0 else 0
    
    if 'Екосистема' in success_deals.columns:
        eco_scores = pd.to_numeric(success_deals['Екосистема'], errors='coerce').fillna(0)
        made_eco_count = len(success_deals[eco_scores > 0])
    else:
        made_eco_count = 0
        
    eco_rate = (made_eco_count / len(success_deals) * 100) if len(success_deals) > 0 else 0

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("📞 Всього дзвінків", f"{total_calls}")
    m_col2.metric("💸 Недоотримано (Основа)", f"{lost_main:,.0f} ₴")
    m_col3.metric("📦 Недоотримано (Крос-сел)", f"{lost_cross:,.0f} ₴")

    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

    p_col1, p_col2, p_col3 = st.columns(3)
    p_col1.metric("🛒 % Зроблених крос-селів", f"{cross_rate:.0f}%", help="Відсоток успішних угод, де ти запропонував супутній товар")
    p_col2.metric("🌐 % Екосистеми", f"{eco_rate:.0f}%", help="Відсоток успішних угод, де ти розповів про додаткові сервіси")
    p_col3.metric("🎯 % Успішних угод", f"{win_rate:.0f}%", help="Твій загальний Win Rate")

    st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
    
    skill_cols = ['Привітання', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття']
    existing_skills = [c for c in skill_cols if c in my_df_filtered.columns]
    
    if existing_skills:
        st.markdown("### 📊 Твій баланс навичок (Hard Skills)")
        skills_mean = my_df_filtered[existing_skills].mean().reset_index()
        skills_mean.columns = ['Навичка', 'Середній бал (з 2.0)']
        
        fig_skills = px.line_polar(skills_mean, r='Середній бал (з 2.0)', theta='Навичка', line_close=True,
                                   range_r=[0, 2], color_discrete_sequence=['#0EA5E9'])
        fig_skills.update_traces(fill='toself')
        st.plotly_chart(fig_skills, use_container_width=True)

# ==========================================
# ПАНЕЛЬ 2: AI-ТРЕНЕР
# ==========================================
with tab_coach:
    st.info("💡 **Як цим користуватися:** Нейромережа аналізує твої розмови і підказує, які фрази або дії допомогли б дотиснути клієнта. Читай поради, щоб прокачати свій скіл!")
    
    if "Порада_для_менеджера" in my_df_filtered.columns:
        advices_df = my_df_filtered[my_df_filtered["Порада_для_менеджера"].str.len() > 10]
        
        if advices_df.empty:
            st.success("🎉 Круто! Поки що ШІ не має зауважень до твоїх дзвінків.")
        else:
            for _, row in advices_df.iterrows():
                with st.expander(f"Розбір дзвінка 📄 {row['Дзвінок']} | Готовність: {row.get('Готовність', '')}", expanded=False):
                    st.markdown(f"**Причина відмови клієнта:** {row.get('ROOT_PROBLEM', 'Невідомо')}")
                    st.warning(f"**🤖 Порада від AI-Тренера:**\n\n{row['Порада_для_менеджера']}")
    else:
        st.write("Поради не знайдені в базі даних.")

# ==========================================
# ПАНЕЛЬ 3: КАРТКА КОНКРЕТНОГО ДЗВІНКА
# ==========================================
with tab_call:
    st.markdown("### 🔎 Детальний розбір твоєї розмови")

    if 'Дзвінок' in my_df_filtered.columns and not my_df_filtered.empty:
        
        display_names = my_df_filtered.apply(
            lambda r: f"🎯 {r.get('Готовність','')} | 🚨 {r.get('ROOT_PROBLEM','')} | 📄 {r['Дзвінок']}",
            axis=1
        ).tolist()
        
        file_mapping = dict(zip(display_names, my_df_filtered['Дзвінок']))
        
        selected_display = st.selectbox("Оберіть файл для розбору:", display_names)

        if selected_display:
            selected_file = file_mapping[selected_display]
            row = my_df_filtered[my_df_filtered['Дзвінок'] == selected_file].iloc[0]

            score_12 = int(row.get('Hard_Бал', 0))
            score_color = "#16A34A" if score_12 >= 10 else ("#F59E0B" if score_12 >= 6 else "#DC2626")
            score_text = "Відмінно" if score_12 >= 10 else ("Нормально" if score_12 >= 6 else "Треба підтягнути")

            hard_skill_keys = ['Привітання', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття']
            likes, norms, dislikes = 0, 0, 0
            for key in hard_skill_keys:
                val = row.get(key, 0)
                if val == 2: likes += 1
                elif val == 1: norms += 1
                else: dislikes += 1

            deg = (score_12 / 12) * 360
            
            html_skills = f"<div style='background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 40px; flex-wrap: wrap;'><div style='text-align: center; min-width: 130px;'><div style='width: 120px; height: 120px; border-radius: 50%; background: conic-gradient({score_color} {deg}deg, #E2E8F0 0deg); display: flex; justify-content: center; align-items: center; margin: 0 auto 12px auto;'><div style='width: 95px; height: 95px; border-radius: 50%; background: white; display: flex; flex-direction: column; justify-content: center; align-items: center;'><span style='font-size: 32px; font-weight: 800; color: #0F172A; line-height: 1;'>{score_12}</span><span style='font-size: 13px; color: #64748B; font-weight: 600;'>з 12</span></div></div><span style='background: {score_color}15; color: {score_color}; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;'>{score_text}</span></div><div style='flex: 1;'><h3 style='margin: 0 0 15px 0; color: #0F172A; font-size: 18px;'>📊 Твої оцінки в цьому дзвінку</h3><div style='display: flex; gap: 15px; flex-wrap: wrap;'><div style='flex: 1; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 15px; text-align: center; min-width: 120px;'><div style='font-size: 24px; margin-bottom: 5px;'>👍</div><div style='font-size: 20px; font-weight: 800; color: #166534;'>{likes}</div><div style='font-size: 13px; color: #15803D; font-weight: 600;'>Твої сильні сторони</div></div><div style='flex: 1; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 15px; text-align: center; min-width: 120px;'><div style='font-size: 24px; margin-bottom: 5px;'>😐</div><div style='font-size: 20px; font-weight: 800; color: #B45309;'>{norms}</div><div style='font-size: 13px; color: #B45309; font-weight: 600;'>Можна краще</div></div><div style='flex: 1; background: #FEF2F2; border: 1px solid #FECACA; border-radius: 10px; padding: 15px; text-align: center; min-width: 120px;'><div style='font-size: 24px; margin-bottom: 5px;'>🚩</div><div style='font-size: 20px; font-weight: 800; color: #991B1B;'>{dislikes}</div><div style='font-size: 13px; color: #B91C1C; font-weight: 600;'>Твої зони росту</div></div></div></div></div>"
            st.markdown(html_skills, unsafe_allow_html=True)

            is_success = row.get("ROOT_PROBLEM", "Немає") == "Немає"
            result_bg = "#F0FDF4" if is_success else "#FEF2F2"
            result_border = "#BBF7D0" if is_success else "#FECACA"
            result_title = "Молодець! Угода успішна 🏆" if is_success else "Угоду втрачено"
            result_desc = "Ти довів клієнта до цільової дії." if is_success else f"Причина відмови клієнта: <b>{row.get('ROOT_PROBLEM', 'Невідомо')}</b>."
            status_icon = '✅' if is_success else '❌'

            lost_total = row.get('Втрачено_грн', 0)
            lost_main = row.get('Втрачено_Головна', 0)
            lost_cross = row.get('Втрачено_Крос', 0)
            
            loss_html = ""
            if lost_total > 0:
                loss_html = f"<div style='margin-top: 15px; padding: 12px; background: #FEF2F2; border: 1px dashed #FECACA; border-radius: 8px; color: #991B1B;'><b style='font-size: 15px;'>💸 Недоотриманий потенціал угоди: {lost_total:,.0f} ₴</b><br><span style='font-size: 13px;'>З них основа: {lost_main:,.0f} ₴ | Крос-сел: {lost_cross:,.0f} ₴</span></div>"

            html_result = f"<div style='background: {result_bg}; border: 1px solid {result_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px;'><div style='display: flex; gap: 15px; align-items: flex-start;'><div style='font-size: 24px; margin-top: 2px;'>{status_icon}</div><div style='width: 100%;'><h4 style='margin: 0 0 4px 0; color: #111827; font-size: 16px;'>Результат: {result_title}</h4><p style='margin: 0; color: #374151; font-size: 14px;'>{result_desc} <br> Готовність клієнта: <b>{row.get('Готовність', 'N/A')}</b> | Крос-сел: <b>{row.get('Спроба_Крос_Селу', 'Ні')}</b></p>{loss_html}</div></div></div>"
            st.markdown(html_result, unsafe_allow_html=True)

            tone_text = row.get("Тон_Розмови", "Тон розмови не проаналізовано.")
            
            html_tone = f"<div style='background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);'><div style='display: flex; gap: 10px; align-items: center; margin-bottom: 8px;'><div style='font-size: 20px;'>🎙️</div><h4 style='margin: 0; color: #0F172A; font-size: 16px;'>Як звучала розмова (Аналіз тону)</h4></div><p style='margin: 0; color: #475569; font-size: 14px; line-height: 1.5; padding-left: 30px;'>{tone_text}</p></div>"
            st.markdown(html_tone, unsafe_allow_html=True)
    else:
        st.info("Немає даних.")

# ==========================================
# ПАНЕЛЬ 4: РЕЙТИНГ МЕНЕДЖЕРІВ
# ==========================================
with tab_rating:
    st.markdown("### 🏆 Загальний рейтинг відділу продажів")
    st.write("Тут ти можеш порівняти свої середні бали за навички з колегами. Максимальний бал -12")

    if not df_full.empty:
        # Рахуємо статистику по ВСІХ менеджерах
        agg_dict = {"Дзвінок": "count"}
        if "Hard_Бал" in df_full.columns: agg_dict["Hard_Бал"] = "mean"
        if "Soft_Бал" in df_full.columns: agg_dict["Soft_Бал"] = "mean"

        rating_df = df_full.groupby("Менеджер").agg(agg_dict).reset_index()
        rating_df.rename(columns={"Дзвінок": "Дзвінків", "Hard_Бал": "Середній_Hard", "Soft_Бал": "Середній_Soft"}, inplace=True)

        # Сортуємо від кращого до гіршого за Hard Skills (основний показник)
        if "Середній_Hard" in rating_df.columns:
            rating_df = rating_df.sort_values(by="Середній_Hard", ascending=False)

        cols_to_style = [c for c in ['Середній_Hard', 'Середній_Soft'] if c in rating_df.columns]

        # Застосовуємо градієнт "Світлофор" (Red-Yellow-Green)
        styled_rating = rating_df.style.format({c: "{:.1f}" for c in cols_to_style}) \
            .background_gradient(cmap='RdYlGn', subset=cols_to_style)

        st.dataframe(styled_rating, use_container_width=True, hide_index=True)
    else:
        st.info("Немає даних для побудови рейтингу.")
