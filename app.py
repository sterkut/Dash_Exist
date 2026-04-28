import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="DealSense.ai | EXIST.UA", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; color: #1E293B; }
    h1, h2, h3 { font-weight: 800; color: #0F172A; }
    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; color: #DC2626; }
    [data-testid="stMetricLabel"] { font-weight: 600; color: #64748B; text-transform: uppercase; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { padding-top: 10px; padding-bottom: 10px; font-size: 1.2rem; font-weight: 600; }
    .card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .check-item { color: #166534; background: #F0FDF4; padding: 8px; border-radius: 6px; margin-bottom: 5px; display: flex; align-items: center; gap: 8px; font-weight: 500; }
    .cross-item { color: #991B1B; background: #FEF2F2; padding: 8px; border-radius: 6px; margin-bottom: 5px; display: flex; align-items: center; gap: 8px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- 2. ЗАВАНТАЖЕННЯ ДАНИХ ---
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
            
        cols_to_fix = ['Крос_сел', 'Екосистема', 'Hard_Бал', 'Робота_з_запереченнями_Бал']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

if df.empty:
    st.error("❌ Не вдалося знайти дані. Перевірте Google Sheets або наявність локального файлу.")
    st.stop()

# --- 3. САЙДБАР ---
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px; border-bottom: 2px solid #f0f2f6; margin-bottom: 15px;">
            <h1 style="color: #1E3A8A; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 28px; letter-spacing: 1px; margin-bottom: 0;">
                DealSense<span style="color: #3B82F6;">.ai</span>
            </h1>
            <p style="color: #6B7280; font-size: 12px; font-weight: 500; text-transform: uppercase; margin-top: 5px;">
                ШІ-аудит відділу продажів
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🔄 Оновити базу даних", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("### 🎛 Фільтри")
    managers_list = sorted(df["Менеджер"].dropna().unique()) if "Менеджер" in df.columns else []
    selected_managers = st.multiselect("👤 Менеджери", managers_list, default=managers_list)
    
    df_step1 = df[df["Менеджер"].isin(selected_managers)] if selected_managers else df
    
    intents_list = sorted(df_step1["Готовність"].dropna().unique()) if "Готовність" in df_step1.columns else []
    selected_intents = st.multiselect("🎯 Готовність", intents_list, default=intents_list)

    df_step2 = df_step1[df_step1["Готовність"].isin(selected_intents)] if selected_intents else df_step1

    root_list = sorted(df_step2["ROOT_PROBLEM"].dropna().unique()) if "ROOT_PROBLEM" in df_step2.columns else []
    selected_roots = st.multiselect("🚨 Причина втрати", root_list, default=root_list)

    df_filtered = df_step2[df_step2["ROOT_PROBLEM"].isin(selected_roots)] if selected_roots else df_step2

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 💰 Фінансові параметри")
    avg_check = st.number_input("Середній чек (грн)", value=1500, step=100)
    
    st.markdown("#### Параметри Крос-селу")
    avg_cross_check = st.number_input("Середній чек доп. товару (грн)", value=150, step=10)
    cross_conv = st.slider("Конверсія у доп. продаж (%)", 0, 100, 10)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    if "Тривалість_хв" in df_filtered.columns:
        total_min = df_filtered["Тривалість_хв"].sum()
        st.metric("⏱ Опрацьовано аудіо", f"{total_min:,.1f} хв")

# Розрахунок математики втрат
intent_weights = {"High": 1.0, "Medium": 0.5, "Low": 0.0}
df_filtered['Потенціал_грн'] = df_filtered['Готовність'].map(intent_weights).fillna(0) * avg_check
df_filtered['Втрачено_Головна'] = df_filtered.apply(lambda x: x['Потенціал_грн'] if x['ROOT_PROBLEM'] != 'Немає' else 0, axis=1)
df_filtered['Втрачено_Крос'] = df_filtered.apply(lambda x: (avg_cross_check * (cross_conv/100)) if (x['ROOT_PROBLEM'] == 'Немає' and x['Спроба_Крос_Селу'] == 'Ні') else 0, axis=1)
df_filtered['Втрачено_грн'] = df_filtered['Втрачено_Головна'] + df_filtered['Втрачено_Крос']

# --- 4. ВКЛАДКИ ---
tab_ceo, tab_history, tab_trends, tab_coach = st.tabs(["💰 Фінанси (CEO)", "🎧 Історія та розбір", "📈 Тренди", "🎓 Матриця навичок"])

# ==========================================
# ПАНЕЛЬ 1: CEO (Гроші та Ефективність)
# ==========================================
with tab_ceo:
    st.markdown("""
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <h3 style="margin-top: 0; margin-bottom: 20px; font-size: 20px; border-bottom: 2px solid #F1F5F9; padding-bottom: 10px;">📊 Ключові показники втрат та ефективності</h3>
        </div>
    """, unsafe_allow_html=True)

    total_lost_main = df_filtered["Втрачено_Головна"].sum()
    total_lost_cross = df_filtered["Втрачено_Крос"].sum()
    total_lost_all = df_filtered["Втрачено_грн"].sum()
    
    hot_med_deals = df_filtered[df_filtered['Готовність'].isin(['High', 'Medium'])]
    hot_med_total = len(hot_med_deals)
    hot_med_lost = len(hot_med_deals[hot_med_deals['ROOT_PROBLEM'] != 'Немає'])
    hot_loss_rate = (hot_med_lost / hot_med_total * 100) if hot_med_total > 0 else 0

    success_deals = df_filtered[df_filtered['ROOT_PROBLEM'] == 'Немає']
    missed_cross_count = len(success_deals[success_deals['Спроба_Крос_Селу'] == 'Ні'])
    missed_cross_rate = (missed_cross_count / len(success_deals) * 100) if len(success_deals) > 0 else 0
    
    if 'Екосистема' in success_deals.columns:
        eco_scores = pd.to_numeric(success_deals['Екосистема'], errors='coerce').fillna(0)
        missed_eco_count = len(success_deals[eco_scores == 0])
    else:
        missed_eco_count = 0
    missed_eco_rate = (missed_eco_count / len(success_deals) * 100) if len(success_deals) > 0 else 0

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("🔥 ЗАГАЛЬНІ ВТРАТИ", f"{total_lost_all:,.0f} ₴")
    m_col2.metric("💰 Втрати (Основні)", f"{total_lost_main:,.0f} ₴")
    m_col3.metric("📦 Втрати (Крос-сел)", f"{total_lost_cross:,.0f} ₴")

    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

    p_col1, p_col2, p_col3 = st.columns(3)
    p_col1.metric("📉 % втрат ГАРЯЧИХ", f"{hot_loss_rate:.0f}%", help="Відсоток клієнтів з High/Medium готовністю, які нічого не купили")
    p_col2.metric("🛒 % без CROSS-SELL", f"{missed_cross_rate:.0f}%", help="Відсоток успішних угод, де менеджер не запропонував супутній товар")
    p_col3.metric("🌐 % без ЕКОСИСТЕМИ", f"{missed_eco_rate:.0f}%", help="Відсоток успішних угод, де не було пропозиції сервісів екосистеми")

    st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
    
    row1_col1, row1_col2 = st.columns([1.2, 1])
    
    with row1_col1:
        st.markdown("### 🎯 Причини втрат (включаючи недоотриманий крос-сел)")
        reasons_data = df_filtered[df_filtered['Втрачено_грн'] > 0].groupby('ROOT_PROBLEM')['Втрачено_грн'].sum().reset_index()
        if total_lost_cross > 0:
            reasons_data.loc[reasons_data['ROOT_PROBLEM'] == 'Немає', 'ROOT_PROBLEM'] = 'Відсутність Крос-селу'
        reasons_data = reasons_data.sort_values(by='Втрачено_грн', ascending=False).head(5)
        
        if not reasons_data.empty:
            fig_reasons = px.bar(reasons_data, x='Втрачено_грн', y='ROOT_PROBLEM', orientation='h', 
                                 color='Втрачено_грн', color_continuous_scale='Reds',
                                 labels={'Втрачено_грн': 'Втрати в гривнях', 'ROOT_PROBLEM': 'Причина'})
            fig_reasons.update_layout(showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_reasons, use_container_width=True)
        else:
            st.success("Втрат немає!")

    with row1_col2:
        st.markdown("### 🚨 Рейтинг фінансових втрат")
        manager_loss = df_filtered.groupby("Менеджер")['Втрачено_грн'].sum().reset_index().sort_values("Втрачено_грн", ascending=False)
        styled_loss = manager_loss.style.format({'Втрачено_грн': '{:,.0f}'}) \
            .background_gradient(cmap='Reds', subset=['Втрачено_грн'])
        st.dataframe(styled_loss, use_container_width=True, hide_index=True)

    # 🟢 ПОВЕРНУТИЙ БЛОК: Деталізація втрат та інсайти для СЕО
    st.markdown("<br>### 🔎 Деталізація втрат та інсайти для СЕО", unsafe_allow_html=True)
    
    # Фільтруємо всі дзвінки, де ROOT_PROBLEM не дорівнює "Немає" (реальні втрати лідів)
    lost_deals_df = df_filtered[df_filtered['ROOT_PROBLEM'] != 'Немає'].copy()
    
    if not lost_deals_df.empty:
        cols_to_show = ['Менеджер', 'Дзвінок', 'Готовність', 'ROOT_PROBLEM', 'Втрачено_грн', 'Інсайт_для_CEO']
        st.dataframe(lost_deals_df[cols_to_show], use_container_width=True, hide_index=True)
    else:
        st.success("Втрат не виявлено! Всі угоди успішні.")


# ==========================================
# ПАНЕЛЬ 2: ІСТОРІЯ ТА КАРТКА ДЗВІНКА
# ==========================================
with tab_history:
    st.markdown("### 🎧 Історія дзвінків")
    st.write("Виділіть рядок у таблиці нижче, щоб переглянути детальний аналіз.")
    
    cols_to_list = ["Дата", "Менеджер", "Дзвінок", "ROOT_PROBLEM", "Hard_Бал", "Готовність"]
    
    try:
        # Інтерактивна таблиця (запрацює після 'pip install --upgrade streamlit')
        event = st.dataframe(
            df_filtered[cols_to_list],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single"
        )
        selected_indices = event.selection.rows
    except:
        # Резервний варіант для старих версій Streamlit
        st.warning("⚠️ Оновіть Streamlit (`pip install --upgrade streamlit`), щоб таблиця стала клікабельною. Поки що використовуємо класичний вибір:")
        display_names = df_filtered.apply(lambda r: f"{r.get('Дата','')} | {r.get('Менеджер','')} | {r['Дзвінок']}", axis=1).tolist()
        file_mapping = dict(zip(display_names, df_filtered['Дзвінок']))
        selected_display = st.selectbox("Оберіть файл дзвінка:", [""] + display_names)
        selected_indices = [df_filtered.index[df_filtered['Дзвінок'] == file_mapping[selected_display]].tolist()[0]] if selected_display else []

    if selected_indices:
        if isinstance(selected_indices[0], int) and selected_indices[0] < len(df_filtered):
             row = df_filtered.iloc[selected_indices[0]]
        else:
             row = df_filtered.loc[selected_indices[0]]

        st.markdown("---")
        st.subheader(f"📄 Картка розмови: {row.get('Менеджер', 'Невідомо')}")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            score = int(row.get('Hard_Бал', 0))
            color = '#16A34A' if score >= 10 else '#F59E0B' if score >= 6 else '#DC2626'
            bg_color = '#BBF7D0' if score >= 10 else '#FDE68A' if score >= 6 else '#FECACA'
            text = 'Відмінно' if score >= 10 else 'Задовільно' if score >= 6 else 'Потребує уваги'
            
            st.markdown(f"""
                <div class="card" style="text-align: center;">
                    <p style="color: #64748B; margin-bottom: 5px; font-weight: 600;">HARD SKILLS (ОЦІНКА)</p>
                    <h1 style="font-size: 54px; color: #0F172A; margin: 0;">{score}<span style="font-size: 20px; color: #64748B;">/12</span></h1>
                    <div style="background: {bg_color}; color: {color}; padding: 5px; border-radius: 20px; font-weight: bold; display: inline-block; padding: 5px 15px; margin-top: 10px;">
                        {text}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("**🛡 Робота з запереченнями**")
                if row.get("Заперечення_Були", "Ні") == "Так":
                    obj_score = row.get('Робота_з_запереченнями_Бал', 0)
                    st.markdown(f"<div style='color: {'#16A34A' if obj_score==2 else '#DC2626'}; font-weight: bold;'>Оцінка відпрацювання: {obj_score}/2</div>", unsafe_allow_html=True)
                    st.write(f"_{row.get('Заперечення_Деталі', 'Деталі відсутні')}_")
                else:
                    st.success("✅ Заперечень не було")

        with c2:
            sc1, sc2 = st.columns(2)
            with sc1:
                st.write("👍 **Сильні сторони**")
                items = str(row.get('Сильні_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean_item = item.strip().replace("- ", "").replace("* ", "")
                    if clean_item and clean_item.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='check-item'>✓ {clean_item}</div>", unsafe_allow_html=True)
                        has_items = True
                if not has_items: st.info("Не виявлено")
            
            with sc2:
                st.write("🚩 **Слабкі сторони**")
                items = str(row.get('Слабкі_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean_item = item.strip().replace("- ", "").replace("* ", "")
                    if clean_item and clean_item.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='cross-item'>✕ {clean_item}</div>", unsafe_allow_html=True)
                        has_items = True
                if not has_items: st.success("Не виявлено")

        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"**💡 Інсайт для бізнесу:** {row.get('Інсайт_для_CEO', 'Немає інсайтів')}")
        
        lost = row.get('Втрачено_грн', 0)
        if lost > 0:
            st.error(f"💸 **Втрачений прибуток з цього ліда:** {lost:,.0f} ₴ (Причина: {row.get('ROOT_PROBLEM')})")

# ==========================================
# ПАНЕЛЬ 3: ТРЕНДИ (ДИНАМІКА)
# ==========================================
with tab_trends:
    st.markdown("### 📈 Динаміка навичок у часі")
    
    if "Дата" in df_filtered.columns and not df_filtered.empty:
        trend_df = df_filtered.groupby(['Дата', 'Менеджер']).agg({
            'Крос_сел': 'mean',
            'Екосистема': 'mean',
            'Hard_Бал': 'mean'
        }).reset_index()
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_cross = px.line(trend_df, x='Дата', y='Крос_сел', color='Менеджер', markers=True,
                               title="Динаміка спроб Крос-селу (0-2 бали)", color_discrete_sequence=px.colors.qualitative.Set1)
            fig_cross.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig_cross, use_container_width=True)
            
        with col_t2:
            fig_eco = px.line(trend_df, x='Дата', y='Екосистема', color='Менеджер', markers=True,
                             title="Пропозиція Екосистеми (0-2 бали)", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_eco.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig_eco, use_container_width=True)
            
        st.markdown("---")
        fig_total = px.area(trend_df, x='Дата', y='Hard_Бал', color='Менеджер', 
                           title="Загальний тренд якості розмов (Hard Бал)", color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig_total, use_container_width=True)
    else:
        st.info("Потрібно більше даних з датами для відображення трендів.")

# ==========================================
# ПАНЕЛЬ 4: COACHING (МАТРИЦЯ НАВИЧОК)
# ==========================================
with tab_coach:
    st.markdown("### 🎓 Детальна матриця навичок")
    
    skill_cols = ['Привітання', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття', 'Привітність', 'Емпатія']
    existing_skills = [c for c in skill_cols if c in df_filtered.columns]
    
    agg_dict = {"Дзвінків": pd.NamedAgg(column="Дзвінок", aggfunc="count")}
    if "Hard_Бал" in df_filtered.columns: agg_dict["Сер_Hard"] = pd.NamedAgg(column="Hard_Бал", aggfunc="mean")
    
    for skill in existing_skills:
        agg_dict[skill] = pd.NamedAgg(column=skill, aggfunc="mean")
        
    coach_stats = df_filtered.groupby("Менеджер").agg(**agg_dict).reset_index()
    if "Сер_Hard" in coach_stats.columns:
        coach_stats = coach_stats.sort_values(by="Сер_Hard", ascending=False)
        
    styled_coach = coach_stats.style.format(precision=1)\
        .background_gradient(cmap='Blues', subset=existing_skills, vmin=0, vmax=2)\
        .background_gradient(cmap='Greens', subset=['Сер_Hard']) if 'Сер_Hard' in coach_stats.columns else coach_stats
        
    st.dataframe(styled_coach, use_container_width=True, hide_index=True)
