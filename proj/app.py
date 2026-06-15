import streamlit as st
import os
import glob

# ローカルに分割した各モジュールから関数をインポート
from data import load_real_data, generate_dummy_data, calculate_indicators
from strategy import generate_trades
from portfolio import calculate_portfolio_value
from visualize import create_combined_animated_chart

st.set_page_config(page_title="Trade Simulation", layout="wide", initial_sidebar_state="expanded")

def main():
    st.title("📈 トレードシミュレーション")
    st.write("設定を変更後、「アニメーション生成 🚀」ボタンを押すとシミュレーションが実行されます。(1分弱掛かる場合があります...)")

    if 'run_simulation' not in st.session_state:
        st.session_state['run_simulation'] = False
        st.session_state['settings'] = {}

    st.sidebar.header("⚙️ シミュレーション設定")
    
    with st.sidebar.form("settings_form"):
        st.markdown("### 📊 データ設定")
        
        # ./data フォルダ内の csv.gz ファイルを検索
        data_dir = "./proj/data"
        # data_dir = "./data"
        file_pattern = os.path.join(data_dir, "*.csv.gz")
        available_files = glob.glob(file_pattern)
        
        if not available_files:
            st.warning(f"「{data_dir}」フォルダにデータファイルが見つかりません。")
            ticker_options = {"ダミーデータを使用": "dummy"}
        else:
            ticker_options = {}
            for file_path in available_files:
                # ファイル名からティッカーを抽出
                file_name = os.path.basename(file_path)
                ticker = file_name.split("_")[0]
                ticker_options[ticker] = file_path
                
        selected_ticker_display = st.selectbox("シミュレーション対象の銘柄", options=list(ticker_options.keys()))
        selected_file_path = ticker_options[selected_ticker_display]
        
        st.markdown("### 💰 資金設定")
        initial_capital = st.slider("初期資金 ($)", min_value=1000, max_value=1000000, value=10000, step=1000)
        
        st.markdown("### 📈 戦略設定")
        strategy_options = ["Golden/Dead Cross", "Bollinger Bands", "SMA Crossover"]
        selected_strategies = st.multiselect("表示する戦略を選択", options=strategy_options, default=["Golden/Dead Cross"])
        
        with st.expander("⚖️ トレードルールの設定", expanded=False):
            allow_short = st.checkbox("空売りを許可する", value=False)
            leverage = st.slider("レバレッジ倍率", min_value=1.0, max_value=20.0, value=1.0, step=1.0)
            enable_margin_cut = st.checkbox("強制決済 (証拠金維持率50%でロスカット)", value=False)
        
        with st.expander("🎯 利確・損切ルール", expanded=False):
            enable_tp = st.checkbox("利確 (Take Profit) を設定する", value=False)
            tp_pct = st.slider("利確ライン (%)", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
            enable_sl = st.checkbox("損切 (Stop Loss) を設定する", value=False)
            sl_pct = st.slider("損切ライン (%)", min_value=1.0, max_value=100.0, value=5.0, step=1.0)
        
        # --- 変更箇所: 戦略パラメータ設定 ---
        strategy_params = {}
        
        with st.expander("🎛️ 戦略パラメータ設定", expanded=False):
            st.markdown("#### Golden/Dead Cross")
            strategy_params['gdc_short'] = st.number_input("短期SMA期間", min_value=1, max_value=200, value=5, key="gdc_s")
            strategy_params['gdc_long'] = st.number_input("中期SMA期間", min_value=1, max_value=200, value=25, key="gdc_l")
                
            st.markdown("#### Bollinger Bands")
            strategy_params['bb_window'] = st.number_input("移動平均期間", min_value=1, max_value=200, value=20, key="bb_w")
            strategy_params['bb_std'] = st.slider("標準偏差 (σ)", min_value=1.0, max_value=5.0, value=2.0, step=0.1, key="bb_s")
                
            st.markdown("#### SMA Crossover")
            strategy_params['sma_cross_short'] = st.number_input("短期SMA期間", min_value=1, max_value=200, value=20, key="sma_s")
            strategy_params['sma_cross_long'] = st.number_input("長期SMA期間", min_value=1, max_value=200, value=50, key="sma_l")

        st.markdown("### ⏱️ アニメーション設定")
        speed = st.slider("再生スピード (速さ)", min_value=1, max_value=10, value=7)
        speed_ms = 1000 // speed
        
        submit_button = st.form_submit_button("アニメーション生成 🚀")

    if submit_button:
        st.session_state['run_simulation'] = True
        st.session_state['settings'] = {
            'selected_file_path': selected_file_path,
            'initial_capital': initial_capital,
            'allow_short': allow_short,
            'leverage': leverage,
            'enable_margin_cut': enable_margin_cut,
            'enable_tp': enable_tp,
            'tp_pct': tp_pct,
            'enable_sl': enable_sl,
            'sl_pct': sl_pct,
            'selected_strategies': selected_strategies,
            'strategy_params': strategy_params, # 追加
            'speed_ms': speed_ms
        }

    if st.session_state['run_simulation']:
        settings = st.session_state['settings']
        current_strategies = settings['selected_strategies']
        current_params = settings['strategy_params']
        
        if not current_strategies:
            st.warning("左側のサイドバーから少なくとも1つの戦略を選択してください。")
            return

        status_text = st.empty()
        progress_bar = st.progress(0.0)

        with st.spinner("シミュレーションを実行中です..."):
            status_text.text("データの読み込みとテクニカル指標の計算中...")
            if settings['selected_file_path'] == "dummy":
                raw_df = generate_dummy_data(300)
            else:
                raw_df = load_real_data(settings['selected_file_path'])
                
            # 計算にパラメータを渡す
            df = calculate_indicators(raw_df, current_params)
            df = generate_trades(df, current_strategies)
            
            status_text.text("バックテスト（損益）を計算中...")
            df = calculate_portfolio_value(
                df, current_strategies, settings['initial_capital'], 
                settings['allow_short'], settings['leverage'], settings['enable_margin_cut'],
                settings['enable_tp'], settings['tp_pct'], 
                settings['enable_sl'], settings['sl_pct'],
                progress_bar=progress_bar
            )

            status_text.text("アニメーションフレームを生成中 (この処理は少し時間がかかります)...")
            fig = create_combined_animated_chart(
                df, current_strategies, settings['speed_ms'], 
                current_params, # 描画にパラメータを渡す
                progress_bar=progress_bar
            )

        status_text.empty()
        progress_bar.empty()
        st.plotly_chart(fig, width="stretch")

        # -----------------------------------------------------
        # 📊 シミュレーション結果サマリーの表示
        # -----------------------------------------------------
        st.markdown("---")
        st.markdown("### 📊 シミュレーション結果サマリー")
        
        # 選択された戦略の数だけ画面をカラム分割
        cols = st.columns(len(current_strategies))
        
        # シグナル列名のマッピング
        signal_cols = {
            "Golden/Dead Cross": "Signal_GDC",
            "SMA Crossover": "Signal_SMA",
            "Bollinger Bands": "Signal_BB"
        }
        
        for idx, strategy in enumerate(current_strategies):
            with cols[idx]:
                st.markdown(f"#### {strategy}")
                
                # --- (1) シグナル数の集計 ---
                sig_col = signal_cols[strategy]
                # 1: 買い, -1: 売り
                buy_count = (df[sig_col] == 1).sum()
                sell_count = (df[sig_col] == -1).sum()
                
                # --- (2) ポートフォリオの結果 ---
                initial_val = settings['initial_capital']
                final_val = df[f'Portfolio_{strategy}'].iloc[-1]
                
                if initial_val > 0:
                    pct_change = ((final_val - initial_val) / initial_val) * 100
                else:
                    pct_change = 0.0
                    
                # 符号付きのフォーマット
                sign = "+" if pct_change > 0 else ""
                
                # --- (3) maxドローダウンと時期 ---
                dd_col = f'Drawdown_{strategy}'
                max_dd = df[dd_col].min() # ドローダウンは負の値で入っているためmin()
                
                # 最大ドローダウンが記録された行のインデックスを取得
                max_dd_idx = df[dd_col].idxmin()
                # 該当する日付を取得し、YYYY/MM/DD フォーマットに変換
                max_dd_date = df.loc[max_dd_idx, 'Date'].strftime('%Y/%m/%d')
                
                # ---------------------------------------------
                # 画面への出力 (マークダウンとメトリック)
                # ---------------------------------------------
                st.markdown(f"""
                - **buy シグナル**: {buy_count} (回)
                - **sell シグナル**: {sell_count} (回)
                """)
                
                # メトリックコンポーネントで目立たせて表示
                st.metric(
                    label="ポートフォリオ", 
                    value=f"${final_val:,.0f}", 
                    delta=f"{sign}{pct_change:.2f}% (初期: ${initial_val:,.0f})"
                )
                
                st.markdown(f"""
                - **max ドローダウン**: <span style='color:red;'>{max_dd:.2f}%</span> 
                  <br>&nbsp;&nbsp;&nbsp;&nbsp;*(時期: {max_dd_date})*
                """, unsafe_allow_html=True)
                
                # カラム間に区切り線 (最後のカラム以外)
                if idx < len(current_strategies) - 1:
                    st.markdown("---")

if __name__ == "__main__":
    main()
