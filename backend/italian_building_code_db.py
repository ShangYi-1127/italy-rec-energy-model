"""
意大利建筑能效法规参数数据库
==============================
来源：DM Linee Guida - Appendix A & B

用途：为建筑原型参数库提供法规标准值
可直接导入 archetype_data.py 或其他计算模块
"""

# ============================================================
# 1. 气候区定义
# ============================================================

CLIMATE_ZONES = {
    'A': {'label': '极温和', 'dd_range': 'DD < 600', 'cities': ['巴勒莫', '卡塔尼亚']},
    'B': {'label': '温和', 'dd_range': '600 ≤ DD < 900', 'cities': ['那不勒斯', '卡利亚里']},
    'C': {'label': '温凉', 'dd_range': '900 ≤ DD < 1400', 'cities': ['罗马', '巴里']},
    'D': {'label': '凉爽', 'dd_range': '1400 ≤ DD < 2100', 'cities': ['米兰', '威尼斯']},
    'E': {'label': '寒冷', 'dd_range': '2100 ≤ DD < 3000', 'cities': ['都灵', '博洛尼亚']},
    'F': {'label': '极寒', 'dd_range': 'DD ≥ 3000', 'cities': ['阿奥斯塔', '特伦托']},
}

# ============================================================
# 2. U值表（新建建筑 - Appendix A）
# ============================================================

U_VALUES_NEW_BUILDING_2019_2021 = {
    """
    新建建筑参考U值标准（2019/2021）
    单位：W/m²·K
    """
    
    'VERTICAL_WALLS': {  # 垂直结构（墙体）
        'A': 0.43,
        'B': 0.43,
        'C': 0.34,
        'D': 0.29,
        'E': 0.26,
        'F': 0.24,
    },
    
    'HORIZONTAL_ROOF': {  # 水平屋顶（含倾斜）
        'A': 0.35,
        'B': 0.35,
        'C': 0.33,
        'D': 0.26,
        'E': 0.22,
        'F': 0.20,
    },
    
    'HORIZONTAL_FLOOR': {  # 水平地板（地下、地上）
        'A': 0.44,
        'B': 0.44,
        'C': 0.38,
        'D': 0.29,
        'E': 0.26,
        'F': 0.24,
    },
    
    'TRANSPARENT_WINDOWS': {  # 透光（窗户、玻璃门）
        'A': 3.00,
        'B': 3.00,
        'C': 2.20,
        'D': 1.80,
        'E': 1.40,
        'F': 1.10,
    },
    
    'SEPARATION_WALLS': {  # 分隔墙（业主间）
        'A': 0.8,
        'B': 0.8,
        'C': 0.8,
        'D': 0.8,
        'E': 0.8,
        'F': 0.8,
    },
}

# ============================================================
# 3. U值表（既有建筑改造 - Appendix B）
# ============================================================

U_VALUES_EXISTING_RENOVATION_2021 = {
    """
    既有建筑能效改造最大U值（2021年标准）
    单位：W/m²·K
    """
    
    'VERTICAL_WALLS': {
        'A': 0.40,
        'B': 0.40,
        'C': 0.36,
        'D': 0.32,
        'E': 0.28,
        'F': 0.26,
    },
    
    'HORIZONTAL_ROOF': {
        'A': 0.32,
        'B': 0.32,
        'C': 0.32,
        'D': 0.26,
        'E': 0.24,
        'F': 0.22,
    },
    
    'HORIZONTAL_FLOOR': {
        'A': 0.42,
        'B': 0.42,
        'C': 0.38,
        'D': 0.32,
        'E': 0.29,
        'F': 0.28,
    },
    
    'TRANSPARENT_WINDOWS': {
        'A': 3.00,
        'B': 3.00,
        'C': 2.00,
        'D': 1.80,
        'E': 1.40,
        'F': 1.00,
    },
}

# ============================================================
# 4. 利用子系统效率 ηu
# ============================================================

UTILIZATION_SUBSYSTEM_EFFICIENCY = {
    """
    包括发射/供应、调节、分配、蓄热的综合效率
    标准：Appendix A 表7
    """
    'HYDRAULIC_DISTRIBUTION': {
        'H': 0.81,  # 采暖
        'C': 0.81,  # 制冷
        'W': 0.70,  # 热水
    },
    'AIR_DISTRIBUTION': {
        'H': 0.83,
        'C': 0.83,
        'W': None,  # 不适用
    },
    'MIXED_DISTRIBUTION': {
        'H': 0.82,
        'C': 0.82,
        'W': None,
    },
}

# ============================================================
# 5. 生成子系统效率 ηgn（新建参考）
# ============================================================

