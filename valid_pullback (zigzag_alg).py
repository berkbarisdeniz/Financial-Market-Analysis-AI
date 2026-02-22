import pandas as pd
import numpy as np
import mplfinance as mpf

df = pd.read_csv("BTCUSDT_15m_Clean.csv")

df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'open_time': 'Date'}, inplace=True)
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

direction = -1 
p_high = None   
p_low = None    
p_high_idx = None
p_low_idx = None

valid_high = df.iloc[0]['High']
valid_low = df.iloc[0]['Low']


zigzag_highs = [np.nan] * len(df)
zigzag_lows = [np.nan] * len(df)
zigzag_lines = [] 


for i in range(1, len(df)):
    curr_high = df.iloc[i]['High']
    curr_low = df.iloc[i]['Low']
    
    is_inside = (curr_high <= valid_high) and (curr_low >= valid_low)
    
    if not is_inside:
        # Dip Arıyoruz
        if direction == -1:
            if p_low is None or curr_low < p_low:
                p_low = curr_low
                p_low_idx = i 
            
            if curr_high > valid_high: # reverse
                if p_high_idx is not None:
                    zigzag_lows[p_low_idx] = p_low 
                    zigzag_lines.append((p_high_idx, p_high, p_low_idx, p_low))
                
                direction = 1
                p_high = curr_high
                p_high_idx = i

        
        # Tepe Arıyoruz
        elif direction == 1:
            if p_high is None or curr_high > p_high:
                p_high = curr_high
                p_high_idx = i
            
            if curr_low < valid_low: # reverse
                if p_low_idx is not None:
                    zigzag_highs[p_high_idx] = p_high
                    zigzag_lines.append((p_low_idx, p_low, p_high_idx, p_high))
                
                direction = -1
                p_low = curr_low
                p_low_idx = i

        
        valid_high = curr_high
        valid_low = curr_low


df['temp_high'] = zigzag_highs
df['temp_low'] = zigzag_lows
df['is_H'] = 0
df['is_L'] = 0


df.loc[df['temp_high'].notna(), 'is_H'] = 1


df.loc[df['temp_low'].notna(), 'is_L'] = 1

output_columns = ['Open', 'High', 'Low', 'Close', 'is_H', 'is_L']
final_df = df[output_columns]

output_filename = "SMC_Zigzag_Binary.csv"
final_df.to_csv(output_filename)

