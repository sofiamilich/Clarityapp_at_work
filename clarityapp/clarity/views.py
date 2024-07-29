from django.shortcuts import render
from django.http import HttpResponse
from .api_handler import get_conversions_zero_sorted
import time
import csv



# Create your views here.


def indexforclarity1(request):
    return render(request, 'indexforclarity1.html')

def indexforclarity2(request):
    return render(request, 'indexforclarity2.html')

def indexforclarity3(request):
    return render(request, 'indexforclarity3.html')


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
    # Заменим на свои значения
    token = 'y0_AgAAAABufa5iAAZAOQAAAAEK0P-_AABjCoq1fnBEO5fz1mTzpTHhe2dK9A'
    clientLogin = 'goszakaz-direct-1'
    goalID = ['301255942']
    stolbec = ['Date', 'CampaignName', 'Clicks', 'Cost', 'Conversions', 'Criteria', 'AdGroupName',
               'TargetingLocationName', 'Age', 'Gender']
    firstDate = "2024-07-19"
    secondDate = "2024-07-20"

    conversions_zero_sorted = get_conversions_zero_sorted(token, clientLogin, goalID, stolbec, firstDate, secondDate)

    # Создаем HTML-страницу для скачивания отчета
    html = f"""
    <html>
    <head>
        <title>Отчет</title>
    </head>
    <body>
        <a href="{generate_download_url(conversions_zero_sorted)}" download>Скачать файл</a>
    </body>
    </html>
    """

    return HttpResponse(html)





# def generate_report(request):
#     # Заменим на свои значения
#     token = 'y0_AgAAAABufa5iAAZAOQAAAAEK0P-_AABjCoq1fnBEO5fz1mTzpTHhe2dK9A'
#     clientLogin = 'goszakaz-direct-1'
#     goalID = ['301255942']
#     stolbec = ['Date', 'CampaignName', 'Clicks', 'Cost', 'Conversions', 'Criteria', 'AdGroupName',
#                'TargetingLocationName', 'Age', 'Gender']
#     firstDate = "2024-07-19"
#     secondDate = "2024-07-20"
#
#     conversions_zero_sorted = get_conversions_zero_sorted(token, clientLogin, goalID, stolbec, firstDate, secondDate)
#
#     # print(conversions_zero_sorted)
#     return HttpResponse(f"Report generated successfully.{conversions_zero_sorted}")


# def generate_report_data(request):
#     # Вызов функции generate_report_data и сохранение результата в переменной
#     data = generate_report()
#
#     # Передача результата в шаблон HTML
#     context = {
#         'data': data
#     }
#
#     return render(request, 'generate_report_data.html', context)