GENERATION_SUBSYSTEM_EFFICIENCY_NEW = {
    """
    各类热源、冷源、电源效率
    单位：无（相对效率或COP/EER/GUE）
    标准：Appendix A 表8
    """
    
    'BOILER': {
        'OIL': {'H': 0.82, 'W': 0.80},
        'GAS': {'H': 0.95, 'W': 0.85},
        'SOLID_FUEL': {'H': 0.72, 'W': 0.70},
        'BIOMASS_SOLID': {'H': 0.72, 'W': 0.65},
        'BIOMASS_LIQUID': {'H': 0.82, 'W': 0.75},
    },
    
    'HEAT_PUMP': {
        'ELECTRIC_VAPOR_COMPRESSION': {
            'H': 3.00,  # COP
            'C': 2.50,  # EER
            'W': 2.50,  # COP
        },
        'ABSORPTION': {
            'H': 1.20,  # GUE
            'C': 0.60,  # 依赖ηgn
            'W': 1.10,  # GUE
        },
        'ENDOTHERMIC': {
            'H': 1.15,
            'C': 1.00,
            'W': 1.05,
        },
    },
    
    'CHILLER': {
        'VAPOR_COMPRESSION': {
            'C': 2.50,  # EER
        },
        'ABSORPTION_INDIRECT': {
            'C': 0.60,  # 乘以ηgn
        },
        'DIRECT_FLAME': {
            'C': 0.60,
        },
    },
    
    'SOLAR': {
        'THERMAL': {'H': 0.30, 'W': 0.30},
        'PHOTOVOLTAIC': {'ELECTRICITY': 0.10},
    },
    
    'NETWORK': {
        'DISTRICT_HEATING': {'H': 0.97},
        'DISTRICT_COOLING': {'C': 0.97},
    },
    
    'COGENERATION': {
        'CHP': {'H': 0.55, 'W': 0.55, 'ELECTRICITY': 0.25},
    },
    
    'ELECTRIC': {
        'RESISTANCE_HEATER': {'H': 1.00},
    },
}

# ============================================================
# 6. 电动热泵最低性能要求（改造）
# ============================================================

HEAT_PUMP_PERFORMANCE_REQUIREMENTS = {
    """
    既有建筑改造的热泵最低COP/EER要求
    标准：Appendix B 表6-7
    """
    
    'HEATING': {
        'AIR_TO_AIR': 3.5,
        'AIR_TO_WATER_SMALL': 3.8,  # ≤35kW
        'AIR_TO_WATER_LARGE': 3.5,  # >35kW
        'GROUND_TO_AIR': 4.0,
        'GROUND_TO_WATER': 4.0,
        'WATER_TO_AIR': 4.2,
        'WATER_TO_WATER': 4.2,
    },
    
    'COOLING': {
        'AIR_TO_AIR': 3.0,
        'AIR_TO_WATER_SMALL': 3.5,  # ≤35kW
        'AIR_TO_WATER_LARGE': 3.0,  # >35kW
        'GROUND_TO_AIR': 4.0,
        'GROUND_TO_WATER': 4.0,
        'WATER_TO_AIR': 4.0,
        'WATER_TO_WATER': 4.2,
    },
}

# ============================================================
# 7. 吸收式热泵性能要求
# ============================================================

ABSORPTION_HEAT_PUMP_GUE = {
    """
    吸收式/内燃机热泵GUE要求
    标准：Appendix B 表8-9
    """
    
    'HEATING': {
        'AIR_TO_AIR': 1.38,
        'AIR_TO_WATER': 1.30,
        'GROUND_TO_AIR': 1.45,
        'GROUND_TO_WATER': 1.40,
        'WATER_TO_AIR': 1.50,
        'WATER_TO_WATER': 1.45,
    },
    
    'COOLING': {
        'ALL_TYPES': 0.6,  # EER统一值
    },
}

# ============================================================
# 8. 通风系统能耗
# ============================================================

VENTILATION_SYSTEM_ENERGY = {
    """
    机械通风系统单位能耗
    单位：Wh/m³
    标准：Appendix A 表9
    """
    
    'SINGLE_FLOW_EXTRACTION': 0.25,
    'SINGLE_FLOW_SUPPLY_FILTERED': 0.30,
    'DUAL_FLOW_NO_RECOVERY': 0.35,
    'DUAL_FLOW_WITH_RECOVERY': 0.50,  # 热回收效率~90%
}

# ============================================================
# 9. 日射性能
# ============================================================

SOLAR_RADIATION_FACTORS = {
    """
    日射传导系数（含活动遮阳）
    标准：Appendix A 表6 & Appendix B 表5
    """
    
    'WINDOW_TRANSMITTANCE_WITH_SHADING': 0.35,  # ggl+sh
}

# ============================================================
# 10. 研究统一默认值
# ============================================================

