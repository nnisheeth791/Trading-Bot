import fxcmpy
import time

#token_path = "/Users/Naman/Desktop/Trading Bot/apitoken.txt"
con = fxcmpy.fxcmpy(access_token = "blocked out api key", log_level = 'error', server = 'demo')
pair = 'EUR/USD'

#get historical data
data = con.get_candles(pair, period='m1', number=250)

#streaming data
con.subscribe_market_data(pair)
con.get_last_price(pair)
con.get_prices(pair)
con.unsubscribe_market_data(pair)

starttime = time.time()
timeout = time.time() + 60*0.2
while time.time() <= timeout:
    print(con.get_last_price(pair)[0])
    
#trading account data
con.get_accounts().T
con.get_open_positions().T
con.get_open_positions_summary().T

con.get_closed_positions()
con.get_orders()

#orders
con.create_market_buy_order(pair, 10)
con.create_market_buy_order('USD/CAD', 10)
con.create_market_sell_order(pair, 10)
con.create_market_sell_order('USD/CAD', 10)

order = con.open_trade(symbol=pair, is_buy=False,is_in_pips=True,
                       amount=10, time_in_force='GTC',
                       stop=-9, trailing_step=True,
                       order_type='AtMarket', limit=1.45)

#con.close_trade(trade_id=tradeID, amount = 1000)
con.close_all_for_symbol('USD/CAD')
con.close()


