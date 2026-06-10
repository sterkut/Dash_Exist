import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# --- 2. БАЗА PIN-КОДІВ (ВСТАВ СЮДИ ЗГЕНЕРОВАНИЙ СЛОВНИК) ---
MANAGER_PINS = {
    "4046": "Баришніков Євген",
    "7462": "Бездухий Олександр",
    "6800": "Безушкевич Микола",
    "6410": "Бережний Дмитро",
    "1745": "Библик Ліана",
    "6106": "Білоножко Юліан",
    "9163": "Білоус Сергій",
    "7254": "Бірганс Яна",
    "3798": "Богданов Олег",
    "9588": "Букшань Кирило",
    "8702": "Варчук Євгеній",
    "4689": "Ведмеденко Дмитро",
    "5940": "Вернер Дмитро",
    "4013": "Гаврилов Ярослав",
    "5007": "Галючек Віталій",
    "1153": "Гардаман Тарас",
    "7617": "Гаськов Віталій",
    "3513": "Деревягін Вадим",
    "3307": "Дирявко Михайло",
    "2492": "Дідух Володимир",
    "5752": "Дроботенко Леонід",
    "9750": "Дрогомирецький Ігор",
    "9507": "Забродський Дмитро",
    "1074": "Карцев Володимир",
    "2094": "Коберник Сергій",
    "7000": "Костюченко Костянтин",
    "5882": "Крижановська Олександра",
    "3594": "Крючков Олександр",
    "6475": "Лаврик Олександр",
    "6617": "Левченко Ігор",
    "9810": "Лінський Богдан",
    "7302": "Лісовенко Євген",
    "9021": "Лісовський Владислав",
    "9347": "Літвіненко Віктор",
    "7446": "Луговий Ярослав",
    "3260": "Магаль Омелян",
    "6210": "Маніта Руслан",
    "1601": "Матвеєв Антон",
    "6389": "Мельник Павло",
    "3214": "Мицик Андрій",
    "1752": "Місаренко Михайло",
    "3072": "Николайчук Володимир",
    "4529": "Паламар Вадим",
    "3652": "Паланичко Микола",
    "2431": "Пащенко Олександр",
    "6784": "Поляков Андрій",
    "2601": "Прендзевський Вячеслав",
    "9117": "Проців Роман",
    "5682": "Процюк Ігор",
    "8833": "Путятін Ігор",
    "3923": "Рєзнік Ігор",
    "4954": "Румянцев Богдан",
    "8890": "Рупан Олексій",
    "3590": "Сидоренко Вячеслав",
    "1933": "Скаткін Денис",
    "7686": "Скляров Ігор",
    "2950": "Смирнов В`ячеслав",
    "9465": "Собейко Олег",
    "5832": "Сопрун Олександр",
    "6581": "Статьєв Артем",
    "6388": "Стіфеєв Олександр",
    "6727": "Тарасенко Максим",
    "9231": "Терещенко Іван",
    "4662": "Товарянський Святослав",
    "1175": "Триндюк Руслан",
    "8492": "Філіппов Ігор",
    "5806": "Червоний Олександр",
    "6627": "Чумакевич Юрій",
    "3582": "Шендра Василь",
    "4133": "Шитель Андрій",
    "8879": "Штаба Євген",
    "9833": "Щуровський Андрій",
    "3775": "Якубовський Сергій",
    "5969": "Ярковий Дмитро",
}

