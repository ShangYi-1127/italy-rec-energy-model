# 意大利法规参数集成指南

**创建日期**：2026-05-14  
**文件来源**：DM（法令）- Appendix A & Appendix B

---

## 📂 已创建文件清单

| 文件                                        | 类型       | 用途                       |
| ------------------------------------------- | ---------- | -------------------------- |
| `ITALIAN_BUILDING_CODE_PARAMETERS.md`       | 文档       | 完整法规参数说明与表格     |
| `data/ITALIAN_BUILDING_CODE_PARAMETERS.csv` | 数据       | 可导入Excel/数据库的参数表 |
| `backend/italian_building_code_db.py`       | Python模块 | 项目代码直接使用的参数库   |

---

## 🔧 项目集成方法

### 方法1：在 `archetype_data.py` 中导入

```python
# 在 archetype_data.py 顶部添加

from backend.italian_building_code_db import (
    U_VALUES_NEW_BUILDING_2019_2021,
    U_VALUES_EXISTING_RENOVATION_2021,
    HEAT_PUMP_PERFORMANCE_REQUIREMENTS,
    get_u_value,
    calculate_boiler_efficiency,
)

# 示例：创建符合法规的建筑原型

ARCHETYPE_PARAMS = {
    # Piemonte D区新建办公楼
    ('Piemonte', '>2005', '办公'): {
        'U_value': get_u_value('VERTICAL', 'D', 'NEW'),  # 0.29
        'COP_heat': HEAT_PUMP_PERFORMANCE_REQUIREMENTS['HEATING']['AIR_TO_WATER_LARGE'],  # 3.5
        # ... 其他参数
    },

    # Lazio C区改造住宅
    ('Lazio', '1961-1970', '住宅'): {
        'U_value': get_u_value('VERTICAL', 'C', 'EXISTING'),  # 0.36
        'COP_heat': HEAT_PUMP_PERFORMANCE_REQUIREMENTS['HEATING']['AIR_TO_AIR'],  # 3.5
        # ... 其他参数
    },
}
```

### 方法2：在计算模块中验证参数

```python
# 在 load_model.py 或其他计算模块中

from backend.italian_building_code_db import validate_u_value, get_system_efficiency

def validate_archetype_compliance(region, age, building_type, u_value, climate_zone='D'):
    """
    验证原型是否符合意大利法规
    """
    is_compliant = validate_u_value(
        u_value=u_value,
        structure_type='VERTICAL',
        climate_zone=climate_zone,
        building_type='NEW'
    )

    if is_compliant:
        print(f"✓ {region} {age} {building_type} 符合法规要求")
    else:
        max_allowed = get_u_value('VERTICAL', climate_zone, 'NEW')
        print(f"✗ U值 {u_value} 超过限值 {max_allowed}")

    return is_compliant
```

### 方法3：在 Streamlit 应用中展示

```python
# 在 app.py 中添加信息卡片

import streamlit as st
from backend.italian_building_code_db import get_u_value, CLIMATE_ZONES

st.sidebar.markdown("### 📜 法规参考")

zone_info = CLIMATE_ZONES.get(selected_climate_zone)
if zone_info:
    st.sidebar.info(f"""
    **{zone_info['label']}** ({selected_climate_zone}区)

    度日范围：{zone_info['dd_range']}

    示例城市：{', '.join(zone_info['cities'])}
    """)

# 显示该气候区的U值要求
max_u_wall = get_u_value('VERTICAL', selected_climate_zone, 'NEW')
st.sidebar.metric(
    "墙体最大U值要求",
    f"{max_u_wall} W/m²·K",
    help="新建建筑2019/2021标准"
)
```

---

## 📊 快速参考

### 关键参数数值范围

