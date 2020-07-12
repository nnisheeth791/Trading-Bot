import fxcmpy
import numpy as np
from stocktrends import Renko
import statsmodels.api as sm
import time
import copy

con = fxcmpy.fxcmpy(access_token = "blacked out api key", 
                    log_level = 'error', server = 'demo')
pairs = ['EUR/USD', 'GBP/USD', 'USD/CHF', 'AUD/USD', 'USD/CAD']
pos_size = 10


#calculate the MACD
def MACD(DF,a,b,c):
    df = DF.copy()
    df["MA_Fast"]=df["Adj Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Adj Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return df

#calculate true range and ATR
def ATR(DF,n):
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Adj Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Adj Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2

#convert data into renko bricks
def renko_DF(DF):
    df = DF.copy()
    df.reset_index(inplace=True)
    df = df.iloc[:,[0,1,2,3,5,6]]
    df.rename(columns = {"Date" : "date", "High" : "high","Low" : "low", "Open" :
                         "open","Adj Close" : "close", "Volume" : "volume"}, 
              inplace = True)
    df2 = Renko(df)
    df2.brick_size = round(ATR(DF,120)["ATR"][-1],0)
    renko_df = df2.get_ohlc_data() 
    return renko_df
    
def slope(ser,n):
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return np.array(slope_angle)

#merges renko DF with the original DF
def renko_merge(DF):
    df = copy.deepcopy(DF)
    df["Date"] = df.index
    renko = renko_DF(df)
    renko.columns = ["Date","open","high","low","close","uptrend","bar_num"]
    m_df = df.merge(renko.loc[:,["Date","bar_num"]],how="outer",on="Date")
    m_df["bar_num"].fillna(method='ffill',inplace=True)
    m_df["macd"]= MACD(m_df,12,26,9)[0]
    m_df["macd_sig"]= MACD(m_df,12,26,9)[1]
    m_df["macd_slope"] = slope(m_df["macd"],5)
    m_df["macd_sig_slope"] = slope(m_df["macd_sig"],5)
    return m_df

def trade_signal(M_DF,l_s):
    signal = ""
    df = copy.deepcopy(M_DF)
    if l_s == "":
        if df["bar_num"].tolist()[-1]>=2 and df["macd"].tolist()[-1]>df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]>df["macd_sig_slope"].tolist()[-1]:
            signal = "Buy"
        elif df["bar_num"].tolist()[-1]<=-2 and df["macd"].tolist()[-1]<df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]<df["macd_sig_slope"].tolist()[-1]:
            signal = "Sell"
            
    elif l_s == "long":
        if df["bar_num"].tolist()[-1]<=-2 and df["macd"].tolist()[-1]<df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]<df["macd_sig_slope"].tolist()[-1]:
            signal = "Close_Sell"
        elif df["macd"].tolist()[-1]<df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]<df["macd_sig_slope"].tolist()[-1]:
            signal = "Close"
            
    elif l_s == "short":
        if df["bar_num"].tolist()[-1]>=2 and df["macd"].tolist()[-1]>df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]>df["macd_sig_slope"].tolist()[-1]:
            signal = "Close_Buy"
        elif df["macd"].tolist()[-1]>df["macd_sig"].tolist()[-1] and df["macd_slope"].tolist()[-1]>df["macd_sig_slope"].tolist()[-1]:
            signal = "Close"
    return signal

#use try/except in the event that the connection fails (or markets are closed)
def main():
    try:
        open_p = con.get_open_positions()
        for currency in pairs:
            long_short = ""
            if len(open_p)>0:
                open_p_cur = open_p[open_p["currency"]==currency]
                if len(open_p_cur)>0:
                    if open_p_cur["isBuy"].tolist()[0]==True:
                        long_short = "long"
                    elif open_p_cur["isBuy"].tolist()[0]==False:
                        long_short = "short"   
            data = con.get_candles(currency, period='m5', number=250)
            ohlc = data.iloc[:,[0,1,2,3,8]]
            ohlc.columns = ["Open","Close","High","Low","Volume"]
            signal = trade_signal(renko_merge(ohlc),long_short)
    
            if signal == "Buy":
                con.open_trade(symbol=currency, is_buy=True, is_in_pips=True, amount=pos_size, 
                               time_in_force='GTC', stop=-8, trailing_step =True, order_type='AtMarket')
                print("New long position for ", currency)
            elif signal == "Sell":
                con.open_trade(symbol=currency, is_buy=False, is_in_pips=True, amount=pos_size, 
                               time_in_force='GTC', stop=-8, trailing_step =True, order_type='AtMarket')
                print("New short position for ", currency)
            elif signal == "Close":
                con.close_all_for_symbol(currency)
                print("All positions closed for ", currency)
            elif signal == "Close_Buy":
                con.close_all_for_symbol(currency)
                print("Existing Short closed for ", currency)
                con.open_trade(symbol=currency, is_buy=True, is_in_pips=True, amount=pos_size, 
                               time_in_force='GTC', stop=-8, trailing_step =True, order_type='AtMarket')
                print("New long position initiated for ", currency)
            elif signal == "Close_Sell":
                con.close_all_for_symbol(currency)
                print("Existing Long closed for ", currency)
                con.open_trade(symbol=currency, is_buy=False, is_in_pips=True, amount=pos_size, 
                               time_in_force='GTC', stop=-8, trailing_step =True, order_type='AtMarket')
                print("New short position initiated for ", currency)
    except:
        print("error encountered")
        
starttime = time.time()
timeout = time.time() + 60*60
while time.time() <= timeout:
    try:
        print("passthrough at ",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        main()
        time.sleep(300 - ((time.time() - starttime) % 300.0)) # 5 minute interval
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()

for currency in pairs:
    print("closing all positions for ",currency)
    con.close_all_for_symbol(currency)
con.close()