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

# --- 2. ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data
def load_data():
    df = pd.read_excel("REPORT_EXIST_CEO.xlsx")
    
    rename_dict = {}
    for col in df.columns:
        if "OOT" in col and "PROBLEM" in col: rename_dict[col] = "ROOT_PROBLEM"
        if "Готовність" in col: rename_dict[col] = "Готовність"
        if "Крос_Сел" in col and "проба" in col: rename_dict[col] = "Спроба_Крос_Селу"
        if "Привітність" in col: rename_dict[col] = "Привітність"
        
    df.rename(columns=rename_dict, inplace=True)
    return df

df = load_data()
    
    # Автоматично виправляємо назви колонок, якщо Excel їх трохи обрізав
    rename_dict = {}
    for col in df.columns:
        if "OOT" in col and "PROBLEM" in col: rename_dict[col] = "ROOT_PROBLEM"
        if "Готовність" in col: rename_dict[col] = "Готовність"
        if "Крос_Сел" in col and "проба" in col: rename_dict[col] = "Спроба_Крос_Селу"
        if "Привітність" in col: rename_dict[col] = "Привітність"
        
    df.rename(columns=rename_dict, inplace=True)
    return df

df = load_data()

if df.empty:
    st.error("❌ У папці 'D:\\виход' немає жодного Excel файлу.")
    st.stop()

# --- 3. САЙДБАР: ФІЛЬТРИ ТА ГРОШІ ---
with st.sidebar:
    st.markdown("### 🎛 Фільтри")
    
    if "Менеджер" in df.columns:
        managers_list = sorted(df["Менеджер"].dropna().unique())
    else:
        managers_list = []
        
    selected_managers = st.multiselect("👤 Менеджери", managers_list, default=managers_list)
    
    if "Готовність" in df.columns:
        intents_list = sorted(df["Готовність"].dropna().unique())
    else:
        intents_list = []
        
    selected_intents = st.multiselect("🎯 Готовність до покупки", intents_list, default=intents_list)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 💰 Фінансові параметри")
    avg_check = st.number_input("Середній чек (грн)", value=1500, step=100)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Вага потенціалу:")
    st.write("🔥 High: 100%")
    st.write("⚡ Medium: 50%")
    st.write("*(Low готовність не враховується у втратах)*")

df_filtered = df[(df["Менеджер"].isin(selected_managers)) & (df["Готовність"].isin(selected_intents))].copy()

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

    no_closing_count = len(df_filtered[df_filtered["Дотиснув_Угоду"] == "Ні"]) if "Дотиснув_Угоду" in df_filtered.columns else 0
    no_closing_rate = (no_closing_count / total_calls * 100) if total_calls > 0 else 0

    no_cross_count = len(df_filtered[df_filtered["Спроба_Крос_Селу"] == "Ні"]) if "Спроба_Крос_Селу" in df_filtered.columns else 0
    no_cross_rate = (no_cross_count / total_calls * 100) if total_calls > 0 else 0

    col1.metric("Втрачено (грн)", f"{total_lost_potential:,.0f} ₴")
    col2.metric("% втрат ГАРЯЧИХ", f"{hot_loss_rate:.0f}%")
    col3.metric("% без CLOSING", f"{no_closing_rate:.0f}%")
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

    st.markdown("<br>### 🔎 Деталі втрат гарячих клієнтів", unsafe_allow_html=True)
    hot_lost_details = df_filtered[(df_filtered['Готовність'] == 'High') & (df_filtered['ROOT_PROBLEM'] != 'Немає')]
    if not hot_lost_details.empty:
        cols_to_show = [c for c in ['Менеджер', 'Дзвінок', 'ROOT_PROBLEM', 'Втрачено_грн', 'Інсайт_для_CEO'] if c in hot_lost_details.columns]
        st.dataframe(hot_lost_details[cols_to_show], use_container_width=True, hide_index=True)
    else:
        st.success("Жоден гарячий клієнт не був втрачений!")

