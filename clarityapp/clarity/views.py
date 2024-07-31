import logging
from django.shortcuts import render
from django.http import HttpResponse
import time
import pandas as pd
import requests
from requests.exceptions import ConnectionError
import json

logger = logging.getLogger(__name__)


# Главная страница:
def indexforclarity1(request):
    return render(request, 'indexforclarity1.html')


# Страница :Обучение:
def indexforclarity2(request):
    return render(request, 'indexforclarity2.html')


# Страница регистрации:
def registration_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        print(f'Name: {name}')
        print(f'Email: {email}')
        return HttpResponse('Данные успешно отправлены')
    return render(request, 'registration_page.html')


# Получение данных по API и их обработка:
def get_conversions_zero_sorted(ReportsURL, token, clientLogin, goalID, stolbec, firstDate, secondDate):
    headers = {
        "Authorization": "Bearer " + token,
        "Client-Login": clientLogin,
        "Accept-Language": "ru",
        "processingMode": "auto",
        "returnMoneyInMicros": "false"
    }

    body = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": firstDate,
                "DateTo": secondDate
            },
            "Goals": goalID,
            "FieldNames": stolbec,
            "ReportName": "Отчет №9",
            "ReportType": "CRITERIA_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
            "IncludeDiscount": "NO"
        }
    }

    body = json.dumps(body, indent=4)

    try:
        while True:
            try:
                req = requests.post(ReportsURL, body, headers=headers)
                req.encoding = 'utf-8'
                if req.status_code == 400:
                    logger.error("Параметры запроса указаны неверно или достигнут лимит отчетов в очереди")
                    logger.error("RequestId: {}".format(req.headers.get("RequestId", False)))
                    logger.error("JSON-код запроса: {}".format(body))
                    logger.error("JSON-код ответа сервера: \n{}".format(req.json()))
                    return None
                elif req.status_code == 200:
                    logger.info("Отчет создан успешно")
                    logger.info("RequestId: {}".format(req.headers.get("RequestId", False)))
                    break
                elif req.status_code == 201:
                    logger.info("Отчет успешно поставлен в очередь в режиме офлайн")
                    retryIn = int(20)
                    logger.info("Повторная отправка запроса через {} секунд".format(retryIn))
                    logger.info("RequestId: {}".format(req.headers.get("RequestId", False)))
                    time.sleep(retryIn)
                elif req.status_code == 202:
                    logger.info("Отчет формируется в режиме офлайн")
                    retryIn = int(req.headers.get("retryIn", 60))
                    logger.info("Повторная отправка запроса через {} секунд".format(retryIn))
                    logger.info("RequestId:  {}".format(req.headers.get("RequestId", False)))
                    time.sleep(retryIn)
                elif req.status_code == 500:
                    logger.error(
                        "При формировании отчета произошла ошибка. Пожалуйста, попробуйте повторить запрос позднее")
                    logger.error("RequestId: {}".format(req.headers.get("RequestId", False)))
                    logger.error("JSON-код ответа сервера: \n{}".format(req.json()))
                    return None
                elif req.status_code == 502:
                    logger.error("Время формирования отчета превысило серверное ограничение.")
                    logger.error("Пожалуйста, попробуйте изменить параметры запроса - уменьшить "
                                 "период и количество запрашиваемых данных.")
                    logger.error("JSON-код запроса: {}".format(body))
                    logger.error("RequestId: {}".format(req.headers.get("RequestId", False)))
                    logger.error("JSON-код ответа сервера: \n{}".format(req.json()))
                    return None
                else:
                    logger.error("Произошла непредвиденная ошибка")
                    logger.error("RequestId:  {}".format(req.headers.get("RequestId", False)))
                    logger.error("JSON-код запроса: {}".format(body))
                    logger.error("JSON-код ответа сервера: \n{}".format(req.json()))
                    return None
            except ConnectionError:
                logger.error("Произошла ошибка соединения с сервером API")
                return None
            except Exception as e:
                logger.error("Произошла непредвиденная ошибка")
                logger.error("Ошибка: {}".format(e))
                return None

        file = open("cashe.csv", "w")
        file.write(req.text)
        file.close()

        # Прочитаем  полученный csv файл, разделитель укажем \t:
        df = pd.read_csv("cashe.csv", header=1, sep='\t', index_col=0, encoding="cp1251")


        # Обработаем пропуски, подготовим файл к сортировкам:
        # Обработка NaN значений перед преобразованием
        df = df.fillna(0)

        # Заменим в столбцах отсутствующие значения, помеченные -- на 0:
        for col in df.columns:
            if 'Conversions' in col:
                df[col] = df[col].replace('--', '0').astype(int)
        # Выберем из всех полученных кампаний ту, что будем анализировать, отсортируем ее по убыванию цены клика:
        df_campaign = df[df["CampaignName"] == "01. ГОС-ПОДРЯД.Франшиза. РСЯ (настройка ф5)"]
        df_campaign = df_campaign.sort_values(by='Conversions_301255942_LSC', ascending=False)



        # Подготовим первый отчет:
        # Оставим те строки, где конверсия отсутствовала, отсортируем по убыванию цены клика:

        conversions_zero = df_campaign[df_campaign['Conversions_301255942_LSC'] == 0].sort_values(by='Cost',ascending=False)

        # Теперь выберем те, что вышли дороже 100 руб/клик:
        conversions_zero_sorted = conversions_zero[conversions_zero['Cost'] > 100]




        # Подготовим второй отчет:
        # Выберем только те строки, где конверсия была, отсортируем по возрстанию цены клика:
        conversions_positive = df_campaign[df_campaign['Conversions_301255942_LSC'] != 0].sort_values(by='Cost',
                                                                                                      ascending=True)
        # Оставим только строки, где цена заявки вышла дешевле 50 руб:
        conversions_positive_sorted = conversions_positive[conversions_positive['Cost'] < 50]



        # Сформируем словарь из полученных датафреймов, для передачи значений и формирования джанго-таблиц:
        dictionary_reports = {
            'Ключевые фразы с положительной конверсией и ценой ниже 50 руб/клик': conversions_positive_sorted,
            'Ключевые фразы, не принесшие заявки, стоимостью дороже 100 руб/клик': conversions_zero_sorted
        }
        logger.info("dictionary_reports создан успешно")
        return dictionary_reports

    except Exception as e:
        logger.error("Ошибка при обработке данных: %s", e)
        return None



