import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="allogarage.ai | EXIST.UA", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Преміальний темний дизайн */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 95%; }
    .stApp { background-color: #0A0F1C; color: #E2E8F0; }
    h1, h2, h3 { font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px; }
    
    /* Світіння метрик */
    [data-testid="stMetricValue"] { font-size: 2.5rem; font-weight: 800; color: #FFFFFF; text-shadow: 0 0 15px rgba(255, 255, 255, 0.15); }
    [data-testid="stMetricLabel"] { font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Вкладки (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; border-bottom: none; }
    .stTabs [data-baseweb="tab"] { padding: 12px 20px; font-size: 1.1rem; font-weight: 600; border-radius: 30px; color: #94A3B8; background-color: #111827; border: 1px solid rgba(255, 255, 255, 0.05); margin-right: 5px; }
    .stTabs [aria-selected="true"] { background-color: #8B5CF6 !important; color: #FFFFFF !important; border-color: #8B5CF6 !important; box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
    
    /* Скляні картки (Glassmorphism) */
    .card { background: linear-gradient(145deg, #111827, #0F172A); border-radius: 20px; padding: 24px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05); transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .card:hover { transform: translateY(-2px); box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1); }
    
    /* Значки результатів */
    .check-item { color: #A3E635; background: rgba(163, 230, 53, 0.1); padding: 8px 12px; border-radius: 8px; margin-bottom: 6px; font-weight: 600; border: 1px solid rgba(163, 230, 53, 0.2); }
    .cross-item { color: #F87171; background: rgba(248, 113, 113, 0.1); padding: 8px 12px; border-radius: 8px; margin-bottom: 6px; font-weight: 600; border: 1px solid rgba(248, 113, 113, 0.2); }
</style>
""", unsafe_allow_html=True)

# --- 2. ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data(ttl=600)
def load_data():
    df = pd.DataFrame()
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        url = "https://docs.google.com/spreadsheets/d/1a1JlK5D4MoRjiHBLOuUN9ScVkKzGPLE6zL1LvXj3Ezw/edit?gid=398555031#gid=398555031"
        df = conn.read(spreadsheet=url)
    except: pass
    
    if df.empty:
        try: df = pd.read_excel(r"D:\виход\REPORT_EXIST_CEO.xlsx")
        except: pass

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if "Дата" in df.columns:
            df["Дата"] = pd.to_datetime(df["Дата"], errors='coerce').dt.date
            
        skill_cols = ['Привітання', 'Виявлення_Потреби', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття', 'Робота_з_запереченнями_Бал']
        for col in skill_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        if 'Hard_Бал' in df.columns: df['Hard_Бал'] = pd.to_numeric(df['Hard_Бал'], errors='coerce').fillna(0)
        if 'Soft_Бал' in df.columns: df['Soft_Бал'] = pd.to_numeric(df['Soft_Бал'], errors='coerce').fillna(0)
    return df

df = load_data()

if df.empty:
    st.error("❌ Не вдалося знайти дані. Перевірте Google Sheets або наявність локального файлу.")
    st.stop()

# --- 3. САЙДБАР ТА ФІЛЬТРИ ---
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px; border-bottom: 2px solid rgba(255,255,255,0.05); margin-bottom: 15px;">
            <h1 style="color: #FFFFFF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 28px; letter-spacing: 1px; margin-bottom: 0;">
                allogarage<span style="color: #8B5CF6;">.ai</span>
            </h1>
            <p style="color: #94A3B8; font-size: 12px; font-weight: 500; text-transform: uppercase; margin-top: 5px;">
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
    
    if "Тон_Розмови" in df.columns:
        show_complaints = st.checkbox("🚨 Показати тільки СКАРГИ", value=False)
        if show_complaints: st.info("⚠️ Інші фільтри заморожено. Показано всі скарги.")
    else: show_complaints = False

    managers_list = sorted(df["Менеджер"].dropna().unique()) if "Менеджер" in df.columns else []
    selected_managers = st.multiselect("👤 Менеджери", managers_list, default=managers_list, disabled=show_complaints)
    df_step1 = df[df["Менеджер"].isin(selected_managers)] if selected_managers else df
    
    if "Тип_Дзвінка" in df_step1.columns:
        types_list = sorted(df_step1["Тип_Дзвінка"].dropna().unique())
        default_types = [t for t in types_list if str(t) != "Холодний"]
        selected_types = st.multiselect("📞 Тип дзвінка", types_list, default=default_types, disabled=show_complaints)
        df_step1 = df_step1[df_step1["Тип_Дзвінка"].isin(selected_types)] if selected_types else df_step1

    if "Вх_Вих" in df_step1.columns:
        dir_list = sorted(df_step1["Вх_Вих"].dropna().unique())
        selected_dir = st.multiselect("📥 Напрямок", dir_list, default=dir_list, disabled=show_complaints)
        df_step1 = df_step1[df_step1["Вх_Вих"].isin(selected_dir)] if selected_dir else df_step1
    
    intents_list = sorted(df_step1["Готовність"].dropna().unique()) if "Готовність" in df_step1.columns else []
    default_intents = [i for i in intents_list if str(i) != "Low"]
    selected_intents = st.multiselect("🎯 Готовність", intents_list, default=default_intents, disabled=show_complaints)
    df_step2 = df_step1[df_step1["Готовність"].isin(selected_intents)] if selected_intents else df_step1

    if "Було_Перемикання" in df_step2.columns:
        transfers_list = sorted(df_step2["Було_Перемикання"].dropna().unique())
        selected_transfers = st.multiselect("🔁 Було перемикання?", transfers_list, default=transfers_list, disabled=show_complaints)
        df_step3 = df_step2[df_step2["Було_Перемикання"].isin(selected_transfers)] if selected_transfers else df_step2
    else: df_step3 = df_step2

    res_col = "Результат_Розмови_Заголовок" if "Результат_Розмови_Заголовок" in df_step3.columns else "Результат_Розмови"
    if res_col in df_step3.columns:
        res_list = sorted(df_step3[res_col].dropna().unique())
        selected_res = st.multiselect("📝 Результат розмови", res_list, default=res_list, disabled=show_complaints)
        df_step4 = df_step3[df_step3[res_col].isin(selected_res)] if selected_res else df_step3
    else: df_step4 = df_step3

    root_list = sorted(df_step4["ROOT_PROBLEM"].dropna().unique()) if "ROOT_PROBLEM" in df_step4.columns else []
    selected_roots = st.multiselect("🚨 Причина втрати", root_list, default=root_list, disabled=show_complaints)
    df_step5 = df_step4[df_step4["ROOT_PROBLEM"].isin(selected_roots)] if selected_roots else df_step4

    if show_complaints:
        df_filtered = df[df["Тон_Розмови"].astype(str).str.startswith("Скарга")]
    else:
        df_filtered = df_step5

    st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    st.markdown("### 💰 Фінансові параметри")
    avg_check = st.number_input("Середній чек (грн)", value=1500, step=100)
    
    st.markdown("#### Параметри Крос-селу")
    avg_cross_check = st.number_input("Середній чек доп. товару (грн)", value=150, step=10)
    cross_conv = st.slider("Конверсія у доп. продаж (%)", 0, 100, 10)
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    if "Тривалість_хв" in df_filtered.columns:
        total_min = df_filtered["Тривалість_хв"].sum()
        st.metric("⏱ Опрацьовано аудіо", f"{total_min:,.1f} хв")

# ==========================================
# 🛑 МАТЕМАТИКА
# ==========================================
intent_weights = {"High": 1.0, "Medium": 0.5, "Low": 0.0}
df_filtered['Потенціал_грн'] = df_filtered['Готовність'].map(intent_weights).fillna(0) * avg_check
df_filtered['Втрачено_Головна'] = df_filtered.apply(lambda x: x['Потенціал_грн'] if x['ROOT_PROBLEM'] != 'Немає' else 0, axis=1)
df_filtered['Втрачено_Крос'] = df_filtered.apply(lambda x: (avg_cross_check * (cross_conv/100)) if (x['ROOT_PROBLEM'] == 'Немає' and x['Спроба_Крос_Селу'] == 'Ні') else 0, axis=1)
df_filtered['Втрачено_грн'] = df_filtered['Втрачено_Головна'] + df_filtered['Втрачено_Крос']


# --- 4. ВКЛАДКИ ---
tab_home, tab_analytics, tab_ceo, tab_history, tab_trends, tab_coach = st.tabs([
    "🏠 Головна", "🎯 Дашборд Ефективності", "💰 Фінанси (CEO)", "🎧 Історія та розбір", "📈 Тренди", "🎓 Матриця навичок"
])

# ==========================================
# ПАНЕЛЬ 0: ГОЛОВНА
# ==========================================
with tab_home:
    total_calls = len(df_filtered)
    df_filtered['Hard_Бал'] = pd.to_numeric(df_filtered['Hard_Бал'], errors='coerce').fillna(0)
    
    avg_hard = df_filtered['Hard_Бал'].mean() if total_calls > 0 else 0
    closed_sales = (df_filtered['ROOT_PROBLEM'] == 'Немає').sum()
    conversion = (closed_sales / total_calls * 100) if total_calls > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📞 Всього дзвінків", f"{total_calls}")
    m2.metric("⭐ Сер. Бал", f"{avg_hard:.1f}/10")
    m3.metric("🎯 Конверсія", f"{conversion:.1f}%")
    m4.metric("💰 Продажів закрито", f"{closed_sales}")

    st.markdown("<br>", unsafe_allow_html=True)

    if total_calls > 0:
        mgr_summary = df_filtered.groupby("Менеджер").agg(
            Дзвінків=('Дзвінок', 'count'),
            Продажів=('ROOT_PROBLEM', lambda x: (x == 'Немає').sum()),
            Сер_Хард=('Hard_Бал', 'mean')
        ).reset_index()

        best_quality_mgr = mgr_summary.sort_values(by='Сер_Хард', ascending=False).iloc[0]
        st.info(f"✨ Менеджер **{best_quality_mgr['Менеджер']}** зараз лідер за якістю обслуговування (сер. бал: {best_quality_mgr['Сер_Хард']:.1f})")

        col_top, col_attention = st.columns(2)

        with col_top:
            st.markdown("### 🏆 Найкращі менеджери")
            top_mgrs = mgr_summary.sort_values(by=['Продажів', 'Сер_Хард'], ascending=False).head(3)
            top_mgr_names = top_mgrs['Менеджер'].tolist() 
            
            for _, mgr in top_mgrs.iterrows():
                st.markdown(f"""
                    <div style='background: rgba(34, 197, 94, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #22C55E; margin-bottom: 12px; border-top: 1px solid rgba(255,255,255,0.02);'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='font-weight: 800; color: #A3E635; font-size: 17px;'>{mgr['Менеджер']}</span>
                            <span style='background: rgba(34, 197, 94, 0.1); color: #A3E635; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold;'>Бал: {mgr['Сер_Хард']:.1f}</span>
                        </div>
                        <div style='margin-top: 5px; color: #94A3B8; font-size: 14px;'>
                            <b>{mgr['Продажів']}</b> продажів з <b>{mgr['Дзвінків']}</b> дзвінків
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with col_attention:
            st.markdown("### ⚠️ Потребують уваги")
            low_mgrs = mgr_summary[(mgr_summary['Сер_Хард'] < 4.0) & (~mgr_summary['Менеджер'].isin(top_mgr_names))].sort_values(by='Сер_Хард', ascending=True).head(3)
            
            if low_mgrs.empty:
                st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.02); padding: 30px; border-radius: 12px; border: 1px dashed rgba(255,255,255,0.1); text-align: center; margin-bottom: 12px;'>
                        <div style='font-size: 40px; margin-bottom: 10px;'>😊</div>
                        <h4 style='color: #E2E8F0; margin: 0;'>Всі менеджери працюють добре!</h4>
                    </div>
                """, unsafe_allow_html=True)
            else:
                for _, mgr in low_mgrs.iterrows():
                    st.markdown(f"""
                        <div style='background: rgba(245, 158, 11, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #F59E0B; margin-bottom: 12px;'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <span style='font-weight: 800; color: #FBBF24; font-size: 17px;'>{mgr['Менеджер']}</span>
                                <span style='background: rgba(245, 158, 11, 0.1); color: #FBBF24; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold;'>Бал: {mgr['Сер_Хард']:.1f}</span>
                            </div>
                            <div style='margin-top: 5px; color: #94A3B8; font-size: 14px;'>
                                Аналіз <b>{mgr['Дзвінків']}</b> розмов | Продажів: <b>{mgr['Продажів']}</b>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

# ==========================================
# ПАНЕЛЬ 1: АНАЛІТИКА
# ==========================================
with tab_analytics:
    st.markdown("### 📊 Аналітика результатів та конверсія")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        res_col = 'Результат_Розмови_Заголовок' if 'Результат_Розмови_Заголовок' in df_filtered.columns else 'Результат_Розмови'
        if res_col in df_filtered.columns:
            def clean_status(val):
                s = str(val).lower()
                if any(k in s for k in ['viber', 'вайбер', 'telegram']): return 'Перехід у месенджер'
                elif any(k in s for k in ['відмов', 'скасовано', 'немає']): return 'Відмова'
                elif any(k in s for k in ['думає', 'порадить', 'вирішує']): return 'Клієнт думає'
                elif any(k in s for k in ['передзвон', 'зв\'яз']): return 'Домовились передзвонити'
                elif any(k in s for k in ['сервіс', 'консультац', 'уточнення']): return 'Сервісний дзвінок'
                elif any(k in s for k in ['оформ', 'підтверд', 'роботі', 'змінено', 'продаж']): return 'Продаж закрито'
                else: return val

            cleaned_series = df_filtered[res_col].apply(clean_status)
            res_counts = cleaned_series.value_counts().reset_index()
            res_counts.columns = ['Результат', 'Кількість']
            
            fig_res = px.pie(res_counts, values='Кількість', names='Результат', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_res.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
            fig_res.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#0A0F1C', width=2)))
            st.plotly_chart(fig_res, use_container_width=True)
            
    with col_d2:
        total_calls = len(df_filtered)
        success_steps = (df_filtered['Зафіксував_Наступний_Крок'] == 'Так').sum() if 'Зафіксував_Наступний_Крок' in df_filtered.columns else 0
        closed_sales = (df_filtered['ROOT_PROBLEM'] == 'Немає').sum()
        
        conv_plot_df = pd.DataFrame({
            'Етап': ['Всі дзвінки', 'Успішні угоди', 'Продажів закрито'],
            'Кількість': [total_calls, success_steps, closed_sales]
        })
        
        fig_conv = px.bar(conv_plot_df, x='Етап', y='Кількість', text='Кількість', color='Етап', color_discrete_map={'Всі дзвінки': '#64748B', 'Успішні угоди': '#3B82F6', 'Продажів закрито': '#10B981'})
        fig_conv.update_layout(showlegend=False, height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8', yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'))
        fig_conv.update_traces(textposition='outside', textfont_color='#E2E8F0', marker_line_width=0)
        st.plotly_chart(fig_conv, use_container_width=True)

    st.markdown("---")
    st.markdown("### 👤 Показники менеджерів")
    if 'Менеджер' in df_filtered.columns:
        df_stats = df_filtered.copy()
        mgr_stats = df_stats.groupby("Менеджер").agg(
            Кількість_дзвінків=('Дзвінок', 'count'),
            Середній_Хард=('Hard_Бал', 'mean'),
            Продажів_шт=('ROOT_PROBLEM', lambda x: (x == 'Немає').sum()),
            Відмов_шт=('ROOT_PROBLEM', lambda x: (x != 'Немає').sum())
        ).reset_index()
        mgr_stats['Конверсія_%'] = (mgr_stats['Продажів_шт'] / mgr_stats['Кількість_дзвінків'] * 100).round(1)
        
        # Використовуємо звичайний dataframe для темної теми без конфліктних градієнтів
        st.dataframe(mgr_stats.style.format({'Середній_Хард': '{:.1f}', 'Конверсія_%': '{:.1f}%'}), use_container_width=True, hide_index=True)

# ==========================================
# ПАНЕЛЬ 2: CEO (Гроші)
# ==========================================
with tab_ceo:
    st.markdown("""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 25px; margin-bottom: 25px;">
            <h3 style="margin-top: 0; color: #E2E8F0; font-size: 20px;">📊 Ключові показники втрат</h3>
        </div>
    """, unsafe_allow_html=True)

    total_lost_main = df_filtered["Втрачено_Головна"].sum()
    total_lost_cross = df_filtered["Втрачено_Крос"].sum()
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("🔥 ЗАГАЛЬНІ ВТРАТИ", f"{total_lost_main + total_lost_cross:,.0f} ₴")
    m_col2.metric("💰 Втрати (Основні)", f"{total_lost_main:,.0f} ₴")
    m_col3.metric("📦 Втрати (Крос-сел)", f"{total_lost_cross:,.0f} ₴")

    st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    
    row1_col1, row1_col2 = st.columns([1.2, 1])
    with row1_col1:
        st.markdown("### 🎯 Причини втрат")
        reasons_data = df_filtered[df_filtered['Втрачено_грн'] > 0].groupby('ROOT_PROBLEM')['Втрачено_грн'].sum().reset_index().sort_values(by='Втрачено_грн', ascending=False).head(5)
        if not reasons_data.empty:
            fig_reasons = px.bar(reasons_data, x='Втрачено_грн', y='ROOT_PROBLEM', orientation='h', color_discrete_sequence=['#EF4444'])
            fig_reasons.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8', xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'))
            st.plotly_chart(fig_reasons, use_container_width=True)

    with row1_col2:
        st.markdown("### 🚨 Рейтинг втрат")
        manager_loss = df_filtered.groupby("Менеджер")['Втрачено_грн'].sum().reset_index().sort_values("Втрачено_грн", ascending=False)
        st.dataframe(manager_loss.style.format({'Втрачено_грн': '{:,.0f}'}), use_container_width=True, hide_index=True)

# ==========================================
# ПАНЕЛЬ 3: ІСТОРІЯ ТА КАРТКА
# ==========================================
with tab_history:
    st.markdown("### 🎧 Історія дзвінків")
    cols_to_list = ["Дата", "Дзвінок", "Вх_Вих", "Тип_Дзвінка", "Результат_Розмови_Заголовок", "Hard_Бал"]
    cols_to_list = [c for c in cols_to_list if c in df_filtered.columns]
    
    try:
        event = st.dataframe(df_filtered[cols_to_list], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=250)
        selected_indices = event.selection.rows
    except:
        selected_indices = []

    if selected_indices:
        row = df_filtered.iloc[selected_indices[0]] if isinstance(selected_indices[0], int) else df_filtered.loc[selected_indices[0]]

        st.markdown("---")
        col_hdr1, col_hdr2 = st.columns([2, 1])
        with col_hdr1: st.subheader(f"📄 Картка розмови: {row.get('Дзвінок', '')}")
        with col_hdr2:
            if "Посилання_на_аудіо" in row and pd.notna(row['Посилання_на_аудіо']): st.audio(row['Посилання_на_аудіо'])
            
        if "Логіка_Аналізу" in row and pd.notna(row['Логіка_Аналізу']):
            with st.expander("🤖 Логіка прийняття рішення ШІ"): st.write(row['Логіка_Аналізу'])
        
        top1, top2, top3 = st.columns(3)
        with top1:
            score = float(row.get('Hard_Бал', 0))
            if score >= 8: score_color, score_text, bg_color = "#A3E635", "Відмінно", "rgba(163, 230, 53, 0.1)"
            elif score >= 5: score_color, score_text, bg_color = "#FBBF24", "Задовільно", "rgba(251, 191, 36, 0.1)"
            elif score >= 3: score_color, score_text, bg_color = "#F87171", "Потребує уваги", "rgba(248, 113, 113, 0.1)"
            else: score_color, score_text, bg_color = "#EF4444", "Критично", "rgba(239, 68, 68, 0.2)"

            deg = (score / 10) * 360
            st.markdown(f"""
                <div class="card" style="height: 100%; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <p style="color: #94A3B8; margin-bottom: 10px; font-weight: 600; font-size: 13px;">HARD SKILLS</p>
                    <div style="width: 90px; height: 90px; border-radius: 50%; background: conic-gradient({score_color} {deg}deg, rgba(255,255,255,0.05) 0deg); display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                        <div style="width: 72px; height: 72px; border-radius: 50%; background: #0A0F1C; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                            <span style="font-size: 26px; font-weight: 800; color: #FFFFFF; line-height: 1; text-shadow: 0 0 10px {score_color};">{score:.1f}</span>
                        </div>
                    </div>
                    <div style="background: {bg_color}; color: {score_color}; border-radius: 20px; font-weight: bold; padding: 4px 12px; font-size: 13px; border: 1px solid {score_color}40;">{score_text}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with top2:
            intent = row.get('Готовність', 'N/A')
            st.markdown(f"""
                <div class="card" style="height: 100%; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <p style="color: #94A3B8; margin-bottom: 5px; font-weight: 600; font-size: 13px;">ГОТОВНІСТЬ КЛІЄНТА</p>
                    <h1 style="color: #8B5CF6; margin: 10px 0; font-size: 32px; text-shadow: 0 0 15px rgba(139, 92, 246, 0.3);">{intent}</h1>
                </div>
            """, unsafe_allow_html=True)

        with top3:
            soft = int(row.get('Soft_Бал', 0))
            tone = str(row.get('Тон_Розмови', ''))
            is_complaint = tone.startswith("Скарга")
            
            tone_bg = "rgba(239, 68, 68, 0.05)" if is_complaint else "rgba(255,255,255,0.02)"
            tone_border = "rgba(239, 68, 68, 0.3)" if is_complaint else "rgba(255,255,255,0.05)"
            tone_text_color = "#F87171" if is_complaint else "#E2E8F0"
            tone_title_color = "#EF4444" if is_complaint else "#94A3B8"
            
            st.markdown(f"""
                <div class="card" style="height: 100%; background: {tone_bg}; border-color: {tone_border};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <p style="color: {tone_title_color}; margin: 0; font-weight: 800; font-size: 13px;">{'🚨 СКАРГА' if is_complaint else 'ТОН РОЗМОВИ'}</p>
                        <span style="background: rgba(255,255,255,0.1); color: #E2E8F0; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">Soft: {soft}/8</span>
                    </div>
                    <p style="margin: 0; color: {tone_text_color}; font-size: 14px; font-style: italic;">"{tone}"</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        manager_summary = row.get('Оцінка_Роботи_Менеджера', '')
        if pd.notna(manager_summary) and str(manager_summary).strip() != "":
            st.info(f"💬 **Оцінка:** {manager_summary}")
        
        if row.get('Було_Перемикання', 'Ні') == 'Так':
            justified = row.get('Перемикання_Виправдане', '')
            if "Так" in str(justified): st.success(f"🔁 **Перемикання:** Виправдане. {justified}")
            elif "Ні" in str(justified): st.error(f"🚫 **Перемикання:** НЕ ВИПРАВДАНЕ! {justified}")
            else: st.warning(f"🔁 **Перемикання:** Невідомо.")

        res_title = row.get('Результат_Розмови_Заголовок', '')
        res_desc = row.get('Результат_Розмови_Опис', '')
        root_prob = row.get('ROOT_PROBLEM', 'Немає')
        
        if root_prob == 'Немає': 
            res_bg, res_border, res_icon_color, res_icon = "rgba(34, 197, 94, 0.05)", "rgba(34, 197, 94, 0.2)", "#A3E635", "✓"
        elif "Відмова" in str(res_title) or root_prob in ['Менеджер', 'Ціна', 'Наявність', 'Термін поставки', 'Процес']: 
            res_bg, res_border, res_icon_color, res_icon = "rgba(239, 68, 68, 0.05)", "rgba(239, 68, 68, 0.3)", "#F87171", "!"
        else: 
            res_bg, res_border, res_icon_color, res_icon = "rgba(245, 158, 11, 0.05)", "rgba(245, 158, 11, 0.3)", "#FBBF24", "?"
        
        st.markdown(f"""
        <div style="background: {res_bg}; border: 1px solid {res_border}; border-radius: 12px; padding: 24px; display: flex; gap: 18px; margin-bottom: 24px;">
            <div style="color: {res_icon_color}; font-size: 32px; font-weight: bold; flex-shrink: 0; text-shadow: 0 0 15px {res_icon_color}80;">{res_icon}</div>
            <div>
                <h4 style="margin: 0 0 10px 0; color: #FFFFFF; font-size: 22px;">Результат: <span style="color: {res_icon_color};">{res_title}</span></h4>
                <p style="margin: 0; color: #94A3B8; font-size: 16px;">{res_desc}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        mid1, mid2 = st.columns([1, 2])
        with mid1:
            with st.container(border=True):
                st.write("**🛡 Заперечення**")
                if row.get("Заперечення_Були", "Ні") == "Так":
                    obj_score = row.get('Робота_з_запереченнями_Бал', 0)
                    st.markdown(f"<div style='color: {'#A3E635' if obj_score==2 else '#F87171'}; font-weight: bold; margin-bottom: 8px;'>Оцінка: {obj_score}/2</div>", unsafe_allow_html=True)
                    st.write(f"<span style='font-size: 14px;'>{row.get('Заперечення_Деталі', '')}</span>", unsafe_allow_html=True)
                else: st.success("✅ Не було")

        with mid2:
            sc1, sc2 = st.columns(2)
            with sc1:
                st.write("👍 **Сильні сторони**")
                items = str(row.get('Сильні_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean = item.strip().replace("- ", "").replace("* ", "")
                    if clean and clean.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='check-item'>✓ {clean}</div>", unsafe_allow_html=True); has_items = True
            
            with sc2:
                st.write("🚩 **Слабкі сторони**")
                items = str(row.get('Слабкі_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean = item.strip().replace("- ", "").replace("* ", "")
                    if clean and clean.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='cross-item'>✕ {clean}</div>", unsafe_allow_html=True); has_items = True

# ==========================================
# ПАНЕЛЬ 4: ТРЕНДИ
# ==========================================
with tab_trends:
    st.markdown("### 📈 Динаміка")
    if "Дата" in df_filtered.columns and not df_filtered.empty:
        trend_all = df_filtered.groupby('Дата').agg({'Крос_сел': 'mean', 'Екосистема': 'mean', 'Hard_Бал': 'mean', 'Дзвінок': 'count'}).reset_index()
        sales_all = df_filtered[df_filtered['ROOT_PROBLEM'] == 'Немає'].groupby('Дата').size().reset_index(name='Продажів')
        trend_all = trend_all.merge(sales_all, on='Дата', how='left').fillna({'Продажів': 0})
        trend_all['Конверсія_%'] = (trend_all['Продажів'] / trend_all['Дзвінок'] * 100).round(1)

        c1, c2, c3 = st.columns(3)
        with c1:
            fig1 = px.line(trend_all, x='Дата', y='Конверсія_%', title="Конверсія (%)")
            fig1.update_traces(line=dict(width=4, color='#A3E635'))
            fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8', yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', range=[0,100]))
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.line(trend_all, x='Дата', y='Крос_сел', title="Крос-сел")
            fig2.update_traces(line=dict(width=4, color='#FBBF24')) 
            fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8', yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', range=[-0.1, 2.1]))
            st.plotly_chart(fig2, use_container_width=True)
        with c3:
            fig3 = px.line(trend_all, x='Дата', y='Екосистема', title="Екосистема")
            fig3.update_traces(line=dict(width=4, color='#8B5CF6')) 
            fig3.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8', yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', range=[-0.1, 2.1]))
            st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# ПАНЕЛЬ 5: МАТРИЦЯ
# ==========================================
with tab_coach:
    st.markdown("### 🎓 Матриця навичок")
    skill_cols = ['Привітання', 'Виявлення_Потреби', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття', 'Привітність', 'Ввічливість', 'Емпатія']
    existing_skills = [c for c in skill_cols if c in df_filtered.columns]
    
    agg_dict = {"Дзвінків": pd.NamedAgg(column="Дзвінок", aggfunc="count")}
    if "Hard_Бал" in df_filtered.columns: agg_dict["Сер_Hard"] = pd.NamedAgg(column="Hard_Бал", aggfunc="mean")
    for skill in existing_skills: agg_dict[skill] = pd.NamedAgg(column=skill, aggfunc="mean")
        
    coach_stats = df_filtered.groupby("Менеджер").agg(**agg_dict).reset_index()
    if "Сер_Hard" in coach_stats.columns: coach_stats = coach_stats.sort_values(by="Сер_Hard", ascending=False)
        
    st.dataframe(coach_stats.style.format(precision=1), use_container_width=True, hide_index=True)
