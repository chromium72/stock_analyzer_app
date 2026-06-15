import yfinance as yf
import pandas as pd
import sys

def fetch_and_save_ohlcv(ticker_symbol: str, start_date: str, end_date: str, interval: str):
    """
    指定されたティッカーの1時間足OHLCVデータを取得し、
    gzip圧縮されたCSVファイルとして保存します。
    """
    # 保存するファイル名を作成 (例: BTC-USD_1h_20250101_20260101.csv.gz)
    safe_start = start_date.replace("-", "")
    safe_end = end_date.replace("-", "")
    output_filename = f"{ticker_symbol}_1h_{safe_start}_{safe_end}.csv.gz"
    
    print(f"[{ticker_symbol}] {start_date} から {end_date} までの{interval}データを取得中...")
    
    try:
        # yfinanceを使用してデータを取得
        # interval="1h" で1時間足を指定
        ticker_obj = yf.Ticker(ticker_symbol)
        df = ticker_obj.history(start=start_date, end=end_date, interval=interval)
        
        # データが空でないかチェック
        if df.empty:
            print(f"エラー: データが取得できませんでした。ティッカー名や期間を確認してください。")
            print("※ yfinanceの仕様上、1時間足データは過去730日までしか取得できない場合があります。")
            return

        # タイムゾーン情報を除去（CSV保存時の互換性を高めるため）
        df.index = df.index.tz_localize(None)

        # 必要なカラムのみに整理 (Open, High, Low, Close, Volume)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

        # compression='gzip' を指定して保存
        df.to_csv("./proj/data/"+output_filename, compression='gzip')
        print(f"成功: {len(df)}行のデータを保存しました。")
        print(f"ファイルパス: {output_filename}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    # ここでティッカーシンボルを指定します。
    # 日本株の場合は "7203.T" (トヨタ)、仮想通貨は "BTC-USD"、米国株は "AAPL" など
    TARGET_TICKER = "BTC-USD" 
    
    # 期間の指定
    START_DATE = "2025-01-01"
    END_DATE = "2026-01-01"
    INTERVAL = "1h"
    
    fetch_and_save_ohlcv(TARGET_TICKER, START_DATE, END_DATE, INTERVAL)