import pandas as pd
import numpy as np
import mplfinance as mpf

df = pd.read_csv("BTCUSDT_15m_Clean.csv")

df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'open_time': 'Date'}, inplace=True)
df['Date'] = pd.to_datetime(df['Date'])

df.set_index('Date', inplace=True)

#ZIGZAG

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

# IDM, BOS, CHOCH 

smc_trend = 0 #  0: başlangıç, 1: bullish, -1: bearish
choch_level = np.nan
bos_level = np.nan
idm_level = np.nan

#gizli idm takibi için

candicate_bull_idm = np.nan
candicate_bear_idm = np.nan
choch_candidate = np.nan 

#indexleri

cand_bull_idm_idx = np.nan
cand_bear_idm_idx = np.nan
idm_idx = np.nan



current_leg_high = np.nan
current_leg_low = np.nan
zigzag_max = np.nan
zigzag_min = np.nan

smc_choch_list = [np.nan] * len(df)
smc_bos_list = [np.nan] * len(df)
smc_idm_list = [np.nan] * len(df)


for i in range(1, len(df)):
    curr_high = df.iloc[i]['High']
    curr_low = df.iloc[i]['Low']
    curr_close = df.iloc[i]["Close"]
    
    is_inside = (curr_high <= valid_high) and (curr_low >= valid_low)
    

    if not is_inside:
        # Dip Arıyoruz
        if direction == -1:
            if p_low is None or curr_low < p_low:
                p_low = curr_low
                p_low_idx = i 
            
            if curr_high > valid_high: # dönüş
                if p_high_idx is not None:
                    zigzag_lows[p_low_idx] = p_low 
                    zigzag_lines.append((p_high_idx, p_high, p_low_idx, p_low))
                
                direction = 1
                p_high = curr_high
                p_high_idx = i
                candicate_bull_idm = p_low
                cand_bull_idm_idx = p_low_idx 

                if smc_trend == 0 and pd.isna(zigzag_min):
                    zigzag_min = p_low

        # Tepe Arıyoruz
        elif direction == 1:
            if p_high is None or curr_high > p_high:
                p_high = curr_high
                p_high_idx = i
            
            if curr_low < valid_low: # dönüş
                if p_low_idx is not None:
                    zigzag_highs[p_high_idx] = p_high
                    zigzag_lines.append((p_low_idx, p_low, p_high_idx, p_high))
                
                direction = -1
                p_low = curr_low
                p_low_idx = i
                candicate_bear_idm = p_high
                cand_bear_idm_idx = p_high_idx 
                
                if smc_trend == 0 and pd.isna(zigzag_max):
                    zigzag_max = p_high

        valid_high = curr_high
        valid_low = curr_low
        
    

    if smc_trend == 1:
        if pd.isna(current_leg_high) or curr_high > current_leg_high:
            current_leg_high = curr_high
    elif smc_trend == -1:
        if pd.isna(current_leg_low) or curr_low < current_leg_low:
            current_leg_low = curr_low

    
    
    #  COLD START 
    if smc_trend == 0:
        if not pd.isna(zigzag_max) and not pd.isna(zigzag_min):
            if curr_close > zigzag_max: 
                smc_trend = 1
                choch_level = zigzag_min 
                current_leg_high = curr_high 
            elif curr_close < zigzag_min: 
                smc_trend = -1
                choch_level = zigzag_max 
                current_leg_low = curr_low

    # BULLISH
    elif smc_trend == 1:
        
        # idm taşıma
        if pd.isna(bos_level):
            idm_level = candicate_bull_idm
            idm_idx = cand_bull_idm_idx 
            
        # (Sweep) ve BOS yaratma
        #  i > idm_idx (Outside Bar hatası için)
        if not pd.isna(idm_level) and not pd.isna(idm_idx) and curr_low <= idm_level and i > idm_idx:
            bos_level = current_leg_high 
            idm_level = np.nan 
            choch_candidate = curr_low   
            
        # Fiyat BOS'u kırmadan daha da düşerse adayı güncelle
        if not pd.isna(bos_level) and curr_low < choch_candidate:
            choch_candidate = curr_low
            
        # BOS İğne Taşıma 
        if not pd.isna(bos_level) and curr_high > bos_level and curr_close <= bos_level:
            bos_level = curr_high
            current_leg_high = curr_high
            
        # CHoCH İğne Taşıma 
        if not pd.isna(choch_level) and curr_low < choch_level and curr_close >= choch_level:
            choch_level = curr_low
            
        # CHoCH Trend Dönüşü
        if not pd.isna(choch_level) and curr_close < choch_level:
            smc_trend = -1
            choch_level = current_leg_high 
            bos_level = np.nan
            idm_level = candicate_bear_idm
            idm_idx = cand_bear_idm_idx 
            current_leg_low = curr_low
            choch_candidate = np.nan
            
        # BOS Trend Devami
        elif not pd.isna(bos_level) and curr_close > bos_level:
            choch_level = choch_candidate 
            bos_level = np.nan
            idm_level = candicate_bull_idm 
            idm_idx = cand_bull_idm_idx 
            current_leg_high = curr_high
            choch_candidate = np.nan

    # BEARISH
    elif smc_trend == -1:
        
        # idm taşıma
        if pd.isna(bos_level):
            idm_level = candicate_bear_idm
            idm_idx = cand_bear_idm_idx 
            
        # (Sweep) ve BOS çizgisini yaratma
        #  i > idm_idx (Outside Bar hatası için)
        if not pd.isna(idm_level) and not pd.isna(idm_idx) and curr_high >= idm_level and i > idm_idx:
            bos_level = current_leg_low 
            idm_level = np.nan 
            choch_candidate = curr_high 
            
        # BOS kırmadan daha da yükselirse adayı güncelle
        if not pd.isna(bos_level) and curr_high > choch_candidate:
            choch_candidate = curr_high
            
        # BOS İğne Taşıma
        if not pd.isna(bos_level) and curr_low < bos_level and curr_close >= bos_level:
            bos_level = curr_low
            current_leg_low = curr_low
            
        # CHoCH İğne Taşıma
        if not pd.isna(choch_level) and curr_high > choch_level and curr_close <= choch_level:
            choch_level = curr_high
            
        # CHoCH Kırılımı trend dönüşü
        if not pd.isna(choch_level) and curr_close > choch_level:
            smc_trend = 1
            choch_level = current_leg_low 
            bos_level = np.nan
            idm_level = candicate_bull_idm
            idm_idx = cand_bull_idm_idx 
            current_leg_high = curr_high
            choch_candidate = np.nan
            
        # BOS trend devamı
        elif not pd.isna(bos_level) and curr_close < bos_level:
            choch_level = choch_candidate 
            bos_level = np.nan
            idm_level = candicate_bear_idm
            idm_idx = cand_bear_idm_idx 
            current_leg_low = curr_low
            choch_candidate = np.nan
