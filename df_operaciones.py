
from pyhomebroker import HomeBroker
import pandas as pd

# Credenciales predefinidas
broker = xxx
dni = 'xx'
user = 'xxx'
password = 'xxx'
account_id = 'xxx'

hb = HomeBroker(broker)
hb.auth.login(dni=dni, user=user, password=password, raise_exception=True)

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