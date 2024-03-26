import pandas as pd  # Importing pandas library for data manipulation
import requests  # Importing requests library for making HTTP requests
from bs4 import BeautifulSoup  # Importing BeautifulSoup for parsing HTML
import time  # Importing time library for timing operations
from requests.exceptions import RequestException  # Importing RequestException for handling request errors
import logging  # Importing logging for logging errors and warnings
import concurrent.futures  # Importing concurrent.futures for parallel execution
from datetime import datetime, timedelta  # Importing datetime for working with dates and times
import threading  # Importing threading for threading operations
import math  # Importing math library for mathematical operations


logging.basicConfig(filename='error_log.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')  # Configuring logging
logging.warning('New Session Has Started')  # Logging a warning for a new session
YEAR = 1950  # Setting a constant for the year
MAX_RETRIES = 3  # Setting maximum retries for HTTP requests
SLEEP_BETWEEN_REQUESTS = 5  # Setting sleep time between HTTP requests
NUM_PROCESSES = 8  # Setting number of processes for parallel execution
BATCH_SIZE = 100  # Setting batch size for processing data

class CarMain:
    def __init__(self) -> None:
        # Initializing class attributes
        self.year = YEAR  # Setting the year attribute to a constant value
        self.category = 'legkovyie-avtomobili'  # Setting the category of cars
        self.session = requests.Session()  # Creating a requests Session object for making HTTP requests
        self.lock = threading.Lock()  # Creating a threading lock for thread safety
        # Constructing the URL for fetching car data based on category and year
        self.URL = f"https://somon.tj/transport/{self.category}/year_min---{self.year}/?page="
        # Initializing dictionaries to store car information for both available and sold cars
        self.car_info = {
            'Name': [], 'PostID': [], 'AuthorName': [], 'AuthorID': [],
            'WhatsApp': [], 'DatePublished':[], 'Description': [],
            'Price': [], 'City': [], 'Кузов': [], 'Год выпуска': [],
            'Цвет': [], 'Привод': [], 'Объем двигателя': [], 'Состояние': [],
            'Вид топлива': [], 'Растаможен в РТ': [], 'Коробка передач': [],
            'Views': []
        }
        self.car_info_sold = {
            'Name': [], 'PostID': [], 'AuthorName': [], 'AuthorID': [],
            'WhatsApp': [], 'DatePublished':[], 'Description': [],
            'Price': [], 'City': [], 'Кузов': [], 'Год выпуска': [],
            'Цвет': [], 'Привод': [], 'Объем двигателя': [], 'Состояние': [],
            'Вид топлива': [], 'Растаможен в РТ': [], 'Коробка передач': [],
            'Views': []
        }
        # Defining headers for the car information
        self.headers = ['Кузов', 'Год выпуска', 'Цвет', 'Привод', 'Объем двигателя',
           'Состояние', 'Вид топлива', 'Растаможен в РТ', 'Коробка передач']

    def fetch_page(self, url):
        try:
            # Sending a GET request to the specified URL using the session object
            response = self.session.get(url)
            # Checking if the response was successful (status code 200)
            response.raise_for_status()
            # Returning the content of the response
            return response.content
        except Exception as e:
            # Logging an error if there was an exception during the request
            logging.error(f'Error fetching page: {url} - {str(e)}')
            # Returning None if there was an error
            return None

    def get_links(self):
        try:
            # Fetching the content of the first page to determine the total number of pages
            soup = BeautifulSoup(self.session.get(f'{self.URL}{1}').content, 'html.parser')
            # Extracting the total number of pages from the last page number link
            page_num = int(soup.find_all('a', class_='page-number')[-1].text)
            links = []

            # Using ThreadPoolExecutor for concurrent execution of fetch_page method
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Creating a dictionary to map each future (task) to its URL
                future_to_url = {executor.submit(self.fetch_page, f'{self.URL}{i}'): i for i in range(1, page_num + 1)}

                # Iterating through completed futures
                for future in concurrent.futures.as_completed(future_to_url):
                    try:
                        # Retrieving the result of the future (response content)
                        response_content = future.result()
                        if response_content:
                            # Parsing the response content with BeautifulSoup
                            soup = BeautifulSoup(response_content, 'html.parser')
                            # Finding all car listing divs on the page
                            divs = soup.find_all(class_='js-item-listing')

                            # Extracting links from each car listing div and appending to links list
                            for div in divs:
                                link = div.find('a')['href']
                                links.append('https://somon.tj' + link)
                            # Logging completion of getting links from the page
                            logging.info(f'Completed getting links from page {future_to_url[future]}/{page_num}')
                    except Exception as e:
                        # Handling exceptions for individual futures
                        error_message = f'Error accessing page: {future_to_url[future]} - {str(e)}'
                        print(error_message)  # Printing error message (optional)
                        logging.error(error_message)  # Logging error message

            return links  # Returning the list of links
        except Exception as e:
            # Logging error if there's an exception in the outer try block
            logging.error(f'Error getting links: {str(e)}')
            return None  # Returning None if there was an error

    def parse_soup(self, car_info_dict, soup, link):
        # Extracting car data and headers from the BeautifulSoup object
        car_data = [i.text for i in soup.find_all(class_='value-chars')]
        car_data_headers = [i.text.replace(':', '') for i in soup.find_all(class_='key-chars')]
        
        # Checking if the extracted data represents a car
        if len(car_data) < 9:
            # Logging that the extracted data does not represent a car
            logging.info(f'{link} - is not a car({car_data})')
            return None

        # Updating car information dictionary with the extracted data
        for header, data in zip(car_data_headers, car_data):
            if header in car_info_dict:
                car_info_dict[header].append(data)

        # Extracting additional information about the car
        name = soup.find(class_='title-announcement').text.replace('\n', '').lstrip().rstrip()
        # Handling multiple names separated by commas
        if ',' in name:
            name = name.split(',')[0]
        # Extracting author name and ID
        car_info_dict['AuthorName'].append(soup.find(class_='author-name js-online-user').text.strip())
        car_info_dict['AuthorID'].append(soup.find(class_='other-announcement-author').get('href').split('/')[-2])
        car_info_dict['Views'].append(soup.find(class_='counter-views').text.split(' ')[1])

        # Handling timestamp of the car listing publication date
        timestamp = soup.find(class_='date-meta').text.replace('Опубликовано: ', '')
        if 'Сегодня' in timestamp:
            current_date = datetime.now().strftime('%d.%m.%Y')
            timestamp = timestamp.replace('Сегодня', current_date)
        elif 'Вчера' in timestamp:
            yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
            timestamp = timestamp.replace('Вчера', yesterday_date)

        # Adding parsed timestamp to car information dictionary
        car_info_dict['DatePublished'].append(timestamp)

        # Extracting WhatsApp contact information if available
        whatsapp_elem = soup.find(class_='btn-author announcement-text-message__button _whatsapp js-messenger')
        if whatsapp_elem is not None:
            car_info_dict['WhatsApp'].append(whatsapp_elem.get('href').split('&')[0].split('phone=')[1])
        else:
            car_info_dict['WhatsApp'].append(None)

        # Adding additional information to the car information dictionary
        car_info_dict['Name'].append(name)
        car_info_dict['PostID'].append(soup.find(class_='number-announcement').text.split(':')[-1].lstrip().rstrip())
        car_info_dict['Description'].append(soup.find(class_='js-description').text.replace('\n', ' '))
        car_info_dict['City'].append(soup.find(class_='announcement__location').text.rstrip().lstrip())
        # Extracting and formatting car price
        car_price = ''.join([i for i in soup.find(class_='announcement-price__cost').text.replace(" ", '').strip().replace('\n', ' ').split()[0] if i.isnumeric()])
        car_info_dict['Price'].append(int(car_price))

    def get_car_info(self, link):
        retries = MAX_RETRIES  # Maximum number of retries for fetching the page
        for _ in range(retries):
            try:
                # Sending a GET request to the provided link
                response = self.session.get(link)
                response.raise_for_status()  # Checking if the response was successful

                soup = BeautifulSoup(response.content, 'html.parser')  # Parsing the HTML content using BeautifulSoup

                # Checking if the car listing is marked as sold
                sold = soup.find(class_='phone-author phone-author--sold phone-author--toggled')
                if not sold:
                    # If the car is not sold, parse its information and break the loop
                    try:
                        self.parse_soup(self.car_info, soup, link)
                        break
                    except RequestException as re:
                        # Logging a warning if there's an error parsing the car info
                        logging.warning(f'Unable to get car info: {re}')
                else:
                    # Logging that the car was sold and parsing its information for the sold cars dictionary
                    logging.info(f'Car was sold - {link}')
                    try:
                        self.parse_soup(self.car_info_sold, soup, link)
                        break
                    except RequestException as re:
                        # Logging a warning if there's an error parsing the car info for sold cars
                        logging.warning(f'Unable to get car info: {re}')

            except RequestException as re:
                # Logging and retrying in case of connection error
                logging.info(f'Retrying due to connection error: {re}')
                print(f'Retrying due to connection error: {re}')
                time.sleep(SLEEP_BETWEEN_REQUESTS)  # Sleeping between retries
        else:
            # Logging if failed after maximum retries
            logging.info(f'Failed after {retries} retries: {link}')
            print(f'Failed after {retries} retries: {link}')

    def process_links(self, link_chunk):
        # Iterating through each link in the link chunk
        for link in link_chunk:
            try:
                # Getting car information for the current link
                self.get_car_info(link)
            except Exception as e:
                # Handling exceptions that might occur during processing
                error_message = f'Error accessing page: {link}-{e}'
                print(error_message)  # Printing the error message (optional)
                logging.error(error_message)  # Logging the error message

    def check_links(self):
        try:
            # Getting new links
            new = self.get_links()
            logging.info(f'All new links are collected - {len(new)}')

            # Checking if new links were collected successfully
            if new is None:
                logging.info('Not able to collect links')
                raise ValueError
            else:
                # Creating a DataFrame for new links
                new_links = pd.DataFrame({"Link": new})

            # Identifying sold and new cars fron freshly collected links
            links_ids = [int(i.split('adv/')[1].split('_')[0]) for i in new_links['Link'].tolist()]
            new_links['PostID'] = links_ids
            df_today = pd.read_excel('ttoday.xlsx')
            new_cars = new_links[~new_links['PostID'].isin(df_today['PostID'].tolist())]
            sold_cars = df_today[~df_today['PostID'].isin(new_links['PostID'].tolist())]

            # Saving new links to the Excel file
            new_links.to_excel('links.xlsx', index=False)

            # Logging and returning the results
            logging.info(f'check_links -> Done (new-{len(new_cars)}, sold-{len(sold_cars)})')
            return [sold_cars['PostID'].tolist(), new_cars['Link'].tolist()]
        except Exception as e:
            # Logging errors if any occur during the process
            logging.error(f'Error checking links: {str(e)}')
            return None

    def update(self):
        try:
            logging.info('Start updating...')
            
            # Checking for new and sold cars
            actions = self.check_links()
            
            # Loading data from Excel files
            df_today = pd.read_excel('ttoday.xlsx')
            df_sold = pd.read_excel('sold.xlsx')

            # Moving rows to the sold base
            postids = actions[0]
            df_sold = df_today[df_today['PostID'].isin(postids)].copy()
            df_today = df_today[~df_today['PostID'].isin(postids)].copy()
            df_sold.reset_index(drop=True, inplace=True)
            df_today.reset_index(drop=True, inplace=True)

            current_date = datetime.now().date()

            # Adding a new column 'sold_date' to df_sold with the current date
            df_sold['sold_date'] = pd.to_datetime(current_date)
            df_sold['Name'] = df_sold['Name'].apply(lambda x: x.split(',')[0] if ',' in x else x)
            df_sold['Mark'] = df_sold['Name'].apply(lambda x: x.split(' ')[0])
            df_sold['Model'] = df_sold['Name'].apply(lambda x: " ".join(x.split(' ')[1:]))
            df_sold_old = pd.read_excel('sold.xlsx')
            df_sold = pd.concat([df_sold_old, df_sold]).reset_index(drop=True)
            
            # Logging total number of sold cars
            logging.info(f'Total # of sold cars - {len(df_sold)}')
            df_sold['Объем двигателя'] = df_sold['Объем двигателя'].apply(self.transform_volume)
            df_sold.to_excel('sold.xlsx', index=False)

            # Logging completion of moving data to the sold base
            logging.info('Data was moved to sold.xlsx')

            # Downloading new data
            batch_size = 5000  # Define the batch size for downloading new data
            total_links = actions[1]  # Get the total links for new cars
            total_iterations = math.ceil(len(total_links) / batch_size)  # Calculate total iterations required

            # Looping through batches of links
            for i in range(total_iterations):
                self.car_info = {key: [] for key in self.car_info.keys()}
                self.car_info_sold = {key: [] for key in self.car_info_sold.keys()}

                start_index = i * batch_size
                end_index = min((i + 1) * batch_size, len(total_links))

                # Extracting links for the current batch
                links = total_links[start_index:end_index]

                link_chunks = [links[j:j + BATCH_SIZE] for j in range(0, len(links), BATCH_SIZE)]

                # Processing links in parallel using ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_PROCESSES) as executor:
                    executor.map(self.process_links, link_chunks)

                # Concatenating new data with existing data and saving to Excel
                df_today_new = pd.DataFrame(self.car_info)
                # df_old = pd.read_excel('ttoday.xlsx')
                df_today = pd.concat([df_today_new, df_today]).reset_index(drop=True)
                df_today['Объем двигателя'] = df_today['Объем двигателя'].apply(self.transform_volume)
                df_today.to_excel('ttoday.xlsx', index=False)
                
                logging.info('Number of actually sold cards: {}'.format(len(self.car_info_sold)))
                df_sold_today = pd.DataFrame(self.car_info_sold)
                df_sold_today['Объем двигателя'] = df_sold_today['Объем двигателя'].apply(self.transform_volume)
                df_sold_old = pd.read_excel('sold.xlsx')
                df_sold_today = pd.concat([df_sold_old, df_sold_today]).reset_index(drop=True)
                df_sold_today.to_excel('sold.xlsx', index=False)

                # Logging completion of downloading data for the current batch
                logging.warning(f'Done downloading {start_index}:{end_index} data!')
        except Exception as e:
            # Logging undefined errors during update
            logging.error(f'Undefined error during update: {str(e)}')

    def transform_volume(self,x):
            try:
                return float(x)
            except Exception as e:
                if x == 0.0:
                    return 0.0
                elif x != 'Электрический':
                    return float(x.strip().split(' ')[0])
                else:
                    return 0.0  

    def export(self):
        try:
            # Reading data from Excel files
            df_today = pd.read_excel('ttoday.xlsx')
            df_sold = pd.read_excel('sold.xlsx')
            try:
                # Removing duplicates from both DataFrames
                df_today = df_today.drop_duplicates()
                df_sold = df_sold.drop_duplicates()
                logging.info('Duplicates cleared.')
            except Exception as e:
                # Logging error if there's an issue clearing duplicates
                logging.error(f'Error clearing duplicates: {str(e)}')

            # Splitting 'Name' column into 'Mark' and 'Model' for sold DataFrame
            df_sold['Name'] = df_sold['Name'].apply(lambda x: x.split(',')[0] if ',' in x else x)
            df_sold['Mark'] = df_sold['Name'].apply(lambda x: x.split(' ')[0])
            df_sold['Model'] = df_sold['Name'].apply(lambda x: " ".join(x.split(' ')[1:]))

            # Splitting 'Name' column into 'Mark' and 'Model' for today DataFrame
            df_today['Name'] = df_today['Name'].apply(lambda x: x.split(',')[0] if ',' in x else x)
            df_today['Mark'] = df_today['Name'].apply(lambda x: x.split(' ')[0])
            df_today['Model'] = df_today['Name'].apply(lambda x: " ".join(x.split(' ')[1:]))

            # Getting current date in YYYY-MM-DD format
            current_date = datetime.now().strftime('%Y-%m-%d')

            # Appending the date to the file names for export
            ttoday_filename = f'export/ttoday_{current_date}.xlsx'
            sold_filename = f'export/sold_{current_date}.xlsx'

            # Exporting transformed DataFrames to Excel files
            df_today.to_excel(ttoday_filename, index=False)
            df_sold.to_excel(sold_filename, index=False)

            # Logging completion of name transformation and export
            logging.info('Name transformation completed.')
        except Exception as e:
            # Logging error if there's an issue exporting names
            logging.error(f'Error exporting names: {str(e)}')

collector = CarMain()
collector.update()
collector.export()

# print(collector.check_links())