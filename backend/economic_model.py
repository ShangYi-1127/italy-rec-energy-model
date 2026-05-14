"""
经济评估模块 (Economic Model)
============================

功能：根据意大利REC框架计算经济效益

补贴机制：
1. CACI (共享电量补贴)
2. CACV (网费返还)
3. RID (电网出售)
"""

import numpy as np
import pandas as pd
from typing import Dict


class EconomicModel:
    """经济评估模型(意大利REC框架)"""
    
    def __init__(self, region: str = 'central', has_pnrr: bool = False):
        """
        初始化经济模型
        
        Parameters:
        -----------
        region : str
            地区(north/central/south) - 影响FC_zonale
        has_pnrr : bool
            是否享受PNRR补助(F=0.5)
        """
        self.region = region
        self.has_pnrr = has_pnrr
        
        # 地区修正系数 FC_zonale [€/MWh]
        self.FC_zonale = {
            'north': 10,
            'central': 4,
            'south': 0
        }.get(region.lower(), 4)
        
        # PNRR补助参数
        self.F = 0.5 if has_pnrr else 0.0
        
        # 电价参数(示例值，实际应从市场获取)
        self.TP_base = 80  # €/MWh
        self.CAP = 120  # €/MWh (补贴上限)
        self.CUA_fa = 30  # €/MWh (网费返还)
        
        self.results = None
    
    def calculate_caci(
        self,
        shared_hourly: pd.Series,
        hourly_prices: pd.Series
    ) -> Dict:
        """
        计算CACI补贴(共享电量补贴)
        
        公式：CACI = Σ TIP_h × E_ACI,h
        
        其中 TIP_h = {min[CAP; TP_base + max(0; 180 - Pz)] + FC_zonale} × (1 - F)
        
        Parameters:
        -----------
        shared_hourly : pd.Series
            逐时共享电量 [kWh]
        hourly_prices : pd.Series
            逐时电价 Pz [€/MWh]
            
        Returns:
        --------
        Dict
            CACI补贴详情
        """
        
        # 计算逐时补贴费率 TIP_h
        price_adjustment = 180 - hourly_prices
        price_adjustment = np.maximum(price_adjustment, 0)
        
        TIP = np.minimum(
            self.CAP,
            self.TP_base + price_adjustment
        ) + self.FC_zonale
        TIP *= (1 - self.F)
        
        # 计算CACI
        caci_hourly = TIP * shared_hourly / 1000  # 转换为€
        caci_total = caci_hourly.sum()
        
        # 月度统计
        monthly_data = pd.DataFrame({
            'Timestamp': shared_hourly.index,
            'CACI': caci_hourly
        })
        monthly_caci = monthly_data.groupby(
            monthly_data['Timestamp'].dt.month
        )['CACI'].sum()
        
        return {
            'total_euro': caci_total,
            'avg_rate_per_kwh': caci_hourly.sum() / shared_hourly.sum() if shared_hourly.sum() > 0 else 0,
            'monthly_breakdown': monthly_caci.to_dict(),
        }
    
    def calculate_cacv(
        self,
        self_consumed_hourly: pd.Series
    ) -> Dict:
        """
        计算CACV补贴(网费返还)
        
        公式：CACV = CUA_fa × E_ACV
        
        Parameters:
        -----------
        self_consumed_hourly : pd.Series
            逐时自消耗电量 [kWh]
            
        Returns:
        --------
        Dict
            CACV补贴详情
        """
        
        cacv_hourly = self.CUA_fa * self_consumed_hourly / 1000  # 转换为€
        cacv_total = cacv_hourly.sum()
        
        monthly_data = pd.DataFrame({
            'Timestamp': self_consumed_hourly.index,
            'CACV': cacv_hourly
        })
        monthly_cacv = monthly_data.groupby(
            monthly_data['Timestamp'].dt.month
        )['CACV'].sum()
        
        return {
            'total_euro': cacv_total,
            'rate_per_kwh': self.CUA_fa / 1000,
            'monthly_breakdown': monthly_cacv.to_dict(),
        }
    
    def calculate_rid(
        self,
        surplus_hourly: pd.Series,
        hourly_prices: pd.Series
    ) -> Dict:
        """
        计算RID补贴(电网出售)
        
        公式：RID = Σ Pz × E_surplus,h
        
        Parameters:
        -----------
        surplus_hourly : pd.Series
            逐时余电量 [kWh]
        hourly_prices : pd.Series
            逐时电价 Pz [€/MWh]
            
        Returns:
        --------
        Dict
            RID补贴详情
        """
        
        rid_hourly = hourly_prices * surplus_hourly / 1000  # 转换为€
        rid_total = rid_hourly.sum()
        
        monthly_data = pd.DataFrame({
            'Timestamp': surplus_hourly.index,
            'RID': rid_hourly
        })
        monthly_rid = monthly_data.groupby(
            monthly_data['Timestamp'].dt.month
        )['RID'].sum()
        
        return {
            'total_euro': rid_total,
            'avg_price_per_kwh': hourly_prices.mean() / 1000,
            'monthly_breakdown': monthly_rid.to_dict(),
        }
    
    def calculate_total_revenue(
        self,
        shared_kwh: float,
        self_consumed_kwh: float,
        surplus_kwh: float,
        avg_hourly_prices: pd.Series,
        hourly_price_series: pd.Series = None
    ) -> Dict:
        """
        计算总收益
        
        Parameters:
        -----------
        shared_kwh : float
            年度共享电量 [MWh]
        self_consumed_kwh : float
            年度自消耗电量 [MWh]
        surplus_kwh : float
            年度余电量 [MWh]
        avg_hourly_prices : float或pd.Series
            平均/逐时电价
        hourly_price_series : pd.Series
            完整的逐时电价序列
            
        Returns:
        --------
        Dict
            总收益分析
        """
        
        if hourly_price_series is None:
            # 使用简化估计
            hourly_price_series = pd.Series(
                [avg_hourly_prices] * 8760
            )
        
        # 估计各补贴(简化版)
        caci = self.TP_base * shared_kwh * (1 - self.F)
        cacv = self.CUA_fa * self_consumed_kwh
        rid = avg_hourly_prices * surplus_kwh if isinstance(avg_hourly_prices, (int, float)) \
              else hourly_price_series.mean() * surplus_kwh
        
        total = caci + cacv + rid
        
        return {
            'caci_euro': caci,
            'cacv_euro': cacv,
            'rid_euro': rid,
            'total_annual_revenue_euro': total,
            'revenue_per_kwh_generated': total / (shared_kwh + self_consumed_kwh + surplus_kwh) 
                                        if (shared_kwh + self_consumed_kwh + surplus_kwh) > 0 else 0,
            'revenue_breakdown_percent': {
                'CACI': caci / total * 100 if total > 0 else 0,
                'CACV': cacv / total * 100 if total > 0 else 0,
                'RID': rid / total * 100 if total > 0 else 0,
            }
        }
    
    def get_incentive_parameters(self) -> Dict:
        """获取当前激励参数设置"""
        return {
            'region': self.region,
            'FC_zonale_eur_per_mwh': self.FC_zonale,
            'has_pnrr': self.has_pnrr,
            'F_parameter': self.F,
            'TP_base_eur_per_mwh': self.TP_base,
            'CAP_eur_per_mwh': self.CAP,
            'CUA_fa_eur_per_mwh': self.CUA_fa,
        }
