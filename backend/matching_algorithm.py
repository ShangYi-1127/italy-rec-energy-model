"""
能源匹配算法 (Matching Algorithm)
================================

功能：计算光伏发电与建筑负荷的匹配情况

核心算法：
E_diff,t = P_pv(t) - E_load(t)

统计指标：
- E_surplus: 年总余电量
- E_deficit: 年总缺电量
- Coverage: 年度覆盖率 = min(E_pv, E_load).sum() / E_load.sum()
"""

import numpy as np
import pandas as pd
from typing import Dict


class MatchingAlgorithm:
    """能源匹配分析"""
    
    def __init__(self):
        self.results = None
    
    def calculate_matching(
        self,
        load_df: pd.DataFrame,
        pv_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        计算逐时能源匹配情况
        
        Parameters:
        -----------
        load_df : pd.DataFrame
            建筑负荷数据，必须包含列 'E_total'
        pv_df : pd.DataFrame
            PV发电数据，必须包含列 'P_pv'
            
        Returns:
        --------
        pd.DataFrame
            匹配结果数据
        """
        
        # 确保时间对齐
        results = pd.DataFrame({
            'Timestamp': load_df['Timestamp'],
            'E_load': load_df['E_total'],
            'P_pv': pv_df['P_pv']
        })
        
        # 计算差值
        results['E_diff'] = results['P_pv'] - results['E_load']
        
        # 分类：余电或缺电
        results['Status'] = results['E_diff'].apply(
            lambda x: 'Surplus' if x > 0 else 'Deficit'
        )
        
        # 共享电量(最小值)
        results['E_shared'] = np.minimum(results['P_pv'], results['E_load'])
        
        # 计算按小时、按日、按月的统计
        results['Hour'] = results['Timestamp'].dt.hour
        results['Day'] = results['Timestamp'].dt.date
        results['Month'] = results['Timestamp'].dt.month
        
        self.results = results
        return results
    
    def get_annual_statistics(self) -> Dict:
        """获取年度统计"""
        if self.results is None:
            raise ValueError("需要先执行calculate_matching()")
        
        E_surplus = self.results[self.results['E_diff'] > 0]['E_diff'].sum()
        E_deficit = self.results[self.results['E_diff'] < 0]['E_diff'].sum()
        E_load_total = self.results['E_load'].sum()
        E_pv_total = self.results['P_pv'].sum()
        
        # 覆盖率：年度最小值之和 / 年度负荷总和
        coverage_rate = self.results['E_shared'].sum() / E_load_total * 100
        
        return {
            'annual_load_kwh': E_load_total,
            'annual_generation_kwh': E_pv_total,
            'annual_surplus_kwh': E_surplus,
            'annual_deficit_kwh': abs(E_deficit),
            'coverage_rate_percent': coverage_rate,
            'peak_load_kw': self.results['E_load'].max(),
            'peak_generation_kw': self.results['P_pv'].max(),
            'load_generation_ratio': E_load_total / E_pv_total if E_pv_total > 0 else 0,
        }
    
    def get_monthly_statistics(self) -> pd.DataFrame:
        """获取月度统计"""
        if self.results is None:
            raise ValueError("需要先执行calculate_matching()")
        
        monthly = self.results.groupby('Month').agg({
            'E_load': 'sum',
            'P_pv': 'sum',
            'E_shared': 'sum',
            'E_diff': ['min', 'max', 'mean']
        }).round(2)
        
        monthly.columns = ['Load (MWh)', 'Generation (MWh)', 'Shared (MWh)', 
                          'Min Diff', 'Max Diff', 'Avg Diff']
        
        # 计算月度覆盖率
        monthly['Coverage %'] = (monthly['Shared (MWh)'] / 
                                 monthly['Load (MWh)'] * 100).round(1)
        
        return monthly
    
    def get_seasonal_statistics(self) -> Dict:
        """获取季节性统计"""
        if self.results is None:
            raise ValueError("需要先执行calculate_matching()")
        
        month = self.results['Month']
        
        seasons = {
            'winter': [12, 1, 2],
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'autumn': [9, 10, 11]
        }
        
        seasonal_stats = {}
        for season_name, months in seasons.items():
            season_data = self.results[month.isin(months)]
            
            load = season_data['E_load'].sum()
            gen = season_data['P_pv'].sum()
            shared = season_data['E_shared'].sum()
            surplus = season_data[season_data['E_diff'] > 0]['E_diff'].sum()
            deficit = abs(season_data[season_data['E_diff'] < 0]['E_diff'].sum())
            
            seasonal_stats[season_name] = {
                'load_kwh': load,
                'generation_kwh': gen,
                'shared_kwh': shared,
                'surplus_kwh': surplus,
                'deficit_kwh': deficit,
                'coverage_rate_percent': (shared / load * 100) if load > 0 else 0,
            }
        
        return seasonal_stats
    
    def get_hourly_statistics(self) -> pd.DataFrame:
        """获取按小时统计的平均特性"""
        if self.results is None:
            raise ValueError("需要先执行calculate_matching()")
        
        hourly = self.results.groupby('Hour').agg({
            'E_load': 'mean',
            'P_pv': 'mean',
            'E_diff': 'mean',
            'E_shared': 'mean',
        }).round(3)
        
        hourly.columns = ['Avg Load (kW)', 'Avg Generation (kW)', 
                         'Avg Diff (kW)', 'Avg Shared (kW)']
        
        return hourly
    
    def get_mismatch_analysis(self) -> Dict:
        """分析供需错配情况"""
        if self.results is None:
            raise ValueError("需要先执行calculate_matching()")
        
        # 每日错配分析
        daily = self.results.groupby('Day').agg({
            'E_load': 'sum',
            'P_pv': 'sum',
            'E_diff': 'sum'
        })
        
        # 缺电天数
        deficit_days = (daily['E_diff'] < 0).sum()
        surplus_days = (daily['E_diff'] > 0).sum()
        
        return {
            'total_days': len(daily),
            'deficit_days': deficit_days,
            'surplus_days': surplus_days,
            'avg_daily_deficit': (
                daily[daily['E_diff'] < 0]['E_diff'].sum() / deficit_days 
                if deficit_days > 0 else 0
            ),
            'avg_daily_surplus': (
                daily[daily['E_diff'] > 0]['E_diff'].sum() / surplus_days 
                if surplus_days > 0 else 0
            ),
        }
