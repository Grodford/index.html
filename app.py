from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    # Ваш код здесь
    
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from datetime import datetime
    import pandas as pd
    import os
    import time

    # Список URL для поиска
    urls = [
        'https://uslugi.yandex.ru/54-yekaterinburg/category/remont-i-stroitelstvo/remont-kvartir-i-domov--1816',
        'https://uslugi.yandex.ru/54-yekaterinburg/category/remont-i-stroitelstvo/stroitelstvo-domov-i-kottedzhej--1954'
    ]

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.delete_all_cookies()

    def save_data(data):
        df = pd.DataFrame(data)
        filename = datetime.now().strftime('Парсинг') + '.xlsx'
        df.to_excel(filename, index=False)
        return filename  # Возвращаем имя файла 

    def scrape_data(url):  # Функция для парсинга данных по одному URL
        driver.get(url)
        data = []  # Инициализация списка для сохранения данных

        while True:  # Цикл для прохода по всем страницам
    
            try:
                html = driver.page_source
                soup = BeautifulSoup(html, 'lxml')
                FIO_elements = soup.find_all('a', class_='Link WorkerCard-Title WorkerCard-Title_withLabel') + soup.find_all('a', class_='Link WorkerCard-Title')

                for element in FIO_elements: 
                    fio = element.text.strip() 
                    href = element['href'] 
                    profile_url = 'https://uslugi.yandex.ru' + href if href else None 
                   
                    if fio and profile_url: 
                        driver.get(profile_url) 
                        time.sleep(10)  # Добавлено ожидание перед загрузкой профиля 

                    # Нажимаем на кнопку 
                    try: 
                        button = WebDriverWait(driver, 10).until(  # Увеличено время ожидания
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".Button2.Button2_width_max.Button2_size_md.Button2_theme_action.Button2_pin_circle.PhoneLoader-Button"))
                        ) 
                        button.click() 
                    except Exception as e: 
                        print(f"Не удалось нажать на кнопку: {e}")
                        continue  # Переход к следующему элементу, если не удалось нажать

                    # Ожидаем появления данных телефона
                    try:
                        phone_data_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "Text Text_fontSize_xxl Text_lineHeight_xxl Text_weight_bold TextBlock PhoneLoader-Phone"))
                        )
                        phone_data = phone_data_element.text.strip()
                        print(f"Данные телефона: {phone_data}")
                    except Exception as e:
                        print(f"Не удалось получить данные телефона: {e}")

                        # Извлечение данных
                        profile_html = driver.page_source
                        profile_soup = BeautifulSoup(profile_html, 'lxml')

                        # Извлечение информации из нового тега
                        phone_data = profile_soup.find('div', class_="Text Text_fontSize_xxl Text_lineHeight_xxl Text_weight_bold TextBlock PhoneLoader-Phone")
                        name_data = profile_soup.find('div', class_="Text Text_fontSize_xxl Text_lineHeight_xxl Text_weight_bold TextBlock")
                        address_data = profile_soup.find('div', class_="WorkerGeo-Address")

                        # Проверка наличия данных
                        name = name_data.text.strip() if name_data else 'Информация недоступна'
                        address = address_data.text.strip() if address_data else 'Информация недоступна'
                        phone = phone_data.text.strip() if phone_data else 'Информация недоступна'
                       
                        record = (name, address, phone, profile_url)  # Создаем кортеж для уникальности

                        # Добавляем запись в список данных
                        data.append({
                            'ФИО или наименование организации': name,
                            'Адрес': address,
                            'Телефон': phone,
                            'Ссылки на анкеты': profile_url
                        })

                # Переход на следующую страницу
                next_page = soup.find('a', class_='Link Link_theme_greyDark Pager-Item', rel='next')
                if next_page:
                    next_url = 'https://uslugi.yandex.ru' + next_page['href']
                    driver.get(next_url)
                    time.sleep(2)  # Ожидание загрузки страницы
                else:
                    break  # Если следующей страницы нет, выходим из цикла

            except Exception as e:
                print(f"Произошла ошибка: {e}")
                break  # Выход из цикла при ошибке

        return data  # Возвращаем собранные данные

    unique_records = set()  # Множество для хранения уникальных записей

    all_data = []  # Список для хранения данных из всех URL 

    for url in urls: 
        print(f"Парсинг данных с {url}...") 
        data = scrape_data(url)  # Парсим данные с текущего URL 
        all_data.extend(data)  # Добавляем все данные из текущего URL в общий список 

    # Сохранение данных в файл 
    if all_data:  # Проверка на наличие собранных данных 
        filename = save_data(all_data) 
        print(f"Данные сохранены в файл: {filename}") 
    else:         
        print("Данные не найдены.")
    
    # Открытие файла
    os.startfile(filename)  # Для Windows

    driver.quit()  # Закрываем драйвер после завершения работы

if __name__ == '__main__':
    app.run(debug=True)
