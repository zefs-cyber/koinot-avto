import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters
import plotly.express as px
from st_aggrid import AgGrid
import pygwalker as pyg
import os
import warnings
import seaborn as sns
from matplotlib import pyplot as plt
import plotly.figure_factory as ff
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import hashlib

st.set_page_config(page_title='Коиноти Нав', page_icon=':bar_chart', layout='wide')

def filter_dataframe(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    This function filters a pandas dataframe based on the provided filters.

    Parameters
    ----------
    df: pd.DataFrame
        The pandas dataframe to be filtered.
    filters: dict
        A dictionary containing the filters to be applied to the dataframe. The keys
        of the dictionary should be the column names, and the values should be a list
        of values to filter by.

    Returns
    -------
    pd.DataFrame
        The filtered pandas dataframe.

    """
    filtered_df = df.copy()  # Create a copy of the original DataFrame to avoid modifying it directly
    # Apply filters to the DataFrame
    for column, values in filters.items():
        if values:  # Check if the list of values for the current column is not empty
            filtered_df = filtered_df[filtered_df[column].isin(values)]
    
    return filtered_df

@st.cache_data
def load_data():
    df_today = pd.read_excel('export/ttoday_2024-03-15.xlsx')
    df_sold = pd.read_excel('export/sold_2024-03-15.xlsx')
    df_today['AuthorID'] = pd.to_numeric(df_today['AuthorID'], errors='coerce')
    df_sold['DatePublished'] = pd.to_datetime(df_sold['DatePublished'], format='%d.%m.%Y %H:%M')
    df_sold['sold_date'] = pd.to_datetime(df_sold['sold_date'], format='%d.%m.%Y %H:%M')

    # Calculate the time taken to sell each model in hours
    df_sold['selling_time_hours'] = round((df_sold['sold_date'] - df_sold['DatePublished']).dt.total_seconds() / 86400, 2) 

    return df_today, df_sold

def display_dashboard():

    df_today, df_sold = load_data()

    new_names_today = ['Пост', 
                'PostID', 
                'Имя автора', 
                'AuthorID', 
                'WhatsApp', 
                'Дата публикации',
                'Description', 
                'Цена', 
                'Город', 
                'Кузов', 
                'Год выпуска', 
                'Цвет',
                'Привод', 
                'Объем двигателя', 
                'Состояние', 
                'Вид топлива',
                'Растаможен в РТ', 
                'Коробка передач', 
                'Марка', 
                'Модель']
    new_names_sold = ['Пост', 
                'PostID', 
                'Имя автора', 
                'AuthorID', 
                'WhatsApp', 
                'Дата публикации',
                'Description', 
                'Цена', 
                'Город', 
                'Кузов', 
                'Год выпуска', 
                'Цвет',
                'Привод', 
                'Объем двигателя', 
                'Состояние', 
                'Вид топлива',
                'Растаможен в РТ', 
                'Коробка передач',
                'sold_date', 
                'Марка', 
                'Модель',
                'selling_time_hours']
    filters =  [
                'Марка', 
                'Модель',
                'Город', 
                'Кузов', 
                'Вид топлива',
                'Привод', 
                'Коробка передач', 
                'Цвет',
                'Растаможен в РТ', 
                'Состояние']
    display_columns = [
                'Марка', 
                'Модель',
                'Цена', 
                'Город', 
                'Год выпуска',
                'Вид топлива', 
                'Состояние']

    df_today.columns = new_names_today
    df_sold.columns = new_names_sold

    #Creating Filter
    dynamic_filters = DynamicFilters(df_today, filters=filters)
    st.sidebar.header('Задайте фильтры:')

    # Adding all filters to sidebar
    with st.sidebar:
        price_range = st.sidebar.slider('Цена', 1000, 5000000, (1000, 5000000))
        year_range = st.sidebar.slider('Год выпуска', df_today['Год выпуска'].min(), df_today['Год выпуска'].max(), (df_today['Год выпуска'].min(), df_today['Год выпуска'].max()))
        dynamic_filters.display_filters()


    #Applyting price and year filters to df
    filtered_df = dynamic_filters.filter_df()
    filtered_df = filtered_df[
            (filtered_df['Цена'] >= price_range[0]) & (filtered_df['Цена'] <= price_range[1]) &
            (filtered_df['Год выпуска'] >= year_range[0]) & (filtered_df['Год выпуска'] <= year_range[1])]


    #Creating body for Dashboard
    st.image('main-logo.svg', width=300)
    # st.header('Коиноти Нав')


    # Creating metric cards
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.container(border=True).metric('Количество машин:', len(filtered_df))

    if len(filtered_df['Цена']) > 0:
        avg_price =int(filtered_df['Цена'].mean())
    else:
        avg_price = 0

    col2.container(border=True).metric('Средняя цена в TJS:', f"{avg_price}")
    col3.container(border=True).metric('Марки:', len(filtered_df['Марка'].unique()))
    col4.container(border=True).metric('Модели:', len(filtered_df['Модель'].unique()))

    sold_filtered = filter_dataframe(df_sold, st.session_state['filters'])
    if len(sold_filtered)>0:
        avg_sold_time = round(sold_filtered['selling_time_hours'].mean(),1)
    else:
        avg_sold_time = 'Нет данных'

    col5.container(border=True).metric('Среднее время продажи.:', f'{avg_sold_time} д')



    main_tab1, main_tab2 = st.tabs(["📈Charts", "🗃Table"])
    chart_tabs = main_tab1.tabs(['🛢️Вид топлива', '🏙️Города', '🚙Кузов', '📆Год выпуска', '⚙️Коробка передач', '🌈Цвет', '🛠️Объем двигателя', '🏎️Модели', '👨‍💼Общее'])

    #Fueltype graphs
    with chart_tabs[0]:
        g1, g2 = chart_tabs[0].columns([2,1])
        fueltypes = filtered_df['Вид топлива'].value_counts()
        fuel_df = pd.DataFrame(fueltypes)
        fuel_df['Percentage'] = round((fuel_df['count'] / fuel_df['count'].sum()) * 100, 1)
        g1.container(border=True).bar_chart(fueltypes, color='#3c324c')
        g2.dataframe(fuel_df)

    #City graphs
    with chart_tabs[1]:
        citytypes = filtered_df['Город'].value_counts()
        chart_tabs[1].container(border=True).bar_chart(citytypes, color='#3c324c')

    #Kuzov graphs
    with chart_tabs[2]:
        g1, g2 = chart_tabs[2].columns(2)
        kuzovtypes = filtered_df['Кузов'].value_counts()
        kuzov_df = pd.DataFrame(kuzovtypes)
        kuzov_df['Percentage'] = round((kuzov_df['count'] / kuzov_df['count'].sum()) * 100, 1)
        g1.container(border=True).bar_chart(kuzovtypes, color='#3c324c')
        g2.dataframe(kuzov_df)

    #Year graphs
    with chart_tabs[3]:
        yeartypes = filtered_df['Год выпуска'].value_counts()
        chart_tabs[3].container(border=True).bar_chart(yeartypes, color='#3c324c')

    #Коробка передач graphs
    with chart_tabs[4]:
        g1, g2 = chart_tabs[4].columns(2)
        korobkatypes = filtered_df['Коробка передач'].value_counts()
        korobka_df = pd.DataFrame(korobkatypes)
        korobka_df['Percentage'] = round((korobka_df['count'] / korobka_df['count'].sum()) * 100, 1)
        g1.container(border=True).bar_chart(korobkatypes, color='#3c324c')
        g2.dataframe(korobka_df)

    #Цвет graphs
    with chart_tabs[5]:
        g1, g2 = chart_tabs[5].columns(2)
        colortypes = filtered_df['Цвет'].value_counts()
        color_df = pd.DataFrame(colortypes)
        color_df['Percentage'] = round((color_df['count'] / color_df['count'].sum()) * 100, 1)
        g1.container(border=True).bar_chart(colortypes, color='#3c324c')
        g2.dataframe(color_df)

    #Объем двигателя graphs
    with chart_tabs[6]:
        volumetypes = filtered_df['Объем двигателя'].value_counts()
        chart_tabs[6].container(border=True).area_chart(volumetypes, color='#3c324c')

    #Объем двигателя graphs
    with chart_tabs[7]:
        modeltypes = filtered_df['Модель'].value_counts().sort_values(ascending=False)
        c1, c2 = chart_tabs[7].columns([3, 1])
        c1.container(border=True).bar_chart(modeltypes.head(30), color='#3c324c')
        c2.dataframe(modeltypes,width=400)

    #Объем двигателя graphs
    with chart_tabs[8]:
        top_authors = filtered_df['AuthorID'].value_counts().sort_values(ascending=False).head(30)
        top_authors_df = pd.DataFrame({
            'AuthorID': top_authors.index,
            'Name': [filtered_df.loc[filtered_df['AuthorID'] == author_id, 'Имя автора'].iloc[0] for author_id in top_authors.index],
            'Count': top_authors.values
            })
        df_sold['sold_date'] = pd.to_datetime(df_sold['sold_date'])
        most_selling_models = df_sold.groupby(['Модель']).size().sort_values(ascending=False).head(30)
        # Get value counts based on the date without time, formatting dates as strings
        month_sales = df_sold['sold_date'].dt.strftime('%Y-%m-%d').value_counts().sort_index(ascending=False)
        # authors = top_authors['AuthorID']
        chart_tabs[8].header('Топ 30 самых активных продавцов')
        c1, c2 = chart_tabs[8].columns([3, 1])
        c1.container(border=True).bar_chart(top_authors, color='#3c324c')
        c2.dataframe(top_authors_df, hide_index=True, width=400)
        chart_tabs[8].header('Продажи за последние 30 дней')
        chart_tabs[8].container(border=True).bar_chart(month_sales, color='#3c324c')
        chart_tabs[8].header('Топ 30 продаваемых моделей')
        chart_tabs[8].container(border=True).bar_chart(most_selling_models, color='#3c324c')

    # Tables
    c1, c2 = main_tab2.columns([2,1])
    c1.dataframe(filtered_df[display_columns])
    grouped_data = filtered_df.groupby(['Модель', 'Марка']).size().reset_index(name='Count')

    # Display as a table
    c2.dataframe(grouped_data, width=400)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

fields = {
    'Form name': 'Login',
    'Username': 'Username',
    'Password': 'Password',
    'Login': 'Login',
}


authenticator.login(fields=fields, max_concurrent_users=1, location='main')
if st.session_state["authentication_status"]:
    authenticator.logout(f"{st.session_state['name']} Logout", 'sidebar')
    display_dashboard()
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')
