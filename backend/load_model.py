"""
建筑耗电量计算模块 (Load Model)
==============================

功能：根据建筑参数、气象数据、占用时间表计算逐时能耗

公式体系：
1. 几何推导: V = Area × Height × 0.9
2. 围护热损失: H_total = H_env + H_vent
3. 年度锚定: Q_H,annual = H_total × HDD × 24
4. 逐时分配: Q_h = Q_annual × w_h / Σw_h
5. 总负荷: E_total = E_light + E_appl + E_vent + E_hvac
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional

from italian_building_code_db import get_research_defaults

# 物理常数
H_VENT_COEFFICIENT = 0.34  # 0.34 = ρ × cp / 3600
CEILING_HEIGHT = 3.0  # 标准层高 [m]
NET_VOLUME_FACTOR = 0.9
PERIMETER_FACTOR = 4.08


class LoadModel:
    """建筑能耗计算模型"""
    
    def __init__(self, archetype_params: Dict, building_area: float = 100.0):
        """
        初始化能耗模型
        
        Parameters:
        -----------
        archetype_params : Dict
            建筑原型参数，优先使用研究字段：
            - Uenv / U_value: 综合围护U值 [W/(m²·K)]
            - Uwall_ref / Uwindow_ref / Uroof_renovated / Ufloor_renovated
            - P_light: 照明功率密度 [W/m²]
            - P_appl: 设备功率密度 [W/m²]
            - ACH_occ / ACH_unocc: 逐时换气次数 [h⁻¹]
            - COP_heat / COP_cool: 供暖/制冷唯一效率
            - SFP: 风机比功率 [kW·s/m³]
            - f_fan: 风机开关 (0/1)
        building_area : float
            建筑面积 [m²]，默认100 m²
        """
        self.params = archetype_params.copy()
        self.area = building_area
        self.height = float(self.params.get('Height', CEILING_HEIGHT))
        self.levels = int(self.params.get('Levels', 1))
        self.net_volume_factor = float(self.params.get('Net_Volume_Factor', NET_VOLUME_FACTOR))
        self.perimeter_factor = float(self.params.get('Perimeter_Factor', PERIMETER_FACTOR))

        self.volume = self.area * self.height * self.net_volume_factor
        self.perimeter = self.perimeter_factor * np.sqrt(self.area)
        self.area_roof = self.area
        self.area_floor = self.area
        self.area_wall = self.perimeter * self.height
        self.window_ratio = float(self.params.get('Window_Ratio', 0.25))
        self.area_window = self.area_wall * self.window_ratio
        self.area_opaque_wall = max(self.area_wall - self.area_window, 0.0)
        self.area_env_total = self.area_opaque_wall + self.area_window + self.area_roof + self.area_floor

        research_defaults = get_research_defaults()
        self.research_defaults = research_defaults
        
        # 设定温度
        self.T_int_heating = float(self.params.get('Heating_Setpoint', research_defaults['HEATING_SETPOINT']))
        self.T_int_cooling = float(self.params.get('Cooling_Setpoint', research_defaults['COOLING_SETPOINT']))
        self.cop_heat_ref = float(self.params.get('COP_heat', research_defaults['COP']))
        self.cop_cool_ref = float(self.params.get('COP_cool', research_defaults['EER']))
        self.sfp = float(self.params.get('SFP', research_defaults['SFP']))
        self.f_fan = int(self.params.get('f_fan', 1))
        self.electric_heating_enabled = bool(self.params.get('Electric_Heating', True))
        self.electric_cooling_enabled = bool(self.params.get('Electric_Cooling', True))
        self.electric_ventilation_enabled = bool(self.params.get('Electric_Ventilation', True))

        self.results = None

    def _prepare_weather_frame(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """统一气象数据列名并保证时间索引可用。"""
        frame = weather_df.copy()

        if 'Timestamp' not in frame.columns:
            if isinstance(frame.index, pd.DatetimeIndex):
                frame = frame.reset_index().rename(columns={'index': 'Timestamp'})
            elif 'DateTime' in frame.columns:
                frame['Timestamp'] = pd.to_datetime(frame['DateTime'])
            else:
                raise ValueError("weather_df 必须包含 Timestamp 或 DateTime 列")

        frame['Timestamp'] = pd.to_datetime(frame['Timestamp'])

        if 'T_amb' not in frame.columns:
            if 'T_Drybulb' in frame.columns:
                frame['T_amb'] = frame['T_Drybulb']
            else:
                raise ValueError("weather_df 必须包含 T_amb 或 T_Drybulb 列")

        return frame

    def _build_schedule_frame(self, schedule_df: pd.DataFrame) -> pd.DataFrame:
        """将 24 小时时间表或年时序表展开为统一格式。"""
        schedule = schedule_df.copy()
        if 'Timestamp' in schedule.columns and len(schedule) == 8760:
            for column in ['Occupancy', 'Lighting', 'Appliance', 'Ventilation']:
                if column not in schedule.columns:
                    schedule[column] = 0.0
            schedule['Timestamp'] = pd.to_datetime(schedule['Timestamp'])
            schedule['Hour'] = schedule['Timestamp'].dt.hour
            return schedule[['Timestamp', 'Hour', 'Occupancy', 'Lighting', 'Appliance', 'Ventilation']].reset_index(drop=True)

        if 'Hour' not in schedule.columns:
            raise ValueError("schedule_df must contain either Hour or Timestamp")

        schedule = schedule.set_index('Hour').reindex(range(24)).fillna(0.0)

        for column in ['Occupancy', 'Lighting', 'Appliance', 'Ventilation']:
            if column not in schedule.columns:
                schedule[column] = 0.0

        schedule = schedule.reset_index().rename(columns={'index': 'Hour'})
        schedule['Timestamp'] = pd.NaT
        return schedule[['Timestamp', 'Hour', 'Occupancy', 'Lighting', 'Appliance', 'Ventilation']]

    def _get_u_env(self) -> float:
        """获取综合 Uenv，优先使用研究字段。"""
        if str(self.params.get('Renovated', False)).lower() in {'true', '1', 'yes'}:
            u_wall = float(self.params.get('Uwall_renovated', self.params.get('Uwall_ref', self.params.get('U_value', 0.0))))
            u_window = float(self.params.get('Uwindow_renovated', self.params.get('Uwindow_ref', self.params.get('U_value', 0.0))))
            u_roof = float(self.params.get('Uroof_renovated', self.params.get('Uwall_ref', self.params.get('U_value', 0.0))))
            u_floor = float(self.params.get('Ufloor_renovated', self.params.get('Uwall_ref', self.params.get('U_value', 0.0))))
            total_area = self.area_opaque_wall + self.area_window + self.area_roof + self.area_floor
            if total_area > 0:
                return (
                    u_wall * self.area_opaque_wall +
                    u_window * self.area_window +
                    u_roof * self.area_roof +
                    u_floor * self.area_floor
                ) / total_area

        return float(self.params.get('Uenv', self.params.get('U_value', 0.0)))
    
    def calculate_hourly_load(
        self, 
        weather_df: pd.DataFrame,
        schedule_df: pd.DataFrame,
        region: str = "central"
    ) -> pd.DataFrame:
        """
        计算全年8760小时的逐时负荷
        
        Parameters:
        -----------
        weather_df : pd.DataFrame
            气象数据，包含列：Timestamp, T_amb, RH, ...
        schedule_df : pd.DataFrame
            占用时间表，包含列：Hour, Occupancy, Lighting, Appliance
        region : str
            地区(用于COP修正)
            
        Returns:
        --------
        pd.DataFrame
            包含各时刻的详细能耗分解
        """
        weather = self._prepare_weather_frame(weather_df)
        schedule = self._build_schedule_frame(schedule_df)

        if len(weather) != 8760:
            raise ValueError(f"weather_df 应为 8760 行，当前为 {len(weather)} 行")

        annual_schedule = len(schedule) == len(weather) and 'Timestamp' in schedule.columns and schedule['Timestamp'].notna().any()

        results = pd.DataFrame({
            'Timestamp': weather['Timestamp'].reset_index(drop=True),
            'T_amb': weather['T_amb'].reset_index(drop=True),
        })
        results['Hour'] = results['Timestamp'].dt.hour

        if annual_schedule:
            schedule = schedule.reset_index(drop=True)
            schedule['Timestamp'] = pd.to_datetime(schedule['Timestamp'])
            schedule_lookup = schedule.set_index('Timestamp')
            results = results.set_index('Timestamp')
            for column, target in [('Lighting', 'S_light'), ('Appliance', 'S_appl'), ('Occupancy', 'S_occ'), ('Ventilation', 'S_vent')]:
                results[target] = results.index.to_series().map(schedule_lookup[column].to_dict()).fillna(0.0).to_numpy()
            results = results.reset_index()
        else:
            schedule_lookup = schedule.set_index('Hour')
            results['S_light'] = results['Hour'].map(schedule_lookup['Lighting'].to_dict()).fillna(0.0)
            results['S_appl'] = results['Hour'].map(schedule_lookup['Appliance'].to_dict()).fillna(0.0)
            results['S_occ'] = results['Hour'].map(schedule_lookup['Occupancy'].to_dict()).fillna(0.0)
            results['S_vent'] = results['Hour'].map(schedule_lookup['Ventilation'].to_dict()).fillna(results['S_occ'])

        # 1. 终端负荷
        results['E_light'] = self.params.get('P_light', 0.0) * self.area * results['S_light'] / 1000.0
        results['E_appl'] = self.params.get('P_appl', 0.0) * self.area * results['S_appl'] / 1000.0

        # 2. 围护结构与通风热损失系数
        results['ACH'] = np.where(results['S_occ'] > 0, self.params.get('ACH_occ', self.research_defaults['ACH_OCCUPIED']), self.params.get('ACH_unocc', self.research_defaults['ACH_UNOCCUPIED']))
        results['H_vent'] = H_VENT_COEFFICIENT * results['ACH'] * self.volume
        results['H_env'] = self._get_u_env() * self.area_env_total
        results['H_total'] = results['H_env'] + results['H_vent']

        # 3. 年度 degree-day 锚定
        results['HDD_h'] = np.maximum(0.0, self.T_int_heating - results['T_amb'])
        results['CDD_h'] = np.maximum(0.0, results['T_amb'] - self.T_int_cooling)
        heating_degree_days = results['HDD_h'].sum() / 24.0
        cooling_degree_days = results['CDD_h'].sum() / 24.0
        h_total_ref = float(results['H_total'].mean())
        q_h_annual = h_total_ref * heating_degree_days * 24.0 / 1000.0
        q_c_annual = h_total_ref * cooling_degree_days * 24.0 / 1000.0

        # 4. 逐时权重分配
        occ_factor = results['S_occ'].clip(lower=0.0, upper=1.0)
        results['w_H'] = results['HDD_h'] * occ_factor
        results['w_C'] = results['CDD_h'] * occ_factor

        heating_weight_sum = results['w_H'].sum()
        cooling_weight_sum = results['w_C'].sum()
        results['w_H_norm'] = results['w_H'] / heating_weight_sum if heating_weight_sum > 0 else 0.0
        results['w_C_norm'] = results['w_C'] / cooling_weight_sum if cooling_weight_sum > 0 else 0.0

        results['Q_H_need'] = q_h_annual * results['w_H_norm']
        results['Q_C_need'] = q_c_annual * results['w_C_norm']

        # 5. HVAC 电耗（统一 COP/EER）
        results['COP_heat'] = self.cop_heat_ref
        results['COP_cool'] = self.cop_cool_ref
        results['E_heating'] = np.where(
            (results['Q_H_need'] > 0) & self.electric_heating_enabled,
            results['Q_H_need'] / results['COP_heat'],
            0.0,
        )
        results['E_cooling'] = np.where(
            (results['Q_C_need'] > 0) & self.electric_cooling_enabled,
            results['Q_C_need'] / results['COP_cool'],
            0.0,
        )
        results['E_hvac'] = results['E_heating'] + results['E_cooling']

        # 6. 风机电耗（与热损失分离）
        ventilation_run = results['S_vent'].clip(lower=0.0, upper=1.0)
        results['P_vent'] = np.where(
            self.electric_ventilation_enabled,
            self.f_fan * (self.volume * results['ACH'] / 3600.0) * self.sfp * ventilation_run,
            0.0,
        )
        results['E_vent'] = results['P_vent']

        # 7. 总负荷
        results['E_total'] = results['E_light'] + results['E_appl'] + results['E_vent'] + results['E_hvac']

        # 8. 记录年度锚定参数，便于调试与页面展示
        results['Q_H_annual'] = q_h_annual
        results['Q_C_annual'] = q_c_annual
        results['HDD_annual'] = heating_degree_days
        results['CDD_annual'] = cooling_degree_days
        results['H_total_ref'] = h_total_ref

        self.results = results
        return results
    
    def _get_cop_heating(self, T_amb):
        """
        根据环境温度计算供暖COP(温度修正)
        
        COP(T) = COP_ref - k × |T - T_ref|
        """
        return np.full_like(np.asarray(T_amb, dtype=float), self.cop_heat_ref, dtype=float)
    
    def _get_cop_cooling(self, T_amb):
        """
        根据环境温度计算制冷COP
        """
        return np.full_like(np.asarray(T_amb, dtype=float), self.cop_cool_ref, dtype=float)
    
    def get_summary_statistics(self) -> Dict:
        """获取年度统计指标"""
        if self.results is None:
            raise ValueError("需要先执行calculate_hourly_load()")

        total = self.results['E_total'].sum()
        hvac_total = self.results['E_hvac'].sum()
        heating_total = self.results['E_heating'].sum()
        cooling_total = self.results['E_cooling'].sum()
        lighting_total = self.results['E_light'].sum()
        appliance_total = self.results['E_appl'].sum()
        vent_total = self.results['E_vent'].sum()

        q_h_annual = float(self.results['Q_H_annual'].iloc[0]) if 'Q_H_annual' in self.results.columns else 0.0
        q_c_annual = float(self.results['Q_C_annual'].iloc[0]) if 'Q_C_annual' in self.results.columns else 0.0
        hdd_annual = float(self.results['HDD_annual'].iloc[0]) if 'HDD_annual' in self.results.columns else 0.0
        cdd_annual = float(self.results['CDD_annual'].iloc[0]) if 'CDD_annual' in self.results.columns else 0.0
        h_total_ref = float(self.results['H_total_ref'].iloc[0]) if 'H_total_ref' in self.results.columns else 0.0

        return {
            'annual_total_kwh': total,
            'annual_avg_kw': self.results['E_total'].mean(),
            'monthly_avg': self.results.groupby(self.results['Timestamp'].dt.month)['E_total'].mean(),
            'lighting_total_kwh': lighting_total,
            'appliance_total_kwh': appliance_total,
            'ventilation_total_kwh': vent_total,
            'hvac_total_kwh': hvac_total,
            'heating_total_kwh': heating_total,
            'cooling_total_kwh': cooling_total,
            'lighting_ratio': lighting_total / total * 100 if total > 0 else 0,
            'appliance_ratio': appliance_total / total * 100 if total > 0 else 0,
            'ventilation_ratio': vent_total / total * 100 if total > 0 else 0,
            'hvac_ratio': hvac_total / total * 100 if total > 0 else 0,
            'heating_ratio': heating_total / total * 100 if total > 0 else 0,
            'cooling_ratio': cooling_total / total * 100 if total > 0 else 0,
            'peak_load_kw': self.results['E_total'].max(),
            'min_load_kw': self.results['E_total'].min(),
            'heating_setpoint_c': self.T_int_heating,
            'cooling_setpoint_c': self.T_int_cooling,
            'cop_heat_ref': self.cop_heat_ref,
            'cop_cool_ref': self.cop_cool_ref,
            'u_env': self._get_u_env(),
            'volume_m3': self.volume,
            'area_env_m2': self.area_env_total,
            'area_wall_m2': self.area_wall,
            'area_window_m2': self.area_window,
            'area_opaque_wall_m2': self.area_opaque_wall,
            'area_roof_m2': self.area_roof,
            'area_floor_m2': self.area_floor,
            'window_ratio': self.window_ratio,
            'q_h_annual_kwh': q_h_annual,
            'q_c_annual_kwh': q_c_annual,
            'hdd_annual': hdd_annual,
            'cdd_annual': cdd_annual,
            'h_total_ref_wk': h_total_ref,
            'h_env_wk': self._get_u_env() * self.area_env_total,
            'sfp': self.sfp,
            'f_fan': self.f_fan,
            'electric_heating': self.electric_heating_enabled,
            'electric_cooling': self.electric_cooling_enabled,
            'electric_ventilation': self.electric_ventilation_enabled,
        }