# ==========================================
# ПАНЕЛЬ 2: MANAGER COACHING (Бали, Софт-скіли, Поради)
# ==========================================
with tab_coach:
    st.markdown("### 📊 Детальний розбір навичок")
    
    skill_cols = ['Привітання', 'Експертиза', 'Презентація', 'Крос_сел', 'Екосистема', 'Закриття', 'Привітність', 'Активне_Слухання', 'Впевненість_Мовлення', 'Емпатія']
    existing_skills = [c for c in skill_cols if c in df_filtered.columns]
    
    # ФІКС ПОМИЛКИ: використовуємо однорідний словник для агрегації
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

            # 1. Математика оцінки (Hard Skills)
            max_hard = 12 
            score_10 = round((row.get('Hard_Бал', 0) / max_hard) * 10, 1) if max_hard else 0

            if score_10 >= 8:
                score_color = "#16A34A" 
                score_text = "Відмінно"
            elif score_10 >= 5:
                score_color = "#EAB308" 
                score_text = "Задовільно"
            else:
                score_color = "#DC2626" 
                score_text = "Погано"

            # 2. Логіка результату
            is_success = row.get("Дотиснув_Угоду") == "Так"
            result_bg = "#F0FDF4" if is_success else "#FEF2F2"
            result_border = "#BBF7D0" if is_success else "#FECACA"
            result_title = "Угода успішна / Дотиснуто" if is_success else "Угоду втрачено"
            result_desc = "Менеджер довів клієнта до цільової дії." if is_success else f"Причина втрати ліда: <b>{row.get('ROOT_PROBLEM', 'Невідомо')}</b>."

            # 3. Логіка "Тону розмови" (Soft Skills)
            soft_score = row.get('Soft_Бал', None)
            tone_html = ""
            
            if pd.notna(soft_score):
                if soft_score >= 7:
                    tone_icon = "😊"
                    tone_text = "Тон спілкування був максимально професійним, ввічливим та впевненим. Менеджер продемонстрував високий рівень емпатії та активного слухання."
                elif soft_score >= 4:
                    tone_icon = "🙂"
                    tone_text = "Робочий та стриманий тон. Менеджер був професійним, але місцями не вистачало активного включення в проблему клієнта або впевненості."
                else:
                    tone_icon = "😐"
                    tone_text = "Проблемний тон розмови. Помітна невпевненість, відсутність емпатії або недостатня привітність до клієнта."
                
                tone_html = f"""
<div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
<div style="display: flex; gap: 10px; align-items: center; margin-bottom: 8px;">
<div style="font-size: 20px;">{tone_icon}</div>
<h4 style="margin: 0; color: #0F172A; font-size: 16px;">Тон розмови (Soft Score: {soft_score}/8)</h4>
</div>
<p style="margin: 0; color: #475569; font-size: 14px; line-height: 1.5; padding-left: 30px;">{tone_text}</p>
</div>
"""

            # 4. Верстка карток (УСІ ТЕГИ ПРИТИСНУТІ ДО ЛІВОГО КРАЮ)
            st.markdown(f"""
<div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
<div style="display: flex; align-items: center; gap: 24px;">
<div style="text-align: center;">
<div style="border: 5px solid {score_color}; border-radius: 50%; width: 90px; height: 90px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 800; color: #0F172A; margin-bottom: 8px;">
{score_10}
</div>
<span style="background: {score_color}20; color: {score_color}; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">{score_text}</span>
</div>
<div>
<h3 style="margin: 0 0 8px 0; color: #0F172A; font-size: 18px;">Оцінка роботи менеджера</h3>
<p style="margin: 0; color: #475569; line-height: 1.5;">{row.get('Порада_для_менеджера', 'Порад немає')}</p>
</div>
</div>
</div>

<div style="background: {result_bg}; border: 1px solid {result_border}; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
<div style="display: flex; gap: 15px; align-items: center;">
<div style="font-size: 24px;">{'✅' if is_success else '❌'}</div>
<div>
<h4 style="margin: 0 0 4px 0; color: #111827; font-size: 16px;">Результат розмови: {result_title}</h4>
<p style="margin: 0; color: #374151; font-size: 14px;">{result_desc} <br> Готовність до покупки: <b>{row.get('Готовність', 'N/A')}</b> | Спроба крос-селу: <b>{row.get('Спроба_Крос_Селу', 'Ні')}</b></p>
</div>
</div>
</div>

{tone_html}

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
