

import SHDA
import pandas as pd

# Credenciales predefinidas
broker = 265  # Negocios Financieros y Bursátiles S.A. (Cocos Capital)
dni = '35465208'
user = 'Renataluciana'
password = 'Amadeo888*'
comitente = '23052'  # Número de comitente

def is_valid_broker(broker):
    return str(broker).isdigit()

def is_valid_dni(dni):
    return dni.isdigit()

def is_valid_user(user):
    return len(user) > 0

def is_valid_password(password):
    return len(password) > 0

def is_valid_account_id(comitente):
    return comitente.isdigit()

if not is_valid_broker(broker):
    print("Número de Agente inválido")
elif not is_valid_dni(dni):
    print("DNI inválido")
elif not is_valid_user(user):
    print("Usuario inválido")
elif not is_valid_password(password):
    print("Clave inválida")
elif not is_valid_account_id(comitente):
    print("Comitente inválido")
else:
    try:
        # Crear una instancia del cliente y realizar la autenticación con SHDA
        hb_shda = SHDA.SHDA(broker, dni, user, password)

        # Obtener la tenencia en cartera utilizando SHDA
        portfolio = hb_shda.account(comitente)
        df_portfolio = pd.DataFrame(portfolio)
        
        # Imprimir el DataFrame tal como está
        print("Datos de la cartera:")
        print(df_portfolio)
        
        # Verificar si el DataFrame está vacío
        if df_portfolio.empty:
            print("No se encontraron tenencias en cartera.")
        else:
            # Verificar la existencia de las columnas antes de intentar renombrarlas y seleccionarlas
            required_columns = ['TICK', 'CANT', 'PCIO', 'CAN0', 'CAN2', 'CAN3']
            if all(column in df_portfolio.columns for column in required_columns):
                # Limpiar y formatear los datos
                df_portfolio = df_portfolio.dropna(subset=required_columns)
                df_portfolio = df_portfolio[df_portfolio['TICK'].notnull() & df_portfolio['CANT'].notnull() & df_portfolio['PCIO'].notnull() & df_portfolio['CAN0'].notnull() & df_portfolio['CAN2'].notnull() & df_portfolio['CAN3'].notnull()]
                
                # Crear un mapeo de los nombres de las columnas
                column_mapping_portfolio = {
                    'TICK': 'symbol',
                    'CANT': 'quantity',
                    'PCIO': 'price',
                    'CAN0': 'can0',
                    'CAN2': 'can2',
                    'CAN3': 'can3'
                }
                
                # Renombrar las columnas del DataFrame
                df_portfolio.rename(columns=column_mapping_portfolio, inplace=True)
                
                # Seleccionar y reordenar las columnas
                df_portfolio = df_portfolio[['symbol', 'quantity', 'price', 'can0', 'can2', 'can3']]
                
                # Eliminar filas duplicadas
                df_portfolio.drop_duplicates(inplace=True)
                
                print("Tenencia en Cartera:")
                print(df_portfolio)
            else:
                print("Las columnas necesarias no están presentes en los datos de la cartera.")
    except Exception as e:
        print(f"Error al obtener los datos: {e}")