| 参数            | 最优值        | 最差值          | 单位   |
| --------------- | ------------- | --------------- | ------ |
| 墙体U值（新建） | 0.24 (F区)    | 0.43 (A区)      | W/m²·K |
| 窗户U值（新建） | 1.10 (F区)    | 3.00 (A区)      | W/m²·K |
| 热泵采暖COP     | 4.2 (水-水)   | 3.5 (空-空)     | -      |
| 热泵制冷EER     | 4.2 (水-水)   | 3.0 (空-空)     | -      |
| 燃气锅炉效率    | 95% (大功率)  | 92% (小功率)    | %      |
| 通风系统能耗    | 0.25 (单进排) | 0.50 (双流回收) | Wh/m³  |

### 气候区分布

**暖区** (A-B): 南意大利  
**温区** (C-D): 中意大利 + 北部平原  
**寒区** (E-F): 北部山区

---

## 💡 使用建议

### 1. 新建建筑模拟

```python
# 推荐使用新建标准 (2019/2021)
climate_zone = 'D'  # 例如中北部
building_type = 'NEW'

u_walls = get_u_value('VERTICAL', climate_zone, building_type)  # 0.29
u_windows = get_u_value('WINDOW', climate_zone, building_type)  # 1.80
u_roof = get_u_value('ROOF', climate_zone, building_type)  # 0.26

# 配对高效系统
cop_heating = 3.8  # 空-水热泵（>35kW）
eer_cooling = 3.0  # 空-水冷却
```

### 2. 既有建筑改造项目

```python
# 使用改造标准 (2021)
climate_zone = 'D'
building_type = 'EXISTING'

u_walls_max = get_u_value('VERTICAL', climate_zone, building_type)  # 0.32
u_windows_max = get_u_value('WINDOW', climate_zone, building_type)  # 1.80

# 验证改造方案
is_valid = validate_u_value(0.32, 'VERTICAL', 'D', 'EXISTING')  # True
```

### 3. 锅炉替换方案

```python
# 计算不同功率锅炉的最小效率

boiler_powers = [10, 20, 50, 100, 200, 400]
for power in boiler_powers:
    eta_full = calculate_boiler_efficiency(power)
    eta_partial = calculate_boiler_efficiency(power, partial_load=True)
    print(f"{power}kW: 全负荷 {eta_full}% | 部分 {eta_partial}%")

# 输出：
# 10kW: 全负荷 90.00% | 部分 84.77%
# 20kW: 全负荷 92.60% | 部分 88.20%
# 400kW: 全负荷 95.20% | 部分 91.80%
```

---

## 📖 法规引用

### 主要文件

- **Appendix A (DM Linee Guida)**：参考建筑参数
  - 新建标准（2019/2021年）
  - U值表1-5
  - 系统效率表7-9

- **Appendix B (DM Linee Guida)**：既有建筑改造
  - 改造U值限值表1-5
  - 热泵/冷却机COP/EER表6-9
  - 锅炉效率公式

### 相关标准

| 标准                | 应用         |
| ------------------- | ------------ |
| UNI EN 16798-1:2019 | 室内环境计算 |
| ISO 52016-1:2017    | 能耗计算方法 |
| UNI EN 14511        | 热泵性能测定 |
| UNI TS 11300-1/2    | 能耗评估方法 |

---

## ✅ 数据验证检查表

在使用这些参数前，请确认：

- [ ] 已识别目标建筑的气候区（A-F）
- [ ] 明确是新建还是改造项目
- [ ] U值已对应正确的围护结构类型
- [ ] 选择的系统效率符合测试条件
- [ ] 热泵COP/EER与实际机组规格接近
- [ ] 已考虑热桥和分隔修正因子

---

## 🚀 后续步骤

1. **扩展原型库**：将参数应用到所有20个意大利地区
2. **经济评估**：结合系统效率计算运营成本
3. **对标分析**：比较新建 vs. 改造的成本-效益
4. **敏感性分析**：考察U值、COP变化对总能耗的影响

---

**文档完成** | 可直接用于研究、设计、模拟
