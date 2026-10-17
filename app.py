import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# Настройка страницы
st.set_page_config(page_title="Эко-паспорт объекта", page_icon="🌿", layout="wide")

# Инициализация данных в сессии
if 'indicators' not in st.session_state:
    st.session_state.indicators = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# Справочник ПДК
PDK_REFERENCE = {
    'NOx': {'limit': 40, 'unit': 'мг/м³', 'type': 'Выбросы'},
    'SO2': {'limit': 20, 'unit': 'мг/м³', 'type': 'Выбросы'},
    'CO': {'limit': 50, 'unit': 'мг/м³', 'type': 'Выбросы'},
    'Нефтепродукты': {'limit': 0.5, 'unit': 'мг/л', 'type': 'Сбросы'},
    'Взвешенные вещества': {'limit': 30, 'unit': 'мг/л', 'type': 'Сбросы'},
}

# Заголовок
st.title("🌿 Эко-паспорт объекта")
st.markdown("---")

# Меню
menu = st.sidebar.selectbox(
    "Меню",
    ["📊 Дашборд", "📝 Ввод данных", "⚠️ Контроль лимитов", "📄 Отчёты", "📚 Справочник ПДК"]
)

# === ДАШБОРД ===
if menu == "📊 Дашборд":
    st.header("Обзор системы")
    
    # Статистика
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Объекты учёта", 2)
    with col2:
        st.metric("Показатели", len(st.session_state.indicators))
    with col3:
        st.metric("Превышения ПДК", len(st.session_state.alerts))
    with col4:
        st.metric("Отчёты", 2)
    
    st.markdown("---")
    
    # Таблица показателей
    st.subheader("Последние показатели")
    if st.session_state.indicators:
        df = pd.DataFrame(st.session_state.indicators)
        st.dataframe(df)
    else:
        st.info("Пока нет данных. Добавьте показатели через меню 'Ввод данных'")

# === ВВОД ДАННЫХ ===
elif menu == "📝 Ввод данных":
    st.header("Внесение экологических показателей")
    
    with st.form("indicator_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            object_id = st.selectbox("Объект учёта", ["OBJ-001: Буровая площадка №1", "OBJ-002: Сервисная база №1"])
            indicator_type = st.selectbox("Тип показателя", ["Выбросы", "Сбросы", "Отходы"])
            parameter = st.selectbox("Параметр", list(PDK_REFERENCE.keys()))
        
        with col2:
            date = st.date_input("Дата", datetime.now())
            value = st.number_input("Значение", min_value=0.0, format="%.2f")
            unit = st.text_input("Единица измерения", PDK_REFERENCE[parameter]['unit'])
        
        comment = st.text_area("Комментарий (обязателен при превышении ПДК)")
        
        submitted = st.form_submit_button("💾 Сохранить показатель")
        
        if submitted:
            # Проверка ПДК
            pdk_info = PDK_REFERENCE[parameter]
            limit = pdk_info['limit']
            
            if value > limit:
                st.error(f"⚠️ Превышение ПДК! Лимит: {limit} {pdk_info['unit']}")
                st.warning(f"Превышение на {((value - limit) / limit * 100):.1f}%")
                
                if not comment:
                    st.error("При превышении ПДК комментарий обязателен!")
                else:
                    # Сохранение
                    indicator = {
                        'Дата': str(date),
                        'Объект': object_id,
                        'Тип': indicator_type,
                        'Параметр': parameter,
                        'Значение': value,
                        'Ед.изм': unit,
                        'Статус': '❌ Превышение',
                        'Комментарий': comment
                    }
                    st.session_state.indicators.append(indicator)
                    
                    alert = {
                        'Дата': str(date),
                        'Объект': object_id,
                        'Параметр': parameter,
                        'Факт': value,
                        'Лимит': limit,
                        'Превышение': f"+{((value - limit) / limit * 100):.1f}%",
                        'Статус': '🔴 Открыто'
                    }
                    st.session_state.alerts.append(alert)
                    
                    st.success("✅ Данные сохранены с предупреждением о превышении")
            else:
                indicator = {
                    'Дата': str(date),
                    'Объект': object_id,
                    'Тип': indicator_type,
                    'Параметр': parameter,
                    'Значение': value,
                    'Ед.изм': unit,
                    'Статус': '✅ В норме',
                    'Комментарий': comment
                }
                st.session_state.indicators.append(indicator)
                st.success("✅ Показатель успешно сохранён")

# === КОНТРОЛЬ ЛИМИТОВ ===
elif menu == "⚠️ Контроль лимитов":
    st.header("Контроль предельно допустимых концентраций")
    
    if st.session_state.alerts:
        df_alerts = pd.DataFrame(st.session_state.alerts)
        st.dataframe(df_alerts)
    else:
        st.success("✅ Превышений ПДК не зафиксировано")

# === ОТЧЁТЫ ===
elif menu == "📄 Отчёты":
    st.header("Формирование отчётов")
    
    col1, col2 = st.columns(2)
    with col1:
        object_name = st.selectbox("Объект", ["Буровая площадка №1", "Сервисная база №1"])
        period = st.selectbox("Период", ["2026-09", "2026-10", "2026-11"])
    
    if st.button("📄 Сформировать отчёт"):
        if st.session_state.indicators:
            # Генерация PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'Сводный экологический отчёт', 0, 1, 'C')
            pdf.ln(5)
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f'Объект: {object_name}', 0, 1)
            pdf.cell(0, 10, f'Период: {period}', 0, 1)
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Показатели:', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            for ind in st.session_state.indicators:
                pdf.cell(0, 8, f"- {ind['Дата']}: {ind['Параметр']} = {ind['Значение']} {ind['Ед.изм']} [{ind['Статус']}]", 0, 1)
            
            filename = f'report_{object_name}_{period}.pdf'
            pdf.output(filename)
            
            st.success(f"✅ Отчёт сформирован: {filename}")
            with open(filename, "rb") as file:
                st.download_button("📥 Скачать отчёт", data=file, file_name=filename, mime="application/pdf")
        else:
            st.warning("Нет данных для формирования отчёта")

# === СПРАВОЧНИК ПДК ===
elif menu == "📚 Справочник ПДК":
    st.header("Справочник предельно допустимых концентраций")
    
    df_pdk = pd.DataFrame([
        {'Параметр': param, 'ПДК': info['limit'], 'Единица': info['unit'], 'Тип': info['type']}
        for param, info in PDK_REFERENCE.items()
    ])
    
    st.dataframe(df_pdk)
    st.info("Источник: СанПиН 1.2.3685-21")
