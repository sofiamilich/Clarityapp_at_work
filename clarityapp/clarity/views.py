from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse, FileResponse
import pandas as pd
import os
import sys
import json
import requests
from requests.exceptions import ConnectionError
from time import sleep


# Create your views here.


def indexforclarity1(request):
    return render(request, 'indexforclarity1.html')

def indexforclarity2(request):
    return render(request, 'indexforclarity2.html')


def registration_page(request):
    if request.method == 'POST':
        # Получаем данные:
        name = request.POST.get('name')
        email = request.POST.get('email')
        # Выведем в консоль:
        print(f'Name: {name}')
        print(f'Email: {email}')

        # http-ответ пользователю:
        return HttpResponse('Данные успешно отправлены')
    return render(request, 'registration_page.html')



def generate_report(request):
    # проверка версии пайтона
    if sys.version_info < (3,):
        def u(x):
            try:
                return x.encode("utf8")
            except UnicodeDecodeError:
                return x
    else:
        def u(x):
            if type(x) == type(b''):
                return x.decode('utf8')
            else:
                return x

    # Адрес сервиса Reports для отправки JSON-запросов (регистрозависимый)
    ReportsURL = 'https://api.direct.yandex.com/json/v5/reports'

    # OAuth-токен пользователя, от имени которого будут выполняться запросы
    token = 'y0_AgAAAABufa5iAAZAOQAAAAEK0P-_AABjCoq1fnBEO5fz1mTzpTHhe2dK9A'

    # Логин клиента рекламного агентства
    # Обязательный параметр, если запросы выполняются от имени рекламного агентства
    clientLogin = 'goszakaz-direct-1'

    # какие столбцы подгрузить
    stolbec = ['Date', 'CampaignName', 'Clicks', 'Cost', 'Conversions', 'Criteria', 'AdGroupName',
               'TargetingLocationName', 'Age', 'Gender']

    # ID цели
    goalID = ['301255942']

    # даты отчета
    firstDate = "2024-07-19"
    secondDate = "2024-07-20"





    # Создание HTTP-заголовков запроса
    headers = {
        # OAuth-токен. Использование слова Bearer обязательно
        "Authorization": "Bearer " + token,
        # Логин клиента рекламного агентства
        "Client-Login": clientLogin,
        # Язык ответных сообщений
        "Accept-Language": "ru",
        # Режим формирования отчета
        "processingMode": "auto",
        # Формат денежных значений в отчете
        "returnMoneyInMicros": "false",
        # Не выводить в отчете строку с названием отчета и диапазоном дат
        # "skipReportHeader": "true",
        # Не выводить в отчете строку с названиями полей
        # "skipColumnHeader": "true",
        # Не выводить в отчете строку с количеством строк статистики
        # "skipReportSummary": "true"
    }

    # Создание тела запроса
    body = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": firstDate,
                "DateTo": secondDate
            },
            "Goals": goalID,
            "FieldNames": stolbec,
            "ReportName": f"Отчет №9",
            "ReportType": "CRITERIA_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
            "IncludeDiscount": "NO"
        }
    }

    # Кодирование тела запроса в JSON
    body = json.dumps(body, indent=4)

    # к цикла для выполнения запросов ---
    # Если получен HTTP-код 200, то выводится содержание отчета
    # Если получен HTTP-код 201 или 202, выполняются повторные запросы
    while True:
        try:
            req = requests.post(ReportsURL, body, headers=headers)

            req.encoding = 'utf-8'  # Принудительная обработка ответа в кодировке UTF-8
            if req.status_code == 400:
                print("Параметры запроса указаны неверно или достигнут лимит отчетов в очереди")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код запроса: {}".format(u(body)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            elif req.status_code == 200:
                print("Отчет создан успешно")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                break
            elif req.status_code == 201:
                print("Отчет успешно поставлен в очередь в режиме офлайн")
                retryIn = int(20)
                print("Повторная отправка запроса через {} секунд".format(retryIn))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                sleep(retryIn)
            elif req.status_code == 202:
                print("Отчет формируется в режиме офлайн")
                retryIn = int(req.headers.get("retryIn", 60))
                print("Повторная отправка запроса через {} секунд".format(retryIn))
                print("RequestId:  {}".format(req.headers.get("RequestId", False)))
                sleep(retryIn)
            elif req.status_code == 500:
                print("При формировании отчета произошла ошибка. Пожалуйста, попробуйте повторить запрос позднее")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            elif req.status_code == 502:
                print("Время формирования отчета превысило серверное ограничение.")
                print(
                    "Пожалуйста, попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
                print("JSON-код запроса: {}".format(body))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            else:
                print("Произошла непредвиденная ошибка")
                print("RequestId:  {}".format(req.headers.get("RequestId", False)))
                print("JSON-код запроса: {}".format(body))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break

        # Обработка ошибки, если не удалось соединиться с сервером API Директа
        except ConnectionError:
            # В данном случае мы рекомендуем повторить запрос позднее
            print("Произошла ошибка соединения с сервером API")
            # Принудительный выход из цикла
            break

        # Если возникла какая-либо другая ошибка
        except:
            # В данном случае мы рекомендуем проанализировать действия приложения
            print("Произошла непредвиденная ошибка")
            # Принудительный выход из цикла
            break

        file = open("cashe.csv", "w")
        file.write(req.text)
        file.close()

        # превращаем ответ в таблицу
        df = pd.read_csv("cashe.csv", header=1, sep='\t', index_col=0, encoding="cp1251")

        # меняем значения в конверсиях - на 0, переводит в int

        for col in df.columns:
            if 'Conversions' in col:
                df[col] = df[col].replace('--', '0').astype(int)
                conv = col

        # проверка таблицы
        df.groupby('CampaignName', as_index=False).agg({'Clicks': 'sum', 'Cost': 'sum', conv: 'sum'}).sort_values(conv)



        # выведем нужную кампанию:
        df_campaign = df[df["CampaignName"] == "01. ГОС-ПОДРЯД.Франшиза. РСЯ (настройка ф5)"]

        # Отсортируем полученную таблицу с кампанией по убыванию по столбцу с конверсией, проверим полученные данные:
        df_campaign = df_campaign.sort_values(by='Conversions_301255942_LSC', ascending=False)

        # Посмотрим - какие ключи не дали конверсию и выходят самыми дорогими по расходу. Для этого выведем новую таблицу с ключами, которые не дали конверсии совсем, отсортируем по убыванию:
        conversions_zero = df_campaign[df_campaign['Conversions_301255942_LSC'] == 0].sort_values(by='Cost',
                                                                                                  ascending=False)

        # Отсортируем те строки, которые не дали конверсии и при этом вышли дороже 100 руб/клик. Выведем 5 строк для проверки.
        conversions_zero_sorted = conversions_zero[conversions_zero['Cost'] > 100]

        # Выгрузим полученный отчет в exel и csv:
        conversions_zero_sorted.to_excel(r'C:\Users\User\PycharmProjects\Reports\сost_zero_max_price.xlsx')
        conversions_zero_sorted.to_csv(r'C:\Users\User\PycharmProjects\Reports\сost_zero_max_price.csv')

        # Сохранение отчета в Excel и CSV
        output_excel = "cost_zero_max_price.xlsx"
        output_csv = "cost_zero_max_price.csv"
        df_campaign.to_excel(output_excel, index=False)
        df_campaign.to_csv(output_csv, index=False)

        # Чтение файлов для отправки на скачивание
        with open(output_excel, 'rb') as excel_file:
            excel_data = excel_file.read()
        with open(output_csv, 'rb') as csv_file:
            csv_data = csv_file.read()

        # Создание ответа для скачивания файлов

        if request.method == 'POST':
            return HttpResponse('Готово')
        return render(request, 'generate_report.html')



