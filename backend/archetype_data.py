"""
建筑原型库数据 (Archetype Data)
=============================

存储建筑原型参数矩阵
"""

import pandas as pd
from typing import Dict, List

from data.params import BASE_PARAMS
from italian_building_code_db import (
    get_research_defaults,
    get_research_uenv_from_year,
    get_u_value,
)


REGION_CLIMATE_ZONE_MAP = {
    'Piemonte': 'E',
    'Lazio': 'D',
    'Sicilia': 'B',
}

BASE_BUILDING_TYPE_KEYS = {
    '住宅': '住宅',
    '办公': '办公',
    '商业': '商业',
    '教育': '教育',
    'Residential': '住宅',
    'Office': '办公',
    'Commercial': '商业',
    'Educational': '教育',
}

BASE_PARAM_KEYS = {
    '住宅': 'ResidentialApartment',
    '办公': 'Office building',
    '商业': 'Commercial building',
    '教育': 'Educational building',
}

DISPLAY_BUILDING_TYPES = ['Residential', 'Office', 'Commercial', 'Educational']


def _parse_age_to_year(age: str) -> int:
    """将年代标签转换为代表年份。"""
    age = str(age).strip()

    if age == '<1900':
        return 1899
    if age == '1901-1945':
        return 1925
    if age == '1946-1975':
        return 1960
    if age == '1976-1990':
        return 1983
    if age == '1991-2005':
        return 1998
    if age in ('2006-至今', '2006-现在', '>2005'):
        return 2015

    if age.startswith('<'):
        try:
            return max(int(age[1:]) - 1, 1890)
        except ValueError:
            return 1899

    if age.startswith('>'):
        try:
            return int(age[1:]) + 1
        except ValueError:
            return 2015

    if '-' in age:
        try:
            start, end = age.split('-', 1)
            return (int(start) + int(end)) // 2
        except ValueError:
            return 2000

    try:
        return int(age)
    except ValueError:
        return 2015


def _period_label_from_age(age: str) -> str:
    """将年代输入映射到研究采用的年代分段标签。"""
    year = _parse_age_to_year(age)
    if year < 1900:
        return '<1900'
    if 1901 <= year <= 1945:
        return '1901-1945'
    if 1946 <= year <= 1975:
        return '1946-1975'
    if 1976 <= year <= 1990:
        return '1976-1990'
    if 1991 <= year <= 2005:
        return '1991-2005'
    return '2006-至今'


