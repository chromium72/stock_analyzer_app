import pandas as pd
import numpy as np

def calculate_portfolio_value(df, selected_strategies, initial_capital, allow_short, leverage, enable_margin_cut, enable_tp, tp_pct, enable_sl, sl_pct, progress_bar=None):
    """初期資金と各種設定をもとに、各戦略のポートフォリオ評価額とドローダウンを計算します。"""
    
    total_strategies = len(selected_strategies)
    total_rows = len(df)
    total_steps = total_strategies * total_rows
    current_step = 0

    for strategy in selected_strategies:
        if strategy == "Golden/Dead Cross":
            col_signal = 'Signal_GDC'
            col_buy = 'Buy_Price_GDC'
            col_sell = 'Sell_Price_GDC'
        elif strategy == "SMA Crossover":
            col_signal = 'Signal_SMA'
            col_buy = 'Buy_Price_SMA'
            col_sell = 'Sell_Price_SMA'
        else:
            col_signal = 'Signal_BB'
            col_buy = 'Buy_Price_BB'
            col_sell = 'Sell_Price_BB'
            
        # 描画用のシグナル価格列をNaNで初期化
        df[col_buy] = np.nan
        df[col_sell] = np.nan
        
        cash = initial_capital
        position_qty = 0.0 # 正ならロング、負ならショート
        entry_price = 0.0
        portfolio_values = []
        is_bankrupt = False
        
        for i in range(len(df)):
            signal = df[col_signal].iloc[i]
            current_price = df['Close'].iloc[i]
            
            # 未実現損益と現在の資産(Equity)の計算
            if position_qty != 0:
                unrealized_pnl = position_qty * (current_price - entry_price)
            else:
                unrealized_pnl = 0
                
            equity = cash + unrealized_pnl
            
            # 破産判定
            if equity <= 0:
                equity = 0
                is_bankrupt = True
                position_qty = 0
                cash = 0
                
            # 強制決済(ロスカット)の判定
            if not is_bankrupt and enable_margin_cut and position_qty != 0:
                position_value = abs(position_qty) * current_price
                required_margin = position_value / leverage
                if required_margin > 0:
                    margin_ratio = equity / required_margin
                    if margin_ratio <= 0.5:
                        cash = equity
                        position_qty = 0
                        unrealized_pnl = 0
                        signal = 0 
                        
            # 利確・損切の判定
            if not is_bankrupt and position_qty != 0:
                price_change_pct = 0
                if position_qty > 0:
                    price_change_pct = (current_price - entry_price) / entry_price * 100
                elif position_qty < 0:
                    price_change_pct = (entry_price - current_price) / entry_price * 100
                    
                is_closed = False
                if enable_tp and price_change_pct >= tp_pct:
                    is_closed = True
                elif enable_sl and price_change_pct <= -sl_pct:
                    is_closed = True
                    
                if is_closed:
                    cash = equity
                    if position_qty > 0:
                        df.loc[df.index[i], col_sell] = current_price
                        df.loc[df.index[i], col_signal] = -2 
                    else:
                        df.loc[df.index[i], col_buy] = current_price
                        df.loc[df.index[i], col_signal] = 2  
                    position_qty = 0
                    unrealized_pnl = 0
                    signal = 0 
                        
            # シグナルに基づく売買
            if not is_bankrupt and signal in [1, -1]:
                # 既存ポジションの決済
                if position_qty != 0:
                    cash = equity
                    position_qty = 0
                    unrealized_pnl = 0
                
                # 新規ポジションの構築
                if signal == 1:
                    trade_amount = cash * leverage
                    position_qty = trade_amount / current_price
                    entry_price = current_price
                    df.loc[df.index[i], col_buy] = current_price
                elif signal == -1 and allow_short:
                    trade_amount = cash * leverage
                    position_qty = -(trade_amount / current_price)
                    entry_price = current_price
                    df.loc[df.index[i], col_sell] = current_price
                elif signal == -1 and not allow_short:
                    df.loc[df.index[i], col_sell] = current_price
                    
            equity = cash + (position_qty * (current_price - entry_price)) if position_qty != 0 else cash
            portfolio_values.append(max(0, equity))
            
            # --- プログレスバーの更新 (UIの負荷を下げるため100行ごとに更新) ---
            current_step += 1
            if progress_bar is not None and i % 100 == 0:
                # 0.0 ~ 0.3 (全体の30%) を計算フェーズの進捗として割り当てる
                progress = (current_step / total_steps) * 0.3
                progress_bar.progress(progress)
            
        df[f'Portfolio_{strategy}'] = portfolio_values
        df[f'CumMax_{strategy}'] = df[f'Portfolio_{strategy}'].cummax()
        df[f'Drawdown_{strategy}'] = (df[f'Portfolio_{strategy}'] - df[f'CumMax_{strategy}']) / df[f'CumMax_{strategy}'] * 100

    return df
