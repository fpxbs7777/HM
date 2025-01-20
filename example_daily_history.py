import datetime
from pyhomebroker import HomeBroker

broker = 265
dni = '35465208'
user = 'Renataluciana'
password = 'Amadeo888*'

hb = HomeBroker(int(broker))
hb.auth.login(dni=dni, user=user, password=password, raise_exception=True)

data = hb.history.get_daily_history('BYMA', datetime.date(2024, 1, 1), datetime.date(2025, 1, 1))
print(data)