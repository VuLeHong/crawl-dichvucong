from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np  
import re
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import math

def get_page_content(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path=r"/usr/local/bin/chromedriver")
    # D:\Pythons\Python3.12\Lib\site-packages\selenium\webdriver\chrome\chromedriver.exe
    # /usr/local/bin/chromedriver
    driver = webdriver.Chrome(service=service, options=options)
    try:
        # Navigate to the URL
        driver.get(url)
        # Wait for the page to load (adjust timeout as needed)
        time.sleep(2)
        # Get the page source
        html_content = driver.page_source
        return html_content
    
    finally:
        # Always close the browser
        driver.quit()
def clean_string(text):
    text = text.replace("\r\n", "\n")
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def load_existing_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

url = 'https://dichvucong.gov.vn/p/home/dvc-trang-chu.html'
html_content = get_page_content(url)
output_file1 = "dichvucongform.json"
output_file2 = "dichvucong_error.json"

# Load existing data
final_data = load_existing_data(output_file1)
final_error = load_existing_data(output_file2)

# Create sets of existing IDs for quick lookup
existing_ids = {item['id'] for item in final_data}
existing_error_ids = {item['event_id'] for item in final_error}

soup = BeautifulSoup(html_content, 'html.parser')
all_cate = soup.find('div', class_='targetgroup-area section')
item_divs = all_cate.find_all('div', class_='item')

for item_div in item_divs:
    item_link = item_div.find('a')['href']
    level_cate2_div = get_page_content(f"https://dichvucong.gov.vn/p/home/{item_link}")
    soup1 = BeautifulSoup(level_cate2_div, 'html.parser')
    all_title_div = soup1.find('ul', class_='list-expand')
    title_divs = all_title_div.find_all('div', class_='title')
    
    for title_div in title_divs:
        onclick_value1 = title_div.get('onclick')
        if onclick_value1 and 'getProcedureByEvent' in onclick_value1:
            event_id = onclick_value1.split('(')[1].strip(')')
            
            url = "https://dichvucong.gov.vn/jsp/rest.jsp"
            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.6",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://dichvucong.gov.vn",
                "Referer": f"https://dichvucong.gov.vn/p/home/{item_link}",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Sec-GPC": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            }
            
            cookies = {
                "route": "1744179329.146.219.582752",
                "JSESSIONID": "8643D1A3A83A10857B9CD150BDBD985C",
                "TS0115bee1": "01f551f5ee8791fc740c25e2eab99fc41478cbe08aff4f215722a279cfae9ba05e4055e781da3ff3c06366f24a3c7a97169f81dc964829546703fd16589c1f52937ebd7107",
                "TSdcf68b45027": "085b7f7344ab20000d83afbbc9d1c6759dae38652b7694942255f8e13c1a327b9e88ad1ee792679a08096541351130000bfa238538be29c5b7ea9f3e59e0d84522e8ce8218c94a176ad86f9186930d0766f506db7bc846d553c858c1c53c5c14"
            }
            
            params = {
                "service": "dvcqg_gets_procedure_by_event_id_limit_v2",
                "type": "ref",
                "limit": 10000,
                "event_id": event_id,
            }
            data = {"params": json.dumps(params)}
            responses = requests.post(url, headers=headers, cookies=cookies, data=data)
            
            if responses.status_code == 200:
                for response in responses.json():
                    procedure_code = response['PROCEDURE_CODE']
                    # Skip if ID already exists
                    if procedure_code in existing_ids:
                        print(f"Skipping existing procedure: {procedure_code}")
                        continue
                        
                    procedure_name = response['PROCEDURE_NAME']
                    detail_page1 = get_page_content(f"https://dichvucong.gov.vn/p/home/dvc-chi-tiet-thu-tuc-hanh-chinh.html?ma_thu_tuc={procedure_code}")
                    soup2 = BeautifulSoup(detail_page1, 'html.parser')
                    detail_content = soup2.find('div', class_='col-sm-8 col-xs-12')
                    detail_link_div = detail_content.find('a', class_='url')
                    detail_link = detail_link_div['href']
                    detail_page2 = get_page_content(f"https://dichvucong.gov.vn/p/home/{detail_link}")
                    soup3 = BeautifulSoup(detail_page2, 'html.parser')
                    model_content = soup3.find('div', class_='modal-body')
                    form_divs = model_content.find_all('span', class_='link')
                    forms = []
                    for form_div in form_divs:
                        onclick_value = form_div.get('onclick')
                        if onclick_value and 'downloadMaudon' in onclick_value:
                            value = onclick_value.split("'")[1]
                            text_content = form_div.get_text(strip=True)
                            data = {
                                "title": text_content,
                                "url": f"https://csdl.dichvucong.gov.vn/web/jsp/download_file.jsp?ma={value}",
                            }
                            forms.append(data)
                    input_data = {
                        "id": procedure_code,
                        "title": procedure_name,
                        "forms": forms,
                    }
                    print(input_data)
                    print('--------------------------------')
                    final_data.append(input_data)
                    existing_ids.add(procedure_code)
                    save_data(output_file1, final_data)  # Save after each successful addition
            else:
                # Skip if error already recorded
                if event_id in existing_error_ids:
                    print(f"Skipping existing error for Event ID: {event_id}")
                    continue
                    
                error = {
                    "event_id": event_id,
                    "status_code": responses.status_code,
                    "response": responses.text
                }
                final_error.append(error)
                existing_error_ids.add(event_id)
                save_data(output_file2, final_error)  # Save after each error addition
                print(f"Failed request for Event ID: {event_id} - Status: {responses.status_code}")

print("Scraping completed. Data saved incrementally.")