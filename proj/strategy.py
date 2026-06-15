import pandas as pd

def generate_trades(df, strategies):
    """選択された戦略と動的指標に基づいて売買シグナルを生成します。"""
    df['Signal_SMA'] = 0
    df['Signal_BB'] = 0
    df['Signal_GDC'] = 0
    
    # 1: 買い, -1: 売り, 0: 何もしない, 2: 決済(買い戻し), -2: 決済(売り)
    if "SMA Crossover" in strategies:
        for i in range(1, len(df)):
            if pd.isna(df['SMA_Cross_Long'].iloc[i]): continue
            # ゴールデンクロス
            if df['SMA_Cross_Short'].iloc[i-1] <= df['SMA_Cross_Long'].iloc[i-1] and df['SMA_Cross_Short'].iloc[i] > df['SMA_Cross_Long'].iloc[i]:
                df.loc[df.index[i], 'Signal_SMA'] = 1
            # デッドクロス
            elif df['SMA_Cross_Short'].iloc[i-1] >= df['SMA_Cross_Long'].iloc[i-1] and df['SMA_Cross_Short'].iloc[i] < df['SMA_Cross_Long'].iloc[i]:
                df.loc[df.index[i], 'Signal_SMA'] = -1
                
    if "Golden/Dead Cross" in strategies:
        for i in range(1, len(df)):
            if pd.isna(df['GDC_Long'].iloc[i]): continue
            if df['GDC_Short'].iloc[i-1] <= df['GDC_Long'].iloc[i-1] and df['GDC_Short'].iloc[i] > df['GDC_Long'].iloc[i]:
                df.loc[df.index[i], 'Signal_GDC'] = 1
            elif df['GDC_Short'].iloc[i-1] >= df['GDC_Long'].iloc[i-1] and df['GDC_Short'].iloc[i] < df['GDC_Long'].iloc[i]:
                df.loc[df.index[i], 'Signal_GDC'] = -1

    if "Bollinger Bands" in strategies:
        for i in range(1, len(df)):
            if pd.isna(df['BB_Lower'].iloc[i]): continue
            # 下のバンドを下抜けたら買い (逆張り)
            if df['Close'].iloc[i-1] >= df['BB_Lower'].iloc[i-1] and df['Close'].iloc[i] < df['BB_Lower'].iloc[i]:
                df.loc[df.index[i], 'Signal_BB'] = 1
            # 上のバンドを上抜けたら売り (逆張り)
            elif df['Close'].iloc[i-1] <= df['BB_Upper'].iloc[i-1] and df['Close'].iloc[i] > df['BB_Upper'].iloc[i]:
                df.loc[df.index[i], 'Signal_BB'] = -1

    return df