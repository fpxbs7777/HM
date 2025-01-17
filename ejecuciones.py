# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 16:20:45 2025

@author: Outlet VL
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Home Broker API - Market data downloader
# https://github.com/crapher/pyhomebroker.git
#
# Copyright 2020 Diego Degese
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from pyhomebroker import HomeBroker
import pandas as pd

# Credenciales predefinidas
broker = xxxxx
dni = 'xxx'
user = 'xxx'
password = 'xxx'
account_id = 'xxx'

hb = HomeBroker(broker)
hb.auth.login(dni=dni, user=user, password=password, raise_exception=True)

# Enviar una orden de compra al mercado
symbol = 'AAPL'
settlement = '48hs'
price = 150.0
size = 10
order_number_buy = hb.orders.send_buy_order(symbol, settlement, price, size)
print(f"Orden de compra enviada, número de orden: {order_number_buy}")

# Enviar una orden de venta al mercado
symbol = 'AAPL'
settlement = '48hs'
price = 155.0
size = 5
order_number_sell = hb.orders.send_sell_order(symbol, settlement, price, size)
print(f"Orden de venta enviada, número de orden: {order_number_sell}")

# Obtener el estado de las órdenes
orders = hb.orders.get_orders_status(account_id)

# Convertir los datos a un DataFrame de pandas
df_orders = pd.DataFrame(orders)
print("Estado de las órdenes:")
print(df_orders)

# Filtrar las órdenes ejecutadas
executed_orders = df_orders[df_orders['status'] == 'executed']

print("Operaciones ya efectuadas:")
print(executed_orders)