# --- 3. ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data(ttl=600)
def load_data():
    df = pd.DataFrame()
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Головна база
        url = "https://docs.google.com/spreadsheets/d/1a1JlK5D4MoRjiHBLOuUN9ScVkKzGPLE6zL1LvXj3Ezw/edit?gid=398555031#gid=398555031"
        df = conn.read(spreadsheet=url)
        
        # Автоматичний мапінг логінів на красиві ПІБ
        try:
            dict_url = "https://docs.google.com/spreadsheets/d/1oL1AREPUAe4qYfJPJPTNz0ga9mMxO3G_mkW_Iyn4aew/edit"
            df_dict = conn.read(spreadsheet=dict_url)
            
            if not df_dict.empty and 'username' in df_dict.columns and "Ім'я" in df_dict.columns:
                def extract_name(full_name):
                    parts = str(full_name).split('/')[0].strip().split()
                    return " ".join(parts[:2]) if len(parts) >= 2 else str(full_name).split('/')[0].strip()
                
                mapping = dict(zip(df_dict['username'].astype(str).str.strip(), df_dict["Ім'я"].apply(extract_name)))
                df['Менеджер'] = df['Менеджер'].astype(str).str.strip().map(lambda x: mapping.get(x, x))
        except:
            pass
            
    except: pass
    
    if df.empty:
        try: df = pd.read_excel(r"D:\виход\REPORT_EXIST_CEO.xlsx")
        except: pass

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if "Дата" in df.columns:
            df["Дата"] = pd.to_datetime(df["Дата"], errors='coerce').dt.date
        
        skill_cols = ['Привітання', 'Виявлення_Потреби', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття', 'Робота_з_запереченнями_Бал', 'Привітність', 'Ввічливість', 'Емпатія']
        for col in skill_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        if 'Hard_Бал' in df.columns: df['Hard_Бал'] = pd.to_numeric(df['Hard_Бал'], errors='coerce').fillna(0)
        if 'Soft_Бал' in df.columns: df['Soft_Бал'] = pd.to_numeric(df['Soft_Бал'], errors='coerce').fillna(0)
    return df

df_full = load_data()

if df_full.empty:
    st.error("❌ Не вдалося знайти дані.")
    st.stop()

df_full["Менеджер_Clean"] = df_full["Менеджер"].astype(str).str.strip()

# --- 4. АВТОРИЗАЦІЯ ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("""
            <div style='margin-bottom: 15px;'>
                <span style='font-size: 42px; font-weight: 900; color: #1E3A8A; letter-spacing: 1px;'>EXIST</span>
                <span style='font-size: 42px; font-weight: 900; color: #F59E0B;'>.UA</span>
            </div>
        """, unsafe_allow_html=True)
        st.subheader("Вхід для менеджерів")
        pin = st.text_input("Введіть свій PIN-код", type="password", autocomplete="off")
        
        if st.button("Увійти", use_container_width=True):
            if pin in MANAGER_PINS:
                st.session_state["authenticated"] = True
                st.session_state["manager_name"] = MANAGER_PINS[pin]
                st.rerun()
            else:
                st.error("Невірний PIN-код")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. ФІЛЬТРАЦІЯ ДАНИХ (З НАДІЙНИМ СКИДАННЯМ RESET KEY) ---
manager_name = st.session_state["manager_name"]

with st.sidebar:
    st.markdown(f"### Вітаємо, {manager_name}! 👋")
    st.write("Твій AI-тренер готовий до розбору.")
    
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🚪 Вийти", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
    with col_nav2:
        if st.button("🔄 Оновити", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 🎛 Фільтри")
    
    if "reset_key_mgr" not in st.session_state:
        st.session_state.reset_key_mgr = 0

    if st.button("❌ Скинути всі фільтри", use_container_width=True):
        st.session_state.reset_key_mgr += 1
        st.rerun()
        
    rk = st.session_state.reset_key_mgr
    
    if "Тон_Розмови" in df_full.columns:
        show_complaints = st.checkbox("🚨 Показати тільки СКАРГИ", value=False, key=f"chk_complaints_mgr_{rk}")
        if show_complaints: st.info("⚠️ Інші фільтри заморожено.")
    else: show_complaints = False

    # Календарний фільтр періоду
    if "Дата" in df_full.columns and not df_full["Дата"].dropna().empty:
        min_date = df_full["Дата"].min()
        max_date = df_full["Дата"].max()
        date_range = st.date_input("📅 Період аналізу", value=(min_date, max_date), min_value=min_date, max_value=max_date, disabled=show_complaints, key=f"dt_range_mgr_{rk}")
        if len(date_range) == 2:
            df_step1 = df_full[(df_full["Дата"] >= date_range[0]) & (df_full["Дата"] <= date_range[1])]
        else:
            df_step1 = df_full
    else:
        df_step1 = df_full
    
    if "Тип_Дзвінка" in df_step1.columns:
        types_list = sorted(df_step1["Тип_Дзвінка"].dropna().unique())
        default_types = [t for t in types_list if str(t) != "Холодний"]
        selected_types = st.multiselect("📞 Тип дзвінка (сервісні вимкнено)", types_list, default=default_types, disabled=show_complaints, key=f"ms_types_mgr_{rk}")
        df_step1 = df_step1[df_step1["Тип_Дзвінка"].isin(selected_types)] if selected_types else df_step1

    if "Вх_Вих" in df_step1.columns:
        dir_list = sorted(df_step1["Вх_Вих"].dropna().unique())
        selected_dir = st.multiselect("📥 Напрямок", dir_list, default=dir_list, disabled=show_complaints, key=f"ms_dirs_mgr_{rk}")
        df_step1 = df_step1[df_step1["Вх_Вих"].isin(selected_dir)] if selected_dir else df_step1
    
    intents_list = sorted(df_step1["Готовність"].dropna().unique()) if "Готовність" in df_step1.columns else []
    default_intents = [i for i in intents_list if str(i) != "Low"]
    selected_intents = st.multiselect("🎯 Готовність (Low вимкнено)", intents_list, default=default_intents, disabled=show_complaints, key=f"ms_intents_mgr_{rk}")
    df_step2 = df_step1[df_step1["Готовність"].isin(selected_intents)] if selected_intents else df_step1

    if "Було_Перемикання" in df_step2.columns:
        transfers_list = sorted(df_step2["Було_Перемикання"].dropna().unique())
        selected_transfers = st.multiselect("🔁 Перемикання?", transfers_list, default=transfers_list, disabled=show_complaints, key=f"ms_transfers_mgr_{rk}")
        df_step3 = df_step2[df_step2["Було_Перемикання"].isin(selected_transfers)] if selected_transfers else df_step2
    else: df_step3 = df_step2

    res_col = "Результат_Розмови_Заголовок" if "Результат_Розмови_Заголовок" in df_step3.columns else "Результат_Розмови"
    if res_col in df_step3.columns:
        res_list = sorted(df_step3[res_col].dropna().unique())
        selected_res = st.multiselect("📝 Результат розмови", res_list, default=res_list, disabled=show_complaints, key=f"ms_results_mgr_{rk}")
        df_step4 = df_step3[df_step3[res_col].isin(selected_res)] if selected_res else df_step3
    else: df_step4 = df_step3

    root_list = sorted(df_step4["ROOT_PROBLEM"].dropna().unique()) if "ROOT_PROBLEM" in df_step4.columns else []
    selected_roots = st.multiselect("🚨 Причина втрати", root_list, default=root_list, disabled=show_complaints, key=f"ms_roots_mgr_{rk}")
    df_step5 = df_step4[df_step4["ROOT_PROBLEM"].isin(selected_roots)] if selected_roots else df_step4

    if show_complaints:
        df_company_filtered = df_full[df_full["Тон_Розмови"].astype(str).str.startswith("Скарга")]
    else:
        df_company_filtered = df_step5

    df_personal = df_company_filtered[df_company_filtered["Менеджер_Clean"] == manager_name]

# --- 6. ГОЛОВНИЙ ІНТЕРФЕЙС ---
st.title("🚀 Мій AI-Тренер")

tab_home, tab_analytics, tab_history, tab_trends, tab_coach = st.tabs([
    "🏠 Головна", "🎯 Дашборд Ефективності", "🎧 Мої дзвінки", "📈 Моя динаміка", "🎓 Матриця навичок"
])

# ==========================================
# ПАНЕЛЬ 0: ГОЛОВНА (ОГЛЯД)
# ==========================================
with tab_home:
    total_calls = len(df_personal)
    avg_hard = df_personal['Hard_Бал'].mean() if total_calls > 0 else 0
    closed_sales = (df_personal['ROOT_PROBLEM'] == 'Немає').sum()
    conversion = (closed_sales / total_calls * 100) if total_calls > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📞 Твої дзвінки", f"{total_calls}")
    m2.metric("⭐ Твій сер. Бал", f"{avg_hard:.1f}/10")
    m3.metric("🎯 Твоя конверсія", f"{conversion:.1f}%")
    m4.metric("💰 Продажів закрито", f"{closed_sales}")

    st.markdown("<br>", unsafe_allow_html=True)

    if not df_company_filtered.empty:
        mgr_summary = df_company_filtered.groupby("Менеджер_Clean").agg(
            Дзвінків=('Дзвінок', 'count'),
            Продажів=('ROOT_PROBLEM', lambda x: (x == 'Немає').sum()),
            Сер_Хард=('Hard_Бал', 'mean')
        ).reset_index()

        best_quality_mgr = mgr_summary.sort_values(by='Сер_Хард', ascending=False).iloc[0]
        
        if best_quality_mgr['Менеджер_Clean'] == manager_name:
            st.success(f"🎉 Вітаємо! Ти зараз **ЛІДЕР** компанії за якістю обслуговування (сер. бал: {best_quality_mgr['Сер_Хард']:.1f})!")
        else:
            st.info(f"✨ Лідер компанії за якістю зараз: **{best_quality_mgr['Менеджер_Clean']}** (сер. бал: {best_quality_mgr['Сер_Хард']:.1f}). Тобі є куди рости!")

        st.markdown("### 🏆 Топ-3 менеджери компанії")
        top_mgrs = mgr_summary.sort_values(by=['Продажів', 'Сер_Хард'], ascending=False).head(3)
        
        for _, mgr in top_mgrs.iterrows():
            is_me = mgr['Менеджер_Clean'] == manager_name
            bg_color = "#DBEAFE" if is_me else "#F0FDF4"
            border_color = "#3B82F6" if is_me else "#22C55E"
            text_color = "#1E3A8A" if is_me else "#166534"
            badge_bg = "#BFDBFE" if is_me else "#DCFCE7"
            
            st.markdown(f"""
                <div style='background: {bg_color}; padding: 15px; border-radius: 12px; border-left: 5px solid {border_color}; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-weight: 800; color: {text_color}; font-size: 17px;'>{mgr['Менеджер_Clean']} {'(ТИ)' if is_me else ''}</span>
                        <span style='background: {badge_bg}; color: {text_color}; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold;'>Бал: {mgr['Сер_Хард']:.1f}</span>
                    </div>
                    <div style='margin-top: 5px; color: #374151; font-size: 14px;'>
                        <b>{mgr['Продажів']}</b> продажів з <b>{mgr['Дзвінків']}</b> дзвінків
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================
# ПАНЕЛЬ 1: АНАЛІТИКА (ТІЛЬКИ ПО СОБІ)
# ==========================================
with tab_analytics:
    st.markdown("### 📊 Твоя аналітика та конверсія")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        res_col = 'Результат_Розмови_Заголовок' if 'Результат_Розмови_Заголовок' in df_personal.columns else 'Результат_Розмови'
        if not df_personal.empty and res_col in df_personal.columns:
            def clean_status(val):
                s = str(val).lower()
                if any(k in s for k in ['viber', 'вайбер', 'telegram', 'телеграм', 'месенджер']): return 'Перехід у месенджер'
                elif any(k in s for k in ['відмов', 'скасовано', 'немає']): return 'Відмова'
                elif any(k in s for k in ['думає', 'порадить', 'вирішує', 'замір']): return 'Клієнт думає'
                elif any(k in s for k in ['передзвон', 'зв\'яз']): return 'Домовились передзвонити'
                elif any(k in s for k in ['сервіс', 'консультац', 'уточнення']): return 'Сервісний дзвінок'
                elif any(k in s for k in ['оформ', 'підтверд', 'роботі', 'змінено', 'скоригов', 'продаж', 'купив', 'успіш']): return 'Продаж закрито'
                else: return val

            cleaned_series = df_personal[res_col].apply(clean_status)
            res_counts = cleaned_series.value_counts().reset_index()
            res_counts.columns = ['Результат', 'Кількість']
            fig_res = px.pie(res_counts, values='Кількість', names='Результат', hole=0.4, title="Твої результати розмов")
            st.plotly_chart(fig_res, use_container_width=True)
        else:
            st.info("Немає даних для діаграми.")
            
    with col_d2:
        total_calls_p = len(df_personal)
        success_steps_p = (df_personal['Зафіксував_Наступний_Крок'] == 'Так').sum() if 'Зафіксував_Наступний_Крок' in df_personal.columns else 0
        closed_sales_p = (df_personal['ROOT_PROBLEM'] == 'Немає').sum()
        conv_rate_p = (closed_sales_p / total_calls_p * 100) if total_calls_p > 0 else 0

        st.markdown("### 🎯 Твоя воронка конверсії")
        st.markdown(f"<p style='color: #64748B; font-size: 14px; margin-top: -15px;'>Твоя реальна ефективність: {conv_rate_p:.1f}%</p>", unsafe_allow_html=True)
        
        conv_plot_df = pd.DataFrame({
            'Етап': ['Всі твої дзвінки', 'Успішні угоди', 'Продажів закрито'],
            'Кількість': [total_calls_p, success_steps_p, closed_sales_p]
        })
        fig_conv = px.bar(conv_plot_df, x='Етап', y='Кількість', text='Кількість', color='Етап', color_discrete_map={'Всі твої дзвінки': '#94A3B8', 'Успішні угоди': '#3B82F6', 'Продажів закрито': '#10B981'})
        fig_conv.update_layout(showlegend=False, height=350, margin=dict(t=10, b=0, l=0, r=0))
        st.plotly_chart(fig_conv, use_container_width=True)

# ==========================================
# ПАНЕЛЬ 2: ІСТОРІЯ ТА РОЗБІР (ПІБ ЗАМІСТЬ ЛОГІНІВ)
# ==========================================
with tab_history:
    st.markdown("### 🎧 Мої дзвінки та розбір помилок")
    
    if df_personal.empty:
        st.warning("Поки що немає проаналізованих дзвінків.")
    else:
        # Стовпець "Дзвінок" в таблиці замінено на красиве "Менеджер" (ПІБ)
        cols_to_list = ["Дата", "Менеджер", "Вх_Вих", "Тип_Дзвінка", res_col, "Hard_Бал"]
        cols_to_list = [c for c in cols_to_list if c in df_personal.columns]
        
        event = st.dataframe(df_personal[cols_to_list], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=250)
        
        selected_indices = event.selection.rows
        if selected_indices:
            row = df_personal.iloc[selected_indices[0]]

            st.markdown("---")
            col_hdr1, col_hdr2 = st.columns([2, 1])
            with col_hdr1: 
                # Картка тепер іменується за красивим ПІБ
                st.subheader(f"📄 Картка розмови: {row.get('Менеджер', 'Невідомо')}")
            with col_hdr2:
                # Вбудований аудіоплеєр розмови
                if "Посилання_на_аудіо" in row and pd.notna(row['Посилання_на_аудіо']):
                    st.audio(row['Посилання_на_аудіо'])
                else:
                    st.caption("Аудіозапис розмови відсутній")
            
            if "Логіка_Аналізу" in row and pd.notna(row['Логіка_Аналізу']):
                with st.expander("🤖 Логіка прийняття рішення ШІ (Чому оцінка саме така?)"):
                    st.write(row['Логіка_Аналізу'])

            top1, top2, top3 = st.columns(3)
            with top1:
                score = float(row.get('Hard_Бал', 0))
                if score >= 8: score_color, score_text, bg_color = "#16A34A", "Відмінно", "#BBF7D0"
                elif score >= 5: score_color, score_text, bg_color = "#F59E0B", "Задовільно", "#FDE68A"
                elif score >= 3: score_color, score_text, bg_color = "#EF4444", "Потребує уваги", "#FECACA"
                else: score_color, score_text, bg_color = "#991B1B", "Критично", "#FCA5A5"

                deg = (score / 10) * 360
                st.markdown(f"""
                    <div class="card" style="height: 100%; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <p style="color: #64748B; margin-bottom: 10px; font-weight: 600; font-size: 13px;">HARD SKILLS (ОЦІНКА)</p>
                        <div style="width: 90px; height: 90px; border-radius: 50%; background: conic-gradient({score_color} {deg}deg, #E2E8F0 0deg); display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                            <div style="width: 72px; height: 72px; border-radius: 50%; background: white; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                <span style="font-size: 26px; font-weight: 800; color: #0F172A; line-height: 1;">{score:.1f}</span>
                                <span style="font-size: 12px; color: #64748B; font-weight: 600;">з 10</span>
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
                tone = str(row.get('Тон_Розмови', 'Дані відсутні'))
                is_complaint = tone.startswith("Скарга")
                tone_bg = "#FEF2F2" if is_complaint else "#ffffff"
                tone_border = "#FECACA" if is_complaint else "#E2E8F0"
                
                st.markdown(f"""
                    <div class="card" style="height: 100%; background-color: {tone_bg}; border-color: {tone_border};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <p style="color: {'#DC2626' if is_complaint else '#64748B'}; margin: 0; font-weight: 800; font-size: 13px;">{'🚨 АЛАРМ: СКАРГА' if is_complaint else 'ТОН РОЗМОВИ'}</p>
                            <span style="background: #F1F5F9; color: #334155; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">Soft: {soft}/8</span>
                        </div>
                        <p style="margin: 0; color: {'#991B1B' if is_complaint else '#334155'}; font-size: 14px; font-style: italic;">"{tone}"</p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            manager_summary = row.get('Оцінка_Роботи_Менеджера', '')
            if pd.notna(manager_summary) and str(manager_summary).strip() != "":
                st.info(f"💬 **Резюме розмови:** {manager_summary}")
            
            if row.get('Було_Перемикання', 'Ні') == 'Так':
                justified = row.get('Перемикання_Виправдане', '')
                if "Так" in str(justified): st.success(f"🔁 **Перемикання:** Виправдане. {justified}")
                elif "Ні" in str(justified): st.error(f"🚫 **Перемикання:** НЕ ВИПРАВДАНЕ! Ти мав вирішити це сам. {justified}")
                else: st.warning(f"🔁 **Перемикання:** Невідомо (клієнт не озвучив суть).")

            res_title = row.get('Результат_Розмови_Заголовок', row.get('Результат_Розмови', 'Не визначено'))
            res_desc = row.get('Результат_Розмови_Опис', 'Опис відсутній.')
            root_prob = row.get('ROOT_PROBLEM', 'Немає')
            
            if root_prob == 'Немає': res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#F0FDF4", "#BBF7D0", "#DCFCE7", "#16A34A", "✓"
            elif root_prob in ['Менеджер', 'Ціна', 'Наявність', 'Термін поставки', 'Процес']: res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#FEF2F2", "#FECACA", "#FEE2E2", "#DC2626", "!"
            else: res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#FEFCE8", "#FEF08A", "#FEF08A", "#B45309", "?"
            
            st.markdown(f"""
            <div style="background-color: {res_bg}; border: 1px solid {res_border}; border-radius: 12px; padding: 20px; display: flex; gap: 15px; margin-bottom: 20px;">
                <div style="background-color: {res_icon_bg}; color: {res_icon_color}; width: 45px; height: 45px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 24px; font-weight: bold; flex-shrink: 0;">{res_icon}</div>
                <div>
                    <h4 style="margin: 0 0 8px 0; color: #0F172A;">Результат: <span style="color: {res_icon_color};">{res_title}</span></h4>
                    <p style="margin: 0; color: #475569;">{res_desc}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            sc1, sc2 = st.columns(2)
            with sc1:
                st.write("👍 **Твої сильні сторони**")
                items = str(row.get('Сильні_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean = item.strip().replace("- ", "").replace("* ", "")
                    if clean and clean.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='check-item'>✓ {clean}</div>", unsafe_allow_html=True); has_items = True
                if not has_items: st.info("Не виявлено")
            
            with sc2:
                st.write("🚩 **Зони для росту**")
                items = str(row.get('Слабкі_Сторони', '')).split('\n')
                has_items = False
                for item in items:
                    clean = item.strip().replace("- ", "").replace("* ", "")
                    if clean and clean.lower() not in ["немає", "ні", "-"]:
                        st.markdown(f"<div class='cross-item'>✕ {clean}</div>", unsafe_allow_html=True); has_items = True
                if not has_items: st.success("Не виявлено")

            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"**📢 Порада від ШІ:** {row.get('Порада_для_менеджера', 'Продовжуй в тому ж дусі!')}")

# ==========================================
# ПАНЕЛЬ 3: МОЯ ДИНАМІКА (ТИ vs КОМПАНІЯ)
# ==========================================
with tab_trends:
    st.markdown("### 📈 Твоя динаміка vs Середнє по компанії")
    if not df_personal.empty and "Дата" in df_personal.columns and not df_company_filtered.empty:
        
        trend_comp = df_company_filtered.groupby("Дата").agg({
            "Hard_Бал": "mean", "Крос_сел": "mean", "Екосистема": "mean", "Дзвінок": "count"
        }).reset_index()
        sales_comp = df_company_filtered[df_company_filtered['ROOT_PROBLEM'] == 'Немає'].groupby("Дата").size().reset_index(name='Продажів')
        trend_comp = trend_comp.merge(sales_comp, on="Дата", how="left").fillna({'Продажів': 0})
        trend_comp['Конверсія_%'] = (trend_comp['Продажів'] / trend_comp['Дзвінок'] * 100).round(1)
        trend_comp['Хто'] = 'Компанія (Середнє)'

        trend_me = df_personal.groupby("Дата").agg({
            "Hard_Бал": "mean", "Крос_сел": "mean", "Екосистема": "mean", "Дзвінок": "count"
        }).reset_index()
        sales_me = df_personal[df_personal['ROOT_PROBLEM'] == 'Немає'].groupby("Дата").size().reset_index(name='Продажів')
        trend_me = trend_me.merge(sales_me, on="Дата", how="left").fillna({'Продажів': 0})
        trend_me['Конверсія_%'] = (trend_me['Продажів'] / trend_me['Дзвінок'] * 100).round(1)
        trend_me['Хто'] = 'Ти (Менеджер)'

        trend_combined = pd.concat([trend_comp, trend_me])

        c1, c2, c3 = st.columns(3)
        color_map = {'Компанія (Середнє)': '#CBD5E1', 'Ти (Менеджер)': '#10B981'}
        with c1:
            fig_c = px.line(trend_combined, x="Дата", y="Конверсія_%", color="Хто", markers=True, title="Конверсія у продаж (%)", color_discrete_map=color_map)
            fig_c.update_traces(line=dict(width=3))
            fig_c.update_yaxes(range=[0, 100])
            st.plotly_chart(fig_c, use_container_width=True)
            
        color_map_cross = {'Компанія (Середнє)': '#CBD5E1', 'Ти (Менеджер)': '#F59E0B'}
        with c2:
            fig_cr = px.line(trend_combined, x="Дата", y="Крос_сел", color="Хто", markers=True, title="Крос-сел (сер. бал)", color_discrete_map=color_map_cross)
            fig_cr.update_traces(line=dict(width=3))
            fig_cr.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig_cr, use_container_width=True)
            
        color_map_eco = {'Компанія (Середнє)': '#CBD5E1', 'Ти (Менеджер)': '#8B5CF6'}
        with c3:
            fig_e = px.line(trend_combined, x="Дата", y="Екосистема", color="Хто", markers=True, title="Екосистема (сер. бал)", color_discrete_map=color_map_eco)
            fig_e.update_traces(line=dict(width=3))
            fig_e.update_yaxes(range=[-0.1, 2.1])
            st.plotly_chart(fig_e, use_container_width=True)
    else:
        st.info("Потрібно більше даних для побудови графіків динаміки.")

# ==========================================
# ПАНЕЛЬ 4: МАТРИЦЯ НАВИЧОК (РАДАР)
# ==========================================
with tab_coach:
    st.markdown("### 🎓 Твій профіль навичок (Радар)")
    
    skill_cols = ['Привітання', 'Виявлення_Потреби', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття', 'Привітність', 'Ввічливість', 'Емпатія']
    existing_skills = [c for c in skill_cols if c in df_personal.columns and c in df_company_filtered.columns]
    
    if existing_skills and not df_personal.empty:
        my_scores = df_personal[existing_skills].mean().values.tolist()
        company_scores = df_company_filtered[existing_skills].mean().values.tolist()
        
        categories = existing_skills + [existing_skills[0]]
        my_scores_closed = my_scores + [my_scores[0]]
        company_scores_closed = company_scores + [company_scores[0]]

        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=company_scores_closed, theta=categories, fill='toself', name='Середнє по компанії',
            line_color='#94A3B8', fillcolor='rgba(148, 163, 184, 0.2)'
        ))
        
        fig_radar.add_trace(go.Scatterpolar(
            r=my_scores_closed, theta=categories, fill='toself', name='Твій результат',
            line_color='#3B82F6', fillcolor='rgba(59, 130, 246, 0.4)'
        ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
            showlegend=True, height=500, title="Аналіз сильних та слабких сторін"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        st.info("💡 **Як читати графік:** Край павутини — це ідеальні 2 бали. Сіра зона — як продає компанія в середньому. Синя зона — твій стиль продажів. Якщо синій кут виходить за межі сірого — ти крутіший за колег!")
    else:
        st.warning("Недостатньо даних для побудови профілю навичок.")
