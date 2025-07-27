import backtrader as bt
import pandas as pd

class SignalStrategy(bt.Strategy):
    params = (
        ('signals', []),
        ('take_profit_pct', 0.0),
        ('atr_multiplier', 0.0), # ATR multiplier for stop loss
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.order = None
        # ATR indicator for dynamic stop loss
        self.atr = bt.indicators.AverageTrueRange(self.datas[0])
        self.signal_map = {pd.to_datetime(s[0]).date(): s[1] for s in self.p.signals}
        self.stop_price = None

    def next(self):
        current_date = self.datas[0].datetime.date(0)

        if self.order:
            return

        if not self.position:
            if current_date in self.signal_map:
                signal_type = self.signal_map[current_date]
                if signal_type == 'long':
                    self.order = self.buy()
                elif signal_type == 'short':
                    self.order = self.sell()
        else:
            # Dynamic stop loss based on ATR
            if self.position.size > 0:  # Long position
                if self.p.atr_multiplier > 0:
                    self.stop_price = self.position.price - self.atr[0] * self.p.atr_multiplier
                if self.stop_price and self.dataclose[0] <= self.stop_price:
                    self.order = self.close()
                elif self.dataclose[0] >= self.position.price * (1 + self.p.take_profit_pct):
                    self.order = self.close()
            elif self.position.size < 0:  # Short position
                if self.p.atr_multiplier > 0:
                    self.stop_price = self.position.price + self.atr[0] * self.p.atr_multiplier
                if self.stop_price and self.dataclose[0] >= self.stop_price:
                    self.order = self.close()
                elif self.dataclose[0] <= self.position.price * (1 - self.p.take_profit_pct):
                    self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                pass
            elif order.issell():
                pass
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            pass

        self.order = None


def run_backtest(df: pd.DataFrame, signals: list, take_profit_pct: float, atr_multiplier: float) -> dict:
    """
    Runs a backtest using Backtrader on a given DataFrame based on entry signals.

    Args:
        df (pd.DataFrame): DataFrame with at least 'Open', 'High', 'Low', 'Close', 'Volume' columns.
        signals (list): A list of tuples, where each tuple is (index, 'long' or 'short').
        take_profit_pct (float): The percentage for take profit.
        atr_multiplier (float): The ATR multiplier for stop loss.

    Returns:
        dict: A dictionary with backtest results.
    """
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SignalStrategy, signals=signals, take_profit_pct=take_profit_pct, atr_multiplier=atr_multiplier)

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    # Analyzer
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    results = cerebro.run()
    strat = results[0]

    trade_analyzer = strat.analyzers.trade_analyzer.get_analysis()
    sharpe_analyzer = strat.analyzers.sharpe.get_analysis()
    drawdown_analyzer = strat.analyzers.drawdown.get_analysis()

    total_trades = trade_analyzer.total.total if 'total' in trade_analyzer else 0
    win_trades = trade_analyzer.won.total if 'won' in trade_analyzer else 0
    win_rate = (win_trades / total_trades) if total_trades > 0 else 0
    
    pnl_net_total = trade_analyzer.pnl.net.total if 'pnl' in trade_analyzer and 'net' in trade_analyzer.pnl else 0
    average_pnl = (pnl_net_total / total_trades) if total_trades > 0 else 0


    return {
        'win_rate': win_rate,
        'total_trades': total_trades,
        'average_pnl': average_pnl,
        'total_pnl': pnl_net_total,
        'sharpe_ratio': sharpe_analyzer.get('sharperatio', 0.0) if sharpe_analyzer else 0.0,
        'max_drawdown': drawdown_analyzer.max.drawdown if 'max' in drawdown_analyzer else 0.0,
    }


def get_backtest_results(df: pd.DataFrame, signals: list, take_profit_pct: float, atr_multiplier: float) -> dict:
    """
    A wrapper for run_backtest to be used in the application.
    """
    return run_backtest(df, signals, take_profit_pct, atr_multiplier)