import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="allogarage.ai | EXIST.UA", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 95%; }
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
                allogarage<span style="color: #3B82F6;">.ai</span>
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
tab_home, tab_analytics, tab_ceo, tab_history, tab_trends, tab_coach = st.tabs([
    "🏠 Головна", "🎯 Дашборд Ефективності", "💰 Фінанси (CEO)", "🎧 Історія та розбір", "📈 Тренди", "🎓 Матриця навичок"
])

# ==========================================
# ПАНЕЛЬ 0: ГОЛОВНА (ОГЛЯД)
# ==========================================
with tab_home:
    total_calls = len(df_filtered)
    df_filtered['Hard_Бал'] = pd.to_numeric(df_filtered['Hard_Бал'], errors='coerce').fillna(0)
    
    avg_hard = df_filtered['Hard_Бал'].mean() if total_calls > 0 else 0
    closed_sales = (df_filtered['ROOT_PROBLEM'] == 'Немає').sum()
    conversion = (closed_sales / total_calls * 100) if total_calls > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📞 Всього дзвінків", f"{total_calls}")
    m2.metric("⭐ Сер. Бал", f"{avg_hard:.1f}/12")
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
                    <div style='background: #F0FDF4; padding: 15px; border-radius: 12px; border-left: 5px solid #22C55E; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='font-weight: 800; color: #166534; font-size: 17px;'>{mgr['Менеджер']}</span>
                            <span style='background: #DCFCE7; color: #166534; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold;'>Бал: {mgr['Сер_Хард']:.1f}</span>
                        </div>
                        <div style='margin-top: 5px; color: #374151; font-size: 14px;'>
                            <b>{mgr['Продажів']}</b> продажів з <b>{mgr['Дзвінків']}</b> дзвінків
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with col_attention:
            st.markdown("### ⚠️ Потребують уваги")
            low_mgrs = mgr_summary[(mgr_summary['Сер_Хард'] < 4.0) & (~mgr_summary['Менеджер'].isin(top_mgr_names))].sort_values(by='Сер_Хард', ascending=True).head(3)
            
            if low_mgrs.empty:
                st.markdown(f"""
                    <div style='background: #F8FAFC; padding: 30px; border-radius: 12px; border: 1px dashed #CBD5E1; text-align: center; margin-bottom: 12px;'>
                        <div style='font-size: 40px; margin-bottom: 10px;'>😊</div>
                        <h4 style='color: #0F172A; margin: 0;'>Всі менеджери працюють добре!</h4>
                        <p style='color: #64748B; margin: 5px 0 0 0; font-size: 14px;'>Немає менеджерів з оцінкою нижче 4.0</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                for _, mgr in low_mgrs.iterrows():
                    st.markdown(f"""
                        <div style='background: #FFF7ED; padding: 15px; border-radius: 12px; border-left: 5px solid #F97316; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <span style='font-weight: 800; color: #9A3412; font-size: 17px;'>{mgr['Менеджер']}</span>
                                <span style='background: #FFEDD5; color: #9A3412; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold;'>Бал: {mgr['Сер_Хард']:.1f}</span>
                            </div>
                            <div style='margin-top: 5px; color: #374151; font-size: 14px;'>
                                Потребує аналізу <b>{mgr['Дзвінків']}</b> розмов | Продажів: <b>{mgr['Продажів']}</b>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("Виберіть дані у фільтрах зліва, щоб побачити огляд.")

# ==========================================
# ПАНЕЛЬ 1: АНАЛІТИКА ТА ЕФЕКТИВНІСТЬ
# ==========================================
with tab_analytics:
    st.markdown("### 📊 Аналітика результатів та конверсія")
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        res_col = 'Результат_Розмови_Заголовок' if 'Результат_Розмови_Заголовок' in df_filtered.columns else 'Результат_Розмови'
        if res_col in df_filtered.columns:
            res_counts = df_filtered[res_col].value_counts().reset_index()
            res_counts.columns = ['Результат', 'Кількість']
            fig_res = px.pie(res_counts, values='Кількість', names='Результат', hole=0.4,
                             title="Структура результатів розмов",
                             color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_res, use_container_width=True)
        else:
            st.info("Немає даних про результати розмов.")
            
    with col_d2:
        total_calls = len(df_filtered)
        success_steps = (df_filtered['Зафіксував_Наступний_Крок'] == 'Так').sum() if 'Зафіксував_Наступний_Крок' in df_filtered.columns else 0
        closed_sales = (df_filtered['ROOT_PROBLEM'] == 'Немає').sum()
        conv_rate = (closed_sales / total_calls * 100) if total_calls > 0 else 0
        
        st.markdown("### 🎯 Конверсія у продаж")
        st.markdown(f"<p style='color: #64748B; font-size: 15px; margin-top: -15px;'>Реальна конверсія: {conv_rate:.1f}% дзвінків завершились продажем</p>", unsafe_allow_html=True)
        
        conv_plot_df = pd.DataFrame({
            'Етап': ['Всі дзвінки', 'Успішні угоди', 'Продажів закрито'],
            'Кількість': [total_calls, success_steps, closed_sales],
            'Колір': ['#94A3B8', '#3B82F6', '#10B981'] 
        })
        
        fig_conv = px.bar(conv_plot_df, x='Етап', y='Кількість', text='Кількість',
                          color='Етап', color_discrete_map={
                              'Всі дзвінки': '#94A3B8', 
                              'Успішні угоди': '#3B82F6', 
                              'Продажів закрито': '#10B981'
                          })
        
        fig_conv.update_layout(showlegend=False, height=350, margin=dict(t=10, b=0, l=0, r=0),
                               xaxis_title=None, yaxis_title=None)
        fig_conv.update_traces(textposition='outside', textfont_size=14, textfont_color='#1E293B')
        
        st.plotly_chart(fig_conv, use_container_width=True)

    st.markdown("---")
    st.markdown("### 👤 Показники менеджерів")

    if 'Менеджер' in df_filtered.columns and 'Hard_Бал' in df_filtered.columns and 'ROOT_PROBLEM' in df_filtered.columns:
        df_stats = df_filtered.copy()
        df_stats['Hard_Бал'] = pd.to_numeric(df_stats['Hard_Бал'], errors='coerce').fillna(0)

        mgr_stats = df_stats.groupby("Менеджер").agg(
            Кількість_дзвінків=('Дзвінок', 'count'),
            Середній_Хард=('Hard_Бал', 'mean'),
            Найвищий_Хард=('Hard_Бал', 'max'),
            Продажів_шт=('ROOT_PROBLEM', lambda x: (x == 'Немає').sum()),
            Відмов_шт=('ROOT_PROBLEM', lambda x: (x != 'Немає').sum())
        ).reset_index()

        mgr_stats = mgr_stats.rename(columns={'Менеджер': 'Прізвище'})
        mgr_stats['Конверсія_%'] = (mgr_stats['Продажів_шт'] / mgr_stats['Кількість_дзвінків'] * 100).round(1)

        styled_mgr = mgr_stats.style.format({
            'Середній_Хард': '{:.1f}',
            'Найвищий_Хард': '{:.0f}',
            'Конверсія_%': '{:.1f}%'
        })\
        .set_properties(subset=['Продажів_шт'], **{'font-weight': 'bold'})\
        .set_properties(subset=['Відмов_шт'], **{'font-weight': 'bold', 'color': '#DC2626'})\
        .background_gradient(cmap='Greens', subset=['Конверсія_%'])

        st.dataframe(styled_mgr, use_container_width=True, hide_index=True)
    else:
        st.warning("Недостатньо колонок для побудови статистики менеджерів.")

# ==========================================
# ПАНЕЛЬ 2: CEO (Гроші та Ефективність)
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

    st.markdown("<br>### 🔎 Деталізація втрат та інсайти для СЕО", unsafe_allow_html=True)
    
    lost_deals_df = df_filtered[df_filtered['ROOT_PROBLEM'] != 'Немає'].copy()
    
    if not lost_deals_df.empty:
        cols_to_show = ['Менеджер', 'Дзвінок', 'Готовність', 'ROOT_PROBLEM', 'Втрачено_грн', 'Інсайт_для_CEO']
        st.dataframe(lost_deals_df[cols_to_show], use_container_width=True, hide_index=True)
    else:
        st.success("Втрат не виявлено! Всі угоди успішні.")

# ==========================================
# ПАНЕЛЬ 3: ІСТОРІЯ ТА КАРТКА ДЗВІНКА
# ==========================================
with tab_history:
    st.markdown("### 🎧 Історія дзвінків")
    st.write("Виділіть рядок у таблиці нижче, щоб переглянути детальний аналіз.")
    
    res_col = "Результат_Розмови_Заголовок" if "Результат_Розмови_Заголовок" in df_filtered.columns else "Результат_Розмови"
    
    cols_to_list = ["Дата", "Менеджер", "Дзвінок", res_col, "Hard_Бал", "Готовність"]
    cols_to_list = [c for c in cols_to_list if c in df_filtered.columns]
    
    try:
        event = st.dataframe(
            df_filtered[cols_to_list],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=250
        )
        selected_indices = event.selection.rows
    except:
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
        
        top1, top2, top3 = st.columns(3)
        
        with top1:
            score = int(row.get('Hard_Бал', 0))
            if score >= 9:
                score_color, score_text, bg_color = "#16A34A", "Відмінно", "#BBF7D0"
            elif score >= 6:
                score_color, score_text, bg_color = "#F59E0B", "Задовільно", "#FDE68A"
            elif score >= 3:
                score_color, score_text, bg_color = "#EF4444", "Потребує уваги", "#FECACA"
            else:
                score_color, score_text, bg_color = "#991B1B", "Критично", "#FCA5A5"

            deg = (score / 12) * 360
            
            st.markdown(f"""
                <div class="card" style="height: 100%; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <p style="color: #64748B; margin-bottom: 10px; font-weight: 600; font-size: 13px;">HARD SKILLS (ОЦІНКА)</p>
                    <div style="width: 90px; height: 90px; border-radius: 50%; background: conic-gradient({score_color} {deg}deg, #E2E8F0 0deg); display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                        <div style="width: 72px; height: 72px; border-radius: 50%; background: white; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                            <span style="font-size: 26px; font-weight: 800; color: #0F172A; line-height: 1;">{score}</span>
                            <span style="font-size: 12px; color: #64748B; font-weight: 600;">з 12</span>
                        </div>
                    </div>
                    <div style="background: {bg_color}; color: {score_color}; border-radius: 20px; font-weight: bold; display: inline-block; padding: 4px 12px; font-size: 13px;">{score_text}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with top2:
            intent = row.get('Готовність', 'N/A')
            st.markdown(f"""
                <div class="card" style="height: 100%; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <p style="color: #64748B; margin-bottom: 5px; font-weight: 600; font-size: 13px;">ГОТОВНІСТЬ КЛІЄНТА</p>
                    <h1 style="color: #1E3A8A; margin: 10px 0; font-size: 32px;">{intent}</h1>
                </div>
            """, unsafe_allow_html=True)

        with top3:
            soft = int(row.get('Soft_Бал', 0))
            tone = row.get('Тон_Розмови', 'Дані відсутні')
            st.markdown(f"""
                <div class="card" style="height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <p style="color: #64748B; margin: 0; font-weight: 600; font-size: 13px;">ТОН РОЗМОВИ</p>
                        <span style="background: #F1F5F9; color: #334155; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">Soft: {soft}/8</span>
                    </div>
                    <p style="margin: 0; color: #334155; font-size: 14px; line-height: 1.5; font-style: italic;">"{tone}"</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- НОВЕ: Оцінка роботи менеджера (Резюме) ---
        manager_summary = row.get('Оцінка_Роботи_Менеджера', '')
        if pd.notna(manager_summary) and str(manager_summary).strip() != "":
            st.info(f"💬 **Оцінка роботи менеджера:** {manager_summary}")
        # ----------------------------------------------
        
        res_title = row.get('Результат_Розмови_Заголовок', row.get('Результат_Розмови', 'Не визначено'))
        res_desc = row.get('Результат_Розмови_Опис', 'Опис відсутній.')
        root_prob = row.get('ROOT_PROBLEM', 'Немає')
        
        # Логіка кольорів результату з урахуванням причин (Збільшені шрифти)
            if root_prob == 'Немає': 
                res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#F0FDF4", "#BBF7D0", "#DCFCE7", "#16A34A", "✓"
                reason_html = ""
            elif "Відмова" in str(res_title) or root_prob in ['Менеджер', 'Ціна', 'Наявність', 'Термін поставки', 'Процес']: 
                res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#FEF2F2", "#FECACA", "#FEE2E2", "#DC2626", "!"
                reason_html = f"<hr style='margin: 12px 0; border-color: {res_border};'><p style='margin: 0; color: {res_icon_color}; font-size: 16px; font-weight: bold;'>Причина відмови: {root_prob}</p>"
            else: 
                res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#FEFCE8", "#FEF08A", "#FEF08A", "#B45309", "?"
                if root_prob and root_prob != 'Немає':
                    reason_html = f"<hr style='margin: 12px 0; border-color: {res_border};'><p style='margin: 0; color: {res_icon_color}; font-size: 16px; font-weight: bold;'>Статус: {root_prob}</p>"
                else:
                    reason_html = ""
            
            st.markdown(f"""
            <div style="background-color: {res_bg}; border: 1px solid {res_border}; border-radius: 12px; padding: 24px; display: flex; align-items: flex-start; gap: 18px; margin-bottom: 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="background-color: {res_icon_bg}; color: {res_icon_color}; width: 50px; height: 50px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 26px; font-weight: bold; flex-shrink: 0;">{res_icon}</div>
                <div style="width: 100%;">
                    <h4 style="margin: 0 0 10px 0; color: #0F172A; font-size: 22px; font-weight: 600;">Результат розмови: <span style="color: {res_icon_color}; font-weight: 900;">{res_title}</span></h4>
                    <p style="margin: 0; color: #475569; font-size: 17px; line-height: 1.6; margin-bottom: 8px;">{res_desc}</p>{reason_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        mid1, mid2 = st.columns([1, 2])
        with mid1:
            with st.container(border=True):
                st.write("**🛡 Робота з запереченнями**")
                if row.get("Заперечення_Були", "Ні") == "Так":
                    obj_score = row.get('Робота_з_запереченнями_Бал', 0)
                    st.markdown(f"<div style='color: {'#16A34A' if obj_score==2 else '#DC2626'}; font-weight: bold; margin-bottom: 8px;'>Оцінка відпрацювання: {obj_score}/2</div>", unsafe_allow_html=True)
                    st.write(f"<span style='font-size: 14px;'>{row.get('Заперечення_Деталі', 'Деталі відсутні')}</span>", unsafe_allow_html=True)
                else:
                    st.success("✅ Заперечень не було")

        with mid2:
            sc1, sc2 = st.columns(2)
            with sc1:
                st.write("👍 **Сильні сторони**")
                items = str(row.get('Сильні_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean = item.strip().replace("- ", "").replace("* ", "")
                    if clean and clean.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='check-item'>✓ {clean}</div>", unsafe_allow_html=True)
                        has_items = True
                if not has_items: st.info("Не виявлено")
            
            with sc2:
                st.write("🚩 **Слабкі сторони**")
                items = str(row.get('Слабкі_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean = item.strip().replace("- ", "").replace("* ", "")
                    if clean and clean.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='cross-item'>✕ {clean}</div>", unsafe_allow_html=True)
                        has_items = True
                if not has_items: st.success("Не виявлено")

        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"**💡 Інсайт для бізнесу:** {row.get('Інсайт_для_CEO', 'Немає інсайтів')}")
        
        lost = row.get('Втрачено_грн', 0)
        if lost > 0:
            st.error(f"💸 **Втрачений прибуток з цього ліда:** {lost:,.0f} ₴ (Причина: {row.get('ROOT_PROBLEM')})")
            
        # --- НОВЕ: Транскрипція розмови ---
        transcript = row.get('Транскрипція', '')
        if pd.notna(transcript) and str(transcript).strip() != "":
            with st.expander("📝 Показати текст розмови"):
                st.write(transcript)
        # ----------------------------------

# ==========================================
# ПАНЕЛЬ 4: ТРЕНДИ (ДИНАМІКА)
# ==========================================
with tab_trends:
    st.markdown("### 📈 Загальна динаміка відділу")
    
    if "Дата" in df_filtered.columns and not df_filtered.empty:
        trend_all = df_filtered.groupby('Дата').agg({
            'Крос_сел': 'mean',
            'Екосистема': 'mean',
            'Hard_Бал': 'mean',
            'Дзвінок': 'count'
        }).reset_index()
        
        sales_all = df_filtered[df_filtered['ROOT_PROBLEM'] == 'Немає'].groupby('Дата').size().reset_index(name='Продажів')
        trend_all = trend_all.merge(sales_all, on='Дата', how='left').fillna({'Продажів': 0})
        trend_all['Конверсія_%'] = (trend_all['Продажів'] / trend_all['Дзвінок'] * 100).round(1)

        c1, c2, c3 = st.columns(3)
        with c1:
            fig1 = px.line(trend_all, x='Дата', y='Конверсія_%', title="Динаміка Конверсії (%)")
            fig1.update_traces(line=dict(width=4, color='#10B981')) 
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.line(trend_all, x='Дата', y='Крос_сел', title="Динаміка Крос-селу (сер. бал)")
            fig2.update_traces(line=dict(width=4, color='#F59E0B')) 
            fig2.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig2, use_container_width=True)
        with c3:
            fig3 = px.line(trend_all, x='Дата', y='Екосистема', title="Динаміка Екосистеми (сер. бал)")
            fig3.update_traces(line=dict(width=4, color='#8B5CF6')) 
            fig3.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
        st.markdown("### 👤 Детальна динаміка по менеджерах")

        trend_mgr = df_filtered.groupby(['Дата', 'Менеджер']).agg({
            'Крос_сел': 'mean',
            'Екосистема': 'mean',
            'Hard_Бал': 'mean'
        }).reset_index()

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_cross_mgr = px.line(trend_mgr, x='Дата', y='Крос_сел', color='Менеджер', markers=True, title="Крос-сел по менеджерах", color_discrete_sequence=px.colors.qualitative.Set1)
            fig_cross_mgr.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig_cross_mgr, use_container_width=True)
            
        with col_t2:
            fig_eco_mgr = px.line(trend_mgr, x='Дата', y='Екосистема', color='Менеджер', markers=True, title="Екосистема по менеджерах", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_eco_mgr.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig_eco_mgr, use_container_width=True)
            
        st.markdown("---")
        fig_total_mgr = px.area(trend_mgr, x='Дата', y='Hard_Бал', color='Менеджер', title="Загальний Hard Бал по менеджерах", color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig_total_mgr, use_container_width=True)
    else:
        st.info("Потрібно більше даних з датами для відображення трендів.")

# ==========================================
# ПАНЕЛЬ 5: COACHING (МАТРИЦЯ НАВИЧОК)
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
