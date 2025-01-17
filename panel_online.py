

from pyhomebroker import HomeBroker

def example_online():

    # Credenciales predefinidas
    broker = 284
    dni = '40476136'
    user = 'cintiaboos'
    password = 'Chuletarubio99_'

    hb = HomeBroker(int(broker), 
        on_open=on_open, 
        on_personal_portfolio=on_personal_portfolio, 
        on_securities=on_securities, 
        on_options=on_options, 
        on_repos=on_repos, 
        on_order_book=on_order_book, 
        on_error=on_error, 
        on_close=on_close)
        
    hb.auth.login(dni=dni, user=user, password=password, raise_exception=True)
    
    hb.online.connect()
    # Suscribirse a otros paneles disponibles
    hb.online.subscribe_securities('bluechips', '48hs')
    hb.online.subscribe_options()
    hb.online.subscribe_repos()
    hb.online.subscribe_order_book('GGAL', '48hs')
    
    input('Press Enter to Disconnect...\n')

    hb.online.unsubscribe_order_book('GGAL', '48hs')
    hb.online.unsubscribe_repos()
    hb.online.unsubscribe_options()
    hb.online.unsubscribe_securities('bluechips', '48hs')

    hb.online.disconnect()

def on_open(online):
    
    print('=================== CONNECTION OPENED ====================')

def on_personal_portfolio(online, portfolio_quotes, order_book_quotes):
    
    print('------------------- Personal Portfolio -------------------')
    print(portfolio_quotes)
    print('------------ Personal Portfolio - Order Book -------------')
    print(order_book_quotes)

def on_securities(online, quotes):
    
    print('----------------------- Securities -----------------------')
    print(quotes)

def on_options(online, quotes):
    
    print('------------------------ Options -------------------------')
    print(quotes)

def on_repos(online, quotes):
    
    print('------------------------- Repos --------------------------')
    print(quotes)

def on_order_book(online, quotes):
    
    print('------------------ Order Book (Level 2) ------------------')
    print(quotes)
    
def on_error(online, exception, connection_lost):
    
    print('@@@@@@@@@@@@@@@@@@@@@@@@@ Error @@@@@@@@@@@@@@@@@@@@@@@@@@')
    print(exception)

def on_close(online):

    print('=================== CONNECTION CLOSED ====================')

if __name__ == '__main__':
    example_online()