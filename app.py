import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="EXIST.UA | Revenue Recovery", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; color: #1E293B; }
    h1, h2, h3 { font-weight: 800; color: #0F172A; }
    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; color: #DC2626; }
    [data-testid="stMetricLabel"] { font-weight: 600; color: #64748B; text-transform: uppercase; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { padding-top: 10px; padding-bottom: 10px; font-size: 1.2rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 2. РОЗУМНЕ ЗАВАНТАЖЕННЯ ДАНИХ (ГІТХАБ + ЛОКАЛЬНО) ---
@st.cache_data(ttl=60) # Кешуємо на хвилину, щоб не грузити базу постійно
def load_data():
    df = pd.DataFrame()
    
    # СПРОБА 1: Google Sheets (Для GitHub)
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet="EXIST_DATA_BASE")
    except Exception:
        pass
    
    # СПРОБА 2: Локальний диск D (Для ПК)
    if df.empty:
        try:
            df = pd.read_excel(r"D:\виход\REPORT_EXIST_CEO.xlsx")
        except Exception:
            pass
            
    # СПРОБА 3: Локальний файл поруч зі скриптом
    if df.empty:
        try:
            df = pd.read_excel("REPORT_EXIST_CEO.xlsx")
        except Exception:
            pass

    if not df.empty:
        # Стандартизація колонок, якщо Excel або Google їх десь змінив
        rename_dict = {}
        for col in df.columns:
            if "OOT" in col and "PROBLEM" in col: rename_dict[col] = "ROOT_PROBLEM"
            if "Готовність" in col: rename_dict[col] = "Готовність"
            if "Крос_Сел" in col and "проба" in col: rename_dict[col] = "Спроба_Крос_Селу"
            if "Дотиснув" in col: rename_dict[col] = "Зафіксував_Наступний_Крок"
            
        df.rename(columns=rename_dict, inplace=True)
    return df

df = load_data()

if df.empty:
    st.error("❌ Не вдалося знайти дані. Перевірте Google Sheets або наявність файлу 'REPORT_EXIST_CEO.xlsx'.")
    st.stop()

# --- 3. САЙДБАР: ФІЛЬТРИ ТА ГРОШІ ---
with st.sidebar:
    st.markdown("### 🎛 Фільтри")
    
    # Фільтр Менеджерів
    managers_list = sorted(df["Менеджер"].dropna().unique()) if "Менеджер" in df.columns else []
    selected_managers = st.multiselect("👤 Менеджери", managers_list, default=managers_list)
    
    # Фільтр Готовності
    intents_list = sorted(df["Готовність"].dropna().unique()) if "Готовність" in df.columns else []
    selected_intents = st.multiselect("🎯 Готовність до покупки", intents_list, default=intents_list)

    # Фільтр ROOT PROBLEM (Нова хотілка)
    root_list = sorted(df["ROOT_PROBLEM"].dropna().unique()) if "ROOT_PROBLEM" in df.columns else []
    selected_roots = st.multiselect("🚨 Причина втрати", root_list, default=root_list)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 💰 Фінансові параметри")
    avg_check = st.number_input("Середній чек (грн)", value=1500, step=100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Вага потенціалу:")
    st.write("🔥 High: 100%")
    st.write("⚡ Medium: 50%")
    st.write("*(Low готовність не враховується у втратах)*")

# Застосовуємо всі фільтри
df_filtered = df[
    (df["Менеджер"].isin(selected_managers)) & 
    (df["Готовність"].isin(selected_intents)) &
    (df["ROOT_PROBLEM"].isin(selected_roots))
].copy()

if df_filtered.empty:
    st.warning("⚠️ Немає даних за вибраними фільтрами.")
    st.stop()

# --- 4. МАТЕМАТИКА ВТРАТ ---
intent_weights = {"High": 1.0, "Medium": 0.5, "Low": 0.0}
df_filtered['Потенціал_грн'] = df_filtered['Готовність'].map(intent_weights).fillna(0) * avg_check
df_filtered['Втрачено_грн'] = df_filtered.apply(lambda x: x['Потенціал_грн'] if x['ROOT_PROBLEM'] != 'Немає' else 0, axis=1)

# --- 5. ЗАГОЛОВОК І ВКЛАДКИ ---
st.title("Аналітика Відділу Продажів (CEO View)")
tab_ceo, tab_coach, tab_call = st.tabs(["💰 CEO: Втрачений прибуток", "🎓 Навчання: Розбір навичок", "🎧 Картка дзвінка"])

# ==========================================
# ПАНЕЛЬ 1: CEO (Гроші, Воронка, Втрати)
# ==========================================
with tab_ceo:
    col1, col2, col3, col4 = st.columns(4)
    
    total_calls = len(df_filtered)
    total_lost_potential = df_filtered["Втрачено_грн"].sum()
    
    hot_total = len(df_filtered[df_filtered['Готовність'] == 'High'])
    hot_lost = len(df_filtered[(df_filtered['Готовність'] == 'High') & (df_filtered['ROOT_PROBLEM'] != 'Немає')])
    hot_loss_rate = (hot_lost / hot_total * 100) if hot_total > 0 else 0

    no_closing_count = len(df_filtered[df_filtered.get("Зафіксував_Наступний_Крок", "Ні") == "Ні"])
    no_closing_rate = (no_closing_count / total_calls * 100) if total_calls > 0 else 0

    no_cross_count = len(df_filtered[df_filtered.get("Спроба_Крос_Селу", "Ні") == "Ні"])
    no_cross_rate = (no_cross_count / total_calls * 100) if total_calls > 0 else 0

    col1.metric("Втрачено (грн)", f"{total_lost_potential:,.0f} ₴")
    col2.metric("% втрат ГАРЯЧИХ", f"{hot_loss_rate:.0f}%")
    col3.metric("% без ЗАКРИТТЯ", f"{no_closing_rate:.0f}%")
    col4.metric("% без CROSS-SELL", f"{no_cross_rate:.0f}%")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    row1_col1, row1_col2 = st.columns([1.2, 1])
    
    with row1_col1:
        st.markdown("### 🎯 ТОП-3 причини втрат (в грошах)")
        reasons_data = df_filtered[df_filtered['ROOT_PROBLEM'] != 'Немає'].groupby('ROOT_PROBLEM')['Втрачено_грн'].sum().reset_index().sort_values(by='Втрачено_грн', ascending=False).head(3)
        if not reasons_data.empty:
            fig_reasons = px.bar(reasons_data, x='Втрачено_грн', y='ROOT_PROBLEM', orientation='h', 
                                 color='Втрачено_грн', color_continuous_scale='Reds',
                                 labels={'Втрачено_грн': 'Втрати в гривнях', 'ROOT_PROBLEM': 'Причина'})
            fig_reasons.update_layout(showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_reasons, use_container_width=True)
        else:
            st.success("Втрат немає!")

    with row1_col2:
        st.markdown("### 🚨 Хто зливає бюджет")
        manager_loss = df_filtered.groupby("Менеджер")['Втрачено_грн'].sum().reset_index().sort_values("Втрачено_грн", ascending=False)
        st.dataframe(
            manager_loss.style.background_gradient(cmap='Reds', subset=['Втрачено_грн']),
            use_container_width=True, hide_index=True
        )

    # Оновлена деталізація: показуємо і High, і Medium
    st.markdown("<br>### 🔎 Деталі всіх втрачених угод (High та Medium)", unsafe_allow_html=True)
    all_lost_details = df_filtered[df_filtered['Втрачено_грн'] > 0]
    
    if not all_lost_details.empty:
        cols_to_show = [c for c in ['Менеджер', 'Дзвінок', 'Готовність', 'ROOT_PROBLEM', 'Втрачено_грн', 'Інсайт_для_CEO'] if c in all_lost_details.columns]
        st.dataframe(all_lost_details[cols_to_show], use_container_width=True, hide_index=True)
    else:
        st.success("Втрат не виявлено! Всі угоди успішні.")

# ==========================================
# ПАНЕЛЬ 2: MANAGER COACHING
# ==========================================
with tab_coach:
    st.markdown("### 📊 Детальний розбір навичок")
    
    skill_cols = ['Привітання', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття', 'Привітність', 'Активне_Слухання', 'Впевненість_Мовлення', 'Емпатія']
    existing_skills = [c for c in skill_cols if c in df_filtered.columns]
    
    agg_dict = {"Дзвінків": pd.NamedAgg(column="Дзвінок", aggfunc="count")}
    if "Hard_Бал" in df_filtered.columns: agg_dict["Середній_Hard"] = pd.NamedAgg(column="Hard_Бал", aggfunc="mean")
    if "Soft_Бал" in df_filtered.columns: agg_dict["Середній_Soft"] = pd.NamedAgg(column="Soft_Бал", aggfunc="mean")
    
    for skill in existing_skills:
        agg_dict[skill] = pd.NamedAgg(column=skill, aggfunc="mean")
        
    coach_stats = df_filtered.groupby("Менеджер").agg(**agg_dict).reset_index()
    
    cols_to_round = coach_stats.columns.drop(['Менеджер', 'Дзвінків'])
    coach_stats[cols_to_round] = coach_stats[cols_to_round].round(1)
    
    col_c1, col_c2 = st.columns([2, 1.2])
    
    with col_c1:
        gradient_cols_main = [c for c in ['Середній_Hard', 'Середній_Soft'] if c in coach_stats.columns]
        gradient_cols_skills = [c for c in existing_skills if c in coach_stats.columns]
        
        st.dataframe(
            coach_stats.style.background_gradient(cmap='Greens', subset=gradient_cols_main)
                         .background_gradient(cmap='Blues', subset=gradient_cols_skills),
            use_container_width=True, hide_index=True
        )
        
    with col_c2:
        st.markdown("**Рекомендації ШІ для вибраних менеджерів:**")
        if "Порада_для_менеджера" in df_filtered.columns:
            for mgr in selected_managers:
                mgr_skills_df = df_filtered[df_filtered["Менеджер"] == mgr]
                if not mgr_skills_df.empty:
                    with st.expander(f"Поради для: {mgr}", expanded=False):
                        for _, row in mgr_skills_df.iterrows():
                            st.write(f"**Файл:** {row['Дзвінок']} (Готовність: {row.get('Готовність', 'N/A')})")
                            st.info(row['Порада_для_менеджера'])
                            st.write("---")
        else:
            st.write("Поради не знайдені в таблиці.")
                    
    st.markdown("<br>### Матриця компетенцій (Raw Data)", unsafe_allow_html=True)
    raw_cols = ['Менеджер', 'Дзвінок'] + existing_skills
    st.dataframe(
        df_filtered[raw_cols].style.background_gradient(cmap='Blues', subset=existing_skills),
        use_container_width=True, hide_index=True
    )

# ==========================================
# ПАНЕЛЬ 3: КАРТКА КОНКРЕТНОГО ДЗВІНКА
# ==========================================
with tab_call:
    st.markdown("### 🔎 Детальний розбір розмови")

    if 'Дзвінок' in df_filtered.columns and not df_filtered.empty:
        selected_file = st.selectbox("Оберіть файл дзвінка для розбору:", df_filtered['Дзвінок'].unique())

        if selected_file:
            row = df_filtered[df_filtered['Дзвінок'] == selected_file].iloc[0]

            # 1. МАТЕМАТИКА БАЛІВ (12 балів)
            score_12 = int(row.get('Hard_Бал', 0))
            
            # Логіка кольорів кільця
            if score_12 >= 10:
                score_color = "#16A34A" # Зелений
                score_text = "Відмінно"
            elif score_12 >= 6:
                score_color = "#F59E0B" # Жовто-помаранчевий (як на скріні)
                score_text = "Задовільно"
            else:
                score_color = "#DC2626" # Червоний
                score_text = "Погано"

            # 2. РАХУЄМО ЛАЙКИ / ДИЗЛАЙКИ (Хард-скіли)
            hard_skill_keys = ['Привітання', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття']
            likes, norms, dislikes = 0, 0, 0
            
            for key in hard_skill_keys:
                val = row.get(key, 0)
                if val == 2: likes += 1
                elif val == 1: norms += 1
                else: dislikes += 1

            # Градус для кругової діаграми (CSS)
            deg = (score_12 / 12) * 360

            # 3. ВЕРСТКА ВЕРХНЬОГО БЛОКУ (КІЛЬЦЕ + БЛОКИ ЕМОДЗІ)
            st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 40px; flex-wrap: wrap;">
                
                <div style="text-align: center; min-width: 130px;">
                    <div style="width: 120px; height: 120px; border-radius: 50%; background: conic-gradient({score_color} {deg}deg, #E2E8F0 0deg); display: flex; justify-content: center; align-items: center; margin: 0 auto 12px auto;">
                        <div style="width: 95px; height: 95px; border-radius: 50%; background: white; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                            <span style="font-size: 32px; font-weight: 800; color: #0F172A; line-height: 1;">{score_12}</span>
                            <span style="font-size: 13px; color: #64748B; font-weight: 600;">з 12</span>
                        </div>
                    </div>
                    <span style="background: {score_color}15; color: {score_color}; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;">{score_text}</span>
                </div>

                <div style="flex: 1;">
                    <h3 style="margin: 0 0 15px 0; color: #0F172A; font-size: 18px;">📊 Аналіз навичок продажу</h3>
                    <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                        <div style="flex: 1; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 15px; text-align: center; min-width: 120px;">
                            <div style="font-size: 24px; margin-bottom: 5px;">👍</div>
                            <div style="font-size: 20px; font-weight: 800; color: #166534;">{likes}</div>
                            <div style="font-size: 13px; color: #15803D; font-weight: 600;">Сильні сторони</div>
                        </div>
                        <div style="flex: 1; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 15px; text-align: center; min-width: 120px;">
                            <div style="font-size: 24px; margin-bottom: 5px;">😐</div>
                            <div style="font-size: 20px; font-weight: 800; color: #B45309;">{norms}</div>
                            <div style="font-size: 13px; color: #B45309; font-weight: 600;">Зона уваги</div>
                        </div>
                        <div style="flex: 1; background: #FEF2F2; border: 1px solid #FECACA; border-radius: 10px; padding: 15px; text-align: center; min-width: 120px;">
                            <div style="font-size: 24px; margin-bottom: 5px;">🚩</div>
                            <div style="font-size: 20px; font-weight: 800; color: #991B1B;">{dislikes}</div>
                            <div style="font-size: 13px; color: #B91C1C; font-weight: 600;">Зони росту</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 4. РЕЗУЛЬТАТ РОЗМОВИ (Успіх / Втрата)
            is_success = row.get("ROOT_PROBLEM", "Немає") == "Немає"
            result_bg = "#F0FDF4" if is_success else "#FEF2F2"
            result_border = "#BBF7D0" if is_success else "#FECACA"
            result_title = "Угода успішна / Дотиснуто" if is_success else "Угоду втрачено"
            result_desc = "Менеджер довів клієнта до цільової дії." if is_success else f"Причина втрати ліда: <b>{row.get('ROOT_PROBLEM', 'Невідомо')}</b>."

            st.markdown(f"""
            <div style="background: {result_bg}; border: 1px solid {result_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                <div style="display: flex; gap: 15px; align-items: center;">
                    <div style="font-size: 24px;">{'✅' if is_success else '❌'}</div>
                    <div>
                        <h4 style="margin: 0 0 4px 0; color: #111827; font-size: 16px;">Результат розмови: {result_title}</h4>
                        <p style="margin: 0; color: #374151; font-size: 14px;">{result_desc} <br> Готовність: <b>{row.get('Готовність', 'N/A')}</b> | Зафіксовано крок: <b>{row.get('Зафіксував_Наступний_Крок', 'Ні')}</b></p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 5. ТОН РОЗМОВИ (Беремо з колонки нейронки)
            tone_text = row.get("Тон_Розмови", "Тон розмови не проаналізовано.")
            st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 8px;">
                    <div style="font-size: 20px;">🎙️</div>
                    <h4 style="margin: 0; color: #0F172A; font-size: 16px;">Тон розмови</h4>
                </div>
                <p style="margin: 0; color: #475569; font-size: 14px; line-height: 1.5; padding-left: 30px;">{tone_text}</p>
            </div>
            """, unsafe_allow_html=True)

            # 6. ІНФО ПРО МЕНЕДЖЕРА
            st.markdown(f"""
            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <div style="flex: 1; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; background: #F8FAFC;">
                    <p style="margin: 0 0 4px 0; color: #64748B; font-size: 12px; text-transform: uppercase;">Менеджер</p>
                    <h4 style="margin: 0; color: #0F172A; font-size: 16px;">👤 {row.get('Менеджер', 'N/A')}</h4>
                </div>
                <div style="flex: 2; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; background: #F8FAFC;">
                    <p style="margin: 0 0 4px 0; color: #64748B; font-size: 12px; text-transform: uppercase;">Файл дзвінка (Ідентифікатор)</p>
                    <h4 style="margin: 0; color: #0F172A; font-size: 14px; word-break: break-all;">📄 {row.get('Дзвінок', 'N/A')}</h4>
                </div>
            </div>

            <div style="background: #FFFBEB; border: 1px solid #FEF3C7; border-radius: 12px; padding: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #92400E; font-size: 16px;">💡 Аналітика для бізнесу (Інсайт)</h4>
                <p style="margin: 0; color: #92400E; line-height: 1.5;">{row.get('Інсайт_для_CEO', 'Немає інсайтів')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Немає даних для відображення.")
