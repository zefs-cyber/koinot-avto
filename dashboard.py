import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters
from streamlit_option_menu import option_menu
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from datetime import datetime, timedelta
import logging
import SomonTJ, Tamozhnya 

st.set_page_config(page_title='Коиноти Нав', page_icon=':bar_chart', layout='wide',)

@st.cache_data # Cache the original DataFrame
def load_data():
    # Get today's date
    current_date = datetime.now().date()

    # Define the maximum number of days to go back in search
    max_days_back = 7

    for i in range(max_days_back):
        # Generate file names based on the current date
        current_file_date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
        today_file = f'export/ttoday_{current_file_date}.xlsx'
        sold_file = f'export/sold_{current_file_date}.xlsx'
        try:
            # Attempt to load the files
            df_today = pd.read_excel(today_file)
            df_sold = pd.read_excel(sold_file)

            # Convert columns to appropriate data types
            df_today['AuthorID'] = pd.to_numeric(df_today['AuthorID'], errors='coerce')
            df_sold['DatePublished'] = pd.to_datetime(df_sold['DatePublished'], format='%d.%m.%Y %H:%M')
            df_sold['sold_date'] = pd.to_datetime(df_sold['sold_date'], format='%d.%m.%Y %H:%M')

            # Calculate the time taken to sell each model in hours
            df_sold['selling_time_hours'] = round((df_sold['sold_date'] - df_sold['DatePublished']).dt.total_seconds() / 86400, 2) 
            df_link = pd.read_excel('links.xlsx')
            merged_df = pd.merge(df_today, df_link, on='PostID', how='left')
            exctracted = pd.read_excel('tamozhnya/extracted.xlsx')
            exctracted['year'] = exctracted['year'].fillna(0).astype(int)
            exctracted['year'] = exctracted['year'].astype(int)

            return merged_df, df_sold, exctracted
        except FileNotFoundError:
            pass  # Continue to the next date if files are not found

    print("No files found within the specified date range.")
    return None, None, None

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


class Myfilter:
    def __init__(self, df, filters):
        self.df = df
        self.filters = filters
        self.results = []
        self.create_fillters()
    
    def create_fillters(self):
        with st.sidebar:
            for i in self.filters:
                self.filters[i] = st.sidebar.multiselect(i, self.filters[i])

    def reset_filters(self):
        copy_filters = st.session_state['filters'].copy()
        for key in st.session_state['filters']:
            if key not in self.filters:
                del copy_filters[key]

        for key in self.filters:
            if key not in copy_filters.keys():
                copy_filters[key] = []

    def filter(self):
        filtered_df = self.df.copy()
        for key, values in st.session_state[self.filters_name].items():
            if values:
                filtered_df = filtered_df[filtered_df[key].isin(values)]
        return filtered_df
    
    
class Dashboard:
    def __init__(self):
        self.apps = []
        self.new_names_today = ['Пост', 
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
                'Просмотры', 
                'Марка', 
                'Модель',
                'Link']
    
        self.new_names_sold = ['Пост', 
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
                    'Просмотры',
                    'sold_date', 
                    'Марка', 
                    'Модель',
                    'selling_time_hours']
        
        self.filters_today =  [
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
        
        self.filters_tamozhnya = [
            'mark',
            'страна отправления/ экспорта'
        ]
        
        self.display_columns = [
                    'Марка', 
                    'Модель',
                    'Цена', 
                    'Город', 
                    'Год выпуска',
                    'Вид топлива', 
                    'Состояние',
                    'Link']

        self.filters =  [
            'Марка', 
            'Модель',
            'Город', 
            'Кузов', 
            'Вид топлива',
            'Привод', 
            'Коробка передач', 
            'Цвет',
            'Растаможен в РТ', 
            'Состояние',
            'mark',
            'страна отправления/ экспорта']
        
        st.session_state['filters'] = {key:[] for key in self.filters}

        with open('config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)

        self.authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['preauthorized']
        )

    def add_app(self, title, function):
        self.apps.append({
            'title': title,
            'function': function
        })

    def display_dashboard(self):
        df_today, df_sold, df_exracted = load_data()
        with st.sidebar:
            app = option_menu(
                menu_title='Menu',
                menu_icon=None,
                options=['SomonTJ', 'Таможня'],
                orientation='Horizontal',
                default_index=0
            )

        self.authenticator.logout(f"{st.session_state['name']} Logout", 'main')

        if app == 'SomonTJ':
            copy_filters = st.session_state['filters'].copy()
            for key in st.session_state['filters']:
                if key not in self.filters_today:
                    del copy_filters[key]

            for key in self.filters_today:
                if key not in copy_filters.keys():
                    copy_filters[key] = []

            st.session_state['filters'] = copy_filters
            print('SomonTJ', st.session_state['filters'])
            SomonTJ.app(df_today, df_sold)

        if app == 'Таможня':
            copy_filters = st.session_state['filters'].copy()
            for key in st.session_state['filters']:
                if key not in self.filters_tamozhnya:
                    del copy_filters[key]

            for key in self.filters_tamozhnya:
                if key not in copy_filters.keys():
                    copy_filters[key] = []
                    
            st.session_state['filters'] = copy_filters
            print('Таможня', st.session_state['filters'])
            Tamozhnya.app(df_exracted)
    
    def run(self):

        fields = {
            'Form name': 'Login',
            'Username': 'Username',
            'Password': 'Password',
            'Login': 'Login',
        }

        # Attempting login with provided fields and settings
        st.image('main-logo.svg', width=300)
        self.authenticator.login(fields=fields, max_concurrent_users=1, location='main')

        # Checking authentication status
        if st.session_state["authentication_status"]:
            # Logging out if authenticated and displaying dashboard
            logging.info(f"User '{st.session_state['name']}' logged in.")
            self.display_dashboard()
        elif st.session_state["authentication_status"] == False:
            # Displaying error message if authentication fails
            st.error('Username/password is incorrect')
        elif st.session_state["authentication_status"] == None:
            # Displaying warning if authentication status is not determined
            st.warning('Please enter your username and password')
        

if __name__ == '__main__':
    dashboard = Dashboard()
    dashboard.run()