RESEARCH_DEFAULTS = {
    'COP': 3.0,
    'EER': 2.8,
    'HEATING_SETPOINT': 20.0,
    'COOLING_SETPOINT': 26.0,
    'NET_VOLUME_FACTOR': 0.9,
    'ACH_OCCUPIED': 0.5,
    'ACH_UNOCCUPIED': 0.1,
    'SFP': 1.5,
}

PERIOD_UENV_RULES = [
    {
        'label': '<1900',
        'year_min': None,
        'year_max': 1900,
        'Uwall': 1.61,
        'Uwindow': 5.70,
        'Uenv': 2.29,
        'description': '厚石墙/砖墙，单层玻璃',
    },
    {
        'label': '1901-1945',
        'year_min': 1901,
        'year_max': 1945,
        'Uwall': 1.55,
        'Uwindow': 5.00,
        'Uenv': 2.16,
        'description': '承重砖墙，无保温',
    },
    {
        'label': '1946-1975',
        'year_min': 1946,
        'year_max': 1975,
        'Uwall': 1.40,
        'Uwindow': 4.50,
        'Uenv': 1.96,
        'description': '空心砖墙，无保温层',
    },
    {
        'label': '1976-1990',
        'year_min': 1976,
        'year_max': 1990,
        'Uwall': 0.80,
        'Uwindow': 3.00,
        'Uenv': 1.26,
        'description': '第一部节能法后，开始有简单保温',
    },
    {
        'label': '1991-2005',
        'year_min': 1991,
        'year_max': 2005,
        'Uwall': 0.55,
        'Uwindow': 2.20,
        'Uenv': 0.90,
        'description': 'L. 10/91 后，保温性能显著提升',
    },
    {
        'label': 'After 2005',
        'year_min': 2006,
        'year_max': None,
        'Uwall': 0.34,
        'Uwindow': 1.80,
        'Uenv': 0.67,
        'description': '满足 D.M. 2005 及后续 NZEB 标准',
    },
]


def get_period_rule_from_year(year: int):
    """根据建造年份返回年代分段规则。"""
    if year is None:
        return PERIOD_UENV_RULES[-1]

    for rule in PERIOD_UENV_RULES:
        if rule['year_min'] is None and year < rule['year_max']:
            return rule
        if rule['year_min'] is not None and year >= rule['year_min'] and (
            rule['year_max'] is None or year <= rule['year_max']
        ):
            return rule

    return PERIOD_UENV_RULES[-1]


def get_research_uenv_from_year(year: int) -> dict:
    """获取未改造建筑的年代映射 U 值。"""
    return get_period_rule_from_year(year).copy()


def get_research_defaults() -> dict:
    """返回研究统一默认值副本。"""
    return RESEARCH_DEFAULTS.copy()

# ============================================================
# 10. 燃锅炉效率公式
# ============================================================

def calculate_boiler_efficiency(power_nominal_kw: float, partial_load: bool = False) -> float:
    """
    计算燃气/燃油锅炉最小效率
    
    参数：
        power_nominal_kw: 锅炉额定功率 (kW)
        partial_load: 是否计算部分负荷（30%）效率
    
    返回：
        最小效率 (%)
    
    公式：
        全负荷：η = 90 + 2 log₁₀(Pn)
        部分负荷：η(30%) = 85 + 3 log₁₀(Pn)
        
    限制：
        Pn > 400 kW 时，用 400 kW 计算
    
    示例：
        >>> calculate_boiler_efficiency(20)  # 92.60
        >>> calculate_boiler_efficiency(100)  # 94.00
        >>> calculate_boiler_efficiency(20, partial_load=True)  # 88.20
    """
    import math
    
    # 限制最大值
    Pn = min(power_nominal_kw, 400)
    
    if partial_load:
        # 部分负荷（30%）
        eta = 85 + 3 * math.log10(Pn)
    else:
        # 全负荷
        eta = 90 + 2 * math.log10(Pn)
    
    return round(eta, 2)


# ============================================================
# 11. 综合数据查询函数
# ============================================================

