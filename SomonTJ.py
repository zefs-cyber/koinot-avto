import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters
from datetime import datetime, timedelta
from NewFilter import MyFilter




def app(df_today, df_sold):

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

    new_names_today = ["Пост", 
                "PostID", 
                "Имя автора", 
                "AuthorID", 
                "WhatsApp", 
                "Дата публикации",
                "Description", 
                "Цена", 
                "Город", 
                "Кузов", 
                "Год выпуска", 
                "Цвет",
                "Привод", 
                "Объем двигателя", 
                "Состояние", 
                "Вид топлива",
                "Растаможен в РТ", 
                "Коробка передач",
                "Просмотры", 
                "Марка", 
                "Модель",
                "Link"]

    new_names_sold = ["Пост", 
                "PostID", 
                "Имя автора", 
                "AuthorID", 
                "WhatsApp", 
                "Дата публикации",
                "Description", 
                "Цена", 
                "Город", 
                "Кузов", 
                "Год выпуска", 
                "Цвет",
                "Привод", 
                "Объем двигателя", 
                "Состояние", 
                "Вид топлива",
                "Растаможен в РТ", 
                "Коробка передач",
                "Просмотры",
                "sold_date", 
                "Марка", 
                "Модель",
                "selling_time_hours"]

    filters_today =  [
        "Марка", 
        "Модель",
        "Город", 
        "Кузов", 
        "Вид топлива",
        "Привод", 
        "Коробка передач", 
        "Цвет",
        "Растаможен в РТ", 
        "Состояние"]

    display_columns = [
                "Марка", 
                "Модель",
                "Цена", 
                "Город", 
                "Год выпуска",
                "Вид топлива", 
                "Состояние",
                "Link"]
    
    df_today.columns = new_names_today
    df_sold.columns = new_names_sold

    #Creating Filter
    filters = MyFilter(df_today, filters_name=filters_today)
    st.sidebar.header("Задайте фильтры:")

    # Adding all filters to sidebar
    with st.sidebar:
        price_from = st.sidebar.number_input("Цена от", min_value=0, max_value=10000000, value=0, step=5000)
        price_till = st.sidebar.number_input("Цена до", min_value=price_from, max_value=10000000, value=10000000, step=5000)
        year_range = st.sidebar.slider("Год выпуска", df_today["Год выпуска"].min(), df_today["Год выпуска"].max(), (df_today["Год выпуска"].min(), df_today["Год выпуска"].max()))
        filters.display_filters()
        
    #Applyting price and year filters to df
    filtered_df = filters.filter()
    filtered_df = filtered_df[
            (filtered_df["Цена"] >= price_from) & (filtered_df["Цена"] <= price_till) &
            (filtered_df["Год выпуска"] >= year_range[0]) & (filtered_df["Год выпуска"] <= year_range[1])]

    # Creating metric cards
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.container(border=True).metric("Количество машин:", len(filtered_df))

    if len(filtered_df["Цена"]) > 0:
        avg_price =int(filtered_df["Цена"].mean())
    else:
        avg_price = 0

    col2.container(border=True).metric("Средняя цена в TJS:", f"{avg_price}")
    col3.container(border=True).metric("Марки:", len(filtered_df["Марка"].unique()))
    col4.container(border=True).metric("Модели:", len(filtered_df["Модель"].unique()))

    sold_filtered = filter_dataframe(df_sold, st.session_state["filters"])
    if len(sold_filtered)>0:
        avg_sold_time = round(sold_filtered["selling_time_hours"].mean(),1)
    else:
        avg_sold_time = "Нет данных"

    col5.container(border=True).metric("Среднее время продажи.:", f"{avg_sold_time} д")

    main_tab1, main_tab2 = st.tabs(["📈Charts", "🗃Table"])
    chart_tabs = main_tab1.tabs(["🏎️Модели", "📋Бренды", "⏲️Публикации", "👨‍💼Общее", "🛢️Вид топлива", "🏙️Города", "🚙Кузов", "📆Год выпуска", "⚙️Коробка передач", "🌈Цвет", "🛠️Объем двигателя"])

    #Модели graphs
    with chart_tabs[0]:
        modeltypes = filtered_df["Модель"].value_counts().sort_values(ascending=False)
        brand_model_views = filtered_df.groupby(["Модель"]).agg({"Просмотры": "sum"}).reset_index()

        # Sort by views in descending order
        brand_model_views = brand_model_views.sort_values(by="Просмотры", ascending=False)

        chart_tabs[0].header("Cамые распространенные модели")
        c1, c2 = chart_tabs[0].columns([3, 1])
        c1.container(border=True).bar_chart(modeltypes.head(30), color="#3c324c")
        c2.dataframe(modeltypes,width=400)
        chart_tabs[0].header("Cамые просматриваемые модели")
        c1, c2 = chart_tabs[0].columns([3, 1])
        c1.container(border=True).bar_chart(brand_model_views.set_index("Модель").head(30), color="#3c324c")
        c2.dataframe(brand_model_views, width=400)

    #Brands graphs
    with chart_tabs[1]:
        modeltypes = filtered_df["Марка"].value_counts().sort_values(ascending=False)
        brand_mark_views = filtered_df.groupby(["Марка"]).agg({"Просмотры": "sum"}).reset_index()
        # Sort by views in descending order
        brand_mark_views = brand_mark_views.sort_values(by="Просмотры", ascending=False)
        chart_tabs[1].header("Cамые распространенные модели")
        c1, c2 = chart_tabs[1].columns([3, 1])
        c1.container(border=True).bar_chart(modeltypes.head(30), color="#3c324c")
        c2.dataframe(modeltypes,width=400)
        chart_tabs[1].header("Cамые просматриваемые модели")
        c1, c2 = chart_tabs[1].columns([3, 1])
        c1.container(border=True).bar_chart(brand_mark_views.set_index("Марка").head(30), color="#3c324c")
        c2.dataframe(brand_mark_views, width=400)

    #Publications graphs
    with chart_tabs[2]:
        filtered_df["Дата публикации"] = pd.to_datetime(filtered_df["Дата публикации"], dayfirst=True)

        # Extract just the date component
        filtered_df["Дата публикации"] = filtered_df["Дата публикации"].dt.date
        views_per_day = filtered_df.groupby("Дата публикации")["Просмотры"].sum().sort_values(ascending=False)

        # Group by date and count the number of publications made on each day
        publications_per_day = filtered_df.groupby("Дата публикации").size().sort_values(ascending=False)
        chart_tabs[2].header("Количество заявок за последние 30 дней")
        chart_tabs[2].area_chart(publications_per_day.head(30), color="#3c324c")
        chart_tabs[2].header("Количество просмотров за последние 30 дней")
        chart_tabs[2].area_chart(views_per_day.head(30), color="#3c324c")

    #Общее graphs
    with chart_tabs[3]:
        df_sold_filtered = df_sold.copy()
        for key, values in st.session_state[filters_today].items():
            if values:
                df_sold_filtered = df_sold_filtered[df_sold_filtered[key].isin(values)]

        top_authors = filtered_df["AuthorID"].value_counts().sort_values(ascending=False).head(30)
        top_authors_df = pd.DataFrame({
            "AuthorID": top_authors.index,
            "Name": [filtered_df.loc[filtered_df["AuthorID"] == author_id, "Имя автора"].iloc[0] for author_id in top_authors.index],
            "Count": top_authors.values
            })
        df_sold["sold_date"] = pd.to_datetime(df_sold["sold_date"])
        most_selling_models = df_sold_filtered.groupby(["Модель"]).size().sort_values(ascending=False).head(30)
        # Get value counts based on the date without time, formatting dates as strings
        month_sales = df_sold_filtered["sold_date"].dt.strftime("%Y-%m-%d").value_counts().sort_index(ascending=False)
        # authors = top_authors["AuthorID"]
        chart_tabs[3].header("Топ 30 самых активных продавцов")
        c1, c2 = chart_tabs[3].columns([3, 1])
        c1.container(border=True).bar_chart(top_authors, color="#3c324c")
        c2.dataframe(top_authors_df, hide_index=True, width=400)
        chart_tabs[3].header("Продажи за последние 30 дней")
        chart_tabs[3].container(border=True).area_chart(month_sales, color="#3c324c")
        chart_tabs[3].header("Топ 30 продаваемых моделей")
        chart_tabs[3].container(border=True).bar_chart(most_selling_models, color="#3c324c")

    #Fueltype graphs
    with chart_tabs[4]:
        g1, g2 = chart_tabs[4].columns([2,1])
        fueltypes = filtered_df["Вид топлива"].value_counts()
        fuel_df = pd.DataFrame(fueltypes)
        fuel_df["Percentage"] = round((fuel_df["count"] / fuel_df["count"].sum()) * 100, 1)
        g1.container(border=True).bar_chart(fueltypes, color="#3c324c")
        g2.dataframe(fuel_df)

    #City graphs
    with chart_tabs[5]:
        citytypes = filtered_df["Город"].value_counts()
        chart_tabs[5].container(border=True).bar_chart(citytypes, color="#3c324c")

    #Kuzov graphs
    with chart_tabs[6]:
        g1, g2 = chart_tabs[6].columns(2)
        kuzovtypes = filtered_df["Кузов"].value_counts()
        kuzov_df = pd.DataFrame(kuzovtypes)
        kuzov_df["Percentage"] = round((kuzov_df["count"] / kuzov_df["count"].sum()) * 100, 1)
        g1.container(border=True).bar_chart(kuzovtypes, color="#3c324c")
        g2.dataframe(kuzov_df)

    #Year graphs
    with chart_tabs[7]:
        yeartypes = filtered_df["Год выпуска"].value_counts()
        average_price_per_year_df = filtered_df.groupby("Год выпуска")["Цена"].mean().reset_index()

        # Convert the "Цена" column (average price) to integers
        average_price_per_year_df["Цена"] = average_price_per_year_df["Цена"].astype(int)
        chart_tabs[7].container(border=True).bar_chart(yeartypes, color="#3c324c")
        chart_tabs[7].dataframe(average_price_per_year_df, width=400)

    #Коробка передач graphs
    with chart_tabs[8]:
        g1, g2 = chart_tabs[8].columns(2)
        korobkatypes = filtered_df["Коробка передач"].value_counts()
        korobka_df = pd.DataFrame(korobkatypes)
        korobka_df["Percentage"] = round((korobka_df["count"] / korobka_df["count"].sum()) * 100, 1)
        g1.container(border=True).bar_chart(korobkatypes, color="#3c324c")
        g2.dataframe(korobka_df)

    #Цвет graphs
    with chart_tabs[9]:
        g1, g2 = chart_tabs[9].columns(2)
        colortypes = filtered_df["Цвет"].value_counts()
        color_df = pd.DataFrame(colortypes)
        color_df["Percentage"] = round((color_df["count"] / color_df["count"].sum()) * 100, 1)
        g1.container(border=True).bar_chart(colortypes, color="#3c324c")
        g2.dataframe(color_df)

    #Объем двигателя graphs
    with chart_tabs[10]:
        volumetypes = filtered_df["Объем двигателя"].value_counts()
        chart_tabs[10].container(border=True).area_chart(volumetypes, color="#3c324c")

    # Tables
    c1, c2 = main_tab2.columns([2,1])
    c1.dataframe(filtered_df[display_columns])
    grouped_data = filtered_df.groupby(["Модель", "Марка"]).size().reset_index(name="Count")

    # Display as a table
    c2.dataframe(grouped_data, width=400)


