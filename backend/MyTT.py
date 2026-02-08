# -*- coding: utf-8 -*-
"""
MyTT - 技术指标计算库
提供常用技术分析指标的计算函数
用于个股筛选系统的技术指标特征工程
"""

import pandas as pd
import numpy as np

# ============================================================================
# 核心工具函数
# ============================================================================

def MA(S, N):
    """N日简单移动平均"""
    return pd.Series(S).rolling(N).mean().values

def EMA(S, N):
    """指数移动平均"""
    return pd.Series(S).ewm(span=N, adjust=False).mean().values

def SMA(S, N, M=1):
    """中国式SMA"""
    return pd.Series(S).ewm(alpha=M / N, adjust=False).mean().values

def REF(S, N=1):
    """向上偏移N周期,返回N周期前的数据"""
    return pd.Series(S).shift(N).values

def DIFF(S, N=1):
    """序列差分"""
    return pd.Series(S).diff(N).values

def STD(S, N):
    """N日标准差"""
    return pd.Series(S).rolling(N).std(ddof=0).values

def SUM(S, N):
    """N日累计和"""
    return pd.Series(S).rolling(N).sum().values if N > 0 else pd.Series(S).cumsum().values

def HHV(S, N):
    """N日最高价"""
    return pd.Series(S).rolling(N).max().values

def LLV(S, N):
    """N日最低价"""
    return pd.Series(S).rolling(N).min().values

def MAX(S1, S2):
    """序列最大值"""
    return np.maximum(S1, S2)

def MIN(S1, S2):
    """序列最小值"""
    return np.minimum(S1, S2)

def ABS(S):
    """绝对值"""
    return np.abs(S)

def CROSS(S1, S2):
    """向上金叉,S1上穿S2"""
    return np.concatenate(([False], np.logical_not((S1 > S2)[:-1]) & (S1 > S2)[1:]))

def COUNT(S, N):
    """N日内满足条件的天数"""
    return SUM(S, N)

def IF(S, A, B):
    """条件函数"""
    return np.where(S, A, B)

# ============================================================================
# 常用技术指标
# ============================================================================

def MACD(CLOSE, SHORT=12, LONG=26, M=9):
    """
    MACD指标
    参数: CLOSE-收盘价序列, SHORT-短期EMA, LONG-长期EMA, M-信号线EMA
    返回: DIF, DEA, MACD
    """
    DIF = EMA(CLOSE, SHORT) - EMA(CLOSE, LONG)
    DEA = EMA(DIF, M)
    MACD = (DIF - DEA) * 2
    return DIF, DEA, MACD

def RSI(CLOSE, N=24):
    """
    RSI相对强弱指标
    参数: CLOSE-收盘价序列, N-周期数
    返回: RSI值
    """
    DIF = CLOSE - REF(CLOSE, 1)
    return SMA(MAX(DIF, 0), N) / SMA(ABS(DIF), N) * 100

def KDJ(CLOSE, HIGH, LOW, N=9, M1=3, M2=3):
    """
    KDJ随机指标
    参数: CLOSE-收盘价, HIGH-最高价, LOW-最低价, N-周期, M1-K平滑, M2-D平滑
    返回: K, D, J
    """
    RSV = (CLOSE - LLV(LOW, N)) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    K = EMA(RSV, (M1 * 2 - 1))
    D = EMA(K, (M2 * 2 - 1))
    J = K * 3 - D * 2
    return K, D, J

def BOLL(CLOSE, N=20, P=2):
    """
    布林带指标
    参数: CLOSE-收盘价序列, N-周期数, P-标准差倍数
    返回: UPPER(上轨), MID(中轨), LOWER(下轨)
    """
    MID = MA(CLOSE, N)
    UPPER = MID + STD(CLOSE, N) * P
    LOWER = MID - STD(CLOSE, N) * P
    return UPPER, MID, LOWER

def ATR(CLOSE, HIGH, LOW, N=20):
    """
    真实波幅均值
    参数: CLOSE-收盘价, HIGH-最高价, LOW-最低价, N-周期数
    返回: ATR值
    """
    TR = MAX(MAX((HIGH - LOW), ABS(REF(CLOSE, 1) - HIGH)), ABS(REF(CLOSE, 1) - LOW))
    return MA(TR, N)