def get_u_value(structure_type: str, climate_zone: str, building_type: str = 'NEW') -> float:
    """
    获取U值
    
    参数：
        structure_type: 'VERTICAL', 'ROOF', 'FLOOR', 'WINDOW', 'SEPARATION'
        climate_zone: 'A', 'B', 'C', 'D', 'E', 'F'
        building_type: 'NEW'（新建）或 'EXISTING'（改造）
    
    返回：
        U值 (W/m²·K)
    """
    
    type_key = {
        'VERTICAL': 'VERTICAL_WALLS',
        'ROOF': 'HORIZONTAL_ROOF',
        'FLOOR': 'HORIZONTAL_FLOOR',
        'WINDOW': 'TRANSPARENT_WINDOWS',
        'SEPARATION': 'SEPARATION_WALLS',
    }.get(structure_type.upper())
    
    if type_key is None:
        raise ValueError(f"Unknown structure type: {structure_type}")

    climate_zone = climate_zone.upper()
    building_type = building_type.upper()

    new_building = {
        'VERTICAL_WALLS': {'A': 0.43, 'B': 0.43, 'C': 0.34, 'D': 0.29, 'E': 0.26, 'F': 0.24},
        'HORIZONTAL_ROOF': {'A': 0.35, 'B': 0.35, 'C': 0.33, 'D': 0.26, 'E': 0.22, 'F': 0.20},
        'HORIZONTAL_FLOOR': {'A': 0.44, 'B': 0.44, 'C': 0.38, 'D': 0.29, 'E': 0.26, 'F': 0.24},
        'TRANSPARENT_WINDOWS': {'A': 3.00, 'B': 3.00, 'C': 2.20, 'D': 1.80, 'E': 1.40, 'F': 1.10},
        'SEPARATION_WALLS': {'A': 0.8, 'B': 0.8, 'C': 0.8, 'D': 0.8, 'E': 0.8, 'F': 0.8},
    }

    existing_building = {
        'VERTICAL_WALLS': {'A': 0.40, 'B': 0.40, 'C': 0.36, 'D': 0.32, 'E': 0.28, 'F': 0.26},
        'HORIZONTAL_ROOF': {'A': 0.32, 'B': 0.32, 'C': 0.32, 'D': 0.26, 'E': 0.24, 'F': 0.22},
        'HORIZONTAL_FLOOR': {'A': 0.42, 'B': 0.42, 'C': 0.38, 'D': 0.32, 'E': 0.29, 'F': 0.28},
        'TRANSPARENT_WINDOWS': {'A': 3.00, 'B': 3.00, 'C': 2.00, 'D': 1.80, 'E': 1.40, 'F': 1.00},
    }

    if building_type == 'NEW':
        table = new_building
    else:
        table = existing_building

    return table[type_key].get(climate_zone)


def get_system_efficiency(system_type: str, component: str, service: str) -> float:
    """
    获取系统效率
    
    参数：
        system_type: 'UTILIZATION' 或 'GENERATION'
        component: 系统子类型
        service: 'H'（采暖）、'C'（制冷）、'W'（热水）或 'ELECTRICITY'
    
    返回：
        效率值（COP/EER/GUE或比例）
    """
    
    if system_type.upper() == 'UTILIZATION':
        data = UTILIZATION_SUBSYSTEM_EFFICIENCY.get(component.upper())
        return data.get(service.upper()) if data else None
    
    elif system_type.upper() == 'GENERATION':
        data = GENERATION_SUBSYSTEM_EFFICIENCY_NEW.get(component.upper())
        if data and isinstance(data, dict):
            return data.get(service.upper())
        return data


# ============================================================
# 12. 数据验证函数
# ============================================================

def validate_u_value(u_value: float, structure_type: str, climate_zone: str, 
                     building_type: str = 'NEW') -> bool:
    """
    验证U值是否符合法规要求
    
    返回：
        True 如果 u_value ≤ 限值，False 否则
    """
    limit = get_u_value(structure_type, climate_zone, building_type)
    return u_value <= limit if limit else False


# ============================================================
# 13. 使用示例
# ============================================================

if __name__ == '__main__':
    # 示例1：查询新建建筑D区墙体U值
    u_wall_d = get_u_value('VERTICAL', 'D', 'NEW')
    print(f"D区新建墙体U值: {u_wall_d} W/m²·K")  # 0.29
    
    # 示例2：改造F区窗户
    u_window_f = get_u_value('WINDOW', 'F', 'EXISTING')
    print(f"F区改造窗户U值: {u_window_f} W/m²·K")  # 1.00
    
    # 示例3：计算锅炉效率
    eta_20kw = calculate_boiler_efficiency(20)
    print(f"20kW锅炉全负荷效率: {eta_20kw}%")  # 92.60%
    
    eta_20kw_partial = calculate_boiler_efficiency(20, partial_load=True)
    print(f"20kW锅炉部分负荷效率: {eta_20kw_partial}%")  # 88.20%
    
    # 示例4：获取热泵COP
    cop_air_air = HEAT_PUMP_PERFORMANCE_REQUIREMENTS['HEATING']['AIR_TO_AIR']
    print(f"空气-空气热泵采暖COP: {cop_air_air}")  # 3.5
    
    # 示例5：获取通风能耗
    eve_recovery = VENTILATION_SYSTEM_ENERGY['DUAL_FLOW_WITH_RECOVERY']
    print(f"双流带回收通风能耗: {eve_recovery} Wh/m³")  # 0.50
    
    # 示例6：验证改造方案
    is_compliant = validate_u_value(0.38, 'ROOF', 'D', 'EXISTING')
    print(f"屋顶U=0.38 D区改造是否符合（限值0.26）: {is_compliant}")  # False
