"""Performance metrics
"""

import pandas as pd
import numpy as np
import scipy.stats as ss
import statsmodels.api as sm
from statsmodels import regression
from typing import Tuple

def semideviation(r: pd.Series):
    """Filter negative returns only"""
    is_negative = r < 0
    return r[is_negative].std(ddof=0)


def sharpe(r: pd.Series, rf=0, freq=252):
    return (r.mean() - rf) / r.std() * np.sqrt(freq)


def sortino(r: pd.Series, rf=0, freq=252):
    return (r.mean() - rf) / semideviation(r) * np.sqrt(freq)

def jensen_alpha():
    """Not implemented yet"""


def treynor(r: pd.Series, beta: float, rf=0):
    """ Treynor ratio
    compute beta with OLS"""
    return (r.mean() - rf) / beta


def calculate_moments(r: pd.Series):
    return r.mean(), r.std(), ss.skew(r, bias=True), ss.kurtosis(r, bias=True)


def historic_var(r: pd.Series, level=5):
    """Historical VaR
    specify level: 0 - 100 percentile
    """
    return -np.percentile(r, level)


def parametric_var(r: pd.Series, level=5):
    r = r.dropna()
    z = ss.norm.ppf(level / 100)
    return -(r.mean() + z * r.std(ddof=0))


def cornish_fisher_var(r: pd.Series, level=5):
    skew = ss.skew(r, bias=True)
    kurt = ss.kurtosis(r, bias=True)
    z = ss.norm.ppf(level/100)
    adj_z = z + skew * (z**2 - 1)/6 + (z ** 3 - 3 * z) * \
        (kurt - 3)/24 - (2*z**3 - 5 * z) * (skew ** 2)/36
    return -(r.mean() + adj_z * r.std(ddof=0))


def historic_cvar(r: pd.Series, level=5):
    """Conditional VaR"""
    isbeyond = r <= -historic_var(r, level=level)
    return -r[isbeyond].mean()


def drawdown(r: pd.Series):
    """
    Returns:
        max drawdown (%)
        max drawdown duration days
    """
    cumret = (1 + r).cumprod()
    rdrawdown = (cumret.cummax() - cumret) / cumret.cummax()
    adrawdown = (cumret.cummax() - cumret)
    # relative drawdown in %
    max_dd = rdrawdown.max() * 100
    # drawdown duration
    temp = adrawdown[adrawdown == 0]
    periods_dd = (temp.index[1:].to_pydatetime() -
                  temp.index[:-1].to_pydatetime())
    max_dd_duration = max(periods_dd)
    return max_dd, max_dd_duration


def capm(bm: pd.Series, pf: pd.Series, rf=0, bm_period=252, pf_period=252) -> Tuple[float, float, float]:
    """bm: market returns, pf: portfolio returns"""
    bm = bm.dropna()
    pf = pf.dropna()
    rf = rf/np.sqrt(pf_period)
    comb_ret = pd.concat([bm-rf, pf-rf], axis=1).dropna()
    comb_ret.columns = ['bm', 'pf']
    x = comb_ret['bm']
    y = comb_ret['pf']

    def linreg(x, y):
        x = sm.add_constant(x)
        model = regression.linear_model.OLS(y, x).fit()

        # x = x[:, 1]
        return model.params[0], model.params[1], model.rsquared, model.summary()
    alpha, beta, r2, summary = linreg(x, y)
    return alpha, beta, r2


def information_ratio(bm: pd.Series, pf: pd.Series, rf: float = 0, bm_period=252, pf_period=252) -> float:
    """ Calculate information ratio
    E(PF returns - BM returns) / std(PF returns - BM returns)

    Args:
        bm: market returns, 
        pf: portfolio returns

    Return:
        information ratio [float]    
    """
    use_period = bm_period if bm_period < pf_period else pf_period
    bm = bm.dropna()
    pf = pf.dropna()
    rf = rf/np.sqrt(pf_period)
    comb_ret = pd.concat([bm-rf, pf-rf], axis=1).dropna()
    comb_ret.columns = ['bm', 'pf']
    bm_cumret = (bm + 1).prod() ** (bm_period/len(bm)) - 1
    pf_cumret = (pf + 1).prod() ** (pf_period/len(pf)) - 1

    return (pf_cumret - bm_cumret) / ((comb_ret['pf'] - comb_ret['bm']).std() * np.sqrt(use_period))