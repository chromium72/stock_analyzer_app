import pandas as pd
import numpy as np

def load_real_data(filepath):
    """保存されたCSV.gzファイルからOHLCVデータを読み込みます。"""
    df = pd.read_csv(filepath, compression='gzip')
    
    # 日付カラムの名前を 'Date' に統一し、datetime型に変換
    if 'Datetime' in df.columns:
        df = df.rename(columns={'Datetime': 'Date'})
        
    if 'Date' not in df.columns and 'Datetime' not in df.columns:
        df = df.reset_index()
        if 'Datetime' in df.columns:
            df = df.rename(columns={'Datetime': 'Date'})
        elif 'index' in df.columns:
            df = df.rename(columns={'index': 'Date'})
            
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date').reset_index(drop=True)
    return df

def generate_dummy_data(days=300):
    """ランダムウォークを用いたダミーの価格データを生成します。"""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=days)
    returns = np.random.normal(loc=0.0005, scale=0.02, size=days)
    price = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({'Date': dates, 'Close': price})
    df['Open'] = df['Close'] * (1 + np.random.normal(0, 0.005, size=days))
    df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.005, size=days)))
    df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.005, size=days)))
    df['Volume'] = np.random.randint(1000, 10000, size=days)
    return df

def calculate_indicators(df, params):
    """ユーザー指定のパラメータに基づいて各種テクニカル指標を動的に計算します。"""
    
    # SMA Crossover用 (汎用名に変更)
    df['SMA_Cross_Short'] = df['Close'].rolling(window=params.get('sma_cross_short', 20)).mean()
    df['SMA_Cross_Long'] = df['Close'].rolling(window=params.get('sma_cross_long', 50)).mean()
    
    # Golden/Dead Cross用 (汎用名に変更)
    df['GDC_Short'] = df['Close'].rolling(window=params.get('gdc_short', 5)).mean()
    df['GDC_Long'] = df['Close'].rolling(window=params.get('gdc_long', 25)).mean()
    
    # Bollinger Bands用 (汎用名とパラメータの適用)
    bb_window = params.get('bb_window', 20)
    bb_std = params.get('bb_std', 2.0)
    
    df['BB_SMA'] = df['Close'].rolling(window=bb_window).mean()
    df['Std_Dev'] = df['Close'].rolling(window=bb_window).std()
    df['BB_Upper'] = df['BB_SMA'] + (df['Std_Dev'] * bb_std)
    df['BB_Lower'] = df['BB_SMA'] - (df['Std_Dev'] * bb_std)
    
    return df