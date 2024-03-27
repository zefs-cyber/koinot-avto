import pandas as pd
import streamlit as st
from NewFilter import MyFilter

def app(df_exracted):
    df_exracted['Дата оформ.'] = pd.to_datetime(df_exracted['Дата оформ.'])


    df_exracted['Month'] = df_exracted['Дата оформ.'].dt.strftime('%Y-%m')
    filters_tamozhnya = [
            'mark',
            'страна отправления/ экспорта'
        ]

    dynamic_filters_tamozhnya = MyFilter(df_exracted, filters_name=filters_tamozhnya)
    st.sidebar.header('Задайте фильтры:')

    # Adding all filters to sidebar
    with st.sidebar:
        price_from = st.sidebar.number_input('Цена от', min_value=0, max_value=500000, value=0, step=5000)
        price_till = st.sidebar.number_input('Цена до', min_value=price_from, max_value=500000, value=500000, step=5000)
        year_range = st.sidebar.slider('year', 1950, 2024, (1950,2024))
        dynamic_filters_tamozhnya.display_filters()
        st.sidebar.text('Выберите даты импорта: ')
        date_start = st.sidebar.date_input('Начало', max_value=df_exracted['Дата оформ.'].max(), min_value=df_exracted['Дата оформ.'].min(), value=df_exracted['Дата оформ.'].min())
        date_end = st.sidebar.date_input('Конец', min_value=date_start, max_value=df_exracted['Дата оформ.'].max(), value=df_exracted['Дата оформ.'].max())

    date_start, date_end = pd.to_datetime(date_start), pd.to_datetime(date_end)
    #Applyting price and year filters to df
    filtered_df = dynamic_filters_tamozhnya.filter()
    filtered_df = filtered_df[
            (filtered_df['Статистическая  стоимость '] >= price_from) & (filtered_df['Статистическая  стоимость '] <= price_till) &
            (filtered_df['year'] >= year_range[0]) & (filtered_df['year'] <= year_range[1]) &
            (filtered_df['Дата оформ.'] >= date_start) & (filtered_df['Дата оформ.'] <= date_end)]

    # Tamozhnya tab
    col_tamozhnya = st.columns(5)
    car_count = len(filtered_df)
    if car_count > 0:
        mark_count = len(filtered_df['mark'].unique())
        mode_year = int(filtered_df['year'].mode()[0])
        stat_price = int(filtered_df['Статистическая  стоимость '].mean())
        # total_tax = round(filtered_df['total tax'].mean(),1)
        exporters = len(filtered_df['Отправитель/экспортер'].unique())
    else:
        mark_count = 0
        mode_year = 0
        stat_price = 0
        total_tax = 0

    # Car Count
    with col_tamozhnya[0]:
        col_tamozhnya[0].container(border=True).metric('Количество машин:', f"{car_count}")

    # Average price
    with col_tamozhnya[1]:
        col_tamozhnya[1].container(border=True).metric('Средняя цена USD:', f"{stat_price}")

    # Mark count
    with col_tamozhnya[2]:
        col_tamozhnya[2].container(border=True).metric('Марки:', f"{mark_count}")

    # Mode year
    with col_tamozhnya[3]:
        col_tamozhnya[3].container(border=True).metric('Частый год:', f"{mode_year}")

    # Total tax
    with col_tamozhnya[4]:
        col_tamozhnya[4].container(border=True).metric('Отправители:', f"{exporters}")

    tabs = st.tabs(['📋Бренды', '🏙️Страны', '📆Год выпуска', '👨‍💼Отправители', 'Импорт по месяцам'])

    with tabs[0]:
        marktypes = filtered_df['mark'].value_counts().sort_values(ascending=False)
        total_tax_per_brand = filtered_df.groupby('mark')['total tax'].mean()

        # Round the mean total tax values to one decimal place
        total_tax_per_brand = total_tax_per_brand.round(1)

        # Sort the result by mean total tax in descending order
        total_tax_per_brand = total_tax_per_brand.sort_values(ascending=False)

        tabs[0].header('Cамые распространенные модели')
        c1, c2 = tabs[0].columns([3, 1])
        c1.container(border=True).bar_chart(marktypes.head(30), color='#3c324c')
        c2.dataframe(marktypes,width=400)

        tabs[0].header('Среднее количество налогов')
        c1, c2 = tabs[0].columns([3, 1])
        c1.container(border=True).bar_chart(total_tax_per_brand.head(30), color='#3c324c')
        c2.dataframe(total_tax_per_brand,width=400)

    with tabs[1]:
        countrytypes = filtered_df['страна отправления/ экспорта'].value_counts().sort_values(ascending=False)
        total_tax_per_country = filtered_df.groupby('страна отправления/ экспорта')['total tax'].mean()

        # Round the mean total tax values to one decimal place
        total_tax_per_country = total_tax_per_country.round(1)

        # Sort the result by mean total tax in descending order
        total_tax_per_country = total_tax_per_country.sort_values(ascending=False)

        tabs[1].header('Страны импортеры')
        c1, c2 = tabs[1].columns([4, 2])
        c1.container(border=True).bar_chart(countrytypes.head(30), color='#3c324c')
        c2.dataframe(countrytypes,width=400)

        tabs[1].header('Среднее количество налогов')
        c1, c2 = tabs[1].columns([4, 2])
        c1.container(border=True).bar_chart(total_tax_per_country.head(30), color='#3c324c')
        c2.dataframe(total_tax_per_country,width=400)

    with tabs[2]:
        yeartypes = filtered_df['year'].value_counts().sort_values(ascending=False)
        total_tax_per_year = filtered_df.groupby('year')['total tax'].mean()

        # Round the mean total tax values to one decimal place
        total_tax_per_year = total_tax_per_year.round(1)

        # Sort the result by mean total tax in descending order
        total_tax_per_year = total_tax_per_year.sort_values(ascending=False)


        tabs[2].header('Количество машин произведнных в разных годах')
        c1, c2 = tabs[2].columns([2, 1])
        c1.container(border=True).bar_chart(yeartypes.head(30), color='#3c324c')
        c2.dataframe(yeartypes,width=400)

        tabs[2].header('Среднее количество налогов')
        c1, c2 = tabs[2].columns([2, 1])
        c1.container(border=True).bar_chart(total_tax_per_year.head(30), color='#3c324c')
        c2.dataframe(total_tax_per_year,width=400)
    
    with tabs[3]:
        exporters = filtered_df['Отправитель/экспортер'].value_counts().sort_values(ascending=False)

        tabs[3].header('Самые активные экспортеры')
        tabs[3].container(border=True).bar_chart(exporters.head(30), color='#3c324c')

        exporters_df = exporters.reset_index()
        exporters_df.columns = ['Отправитель/экспортер', 'Количество']

        # Display the dataframe in the second column
        tabs[3].dataframe(exporters_df)

    with tabs[4]:
        # Group by month and count occurrences
        months = filtered_df['Month'].value_counts().sort_index()

        tabs[4].header('Самые активные экспортеры по месяцам')

        # Display the bar chart
        tabs[4].container(border=True).bar_chart(months.head(30), color='#3c324c')

        # Convert the series to DataFrame and reset the index
        exporters_df = months.reset_index()
        exporters_df.columns = ['Месяц', 'Количество']

        # Display the dataframe in the second column
        tabs[4].dataframe(exporters_df, width=400)
