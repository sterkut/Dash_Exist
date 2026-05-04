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

# --- 2. БАЗА PIN-КОДІВ (ЗАЛИШИВ ЯК Є) ---
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
        
        # 1. Виправляємо картинку (логотип) через HTML
        # Красивий текстовий логотип замість картинки
        st.markdown("""
            <div style='margin-bottom: 15px;'>
                <span style='font-size: 42px; font-weight: 900; color: #1E3A8A; letter-spacing: 1px;'>EXIST</span>
                <span style='font-size: 42px; font-weight: 900; color: #F59E0B;'>.UA</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Вхід для менеджерів")
        
        # 2. Відключаємо нав'язливий менеджер паролів Google
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

# --- 5. ФІЛЬТРАЦІЯ ДАНИХ (ПЕРСОНАЛІЗАЦІЯ) ---
manager_name = st.session_state["manager_name"]
df_full["Менеджер_Clean"] = df_full["Менеджер"].astype(str).str.strip()
df_personal = df_full[df_full["Менеджер_Clean"] == manager_name].copy()

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
# ВКЛАДКА 1: ДАШБОРД ЕФЕКТИВНОСТІ
# ==========================================
with tab_analytics:
    st.markdown("### 📊 Твої особисті показники та місце в рейтингу")
    
    c1, c2 = st.columns(2)
    with c1:
        # Тільки твої результати розмов
        res_col = 'Результат_Розмови_Заголовок' if 'Результат_Розмови_Заголовок' in df_personal.columns else 'Результат_Розмови'
        if not df_personal.empty and res_col in df_personal.columns:
            res_counts = df_personal[res_col].value_counts().reset_index()
            res_counts.columns = ['Результат', 'Кількість']
            fig_res = px.pie(res_counts, values='Кількість', names='Результат', hole=0.4, title="Твої результати розмов")
            st.plotly_chart(fig_res, use_container_width=True)
        else:
            st.info("Немає даних для діаграми.")
            
    with c2:
        # Твоя конверсія
        total_calls = len(df_personal)
        success_steps = (df_personal['Зафіксував_Наступний_Крок'] == 'Так').sum() if 'Зафіксував_Наступний_Крок' in df_personal.columns else 0
        closed_sales = (df_personal['ROOT_PROBLEM'] == 'Немає').sum()
        conv_rate = (closed_sales / total_calls * 100) if total_calls > 0 else 0

        st.markdown("### 🎯 Твоя конверсія")
        st.markdown(f"<p style='color: #64748B; font-size: 14px; margin-top: -15px;'>Твоя реальна ефективність: {conv_rate:.1f}%</p>", unsafe_allow_html=True)
        
        conv_plot_df = pd.DataFrame({
            'Етап': ['Всі твої дзвінки', 'Успішні угоди', 'Продажів закрито'],
            'Кількість': [total_calls, success_steps, closed_sales]
        })
        
        fig_conv = px.bar(conv_plot_df, x='Етап', y='Кількість', text='Кількість',
                          color='Етап', color_discrete_map={'Всі твої дзвінки': '#94A3B8', 'Успішні угоди': '#3B82F6', 'Продажів закрито': '#10B981'})
        fig_conv.update_layout(showlegend=False, height=300, margin=dict(t=10, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_conv, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏆 Загальний рейтинг менеджерів")
    
    leaderboard = df_full.groupby("Менеджер_Clean").agg(
        Дзвінків=('Дзвінок', 'count'),
        Середній_Хард=('Hard_Бал', 'mean'),
        Найвищий_Хард=('Hard_Бал', 'max'),
        Продажів=('ROOT_PROBLEM', lambda x: (x == 'Немає').sum())
    ).reset_index()
    leaderboard['Конверсія_%'] = (leaderboard['Продажів'] / leaderboard['Дзвінків'] * 100).round(1)
    leaderboard = leaderboard.rename(columns={'Менеджер_Clean': 'Прізвище'}).sort_values(by="Середній_Хард", ascending=False)
    
    def highlight_self(s):
        return ['background-color: #E0F2FE; font-weight: bold' if s.Прізвище == manager_name else '' for _ in s]

    st.dataframe(leaderboard.style.apply(highlight_self, axis=1).format({'Середній_Хард': '{:.1f}', 'Конверсія_%': '{:.1f}%'}), use_container_width=True, hide_index=True)

# ==========================================
# ВКЛАДКА 2: МОЇ ДЗВІНКИ ТА РОЗБІР
# ==========================================
with tab_history:
    st.markdown(f"### 🎧 Твої останні розмови")
    
    if df_personal.empty:
        st.warning(f"Поки що немає проаналізованих дзвінків для менеджера {manager_name}.")
    else:
        res_col_p = 'Результат_Розмови_Заголовок' if 'Результат_Розмови_Заголовок' in df_personal.columns else 'Результат_Розмови'
        cols_to_show = ["Дата", "Дзвінок", res_col_p, "Hard_Бал", "Готовність"]
        cols_to_show = [c for c in cols_to_show if c in df_personal.columns]
        
        event = st.dataframe(df_personal[cols_to_show], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=250)
        
        selected_indices = event.selection.rows
        if selected_indices:
            row = df_personal.iloc[selected_indices[0]]
            st.markdown("---")
            
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
                st.markdown(f"""<div class="card" style="height: 100%; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <p style="color: #64748B; margin-bottom: 5px; font-weight: 600; font-size: 13px;">ГОТОВНІСТЬ КЛІЄНТА</p>
                    <h1 style="color: #1E3A8A; margin: 10px 0; font-size: 32px;">{intent}</h1>
                </div>""", unsafe_allow_html=True)

            with top3:
                soft = int(row.get('Soft_Бал', 0))
                tone = row.get('Тон_Розмови', 'Дані відсутні')
                st.markdown(f"""<div class="card" style="height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <p style="color: #64748B; margin: 0; font-weight: 600; font-size: 13px;">ТОН РОЗМОВИ</p>
                        <span style="background: #F1F5F9; color: #334155; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">Soft: {soft}/8</span>
                    </div>
                    <p style="margin: 0; color: #334155; font-size: 14px; line-height: 1.5; font-style: italic;">"{tone}"</p>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Оцінка роботи менеджера (Резюме) ---
            manager_summary = row.get('Оцінка_Роботи_Менеджера', '')
            if pd.notna(manager_summary) and str(manager_summary).strip() != "":
                st.info(f"💬 **Оцінка роботи менеджера:** {manager_summary}")
            # ----------------------------------------------
            
            # 🟢 ДИНАМІЧНИЙ БЛОК РЕЗУЛЬТАТУ РОЗМОВИ
            res_title = row.get('Результат_Розмови_Заголовок', row.get('Результат_Розмови', 'Не визначено'))
            res_desc = row.get('Результат_Розмови_Опис', 'Опис відсутній.')
            root_prob = row.get('ROOT_PROBLEM', 'Немає')
            
            # Логіка кольорів результату з урахуванням причин
            if root_prob == 'Немає': 
                res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#F0FDF4", "#BBF7D0", "#DCFCE7", "#16A34A", "✓"
                reason_html = ""
            elif "Відмова" in str(res_title) or root_prob in ['Менеджер', 'Ціна', 'Наявність', 'Термін поставки', 'Процес']: 
                res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#FEF2F2", "#FECACA", "#FEE2E2", "#DC2626", "!"
                reason_html = f"<hr style='margin: 10px 0; border-color: {res_border};'><p style='margin: 0; color: {res_icon_color}; font-size: 14px; font-weight: bold;'>Причина відмови: {root_prob}</p>"
            else: 
                res_bg, res_border, res_icon_bg, res_icon_color, res_icon = "#FEFCE8", "#FEF08A", "#FEF08A", "#B45309", "?"
                if root_prob and root_prob != 'Немає':
                    reason_html = f"<hr style='margin: 10px 0; border-color: {res_border};'><p style='margin: 0; color: {res_icon_color}; font-size: 14px; font-weight: bold;'>Статус: {root_prob}</p>"
                else:
                    reason_html = ""
            
            st.markdown(f"""
            <div style="background-color: {res_bg}; border: 1px solid {res_border}; border-radius: 12px; padding: 20px; display: flex; align-items: flex-start; gap: 16px; margin-bottom: 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="background-color: {res_icon_bg}; color: {res_icon_color}; width: 42px; height: 42px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 22px; font-weight: bold; flex-shrink: 0;">{res_icon}</div>
                <div style="width: 100%;">
                    <h4 style="margin: 0 0 8px 0; color: #0F172A; font-size: 18px;">Результат розмови: {res_title}</h4>
                    <p style="margin: 0; color: #475569; font-size: 15px; line-height: 1.5; margin-bottom: 5px;">{res_desc}</p>
                    {reason_html}
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
                    st.write("👍 **Твої сильні сторони**")
                    items = str(row.get('Сильні_Сторони', '')).split('\n')
                    has_items = False
                    for item in items:
                        clean = item.strip().replace("- ", "").replace("* ", "")
                        if clean and clean.lower() not in ["немає", "ні", "-"]:
                            st.markdown(f"<div class='check-item'>✓ {clean}</div>", unsafe_allow_html=True)
                            has_items = True
                    if not has_items: st.info("Не виявлено")
                
                with sc2:
                    st.write("🚩 **Зони для росту**")
                    items = str(row.get('Слабкі_Сторони', '')).split('\n')
                    has_items = False
                    for item in items:
                        clean = item.strip().replace("- ", "").replace("* ", "")
                        if clean and clean.lower() not in ["немає", "ні", "-"]:
                            st.markdown(f"<div class='cross-item'>✕ {clean}</div>", unsafe_allow_html=True)
                            has_items = True
                    if not has_items: st.success("Не виявлено")

            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"**📢 Порада від ШІ:** {row.get('Порада_для_менеджера', 'Продовжуй в тому ж дусі!')}")
            
            # --- Транскрипція розмови ---
            transcript = row.get('Транскрипція', '')
            if pd.notna(transcript) and str(transcript).strip() != "":
                with st.expander("📝 Показати текст розмови"):
                    st.write(transcript)

# ==========================================
# ВКЛАДКА 3: МОЯ ДИНАМІКА
# ==========================================
with tab_trends:
    st.markdown("### 📈 Твоя динаміка розвитку та конверсії")
    if not df_personal.empty and "Дата" in df_personal.columns:
        # Рахуємо середні бали та кількість дзвінків
        trend_data = df_personal.groupby("Дата").agg({
            "Hard_Бал": "mean", 
            "Крос_сел": "mean",
            "Дзвінок": "count"
        }).reset_index()
        
        # Рахуємо конверсію
        sales_data = df_personal[df_personal['ROOT_PROBLEM'] == 'Немає'].groupby("Дата").size().reset_index(name='Продажів')
        trend_data = trend_data.merge(sales_data, on="Дата", how="left").fillna({'Продажів': 0})
        trend_data['Конверсія_%'] = (trend_data['Продажів'] / trend_data['Дзвінок'] * 100).round(1)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_conv_personal = px.line(trend_data, x="Дата", y="Конверсія_%", markers=True, title="Моя конверсія у продаж (%)", color_discrete_sequence=['#10B981'])
            st.plotly_chart(fig_conv_personal, use_container_width=True)
            
        with col_t2:
            fig_personal = px.line(trend_data, x="Дата", y="Hard_Бал", markers=True, title="Мій прогрес (Середній Hard Бал)", color_discrete_sequence=['#3B82F6'])
            st.plotly_chart(fig_personal, use_container_width=True)
    else:
        st.info("Потрібно більше закритих днів з даними, щоб побудувати графіки.")
