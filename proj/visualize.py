import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_combined_animated_chart(df, selected_strategies, speed_ms, params, progress_bar=None):
    """PlotlyのSubplots機能を使用して、選択された複数の戦略を縦に並べたアニメーション付きの1つのグラフを生成します。"""
    
    num_strategies = len(selected_strategies)
    if num_strategies == 0:
        return go.Figure()

    row_height = 400
    row_heights = [1.0] * num_strategies
    row_heights.append(0.6) 
    row_heights.append(0.4) 
    
    subplot_titles = [f"{s} (価格とシグナル)" for s in selected_strategies]
    subplot_titles.append("ポートフォリオ評価額 (損益比較)")
    subplot_titles.append("ドローダウン比較 (%)")

    fig = make_subplots(
        rows=num_strategies + 2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=row_heights,
        subplot_titles=subplot_titles
    )

    # Y軸の範囲固定用の計算
    price_max = df['High'].max()
    price_min = df['Low'].max() * 0.5 
    if pd.isna(price_min): price_min = df['Low'].min()

    port_max = 0
    port_min = float('inf')
    for s in selected_strategies:
        col = f'Portfolio_{s}'
        if col in df.columns:
            m = df[col].max()
            mi = df[col].min()
            if m > port_max: port_max = m
            if mi < port_min: port_min = mi

    # --- 変更箇所: ドローダウンの最大下落幅を計算してY軸下限を決める ---
    dd_min = 0
    for s in selected_strategies:
        col = f'Drawdown_{s}'
        if col in df.columns:
            mi = df[col].min()
            if mi < dd_min: dd_min = mi
            
    # 最大下落幅の1.1倍（少し余白を持たせる）を下限とする。下落がない場合は -10 を設定
    dd_lower_bound = dd_min * 1.1 if dd_min < 0 else -10
    dd_lower_bound -= 5

    df_init = df.iloc[:1]
    
    strategy_colors = {
        "Golden/Dead Cross": "gold",
        "Bollinger Bands": "green",
        "SMA Crossover": "darkorange"
    }
    
    for idx, strategy in enumerate(selected_strategies):
        row = idx + 1
        theme_color = strategy_colors.get(strategy, "blue")
        
        # --- 価格(Close) ---
        fig.add_trace(go.Scatter(
            x=df_init['Date'], y=df_init['Close'], 
            mode='lines', name=f'{strategy} Close', 
            line=dict(color=theme_color, width=2), 
            legendgroup=strategy, showlegend=True
        ), row=row, col=1)
        
        # --- 動的な名前によるインジケーターの描画 ---
        if strategy == "SMA Crossover":
            name_short = f"SMA {params.get('sma_cross_short', 20)}"
            name_long = f"SMA {params.get('sma_cross_long', 50)}"
            fig.add_trace(go.Scatter(x=df_init['Date'], y=df_init['SMA_Cross_Short'], mode='lines', name=name_short, line=dict(color='royalblue', width=1, dash='dot'), legendgroup=strategy), row=row, col=1)
            fig.add_trace(go.Scatter(x=df_init['Date'], y=df_init['SMA_Cross_Long'], mode='lines', name=name_long, line=dict(color='magenta', width=1, dash='dot'), legendgroup=strategy), row=row, col=1)
        
        elif strategy == "Golden/Dead Cross":
            name_short = f"SMA {params.get('gdc_short', 5)}"
            name_long = f"SMA {params.get('gdc_long', 25)}"
            fig.add_trace(go.Scatter(x=df_init['Date'], y=df_init['GDC_Short'], mode='lines', name=name_short, line=dict(color='royalblue', width=1, dash='dot'), legendgroup=strategy), row=row, col=1)
            fig.add_trace(go.Scatter(x=df_init['Date'], y=df_init['GDC_Long'], mode='lines', name=name_long, line=dict(color='magenta', width=1, dash='dot'), legendgroup=strategy), row=row, col=1)
        
        elif strategy == "Bollinger Bands":
            name_upper = f"+{params.get('bb_std', 2.0)}σ"
            name_lower = f"-{params.get('bb_std', 2.0)}σ"
            fig.add_trace(go.Scatter(x=df_init['Date'], y=df_init['BB_Upper'], mode='lines', name=name_upper, line=dict(color='gray', width=1, dash='dash'), legendgroup=strategy), row=row, col=1)
            fig.add_trace(go.Scatter(x=df_init['Date'], y=df_init['BB_Lower'], mode='lines', name=name_lower, line=dict(color='gray', width=1, dash='dash'), legendgroup=strategy), row=row, col=1)

        # --- 売買シグナルマーカー ---
        if strategy == "Golden/Dead Cross":
            buy_col, sell_col = 'Buy_Price_GDC', 'Sell_Price_GDC'
        elif strategy == "SMA Crossover":
            buy_col, sell_col = 'Buy_Price_SMA', 'Sell_Price_SMA'
        else:
            buy_col, sell_col = 'Buy_Price_BB', 'Sell_Price_BB'
            
        fig.add_trace(go.Scatter(
            x=df_init['Date'], y=df_init[buy_col], mode='markers', name=f'{strategy} Buy', 
            marker=dict(color='green', symbol='triangle-up', size=15, line=dict(width=1, color='DarkSlateGrey')), 
            legendgroup=strategy
        ), row=row, col=1)
        
        fig.add_trace(go.Scatter(
            x=df_init['Date'], y=df_init[sell_col], mode='markers', name=f'{strategy} Sell', 
            marker=dict(color='red', symbol='triangle-down', size=15, line=dict(width=1, color='DarkSlateGrey')), 
            legendgroup=strategy
        ), row=row, col=1)

    # --- ポートフォリオ評価額グラフ ---
    for strategy in selected_strategies:
        theme_color = strategy_colors.get(strategy, "blue")
        fig.add_trace(go.Scatter(
            x=df_init['Date'], y=df_init[f'Portfolio_{strategy}'], 
            mode='lines', name=f'{strategy} Portfolio',
            line=dict(color=theme_color, width=2)
        ), row=num_strategies + 1, col=1)
        
    # --- ドローダウングラフ ---
    for strategy in selected_strategies:
        theme_color = strategy_colors.get(strategy, "blue")
        fig.add_trace(go.Scatter(
            x=df_init['Date'], y=df_init[f'Drawdown_{strategy}'], 
            mode='lines', name=f'{strategy} Drawdown',
            line=dict(color=theme_color, width=1), fill='tozeroy'
        ), row=num_strategies + 2, col=1)

    # -----------------------------------------------------
    # アニメーションフレームの生成
    # -----------------------------------------------------
    frames = []
    max_frames = 150 
    step_size = max(2, len(df) // max_frames)
    
    frame_indices = list(range(5, len(df), step_size))
    if not frame_indices or frame_indices[-1] != len(df):
        frame_indices.append(len(df))

    total_frames = len(frame_indices)

    for idx, i in enumerate(frame_indices): 
        df_slice = df.iloc[:i]
        frame_data = []
        alert_messages = []
        
        for strategy in selected_strategies:
            
            # (A) 価格(Close) の更新
            frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice['Close']))
            
            # (B) インジケーター の更新 (列名汎用化対応)
            if strategy == "SMA Crossover":
                frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice['SMA_Cross_Short']))
                frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice['SMA_Cross_Long']))
            elif strategy == "Golden/Dead Cross":
                frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice['GDC_Short']))
                frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice['GDC_Long']))
            elif strategy == "Bollinger Bands":
                frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice['BB_Upper']))
                frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice['BB_Lower']))

            # (C) シグナルマーカー の更新
            if strategy == "Golden/Dead Cross":
                buy_col, sell_col, sig_col = 'Buy_Price_GDC', 'Sell_Price_GDC', 'Signal_GDC'
            elif strategy == "SMA Crossover":
                buy_col, sell_col, sig_col = 'Buy_Price_SMA', 'Sell_Price_SMA', 'Signal_SMA'
            else:
                buy_col, sell_col, sig_col = 'Buy_Price_BB', 'Sell_Price_BB', 'Signal_BB'
                
            frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice[buy_col]))
            frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice[sell_col]))

            # 最新シグナルチェック
            last_signal = df_slice[sig_col].iloc[-1]
            if last_signal == 1: alert_messages.append(f"{strategy}: BUY")
            elif last_signal == -1: alert_messages.append(f"{strategy}: SELL")
            elif last_signal == 2: alert_messages.append(f"{strategy}: BUY (Close)")
            elif last_signal == -2: alert_messages.append(f"{strategy}: SELL (Close)")

        # (D) ポートフォリオ評価額グラフ の更新
        for strategy in selected_strategies:
            frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice[f'Portfolio_{strategy}']))
            
        # (E) ドローダウングラフ の更新
        for strategy in selected_strategies:
            frame_data.append(go.Scatter(x=df_slice['Date'], y=df_slice[f'Drawdown_{strategy}']))

        frames.append(go.Frame(data=frame_data, name=str(i), layout=go.Layout(annotations=[dict(text=" | ".join(alert_messages) if alert_messages else "")])))

        if progress_bar is not None:
            progress = 0.3 + (0.7 * (idx + 1) / total_frames)
            progress_bar.progress(progress)

    fig.frames = frames

    fig.update_layout(
        height=row_height * num_strategies + 500,
        title_text="シミュレーション再生",
        showlegend=True, # 凡例を表示してパラメータを確認できるように変更
        hovermode="x unified",
        margin=dict(t=120, b=50, l=50, r=50),
        updatemenus=[dict(
            type="buttons",
            bgcolor="rgba(240, 240, 240, 0.9)", bordercolor="rgba(150, 150, 150, 0.8)", borderwidth=2,
            font=dict(color="black", size=14, family="Arial, sans-serif"),
            buttons=[
                dict(label="Play ▶️", method="animate", args=[None, dict(frame=dict(duration=speed_ms, redraw=False), fromcurrent=True, transition=dict(duration=0))]),
                dict(label="Pause ⏸️", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]),
                dict(label="Reset 🔄", method="animate", args=[[str(frame_indices[0])], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
            ],
            direction="left", pad={"r": 10, "t": 10}, showactive=False, x=0.0, xanchor="left", y=1.1, yanchor="top"
        )]
    )

    for row in range(1, num_strategies + 1):
        fig.update_yaxes(range=[price_min * 0.9, price_max * 1.1], row=row, col=1)
        
    fig.update_yaxes(range=[port_min * 0.9, port_max * 1.1], row=num_strategies + 1, col=1, title="資産額")
    
    # --- 変更箇所: -100 決め打ちではなく計算した下限値を使用 ---
    fig.update_yaxes(range=[dd_lower_bound, 0], row=num_strategies + 2, col=1, title="下落率 (%)")
    fig.update_xaxes(range=[df['Date'].min(), df['Date'].max()])

    return fig