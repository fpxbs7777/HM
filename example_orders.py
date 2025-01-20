from pyhomebroker import HomeBroker
import simplejson
from pycocos import RestClient

# Credenciales predefinidas
broker = '265'
dni = '35465208'
user = 'Renataluciana'
password = 'Amadeo888*'

def is_valid_broker(broker):
    return str(broker).isdigit()

def is_valid_dni(dni):
    return dni.isdigit()

def is_valid_user(user):
    return len(user) > 0

def is_valid_password(password):
    return len(password) > 0

if not is_valid_broker(broker):
    print("Número de Agente inválido")
elif not is_valid_dni(dni):
    print("DNI inválido")
elif not is_valid_user(user):
    print("Usuario inválido")
elif not is_valid_password(password):
    print("Clave inválida")
else:
    try:
        # Crear una instancia del cliente y realizar la autenticación con pyhomebroker
        hb = HomeBroker(int(broker))
        hb.auth.login(dni=dni, user=user, password=password, raise_exception=True)

        # Crear una instancia del cliente REST de pyCocos
        client = RestClient()

        # Obtener el token de autenticación de pyhomebroker
        token = hb.auth.cookies.get('token')  # Obtener el token de las cookies

        # Actualizar los headers de la sesión con el token
        client.update_session_headers({'Authorization': f'Bearer {token}'})

        # Obtener el historial de órdenes
        orders = client.get_orders()
        print("Órdenes obtenidas:", simplejson.dumps(orders, indent=4))
    except Exception as e:
        print(f"Error al obtener las órdenes: {e}")