# 建筑原型参数示例库
ARCHETYPE_PARAMS = {
    # 格式: (地区, 年代, 类型) -> 参数字典
    
    # ========== 北部 (Piemonte) ==========
    
    # 住宅
    ('Piemonte', '<1919', '住宅'): {
        'U_value': 1.8,
        'P_light': 8,
        'P_appl': 3,
        'ACH_occ': 0.8,
        'ACH_unocc': 0.2,
        'COP_heat': 1.9,
        'COP_cool': 2.1,
        'Window_Ratio': 0.25,
        'Thermal_Mass': 'High',
        'Description': '极老住宅，很差隔热'
    },
    ('Piemonte', '1946-1960', '住宅'): {
        'U_value': 0.9,
        'P_light': 8,
        'P_appl': 3,
        'ACH_occ': 0.9,
        'ACH_unocc': 0.3,
        'COP_heat': 2.4,
        'COP_cool': 2.6,
        'Window_Ratio': 0.28,
        'Thermal_Mass': 'Medium',
        'Description': '战后典型住宅'
    },
    ('Piemonte', '>2005', '住宅'): {
        'U_value': 0.18,
        'P_light': 8,
        'P_appl': 3,
        'ACH_occ': 1.0,
        'ACH_unocc': 0.35,
        'COP_heat': 3.8,
        'COP_cool': 4.0,
        'Window_Ratio': 0.40,
        'Thermal_Mass': 'Low',
        'Description': '新建高效住宅'
    },
    
    # 办公
    ('Piemonte', '<1919', '办公'): {
        'U_value': 1.9,
        'P_light': 12,
        'P_appl': 6,
        'ACH_occ': 1.5,
        'ACH_unocc': 0.3,
        'COP_heat': 1.8,
        'COP_cool': 2.0,
        'Window_Ratio': 0.35,
        'Thermal_Mass': 'High',
        'Description': '老式办公楼'
    },
    ('Piemonte', '>2005', '办公'): {
        'U_value': 0.22,
        'P_light': 12,
        'P_appl': 6,
        'ACH_occ': 2.0,
        'ACH_unocc': 0.4,
        'COP_heat': 3.6,
        'COP_cool': 3.8,
        'Window_Ratio': 0.45,
        'Thermal_Mass': 'Low',
        'Description': '新建智能办公楼'
    },
    
    # 商业
    ('Piemonte', '<1919', '商业'): {
        'U_value': 1.7,
        'P_light': 15,
        'P_appl': 10,
        'ACH_occ': 1.2,
        'ACH_unocc': 0.3,
        'COP_heat': 2.0,
        'COP_cool': 2.2,
        'Window_Ratio': 0.40,
        'Thermal_Mass': 'High',
        'Description': '传统商店'
    },
    ('Piemonte', '>2005', '商业'): {
        'U_value': 0.20,
        'P_light': 15,
        'P_appl': 10,
        'ACH_occ': 1.8,
        'ACH_unocc': 0.4,
        'COP_heat': 3.5,
        'COP_cool': 3.9,
        'Window_Ratio': 0.50,
        'Thermal_Mass': 'Low',
        'Description': '现代超市/购物中心'
    },
    
    # 教育
    ('Piemonte', '1961-1970', '教育'): {
        'U_value': 0.8,
        'P_light': 10,
        'P_appl': 5,
        'ACH_occ': 2.0,
        'ACH_unocc': 0.5,
        'COP_heat': 2.3,
        'COP_cool': 2.5,
        'Window_Ratio': 0.35,
        'Thermal_Mass': 'Medium',
        'Description': '1960年代学校'
    },
    ('Piemonte', '>2005', '教育'): {
        'U_value': 0.16,
        'P_light': 10,
        'P_appl': 5,
        'ACH_occ': 2.5,
        'ACH_unocc': 0.5,
        'COP_heat': 3.7,
        'COP_cool': 4.1,
        'Window_Ratio': 0.48,
        'Thermal_Mass': 'Low',
        'Description': '新建生态校舍'
    },
    
    # ========== 中部 (Lazio) ==========
    
    ('Lazio', '<1919', '住宅'): {
        'U_value': 1.5,
        'P_light': 8,
        'P_appl': 3,
        'ACH_occ': 0.9,
        'ACH_unocc': 0.25,
        'COP_heat': 2.6,
        'COP_cool': 2.8,
        'Window_Ratio': 0.30,
        'Thermal_Mass': 'Medium',
        'Description': '老式罗马住宅'
    },
    ('Lazio', '>2005', '住宅'): {
        'U_value': 0.16,
        'P_light': 8,
        'P_appl': 3,
        'ACH_occ': 1.0,
        'ACH_unocc': 0.35,
        'COP_heat': 3.9,
        'COP_cool': 4.2,
        'Window_Ratio': 0.42,
        'Thermal_Mass': 'Low',
        'Description': '现代罗马公寓'
    },
    
    # ========== 南部 (Sicilia) ==========
    
    ('Sicilia', '<1919', '住宅'): {
        'U_value': 1.3,
        'P_light': 8,
        'P_appl': 3,
        'ACH_occ': 1.0,
        'ACH_unocc': 0.3,
        'COP_heat': 3.2,
        'COP_cool': 3.5,
        'Window_Ratio': 0.25,
        'Thermal_Mass': 'High',
        'Description': '传统西西里建筑'
    },
    ('Sicilia', '>2005', '住宅'): {
        'U_value': 0.15,
        'P_light': 8,
        'P_appl': 3,
        'ACH_occ': 1.0,
        'ACH_unocc': 0.35,
        'COP_heat': 4.0,
        'COP_cool': 4.5,
        'Window_Ratio': 0.45,
        'Thermal_Mass': 'Low',
        'Description': '南部现代高效住宅'
    },
}