# Распакуем словарь с датасетами и, если они подходят под условие (таблица), выведем их на экран с отчетами:
def generate_report(request):
    # Данные с кампании:
    ReportsURL = 'https://api.direct.yandex.com/json/v5/reports'
    token = 'y0_AgAAAABufa5iAAZAOQAAAAEK0P-_AABjCoq1fnBEO5fz1mTzpTHhe2dK9A'
    clientLogin = 'goszakaz-direct-1'
    goalID = ['301255942']

    # Наименования столбцов:
    stolbec = ['Date', 'CampaignName', 'Clicks', 'Cost', 'Conversions', 'Criteria', 'AdGroupName',
               'TargetingLocationName', 'Age', 'Gender']

    # Интересуемые даты:
    firstDate = "2024-07-19"
    secondDate = "2024-07-20"


    # Запустим функцию, в параметры передадим данные кампании:
    try:
        dictionary_reports = get_conversions_zero_sorted(ReportsURL, token, clientLogin, goalID, stolbec, firstDate,
                                                         secondDate)
        logger.info("dictionary_reports: %s", dictionary_reports)
    except Exception as e:
        logger.error("Ошибка при получении данных от API: %s", e)
        return HttpResponse("Ошибка при получении данных от API", status=500)

    if dictionary_reports is None:
        logger.error("dictionary_reports вернул None")
        return HttpResponse("Ошибка: не удалось получить данные от API", status=500)

    if 'Ключевые фразы с положительной конверсией и ценой ниже 50 руб/клик' not in dictionary_reports or ('Ключевые фразы,'
        ' не принесшие заявки, стоимостью дороже 100 руб/клик') not in dictionary_reports:
        logger.error("Необходимые данные отсутствуют в ответе API")
        return HttpResponse("Ошибка: необходимые данные отсутствуют в ответе API", status=500)

    return render(request, 'generate_report.html', {'dictionary_reports': dictionary_reports})