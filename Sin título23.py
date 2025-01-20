from pyhomebroker import HomeBroker
import simplejson

# Credenciales predefinidas
broker = '265'
dni = '35465208'
user = 'Renataluciana'
password = 'Amadeo888*'
account_id = '23052'

def is_valid_broker(broker):
    return str(broker).isdigit()

def is_valid_dni(dni):
    return dni.isdigit()

def is_valid_user(user):
    return len(user) > 0

def is_valid_password(password):
    return len(password) > 0

def is_valid_account_id(account_id):
    return account_id.isdigit()

if not is_valid_broker(broker):
    print("Número de Agente inválido")
elif not is_valid_dni(dni):
    print("DNI inválido")
elif not is_valid_user(user):
    print("Usuario inválido")
elif not is_valid_password(password):
    print("Clave inválida")
elif not is_valid_account_id(account_id):
    print("Comitente inválido")
else:
    try:
        # Crear una instancia del cliente y realizar la autenticación con pyhomebroker
        hb = HomeBroker(int(broker))
        hb.auth.login(dni=dni, user=user, password=password, raise_exception=True)

        # Obtener el estado de las órdenes
        orders = hb.orders.get_orders_status(account_id)
        print("Estado de las órdenes obtenidas:", orders)
    except Exception as e:
        print(f"Error al obtener el estado de las órdenes: {e}")