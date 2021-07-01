import datetime as dt


def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    now_year = dt.date.today().year
    return {
        'year': now_year
    }
