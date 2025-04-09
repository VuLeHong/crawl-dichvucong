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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "item"))
        )
        
        # Get the page source
        html_content = driver.page_source
        
        return html_content
    
    finally:
        # Always close the browser
        driver.quit()
def clean_string(text):
    text = text.replace("\r\n", "\n")  # Replace \r\n with \n
    text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with a single \n
    text = re.sub(r' +', ' ', text)  # Replace multiple spaces with a single space
    text = "\n".join(line.strip() for line in text.split("\n"))  # Trim spaces around each line
    return text.strip()  # Trim leading/trailing spaces and newlines


url = 'https://dichvucong.gov.vn/p/home/dvc-trang-chu.html'
html_content = get_page_content(url)
final_data = []
final_error = []
soup = BeautifulSoup(html_content, 'html.parser')

item_divs = soup.find_all('div', class_='item')
for item_div in item_divs:
    item_link = item_div.find('a')['href']
    group_event_id = item_link.split('?')[1].split('=')[1]
    url = "https://dichvucong.gov.vn/jsp/rest.jsp"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": "route=1744179329.146.219.582752; JSESSIONID=7F9F5BF68FAFC4BB674F18D6A260679E; TS0115bee1=01f551f5ee54e305f6155dcb32073baa712f74ee23e0c23ed06f360bf4a59c8cc01d3b79b6f03f4de39d4f9f37e06a374d17e8d57e389b50b67b331773a63f278a6c9ba69803aed71166ed5b881933c446c695e67e; TSdcf68b45027=085b7f7344ab2000fae2e321ff30a768ec45b592043214c9646028919985fdc69424f900a6ce96150812f69be71130002c240b19923963a1e35fd660c8a5391ae7a373183134e6d561697eb297197a1ce9719f34f2ea0ef350b76dc8b8821f81",
        "Origin": "https://dichvucong.gov.vn",
        "Referer": "https://dichvucong.gov.vn/p/home/dvc-danh-sach-thu-tuc-theo-nhom-su-kien.html?objectId=1&groupEventId=751",
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
    headers["Referer"] = f"https://dichvucong.gov.vn/p/home/dvc-danh-sach-thu-tuc-theo-nhom-su-kien.html?objectId=1&groupEventId={group_event_id}"
    params = {
            "service": "dvcqg_get_all_procedure_by_group_event_v2",
            "type": "ref",
            "groupEventId": group_event_id,
            "number_record": 200,
            "current_page": 1,
            "keyWord": ""
        }
        
    data = {"params": json.dumps(params)}
    responses = requests.post(
            "https://dichvucong.gov.vn/jsp/rest.jsp",
            headers=headers,
            data=data,
            timeout=10
        )
    if responses.status_code == 200:
        i=0
        procedure_codes = [item["ID"] for item in responses.json()]
        for item in responses.json():
            id = item["ID"]
            name = item["PROCEDURE_NAME"]
            detail_url = f"https://dichvucong.gov.vn/p/home/dvc-tthc-thu-tuc-hanh-chinh-chi-tiet.html?ma_thu_tuc={id}&open_popup=1"
            detail_html_content = get_page_content(detail_url)
            soup1 = BeautifulSoup(detail_html_content, 'html.parser')
            model_content = soup1.find('div', class_='modal-body')
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
                "id": id,
                "title": name,
                "forms": forms,
            }
            print(input_data)
            print('--------------------------------')
            final_data.append(input_data)
            # Extract other information
    else:
        error = {
            "group_event_id": group_event_id,
            "status_code": responses.status_code,
            "response": responses.text
        }
        final_error.append(error)
        print(f"Failed request for Group Event ID: {group_event_id} - Status: {responses.status_code}")
        
        
output_file1 = "dichvucongform.json"                    
with open(output_file1, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)
    
output_file2 = "dichvucong_error.json"                    
with open(output_file2, "w", encoding="utf-8") as f:
    json.dump(final_error, f, ensure_ascii=False, indent=4)
    