def CCI(CLOSE, HIGH, LOW, N=14):
    """
    顺势指标
    参数: CLOSE-收盘价, HIGH-最高价, LOW-最低价, N-周期数
    返回: CCI值
    """
    def AVEDEV(S, N):
        return pd.Series(S).rolling(N).apply(lambda x: (np.abs(x - x.mean())).mean()).values
    
    TP = (HIGH + LOW + CLOSE) / 3
    return (TP - MA(TP, N)) / (0.015 * AVEDEV(TP, N))

def WR(CLOSE, HIGH, LOW, N=10, N1=6):
    """
    威廉指标
    参数: CLOSE-收盘价, HIGH-最高价, LOW-最低价, N-第一周期, N1-第二周期
    返回: WR (只返回第一个指标，与m3_technical_features.py兼容)
    """
    WR = (HHV(HIGH, N) - CLOSE) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    return WR

def BIAS(CLOSE, L1=6, L2=12, L3=24):
    """
    乖离率指标
    参数: CLOSE-收盘价, L1/L2/L3-三条均线周期
    返回: BIAS1, BIAS2, BIAS3
    """
    BIAS1 = (CLOSE - MA(CLOSE, L1)) / MA(CLOSE, L1) * 100
    BIAS2 = (CLOSE - MA(CLOSE, L2)) / MA(CLOSE, L2) * 100
    BIAS3 = (CLOSE - MA(CLOSE, L3)) / MA(CLOSE, L3) * 100
    return BIAS1, BIAS2, BIAS3

def DMI(CLOSE, HIGH, LOW, M1=14, M2=6):
    """
    动向指标(含ADX)
    参数: CLOSE-收盘价, HIGH-最高价, LOW-最低价, M1-第一周期, M2-第二周期
    返回: PDI(上升动向), MDI(下降动向), ADX(趋势强度), ADXR
    """
    TR = SUM(MAX(MAX(HIGH - LOW, ABS(HIGH - REF(CLOSE, 1))), ABS(LOW - REF(CLOSE, 1))), M1)
    HD = HIGH - REF(HIGH, 1)
    LD = REF(LOW, 1) - LOW
    
    DMP = SUM(IF((HD > 0) & (HD > LD), HD, 0), M1)
    DMM = SUM(IF((LD > 0) & (LD > HD), LD, 0), M1)
    PDI = DMP * 100 / TR
    MDI = DMM * 100 / TR
    ADX = MA(ABS(MDI - PDI) / (PDI + MDI) * 100, M2)
    ADXR = (ADX + REF(ADX, M2)) / 2
    return PDI, MDI, ADX, ADXR

def OBV(CLOSE, VOL):
    """
    能量潮指标
    参数: CLOSE-收盘价, VOL-成交量
    返回: OBV值
    """
    return SUM(IF(CLOSE > REF(CLOSE, 1), VOL, IF(CLOSE < REF(CLOSE, 1), -VOL, 0)), 0) / 10000

def EVERY(S, N):
    """N日内全部满足条件"""
    return IF(SUM(S, N) == N, True, False)

def EXIST(S, N):
    """N日内存在满足条件"""
    return IF(SUM(S, N) > 0, True, False)

def PSY(CLOSE, N=12, M=6):
    """心理线指标"""
    PSY = COUNT(CLOSE > REF(CLOSE, 1), N) / N * 100
    PSYMA = MA(PSY, M)
    return PSY, PSYMA

def BBI(CLOSE, M1=3, M2=6, M3=12, M4=20):
    """多空指数"""
    return (MA(CLOSE, M1) + MA(CLOSE, M2) + MA(CLOSE, M3) + MA(CLOSE, M4)) / 4

def VR(CLOSE, VOL, M1=26):
    """容量比率"""
    LC = REF(CLOSE, 1)
    return SUM(IF(CLOSE > LC, VOL, 0), M1) / SUM(IF(CLOSE <= LC, VOL, 0), M1) * 100

def EXPMA(CLOSE, N1=12, N2=50):
    """EMA指数平均数指标"""
    return EMA(CLOSE, N1), EMA(CLOSE, N2)

def MFI(CLOSE, HIGH, LOW, VOL, N=14):
    """MFI指标(成交量的RSI)"""
    TYP = (HIGH + LOW + CLOSE) / 3
    V1 = SUM(IF(TYP > REF(TYP, 1), TYP * VOL, 0), N) / SUM(IF(TYP < REF(TYP, 1), TYP * VOL, 0), N)
    return 100 - (100 / (1 + V1))
