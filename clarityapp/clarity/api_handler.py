import sys
import requests
import json
import time
import pandas as pd

def get_conversions_zero_sorted(token, clientLogin, goalID, stolbec, firstDate, secondDate):
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
                time.sleep(retryIn)
            elif req.status_code == 202:
                print("Отчет формируется в режиме офлайн")
                retryIn = int(req.headers.get("retryIn", 60))
                print("Повторная отправка запроса через {} секунд".format(retryIn))
                print("RequestId:  {}".format(req.headers.get("RequestId", False)))
                time.sleep(retryIn)
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

        # Сохранение ответа в файл
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


        # выведем нужную кампанию:
        df_campaign = df[df["CampaignName"] == "01. ГОС-ПОДРЯД.Франшиза. РСЯ (настройка ф5)"]

        # Отсортируем полученную таблицу с кампанией по убыванию по столбцу с конверсией:
        df_campaign = df_campaign.sort_values(by='Conversions_301255942_LSC', ascending=False)

        # Посмотрим - какие ключи не дали конверсию и выходят самыми дорогими по расходу. Для этого выведем новую таблицу с ключами, которые не дали конверсии совсем, отсортируем по убыванию:
        conversions_zero = df_campaign[df_campaign['Conversions_301255942_LSC'] == 0].sort_values(by='Cost',
                                                                                                  ascending=False)

        # Отсортируем те строки, которые не дали конверсии и при этом вышли дороже 100 руб/клик. Выведем 5 строк для проверки.
        conversions_zero_sorted = conversions_zero[conversions_zero['Cost'] > 100]
        return conversions_zero_sorted