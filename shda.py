from os import path
import re
import json
import datetime
import requests
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq
from common import brokers, BrokerNotSupportedException, convert_to_numeric_columns, SessionException

class SHDA:
    __settlements_int_map = {
        '1': 'spot',
        '2': '24hs',
        '3': '48hs'}

    __personal_portfolio_index = ['symbol', 'settlement']
    __personal_portfolio_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'expiration', 'strike', 'kind', 'underlying_asset', 'close']
    __empty_personal_portfolio = pd.DataFrame(columns=__personal_portfolio_columns).set_index(__personal_portfolio_index)

    __repos_index = ['symbol', 'settlement']
    __repos_columns = ['symbol', 'days', 'settlement', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'close']
    __empty_repos = pd.DataFrame(columns=__repos_columns).set_index(__repos_index)

    __call_put_map = {
            0: '',
            1: 'CALL',
            2: 'PUT'}
    __boards = {
            0:"",
            'accionesLideres':'bluechips',
            'panelGeneral':'general_board',
            'cedears': 'cedears',
            'rentaFija':'government_bonds',
            'letes':'short_term_government_bonds',
            'obligaciones':'corporate_bonds'}

    __settlements_map = {'':0,'spot': 1,'24hs': 2,'48hs': 3}
    __securities_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'group']
    __filter_columns = ['Symbol', 'Term', 'BuyQuantity', 'BuyPrice', 'SellPrice', 'SellQuantity', 'LastPrice', 'VariationRate', 'StartPrice', 'MaxPrice', 'MinPrice', 'PreviousClose', 'TotalAmountTraded', 'TotalQuantityTraded', 'Trades', 'TradeDate', 'Panel']
    __numeric_columns = ['last', 'open', 'high', 'low', 'volume', 'turnover', 'operations', 'change', 'bid_size', 'bid', 'ask_size', 'ask', 'previous_close']
    __numeric_columns_sp = ['last', 'high', 'low','change']
    __filter_columns_sp = ['Symbol', 'LastPrice', 'VariationRate', 'MaxPrice', 'MinPrice', 'Panel']
    __sp_columns=['symbol','last','change','high','low','group']
    
    def __init__(self,broker,dni,user,password):
        self.__s = requests.session()
        self.__host = self.__get_broker_data(broker)['page']
        self.__is_user_logged_in = False

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "DNT" : "1",    
            "Connection" : "keep-alive",    
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "none",
            "Sec-Fetch-User" : "?1"   
        }

        response = self.__s.get(url = f"https://{self.__host}", headers=headers)
        status = response.status_code
        if status != 200:
          print("Server Down", status)  
          exit()

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "Content-Type" : "application/x-www-form-urlencoded",
            "Origin" : f"https://{self.__host}/",
            "DNT" : "1",    
            "Connection" : "keep-alive",
            "Referer" : f"https://{self.__host}/",
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "same-origin",
            "Sec-Fetch-User" : "?1",
            "TE" : "trailers"
        }

        data = {
            "IpAddress": "",
            "Dni": dni,
            "Usuario": user,
            "Password": password
        }  

        try:
            response = self.__s.post(url = f"https://{self.__host}/Login/Ingresar", headers=headers, data = data, allow_redirects=True)

            response.raise_for_status()

            doc = pq(response.text)
            if not doc('#usuarioLogueado'):
                print("Check login credentials")
                errormsg = doc('.callout-danger')
                if errormsg:
                    raise SessionException(errormsg.text())

                raise SessionException('Session cannot be created.  Check the entered information and try again.')

            print("Connected!")
            self.__is_user_logged_in = True
        except Exception as ex:
            self.__is_user_logged_in = False
            exit()

    def get_bluechips(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"accionesLideres","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_galpones(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"panelGeneral","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_cedear(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"cedears","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"rentaFija","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_short_term_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"letes","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_corporate_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
           from os import path
import re
import json
import datetime
import requests
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq
from common import brokers, BrokerNotSupportedException, convert_to_numeric_columns, SessionException

class SHDA:
    __settlements_int_map = {
        '1': 'spot',
        '2': '24hs',
        '3': '48hs'}

    __personal_portfolio_index = ['symbol', 'settlement']
    __personal_portfolio_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'expiration', 'strike', 'kind', 'underlying_asset', 'close']
    __empty_personal_portfolio = pd.DataFrame(columns=__personal_portfolio_columns).set_index(__personal_portfolio_index)

    __repos_index = ['symbol', 'settlement']
    __repos_columns = ['symbol', 'days', 'settlement', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'close']
    __empty_repos = pd.DataFrame(columns=__repos_columns).set_index(__repos_index)

    __call_put_map = {
            0: '',
            1: 'CALL',
            2: 'PUT'}
    __boards = {
            0:"",
            'accionesLideres':'bluechips',
            'panelGeneral':'general_board',
            'cedears': 'cedears',
            'rentaFija':'government_bonds',
            'letes':'short_term_government_bonds',
            'obligaciones':'corporate_bonds'}

    __settlements_map = {'':0,'spot': 1,'24hs': 2,'48hs': 3}
    __securities_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'group']
    __filter_columns = ['Symbol', 'Term', 'BuyQuantity', 'BuyPrice', 'SellPrice', 'SellQuantity', 'LastPrice', 'VariationRate', 'StartPrice', 'MaxPrice', 'MinPrice', 'PreviousClose', 'TotalAmountTraded', 'TotalQuantityTraded', 'Trades', 'TradeDate', 'Panel']
    __numeric_columns = ['last', 'open', 'high', 'low', 'volume', 'turnover', 'operations', 'change', 'bid_size', 'bid', 'ask_size', 'ask', 'previous_close']
    __numeric_columns_sp = ['last', 'high', 'low','change']
    __filter_columns_sp = ['Symbol', 'LastPrice', 'VariationRate', 'MaxPrice', 'MinPrice', 'Panel']
    __sp_columns=['symbol','last','change','high','low','group']
    
    def __init__(self,broker,dni,user,password):
        self.__s = requests.session()
        self.__host = self.__get_broker_data(broker)['page']
        self.__is_user_logged_in = False

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "DNT" : "1",    
            "Connection" : "keep-alive",    
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "none",
            "Sec-Fetch-User" : "?1"   
        }

        response = self.__s.get(url = f"https://{self.__host}", headers=headers)
        status = response.status_code
        if status != 200:
          print("Server Down", status)  
          exit()

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "Content-Type" : "application/x-www-form-urlencoded",
            "Origin" : f"https://{self.__host}/",
            "DNT" : "1",    
            "Connection" : "keep-alive",
            "Referer" : f"https://{self.__host}/",
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "same-origin",
            "Sec-Fetch-User" : "?1",
            "TE" : "trailers"
        }

        data = {
            "IpAddress": "",
            "Dni": dni,
            "Usuario": user,
            "Password": password
        }  

        try:
            response = self.__s.post(url = f"https://{self.__host}/Login/Ingresar", headers=headers, data = data, allow_redirects=True)

            response.raise_for_status()

            doc = pq(response.text)
            if not doc('#usuarioLogueado'):
                print("Check login credentials")
                errormsg = doc('.callout-danger')
                if errormsg:
                    raise SessionException(errormsg.text())

                raise SessionException('Session cannot be created.  Check the entered information and try again.')

            print("Connected!")
            self.__is_user_logged_in = True
        except Exception as ex:
            self.__is_user_logged_in = False
            exit()

    def get_bluechips(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"accionesLideres","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_galpones(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"panelGeneral","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_cedear(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"cedears","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"rentaFija","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_short_term_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"letes","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_corporate_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
           from os import path
import re
import json
import datetime
import requests
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq
from common import brokers, BrokerNotSupportedException, convert_to_numeric_columns, SessionException

class SHDA:
    __settlements_int_map = {
        '1': 'spot',
        '2': '24hs',
        '3': '48hs'}

    __personal_portfolio_index = ['symbol', 'settlement']
    __personal_portfolio_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'expiration', 'strike', 'kind', 'underlying_asset', 'close']
    __empty_personal_portfolio = pd.DataFrame(columns=__personal_portfolio_columns).set_index(__personal_portfolio_index)

    __repos_index = ['symbol', 'settlement']
    __repos_columns = ['symbol', 'days', 'settlement', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'close']
    __empty_repos = pd.DataFrame(columns=__repos_columns).set_index(__repos_index)

    __call_put_map = {
            0: '',
            1: 'CALL',
            2: 'PUT'}
    __boards = {
            0:"",
            'accionesLideres':'bluechips',
            'panelGeneral':'general_board',
            'cedears': 'cedears',
            'rentaFija':'government_bonds',
            'letes':'short_term_government_bonds',
            'obligaciones':'corporate_bonds'}

    __settlements_map = {'':0,'spot': 1,'24hs': 2,'48hs': 3}
    __securities_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'group']
    __filter_columns = ['Symbol', 'Term', 'BuyQuantity', 'BuyPrice', 'SellPrice', 'SellQuantity', 'LastPrice', 'VariationRate', 'StartPrice', 'MaxPrice', 'MinPrice', 'PreviousClose', 'TotalAmountTraded', 'TotalQuantityTraded', 'Trades', 'TradeDate', 'Panel']
    __numeric_columns = ['last', 'open', 'high', 'low', 'volume', 'turnover', 'operations', 'change', 'bid_size', 'bid', 'ask_size', 'ask', 'previous_close']
    __numeric_columns_sp = ['last', 'high', 'low','change']
    __filter_columns_sp = ['Symbol', 'LastPrice', 'VariationRate', 'MaxPrice', 'MinPrice', 'Panel']
    __sp_columns=['symbol','last','change','high','low','group']
    
    def __init__(self,broker,dni,user,password):
        self.__s = requests.session()
        self.__host = self.__get_broker_data(broker)['page']
        self.__is_user_logged_in = False

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "DNT" : "1",    
            "Connection" : "keep-alive",    
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "none",
            "Sec-Fetch-User" : "?1"   
        }

        response = self.__s.get(url = f"https://{self.__host}", headers=headers)
        status = response.status_code
        if status != 200:
          print("Server Down", status)  
          exit()

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "Content-Type" : "application/x-www-form-urlencoded",
            "Origin" : f"https://{self.__host}/",
            "DNT" : "1",    
            "Connection" : "keep-alive",
            "Referer" : f"https://{self.__host}/",
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "same-origin",
            "Sec-Fetch-User" : "?1",
            "TE" : "trailers"
        }

        data = {
            "IpAddress": "",
            "Dni": dni,
            "Usuario": user,
            "Password": password
        }  

        try:
            response = self.__s.post(url = f"https://{self.__host}/Login/Ingresar", headers=headers, data = data, allow_redirects=True)

            response.raise_for_status()

            doc = pq(response.text)
            if not doc('#usuarioLogueado'):
                print("Check login credentials")
                errormsg = doc('.callout-danger')
                if errormsg:
                    raise SessionException(errormsg.text())

                raise SessionException('Session cannot be created.  Check the entered information and try again.')

            print("Connected!")
            self.__is_user_logged_in = True
        except Exception as ex:
            self.__is_user_logged_in = False
            exit()

    def get_bluechips(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"accionesLideres","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_galpones(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"panelGeneral","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_cedear(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"cedears","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"rentaFija","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_short_term_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"letes","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_corporate_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
           from os import path
import re
import json
import datetime
import requests
import numpy as np
import pandas as pd
from pyquery import PyQuery as pq
from common import brokers, BrokerNotSupportedException, convert_to_numeric_columns, SessionException

class SHDA:
    __settlements_int_map = {
        '1': 'spot',
        '2': '24hs',
        '3': '48hs'}

    __personal_portfolio_index = ['symbol', 'settlement']
    __personal_portfolio_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'expiration', 'strike', 'kind', 'underlying_asset', 'close']
    __empty_personal_portfolio = pd.DataFrame(columns=__personal_portfolio_columns).set_index(__personal_portfolio_index)

    __repos_index = ['symbol', 'settlement']
    __repos_columns = ['symbol', 'days', 'settlement', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'close']
    __empty_repos = pd.DataFrame(columns=__repos_columns).set_index(__repos_index)

    __call_put_map = {
            0: '',
            1: 'CALL',
            2: 'PUT'}
    __boards = {
            0:"",
            'accionesLideres':'bluechips',
            'panelGeneral':'general_board',
            'cedears': 'cedears',
            'rentaFija':'government_bonds',
            'letes':'short_term_government_bonds',
            'obligaciones':'corporate_bonds'}

    __settlements_map = {'':0,'spot': 1,'24hs': 2,'48hs': 3}
    __securities_columns = ['symbol', 'settlement', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime', 'group']
    __filter_columns = ['Symbol', 'Term', 'BuyQuantity', 'BuyPrice', 'SellPrice', 'SellQuantity', 'LastPrice', 'VariationRate', 'StartPrice', 'MaxPrice', 'MinPrice', 'PreviousClose', 'TotalAmountTraded', 'TotalQuantityTraded', 'Trades', 'TradeDate', 'Panel']
    __numeric_columns = ['last', 'open', 'high', 'low', 'volume', 'turnover', 'operations', 'change', 'bid_size', 'bid', 'ask_size', 'ask', 'previous_close']
    __numeric_columns_sp = ['last', 'high', 'low','change']
    __filter_columns_sp = ['Symbol', 'LastPrice', 'VariationRate', 'MaxPrice', 'MinPrice', 'Panel']
    __sp_columns=['symbol','last','change','high','low','group']
    
    def __init__(self,broker,dni,user,password):
        self.__s = requests.session()
        self.__host = self.__get_broker_data(broker)['page']
        self.__is_user_logged_in = False

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "DNT" : "1",    
            "Connection" : "keep-alive",    
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "none",
            "Sec-Fetch-User" : "?1"   
        }

        response = self.__s.get(url = f"https://{self.__host}", headers=headers)
        status = response.status_code
        if status != 200:
          print("Server Down", status)  
          exit()

        headers = {
            "Host" : f"{self.__host}",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate",
            "Content-Type" : "application/x-www-form-urlencoded",
            "Origin" : f"https://{self.__host}/",
            "DNT" : "1",    
            "Connection" : "keep-alive",
            "Referer" : f"https://{self.__host}/",
            "Upgrade-Insecure-Requests" : "1",
            "Sec-Fetch-Dest" : "document",
            "Sec-Fetch-Mode" : "navigate",
            "Sec-Fetch-Site" : "same-origin",
            "Sec-Fetch-User" : "?1",
            "TE" : "trailers"
        }

        data = {
            "IpAddress": "",
            "Dni": dni,
            "Usuario": user,
            "Password": password
        }  

        try:
            response = self.__s.post(url = f"https://{self.__host}/Login/Ingresar", headers=headers, data = data, allow_redirects=True)

            response.raise_for_status()

            doc = pq(response.text)
            if not doc('#usuarioLogueado'):
                print("Check login credentials")
                errormsg = doc('.callout-danger')
                if errormsg:
                    raise SessionException(errormsg.text())

                raise SessionException('Session cannot be created.  Check the entered information and try again.')

            print("Connected!")
            self.__is_user_logged_in = True
        except Exception as ex:
            self.__is_user_logged_in = False
            exit()

    def get_bluechips(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"accionesLideres","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_galpones(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"panelGeneral","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_cedear(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"cedears","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"rentaFija","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_short_term_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
            "Connection" : "keep-alive",    
            "Content-Type" : "application/json; charset=utf-8",
            "DNT" : "1",    
            "Host" : f"{self.__host}",
            "Origin" : f"https://{self.__host}",
            "Referer" : f"https://{self.__host}/Prices/Stocks",
            "Sec-Fetch-Dest" : "empty",
            "Sec-Fetch-Mode" : "cors",
            "Sec-Fetch-Site" : "same-origin",
            "TE" : "trailers",
            "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = '{"panel":"letes","term":"'+str(self.__settlements_map[settlement])+'"}'
        response = self.__s.post(url = f"https://{self.__host}/Prices/GetByPanel", headers=headers, data = data)
        status = response.status_code
        if status != 200:
            print("GetByPanel", status)  
            exit()
        data = response.json()
        df = pd.DataFrame(data['Result']['Stocks'])
        df = pd.DataFrame(data['Result']['Stocks']) if data['Result'] and data['Result']['Stocks'] else pd.DataFrame()
        df.TradeDate = pd.to_datetime(df.TradeDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[self.__filter_columns].copy()
        df.columns = self.__securities_columns
        df = convert_to_numeric_columns(df, self.__numeric_columns)
        df.group = df.group.apply(lambda x: self.__boards[x] if x in self.__boards else self.__boards[0])
        df.settlement=settlement 
        return df

    def get_corporate_bonds(self,settlement):
        if not self.__is_user_logged_in:
            print('You must be logged first')
            exit()
        headers = {
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.5",
           
            "Connection": "keep-alive",
            "Content-Type": "application/json; charset=utf-8",
            "DNT": "1",
            "Host": f"{self.__host}",
            "Origin": f"https://{self.__host}",
            "Referer": f"https://{self.__host}/Orders/History",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "X-Requested-With": "XMLHttpRequest"
        }

        data = json.dumps({"comitente": str(comitente)})
        response = self.__s.post(url=f"https://{self.__host}/Orders/GetOrderHistory", headers=headers, data=data)
        status = response.status_code
        if status != 200:
            print("GetOrderHistory", status)
            exit()

        data = response.json()
        df = pd.DataFrame(data['Result']['Orders'])
        df = pd.DataFrame(data['Result']['Orders']) if data['Result'] and data['Result']['Orders'] else pd.DataFrame()
        df.OrderDate = pd.to_datetime(df.OrderDate, format='%Y%m%d', errors='coerce') + pd.to_timedelta(df.Hour, errors='coerce')
        df = df[['OrderID', 'Symbol', 'OrderType', 'Quantity', 'Price', 'OrderDate', 'Status']].copy()
        df.columns = ['order_id', 'symbol', 'order_type', 'quantity', 'price', 'order_date', 'status']
        df = convert_to_numeric_columns(df, ['quantity', 'price'])
        return df

    #########################
    #### PRIVATE METHODS ####
    #########################
    def __convert_datetime_to_epoch(self, dt):

        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, '%Y-%m-%d')

        dt_zero = datetime.date(1970, 1, 1)
        time_delta = dt - dt_zero
        return int(time_delta.total_seconds())
    
    def __get_broker_data(self, broker_id):

        broker_data = [broker for broker in brokers if broker['broker_id'] == broker_id]

        if not broker_data:
            supported_brokers = ''.join([str(broker['broker_id']) + ', ' for broker in brokers])[0:-2]
            raise BrokerNotSupportedException('Broker not supported.  Brokers supported: {}.'.format(supported_brokers))

        return broker_data[0]