class ArchetypeDataManager:
    """建筑原型数据管理"""
    
    def __init__(self):
        self.archetypes = ARCHETYPE_PARAMS
    
    def get_archetype_params(
        self,
        region: str,
        age: str,
        building_type: str
    ) -> Dict:
        """
        获取指定建筑原型的参数
        
        Parameters:
        -----------
        region : str
            地区名称
        age : str
            建造年代
        building_type : str
            建筑类型
            
        Returns:
        --------
        Dict
            建筑参数字典
        """
        key = (region, age, building_type)
        normalized_type = BASE_BUILDING_TYPE_KEYS.get(building_type, building_type)
        
        if key not in self.archetypes:
            # 如果精确匹配不到，返回同类型的最接近原型
            similar = [
                v for k, v in self.archetypes.items()
                if k[2] == normalized_type
            ]
            if similar:
                params = similar[0].copy()
            else:
                raise ValueError(f"找不到匹配的建筑原型: {region}, {age}, {building_type}")
        else:
            params = self.archetypes[key].copy()

        research_defaults = get_research_defaults()
        building_year = _parse_age_to_year(age)
        period_label = _period_label_from_age(age)
        climate_zone = REGION_CLIMATE_ZONE_MAP.get(region, 'D')

        # 保留 legacy 参数，同时补充研究计算需要的唯一值字段
        params['BuildingYear'] = building_year
        params['PeriodLabel'] = period_label
        params['ClimateZone'] = climate_zone
        params['Renovated'] = False

        # 研究默认的 HVAC 与通风参数
        base_key = BASE_PARAM_KEYS.get(normalized_type)
        base_components = BASE_PARAMS.get(base_key, {}).get('components', {}) if base_key else {}
        if base_components:
            params['P_light'] = float(base_components.get('Lighting', params.get('P_light', 0.0)))
            params['P_appl'] = float(base_components.get('Appliances', params.get('P_appl', 0.0)))
            params['Occupant_Density'] = float(base_components.get('Density', 0.0))

        params['COP_heat'] = research_defaults['COP']
        params['COP_cool'] = research_defaults['EER']
        params['ACH_occ'] = research_defaults['ACH_OCCUPIED']
        params['ACH_unocc'] = research_defaults['ACH_UNOCCUPIED']
        params['SFP'] = research_defaults['SFP']
        params['f_fan'] = 0 if normalized_type == '住宅' and building_year < 2015 else 1

        # 几何默认值，用于研究公式的面积加权和体积计算
        params['Height'] = params.get('Height', 3.0)
        params['Levels'] = params.get('Levels', 1)
        params['Net_Volume_Factor'] = research_defaults['NET_VOLUME_FACTOR']
        params['Perimeter_Factor'] = 4.08
        params['Window_Ratio'] = params.get('Window_Ratio', 0.25)

        # 未改造建筑：使用年代映射 Uenv
        age_uenv = get_research_uenv_from_year(building_year)
        params['Uwall_ref'] = age_uenv['Uwall']
        params['Uwindow_ref'] = age_uenv['Uwindow']
        params['Uenv'] = age_uenv['Uenv']
        params['U_value'] = age_uenv['Uenv']
        params['Uenv_description'] = age_uenv['description']

        # 已改造建筑的详细参考值保留为可选字段，便于后续按面积加权
        params['Uwall_renovated'] = get_u_value('VERTICAL', climate_zone, 'EXISTING')
        params['Uroof_renovated'] = get_u_value('ROOF', climate_zone, 'EXISTING')
        params['Ufloor_renovated'] = get_u_value('FLOOR', climate_zone, 'EXISTING')
        params['Uwindow_renovated'] = get_u_value('WINDOW', climate_zone, 'EXISTING')

        return params
    
    def list_available_regions(self) -> List[str]:
        """列出所有可用地区"""
        regions = set()
        for region, _, _ in self.archetypes.keys():
            regions.add(region)
        return sorted(list(regions))
    
    def list_available_ages(self) -> List[str]:
        """列出所有可用年代"""
        return ['<1900', '1901-1945', '1946-1975', '1976-1990', '1991-2005', '2006-至今']
    
    def list_available_types(self) -> List[str]:
        """列出所有可用类型"""
        return DISPLAY_BUILDING_TYPES.copy()
    
    def get_all_archetypes_dataframe(self) -> pd.DataFrame:
        """返回所有原型的DataFrame格式"""
        data = []
        for (region, age, btype), params in self.archetypes.items():
            row = {
                'Region': region,
                'Age_Period': age,
                'BuildingType': btype,
                **params
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def compare_archetypes(
        self,
        archetype1: tuple,
        archetype2: tuple
    ) -> Dict:
        """
        对比两个建筑原型的关键参数差异
        
        Parameters:
        -----------
        archetype1, archetype2 : tuple
            (region, age, building_type)
        """
        params1 = self.get_archetype_params(*archetype1)
        params2 = self.get_archetype_params(*archetype2)
        
        comparison = {
            'Archetype 1': f"{archetype1[0]} {archetype1[1]} {archetype1[2]}",
            'Archetype 2': f"{archetype2[0]} {archetype2[1]} {archetype2[2]}",
            'Differences': {}
        }
        
        for key in ['U_value', 'P_light', 'P_appl', 'COP_heat', 'COP_cool']:
            if key in params1 and key in params2:
                diff = ((params2[key] - params1[key]) / params1[key] * 100) \
                       if params1[key] != 0 else 0
                comparison['Differences'][key] = {
                    'Archetype1_value': params1[key],
                    'Archetype2_value': params2[key],
                    'Percent_change': diff
                }
        
        return comparison
