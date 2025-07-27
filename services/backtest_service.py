import backtrader as bt
import pandas as pd

class TradeLogger(bt.Analyzer):
    """Analyzer to log all trades with details."""
    def __init__(self):
        self.trades = {}
        self.closed_trades = []

    def notify_trade(self, trade):
        if trade.isopen:
            self.trades[trade.ref] = {
                'ref': trade.ref,
                'direction': 'long' if trade.size > 0 else 'short',
                'entry_date': bt.num2date(trade.dtopen).isoformat(),
                'entry_price': trade.price,
                'size': trade.size,
                'strategy': trade.data.strategy_name # Capture strategy on open
            }

        if trade.isclosed:
            if trade.ref in self.trades:
                open_trade = self.trades.pop(trade.ref)
                exit_price = (trade.pnl / open_trade['size']) + open_trade['entry_price']

                self.closed_trades.append({
                    'ref': trade.ref,
                    'direction': open_trade['direction'],
                    'strategy': open_trade['strategy'],
                    'entry_date': open_trade['entry_date'],
                    'entry_price': f"{open_trade['entry_price']:.2f}",
                    'exit_date': bt.num2date(trade.dtclose).isoformat(),
                    'exit_price': f'{exit_price:.2f}',
                    'pnl': f'{trade.pnl:.2f}',
                    'pnl_net': f'{trade.pnlcomm:.2f}',
                })

    def get_analysis(self):
        return self.closed_trades

class SignalStrategy(bt.Strategy):
    params = (
        ('signals', []),
        ('atr_multiplier', 2.0),
        ('reward_risk_ratio', 2.0),
    )

    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(self.datas[0])
        self.signal_map = {pd.to_datetime(s[0]).date(): (s[1], s[2]) for s in self.p.signals}
        self.order = None

    def next(self):
        if self.order or self.position:
            return

        current_date = self.datas[0].datetime.date(0)
        if current_date in self.signal_map:
            signal_type, strategy_name = self.signal_map[current_date]
            self.data.strategy_name = strategy_name # Store strategy name for the logger

            stop_loss_distance = self.atr[0] * self.p.atr_multiplier
            take_profit_distance = stop_loss_distance * self.p.reward_risk_ratio

            if signal_type == 'long':
                entry_price = self.datas[0].close[0]
                sl_price = entry_price - stop_loss_distance
                tp_price = entry_price + take_profit_distance
                self.order = self.buy_bracket(sl=sl_price, tp=tp_price)

            elif signal_type == 'short':
                entry_price = self.datas[0].close[0]
                sl_price = entry_price + stop_loss_distance
                tp_price = entry_price - take_profit_distance
                self.order = self.sell_bracket(sl=sl_price, tp=tp_price)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None

def run_backtest(df: pd.DataFrame, signals: list, atr_multiplier: float, reward_risk_ratio: float) -> dict:
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SignalStrategy, signals=signals, atr_multiplier=atr_multiplier, reward_risk_ratio=reward_risk_ratio)

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(TradeLogger, _name='trade_logger')

    results = cerebro.run()
    strat = results[0]

    trade_analyzer = strat.analyzers.trade_analyzer.get_analysis()
    sharpe_analyzer = strat.analyzers.sharpe.get_analysis()
    drawdown_analyzer = strat.analyzers.drawdown.get_analysis()
    trade_logger = strat.analyzers.trade_logger.get_analysis()

    total_trades = trade_analyzer.total.total if 'total' in trade_analyzer else 0
    win_trades = trade_analyzer.won.total if 'won' in trade_analyzer else 0
    win_rate = (win_trades / total_trades) if total_trades > 0 else 0
    
    pnl_net_total = trade_analyzer.pnl.net.total if 'pnl' in trade_analyzer and 'net' in trade_analyzer.pnl else 0
    average_pnl = (pnl_net_total / total_trades) if total_trades > 0 else 0

    return {
        'summary': {
            'win_rate': win_rate,
            'total_trades': total_trades,
            'average_pnl': average_pnl,
            'total_pnl': pnl_net_total,
            'sharpe_ratio': sharpe_analyzer.get('sharperatio', 0.0) if sharpe_analyzer else 0.0,
            'max_drawdown': drawdown_analyzer.max.drawdown if 'max' in drawdown_analyzer else 0.0,
        },
        'trades': trade_logger
    }

def get_backtest_results(df: pd.DataFrame, signals: list, atr_multiplier: float, reward_risk_ratio: float) -> dict:
    """
    A wrapper for run_backtest to be used in the application.
    """
    return run_backtest(df, signals, atr_multiplier, reward_risk_ratio)