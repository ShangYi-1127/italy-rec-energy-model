# 单栋建筑电能模拟演示系统

## 项目规范与技术文档

**版本**：v1.0  
**日期**：2026年5月14日  
**目标受众**：导师评审、研究验证

---

## 📋 目录

1. [项目概述](#项目概述)
2. [核心目标](#核心目标)
3. [系统架构](#系统架构)
4. [参数配置](#参数配置)
5. [功能模块](#功能模块)
6. [数据库结构](#数据库结构)
7. [计算公式体系](#计算公式体系)
8. [Streamlit框架](#streamlit框架)
9. [文件结构](#文件结构)
10. [部署指南](#部署指南)

---

## 项目概述

### 项目名称

**意大利建筑原型单栋电能模拟演示系统**  
_Italian Building Archetype Single-Unit Electrical Energy Simulation Demo_

### 项目背景

本系统用于展示**单栋建筑**在不同**地区**、**建造年代**、**建筑类型**条件下，根据数学公式计算得出的：

- 年度电能消耗量变化规律
- 光伏发电产出特性
- 电量余缺实时变化

### 创新点

✅ **教育性强**：每个计算步骤都展示对应的数学公式  
✅ **参数细致**：20个意大利地区 × 8个年代 × 4种类型 = 640种组合  
✅ **完全开源**：基于Streamlit云部署，支持公网访问  
✅ **互动式**：用户可自由组合参数，实时观察结果变化

---

## 核心目标

### 主要目标

1. **演示建筑能耗计算方法论**
   - 不同年代建筑的能效差异（U值从2.0到0.12 W/m²·K）
   - 不同类型建筑的使用特性（住宅vs办公的日内负荷曲线差异）
   - 地理位置对气象条件的影响（北部vs南部的供暖/制冷需求差异）

2. **展示光伏系统运行特性**
   - 季节性变化（夏季高峰vs冬季低谷）
   - 日内变化（晨间、正午、傍晚的发电曲线）
   - 地区差异（同样装机容量在不同纬度的发电效能）

3. **分析电量余缺动态**
   - 月度/日/小时尺度的能源平衡
   - 缺电/余电的时空分布
   - 建筑原型组合对总体覆盖率的影响

### 演示对象

- 👨‍🎓 研究生论文答辩
- 👨‍🏫 能源工程教学
- 🏛️ 建筑节能政策评估
- 🏘️ 能源社区规划工具

---

## 系统架构

### 三层架构

```
┌─────────────────────────────────────────────────┐
│         用户界面层 (Presentation Layer)          │
│  Streamlit Web应用 + 交互式参数配置              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         业务逻辑层 (Business Logic Layer)        │
│  ├─ 能耗计算模块 (Load Model)                   │
│  ├─ 光伏模块 (PV Model)                         │
│  ├─ 匹配算法 (Matching Algorithm)               │
│  └─ 数据查询 (Data Query)                       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         数据层 (Data Layer)                     │
│  ├─ archetype_matrix.csv (建筑参数库)           │
│  ├─ regions_italy.csv (地区库)                  │
│  ├─ schedules/ (时间表库)                       │
│  └─ weather/ (气象数据缓存)                     │
└─────────────────────────────────────────────────┘
```

### 信息流

```
用户选择参数
   ↓
[地区] [年代] [建筑类型]
   ↓
数据库查询
   ↓
获取建筑参数(U值、功率密度等) + 气象数据(GHI、温度)
   ↓
逐时计算 (8760小时)
   ↓
【TAB 1】E_load(t) 能耗曲线
【TAB 2】P_pv(t) 发电曲线
【TAB 3】E_diff(t) = P_pv(t) - E_load(t) 差值分析
   ↓
展示公式 + 曲线 + 统计表
```

---

## 参数配置

### 1. 地区选择（Region Selection）

**选项**：意大利20个地区

| 地区分组      | 包含地区                                             | 纬度    | 气候类型   | 特征                               |
| ------------- | ---------------------------------------------------- | ------- | ---------- | ---------------------------------- |
| **北部**      | 皮埃蒙特、伦巴第、威尼托、特伦蒂诺、弗留利           | 44-46°N | 大陆性气候 | HDD高，冬季长(>2500°C·d)，PV冬季弱 |
| **中部**      | 托斯卡纳、拉齐奥、翁布里亚、马尔凯、艾米利亚         | 41-43°N | 温和气候   | 过渡区，四季均衡                   |
| **南部+岛屿** | 坎帕尼亚、莫利塞、普利亚、卡拉布里亚、西西里、撒丁岛 | 37-40°N | 地中海气候 | CDD高，冬季短(<500°C·d)，PV夏季强  |

**对应影响**：

- ✓ 气象数据（PVGIS数据库中的坐标点）
- ✓ 供暖度日数(HDD)和制冷度日数(CDD)
- ✓ PV系统发电基准
- ✓ 建筑U值修正系数

### 2. 建筑建造年代（Building Age Period）

**选项**：8个时代跨度

| 年代 | 时间跨度  | 建造背景     | U值范围   | 窗户比 | COP系统 | 特征描述                     |
| ---- | --------- | ------------ | --------- | ------ | ------- | ---------------------------- |
| 1    | <1919     | 前现代       | 1.2-2.0   | 低     | 1.8-2.0 | 砌体厚重、通风无控制、极低效 |
| 2    | 1919-1945 | 战前         | 0.9-1.5   | 中     | 2.0-2.3 | 开始标准化施工、修复价值考量 |
| 3    | 1946-1960 | 战后重建     | 0.7-1.2   | 中     | 2.2-2.5 | 经济型建筑、混凝土应用       |
| 4    | 1961-1970 | 现代化初期   | 0.6-1.0   | 中高   | 2.3-2.6 | 标准化、HVAC开始普及         |
| 5    | 1971-1980 | 能源危机后   | 0.4-0.7   | 中     | 2.5-2.8 | 开始考虑隔热、重要分水岭     |
| 6    | 1981-1990 | 1980年代标准 | 0.3-0.6   | 中高   | 2.7-3.0 | 有隔热规范、相对高效         |
| 7    | 1991-2005 | 2000年代初   | 0.2-0.4   | 高     | 3.0-3.5 | 节能意识增强、接近现代       |
| 8    | >2005     | 新建筑       | 0.12-0.25 | 高     | 3.3-4.0 | 严格节能标准、高效热泵       |

**关键说明**：

- U值越低 = 隔热越好 = 能耗越低
- COP（制冷/制热性能系数）越高 = 系统效率越高

### 3. 建筑类型（Building Type）

**选项**：4种建筑功能

| 类型 | 英文名      | 典型使用时间 | 占用特点       | 功率特点       | 日内模式         |
| ---- | ----------- | ------------ | -------------- | -------------- | ---------------- |
| 住宅 | Residential | 全天(+周末)  | 夜间+清晨+傍晚 | 基础负荷低     | 双峰(晨间/夜间)  |
| 办公 | Office      | 工作日9-17点 | 集中白天       | 照明+电脑+空调 | 单峰(正午)       |
| 商业 | Commercial  | 扩展营业时间 | 分散全天       | 灯光+冷链+客流 | 平稳+傍晚峰      |
| 教育 | Educational | 学年+课时表  | 白天+季节性    | 大空间+高照度  | 工作日高，假期低 |

**占用时间表示例**：

```
住宅(Residential):
  工作日:   22-7点(夜间), 7-9点(早), 18-22点(晚)
  周末/假期: 全天活跃

办公(Office):
  工作日:   8-17点(集中)
  周末/假期: 基本无人

商业(Commercial):
  工作日:   9-21点(开店), 18-21点(高峰)
  周末:     9-21点(活跃)

教育(Educational):
  工作日/学期: 8-16点(课时)
  假期/周末:  无人使用
```

---

## 功能模块

### TAB 1: ⚡ 耗电量计算

**目标**：展示建筑电能消耗如何通过公式计算

#### 内容结构

**第一步 - 参数显示**

```
┌────────────────────────────────┐
│ 选中的建筑配置                  │
├────────────────────────────────┤
│ 地区：   [用户选择]             │
│ 年代：   [用户选择]             │
│ 类型：   [用户选择]             │
│ 面积：   100 m²（示例）         │
└────────────────────────────────┘
```

**第二步 - 建筑参数库查询**

```
┌────────────────────────────────────────┐
│ 从数据库获取的建筑特性参数             │
├────────────────────────────────────────┤
│ U值(传热系数):  0.35 W/(m²·K)         │
│ P_light(照明):   8 W/m²               │
│ P_appl(设备):    4 W/m²               │
│ ACH_occupied(占用): 1.2 h⁻¹           │
│ ACH_unoccupied(无人): 0.3 h⁻¹         │
│ COP_heating:     2.8                  │
│ COP_cooling:     3.2                  │
└────────────────────────────────────────┘
```

**第三步 - 逐时计算公式展示**

3.1 照明负荷

```
E_light,t = P_light × A_zone × S_light(t)
           = 8 W/m² × 100 m² × S_light(t)

其中 S_light(t) 是逐时占用系数(0-1)
```

3.2 设备负荷

```
E_appl,t = P_appl × A_zone × S_appl(t)
         = 4 W/m² × 100 m² × S_appl(t)
```

3.3 通风热损失（计入HVAC）

```
H_vent = 0.34 × n × V

P_vent,t = H_vent × (T_int - T_out) / 1000

其中：
- n = 换气次数(ACH, h⁻¹)，可由占用/无人时段时间表给出 n(t)
- V = 建筑内部净体积 (m³)
- 0.34 = ρ_air × c_p / 3600 的近似换算系数
```

3.4 通风设备电耗（独立于HVAC热损失）

```
P_vent(t) = f_fan × V_vent(t) × SFP × S_occ(t)
E_vent,t = P_vent(t) × Δt

其中：
- P_vent(t) = 通风设备瞬时功率 (kW)
- E_vent,t = 通风设备辅助电耗 (kWh)
- f_fan = 风机开关函数 (0/1)
- V_vent(t) = 送/排风量 (m³/s)
- SFP = Specific Fan Power，风机比功率 [kW/(m³/s)]
- S_occ(t) = 占用/运行系数 [0-1]
- Δt = 时间步长；按小时序列时通常取 1 h

条件触发逻辑：
- 旧住宅 / 普通公寓：通常无机械通风系统，E_vent,t = 0
- 现代 NZEB 住宅 / 别墅：若配置VMC系统，则按 SFP × 风量 × 运行小时计算
- 办公 / 学校 / 商业：通常需要计入机械通风电耗
```

3.5 供暖/制冷负荷（年值估算 + 逐时分配）

```
考虑到当前研究的数据结构更适合采用年度锚定 + 逐时分配的稳态方法，
本研究对HVAC部分采用度日数法（Degree Days Method）确定年需求，
再通过逐时权重把年度需求分解为8760小时序列。

年度供暖/制冷需求先由围护结构与气候统计量估算：

H_total = H_env + H_vent
  = (U_env · A_env) + (0.34 · n · V)

Q_H,annual = H_total · HDD · 24
Q_C,annual = H_total · CDD · 24

其中：
- H_env = 围护结构传热热损失系数 (W/K)
- H_vent = 通风换气热损失系数 (W/K)
- H_total = 建筑总热损失系数 (W/K)
- U_env = 围护结构平均传热系数 (W/m²·K)
- A_env = 围护结构总面积
- n = 换气次数(ACH, h⁻¹)
- V = 建筑内部净体积 (m³)
- HDD = 供暖度日数
- CDD = 制冷度日数
- 24 = 将度日数换算为逐时累计量的系数

随后，将年度总需求按逐小时权重分配：

w_H,h = max(0, θ_H - θ_out,h) · g_occ,h
w_C,h = max(0, θ_out,h - θ_C) · g_occ,h
ẇ_H,h = w_H,h / Σ w_H,h
ẇ_C,h = w_C,h / Σ w_C,h
Q_H,need,h = Q_H,annual · ẇ_H,h
Q_C,need,h = Q_C,annual · ẇ_C,h

其中：
- θ_H = 供暖基准温度 (20°C)
- θ_C = 制冷基准温度 (26°C)
- θ_out,h = 第h小时室外温度
- g_occ,h = 第h小时占用/运行因子
- w_H,h / w_C,h = 第h小时供暖/制冷原始权重
- ẇ_H,h / ẇ_C,h = 归一化后的供暖/制冷逐小时权重
- Q_H,annual / Q_C,annual = 年度供暖/制冷总需求

权重满足归一化条件：

Σ ẇ_H,h = 1,  Σ ẇ_C,h = 1

该方法保证年度总量与HDD/CDD口径一致，同时保留小时级波动特征。
```

3.6 转换为电能消耗

```
E_HVAC,h = Q_H,need,h / COP             (供暖)
E_HVAC,h = Q_C,need,h / EER             (制冷)

其中COP/EER可按原型固定值或温度修正值取用；
若采用简化法，则直接使用建筑原型表中的COP_heating / COP_cooling。
```

**第五步 - 总耗电量**

```
E_total,t = E_light,t + E_appl,t + E_vent,t + E_HVAC,t
```

**第六步 - 8760小时时间序列图**

```
图表类型：线性图 (plotly)

X轴：月份(1-12) 或 日期
Y轴：耗电功率(kW)

曲线特征：
- 冬季高峰(供暖需求)
- 夏季次高峰(制冷需求)
- 春秋谷值(过渡季)
- 日内波动(占用模式)
```

**第六步 - 统计表格**

```
┌─────────────────────────────────────┐
│ 年度能耗统计                         │
├─────────────────────────────────────┤
│ 年平均功率:     1,850 kW            │
│ 年总耗电量:     16,198 MWh          │
│ 月度最高:       2月 (2,500 kW)      │
│ 月度最低:       7月 (1,200 kW)      │
│ 峰谷比:         2.08                │
│ 照明占比:       8.5%                │
│ 设备占比:       12.3%               │
│ HVAC占比:       79.2%               │
└─────────────────────────────────────┘
```

---

### TAB 2: ☀️ 生产量计算

**目标**：展示光伏系统发电如何通过气象数据与PV模型计算

#### 内容结构

**第一步 - PV系统配置**

```
┌────────────────────────────────┐
│ PV系统参数(默认配置)           │
├────────────────────────────────┤
│ 装机容量(P_rated): 10 kW      │
│ 倾角(Tilt): 35°                │
│ 方位角(Azimuth): 0° (正南)    │
│ 面积: 50 m²                    │
│ 技术: 单晶硅 (η_STC = 19%)     │
└────────────────────────────────┘
```

**第二步 - 气象数据**

```
数据来源：PVGIS (欧洲光伏地理信息系统)

┌────────────────────────────────────────┐
│ [选定地区] 的气象特性                  │
├────────────────────────────────────────┤
│ GHI(全球水平辐照度):                  │
│   - 北部平均: 800 W/m²/天             │
│   - 中部平均: 900 W/m²/天             │
│   - 南部平均: 1000 W/m²/天            │
│                                       │
│ 环境温度(T_amb):                      │
│   - 冬季: 0-5°C                      │
│   - 夏季: 25-35°C                    │
│                                       │
│ 空气质量(AM): 1.5 (相对标准大气)     │
└────────────────────────────────────────┘
```

**第三步 - PV模型公式(Pvlib)**

3.1 入射辐照度计算

```
POA_irr(t) = GHI(t) × cos(θ_inc) + Diffuse
           = [考虑倾角和方位角的调整]
```

3.2 电池温度

```
T_cell(t) = T_amb(t) + (NOCT - 20) × POA_irr(t) / 800
其中 NOCT(额定运行电池温度) ≈ 45°C

例：T_amb = 25°C, POA = 800 W/m²
    T_cell = 25 + (45-20) × 800/800 = 50°C
```

3.3 温度修正系数

```
η_temp(T) = 1 + γ × (T_cell - T_ref)
其中 γ ≈ -0.005 /°C (硅电池)

例：T_cell = 50°C (T_ref = 25°C)
    η_temp = 1 + (-0.005) × (50-25) = 1 - 0.125 = 0.875
    → 温度升高使效率下降12.5%
```

3.4 积尘损失

```
η_soiling ≈ 0.97 (年平均)
→ 表面污垢造成约3%的功率损失
```

3.5 逆变器效率

```
η_inverter ≈ 0.96
```

3.6 最终发电功率

```
P_pv(t) = P_rated × η_temp(t) × η_soiling × η_inverter
          × [POA_irr(t) / 1000]

完整示例(晨间8:00):
  POA_irr = 200 W/m²
  T_cell = 30°C
  η_temp = 1 + (-0.005)×(30-25) = 0.975
  η_soiling = 0.97
  η_inverter = 0.96

  P_pv = 10 kW × 0.975 × 0.97 × 0.96 × (200/1000)
       = 10 × 0.975 × 0.97 × 0.96 × 0.2
       = 1.80 kW
```

**第四步 - 日内发电曲线**

```
典型夏日(6月21日)的发电曲线：

发电功率(kW)
▲ 10  ┌────────
│     │   ╱╲
│ 5   │  ╱  ╲
│     │╱      ╲
│ 0   └────────▶ 时刻(h)
      6  12  18

特征：单峰，正午最高，日出/日落为0
```

**第五步 - 8760小时全年曲线**

```
图表类型：线性图 + 阴影区(Streamlit plotly)

X轴：月份(1-12)
Y轴：发电功率(kW)

曲线特征：
- 夏季高(6-8月，高GHI + 高日出角)
- 冬季低(11-2月，低GHI + 低日出角)
- 春秋过渡
```

**第六步 - 统计表格**

```
┌──────────────────────────────────────┐
│ 年度发电统计                         │
├──────────────────────────────────────┤
│ 年平均功率:      5.2 kW              │
│ 年总发电量:      12,408 MWh          │
│ 月度高峰:        6月 (8.5 kW)        │
│ 月度低谷:        12月 (2.1 kW)       │
│ 峰谷比:          4.05                │
│ 系统效率:        14.5%               │
│ 利用小时数:      1,241 h/年          │
└──────────────────────────────────────┘
```

---

### TAB 3: 📊 差值分析

**目标**：展示电量余缺的动态变化

#### 内容结构

**第一步 - 差值定义**

```
E_diff,t = P_pv,t - E_load,t

若 E_diff > 0: 余电(可用于储存/出售/邻居共享)
若 E_diff < 0: 缺电(需要从网购买)
```

**第二步 - 双Y轴对比曲线**

```
图表类型：Plotly dual-axis chart

左Y轴(蓝色): 耗电量(kW)
右Y轴(黄色): 发电量(kW)
阴影区(绿色): E_diff > 0的时段

观察：
- 冬季: 发电远低于耗电 (缺电严重)
- 夏日正午: 可能发电>耗电 (有余)
- 夜间: 发电=0，必需耗电 (100%缺失)
```

**第三步 - 月度汇总表**

```
┌────────────────────────────────────────────────────┐
│ 月份│ 耗电  │ 发电  │ 余量  │ 缺失  │ 覆盖率    │
│    │(MWh) │(MWh) │(MWh) │(MWh) │(%)       │
├────┼──────┼──────┼──────┼──────┼──────────┤
│ 1月│ 1580 │ 1020 │  0   │ 560  │ 64.6%    │
│ 2月│ 1420 │ 1150 │  0   │ 270  │ 81.0%    │
│ 3月│ 1320 │ 1450 │ 130  │  0   │ 109.8%   │
│ 4月│ 1100 │ 1520 │ 420  │  0   │ 138.2%   │
│ 5月│ 1050 │ 1680 │ 630  │  0   │ 160.0%   │
│ 6月│ 1200 │ 1380 │ 180  │  0   │ 115.0%   │
│ ... (续) ...                                   │
│12月│ 1650 │  800 │  0   │ 850  │ 48.5%    │
├────┼──────┼──────┼──────┼──────┼──────────┤
│全年│16198 │12408 │ 2180 │ 6000 │ 76.5%    │
└────────────────────────────────────────────────────┘
```

**第四步 - 关键指标卡片(Streamlit metrics)**

```
┌──────────────────┬──────────────────┬──────────────────┐
│ 年总缺电量       │ 年总余电量       │ 年度覆盖率       │
│ 6,000 MWh        │ 2,180 MWh        │ 76.5%            │
├──────────────────┴──────────────────┴──────────────────┤
│ 峰谷功率差：1,300 kW                                   │
│ 最大缺电月：1月 (564 MWh)                             │
│ 最大余电月：5月 (630 MWh)                             │
└──────────────────────────────────────────────────────┘
```

**第五步 - 季节分类分析**

```
图表类型：堆积柱状图或分类总结

冬季(11-2月):
  ├─ 耗电: 6,280 MWh (38.8%)
  ├─ 发电: 3,970 MWh (32.0%)
  ├─ 缺失: 2,310 MWh ⚠️ [关键挑战]
  └─ 覆盖率: 63.2%

过渡季(3,4,9,10月):
  ├─ 耗电: 4,490 MWh (27.7%)
  ├─ 发电: 4,820 MWh (38.8%)
  ├─ 余电: +330 MWh [基本平衡]
  └─ 覆盖率: 107.3%

夏季(5-8月):
  ├─ 耗电: 4,800 MWh (29.6%)
  ├─ 发电: 3,618 MWh (29.2%)
  ├─ 余电: +360 MWh [可出售/储存]
  └─ 覆盖率: 75.4%
```

**第六步 - 实时逐时数据表**

```
st.dataframe() - 可搜索、可排序的表格

列：[日期时间, 耗电(kW), 发电(kW), 差值(kW), 状态(余/缺)]
行：可选显示日/周/月的代表小时

提供下载按钮：导出为CSV
```

---

## 数据库结构

### 1. regions_italy.csv

**用途**：地区基本信息与PVGIS数据点映射

```csv
Region_Code,Region_Name_IT,Region_Name_EN,Latitude,Longitude,Zone_Climate,PVGIS_Point_ID,HDD_reference,CDD_reference
01,皮埃蒙特,Piemonte,45.2,7.7,Alpine,piemonte_2024,3200,400
02,瓦莱达奥斯塔,Valle d'Aosta,45.7,7.3,Alpine,aosta_2024,3400,350
...
16,西西里,Sicilia,37.6,14.0,Mediterranean,sicilia_2024,800,2200
17,撒丁岛,Sardegna,40.0,9.1,Mediterranean,sardegna_2024,900,2000
```

**关键字段**：

- `Latitude, Longitude`: 用于PVGIS API调用
- `PVGIS_Point_ID`: 对应weather/\*.csv文件的存储标识
- `HDD_reference, CDD_reference`: 参考度日数，用于能耗验证

### 2. archetype_matrix.csv

**用途**：建筑原型库，存储640种组合的参数

```csv
Region,Age_Period,BuildingType,U_value,P_light,P_appl,ACH_occ,ACH_unocc,COP_heat,COP_cool,Window_Ratio,Thermal_Mass,Infiltration_Rate
皮埃蒙特,<1919,住宅,1.8,8,3,0.8,0.2,1.9,2.1,0.25,High,0.15
皮埃蒙特,<1919,办公,1.9,12,6,1.5,0.3,1.8,2.0,0.35,Medium,0.18
...
撒丁岛,>2005,教育,0.15,10,4,2.0,0.4,3.8,4.2,0.50,Low,0.05
```

**关键参数解释**：

- `U_value`: 建筑传热系数 (W/m²·K)
- `P_light`: 照明功率密度 (W/m²)
- `P_appl`: 设备功率密度 (W/m²)
- `ACH_occ/unocc`: 占用/无人时的换气次数 (h⁻¹)
- `COP_heat/cool`: 供暖/制冷系统性能系数
- `Window_Ratio`: 窗墙面积比
- `Thermal_Mass`: 热容性(High/Medium/Low) - 影响温度变化速率
- `Infiltration_Rate`: 渗漏率 - 影响无控制通风

### 3. schedules/\*.csv

**用途**：建筑类型的逐时占用与功能系数

```csv
Hour,Occupancy_Residential_WD,Appliance_Residential_WD,Lighting_Residential_WD,Occupancy_Residential_WE,...
0,0.0,0.2,0.0,...
1,0.0,0.2,0.0,...
...
7,0.8,0.4,0.6,...
8,0.1,0.3,0.3,...
...
18,0.9,0.7,0.8,...
19,1.0,0.8,0.9,...
...
```

**文件清单**：

```
├── schedule_residential_weekday.csv
├── schedule_residential_weekend.csv
├── schedule_office_weekday.csv
├── schedule_office_weekend.csv
├── schedule_commercial_weekday.csv
├── schedule_commercial_weekend.csv
├── schedule_educational_schoolday.csv
└── schedule_educational_holiday.csv
```

**系数定义**：

- 0.0 = 完全无人/无负荷
- 1.0 = 满负荷/完全占用
- 0.5 = 中等使用

### 4. weather/\*.csv

**用途**：PVGIS提供的逐时气象数据(缓存)

```csv
Timestamp,GHI,Diffuse,T_amb,RH,Wind_speed
2024-01-01 00:00,0,0,2.3,75,3.2
2024-01-01 01:00,0,0,2.1,76,3.1
...
2024-01-01 12:00,280,120,8.5,65,2.8
...
```

**关键变量**：

- `GHI`: 全球水平辐照度 (W/m²)
- `Diffuse`: 散射辐照度 (W/m²)
- `T_amb`: 环境温度 (°C)
- `RH`: 相对湿度 (%)
- `Wind_speed`: 风速 (m/s)

**采集频率**：每小时，全年8760条

---

## 计算公式体系

### 耗电量计算模块

#### 1. 照明负荷

```
E_light,t = P_light × A_zone × S_light(t)

其中：
- P_light: 照明功率密度 [W/m²] (从archetype_matrix读取)
- A_zone: 建筑面积 [m²] (用户输入或示例100m²)
- S_light(t): 逐时照明系数 [0-1] (从schedules/*.csv读取)

例：夜间(0-6时)
    S_light = 0.0 (无人或自然光充足)
    E_light = 8 W/m² × 100 m² × 0 = 0 kW

例：工作时间(9-17时)
    S_light = 0.9 (灯光开启)
    E_light = 8 W/m² × 100 m² × 0.9 = 0.72 kW
```

#### 2. 设备/插座负荷

```
E_appl,t = P_appl × A_zone × S_appl(t)

其中：
- P_appl: 设备功率密度 [W/m²]
- S_appl(t): 逐时设备系数 [0-1]

建筑类型差异：
- 住宅: P_appl ≈ 3-4 W/m² (低)，S_appl夜间也有(电冰箱等)
- 办公: P_appl ≈ 6-8 W/m² (中)，S_appl仅工作时间
- 商业: P_appl ≈ 8-12 W/m² (高)，S_appl扩展营业时间
- 教育: P_appl ≈ 5-7 W/m² (中)，S_appl仅课时
```

#### 3. 通风负荷

```
H_total = H_env + H_vent
    = (U_eff × A_env) + (0.34 × n × V)

P_vent,t = H_vent × (T_int - T_out(t)) / 1000

其中：
- H_env = 围护结构传热系数 (W/K)
- H_vent = 通风换气热损失系数 (W/K)
- U_eff = 建筑有效传热系数 (W/m²·K)
- A_env = 围护结构总面积 (m²)
- 0.34 = ρ_air × c_p / 3600 的近似换算系数
- n = 换气次数(ACH, h⁻¹)，可由占用/无人时段的时间表给出 n(t)
- V = 建筑内部净体积 (m³)，可写作 V = A_zone × h_ceiling
- T_int = 室内设定温度 (21°C冬季，26°C夏季)
- T_out(t) = 环境温度(从weather/*.csv)

例：冬季清晨，占用时段
  U_eff × A_env = 180 W/K
  n = 1.2 h⁻¹，V = 300 m³
  H_vent = 0.34 × 1.2 × 300 = 122.4 W/K
  H_total = 180 + 122.4 = 302.4 W/K

    T_int = 21°C，T_out = 0°C
  P_vent = 122.4 × 21 / 1000
       = 2.57 kW
```

#### 4. 供暖/制冷负荷

**建筑热平衡方程(简化)**：

```
室内温度变化率：
ρ × c_p × V_zone × dT_int/dt =
  - H_env × (T_int - T_out)            [围护结构传热损失]
  - H_vent × (T_int - T_out)           [通风换气损失]
    + Q_light                             [照明内得热]
    + Q_appl                              [设备内得热]
    + Q_occupant                          [人员代谢热]
    + Q_sol                               [太阳得热]
    + Q_sys                               [HVAC供热/冷]
```

**年度锚定 + 逐时分配**：

```
H_total = H_env + H_vent
  = (U_env × A_env) + (0.34 × n × V)

Q_H,annual = H_total × HDD × 24
Q_C,annual = H_total × CDD × 24

w_H,h = max(0, θ_H - θ_out,h) × g_occ,h
w_C,h = max(0, θ_out,h - θ_C) × g_occ,h
ẇ_H,h = w_H,h / Σ w_H,h
ẇ_C,h = w_C,h / Σ w_C,h
Q_H,need,h = Q_H,annual × ẇ_H,h
Q_C,need,h = Q_C,annual × ẇ_C,h

E_HVAC,h = Q_H,need,h / COP        [供暖]
E_HVAC,h = Q_C,need,h / EER        [制冷]
```

其中：

- H_total = 建筑总热损失系数（围护结构 + 通风）
- U_env = 围护结构平均传热系数
- A_env = 围护结构总面积
- n = 换气次数(ACH)
- V = 建筑净体积
- Q_H,annual / Q_C,annual = 年度供暖/制冷总需求
- θ_H = 供暖基准温度
- θ_C = 制冷基准温度
- g_occ,h = 占用/运行因子
- COP/EER = 设备能效参数

该方法的核心是先保证全年总量由度日数锚定，再把总量按气象与使用行为共同决定的权重拆分到小时尺度。

#### 5. 通风设备电耗

```
P_vent(t) = f_fan × V_vent(t) × SFP × S_occ(t)
E_vent,t = P_vent(t) × Δt

其中：
- P_vent(t) = 通风设备瞬时功率 (kW)
- E_vent,t = 通风设备辅助电耗 (kWh)
- f_fan = 风机开关函数 (0/1)
- V_vent(t) = 送/排风量 (m³/s)
- SFP = Specific Fan Power，风机比功率 [kW/(m³/s)]
- S_occ(t) = 占用/运行系数 [0-1]
- Δt = 时间步长；按小时序列时通常取 1 h

条件触发逻辑：
- 旧住宅 / 普通公寓：通常无机械通风系统，E_vent,t = 0
- 现代 NZEB 住宅 / 别墅：若配置VMC系统，则按 SFP × 风量 × 运行小时计算
- 办公 / 学校 / 商业：通常需要计入机械通风电耗
```

#### 6. 总耗电量

```
E_total,t = E_light,t + E_appl,t + E_vent,t + E_HVAC,t
```

---

### 发电量计算模块(Pvlib)

#### 1. 位置和时间信息

```python
location = {
    'latitude': lat,        # 从regions_italy.csv读取
    'longitude': lon,
    'altitude': elevation,  # 数据库中可选
    'tz': 'Europe/Rome'     # 意大利时区
}

times = pd.date_range('2024-01-01', '2024-12-31', freq='h', tz='Europe/Rome')
```

#### 2. 清空指数和绝对相对质量

```
Clearness Index (Kt): 地面接收的太阳辐射与TOA辐射的比值
Absolute Air Mass (AM): 大气厚度相对于标准大气的倍数
  AM = 1.0 (太阳在天顶)
  AM = 1.5 (标准测试条件STC)
  AM > 3 (日出/日落附近)
```

#### 3. 入射角度和平面入射辐照度

```
太阳位置计算：
- 高度角(Altitude): 太阳与地平线的夹角
- 方位角(Azimuth): 太阳在指南针上的方向

PV组件位置：
- 倾角(Tilt): PV板与水平面的夹角(默认35°)
- 方位角(Azimuth): PV板的朝向(0°=正南，-90°=正东)

入射角度(Incidence Angle):
  cos(θ_inc) = sin(altitude) × cos(tilt)
               + cos(altitude) × sin(tilt) × cos(azimuth - sun_azimuth)

平面入射辐照度(POA):
  POA = GHI × cos(θ_inc) + Diffuse_factor
```

#### 4. PV电池温度

```
NOCT模型(Nominal Operating Cell Temperature):

T_cell(t) = T_amb(t) + (NOCT - 20) × POA(t) / 800

其中NOCT是PV电池在标准条件(1000 W/m², 20°C环境)下的运行温度
对于晶硅电池，NOCT ≈ 43-47°C

例：
  T_amb = 25°C (夏日正午)
  POA = 900 W/m² (清晰晴天)
  NOCT = 45°C

  T_cell = 25 + (45-20) × 900/800
         = 25 + 25 × 1.125
         = 25 + 28.1 = 53.1°C
```

#### 5. 光谱影响

```
相对光谱辐照度(Relative Spectral Irradiance):

Air Mass Index (AM) 影响太阳光谱分布
- AM小(中午): 蓝光多，对Si电池更有利
- AM大(日出/日落): 红光多，效率下降

修正系数：
  f_airmass ≈ 1.05 (AM=1.5) 到 0.85 (AM>4)
```

#### 6. 温度系数

```
相对效率：
  η(T) = η_ref × [1 + γ × (T_cell - T_ref)]

其中：
- γ = 温度系数 ≈ -0.005 /°C (晶硅电池)
- T_ref = 25°C (标准测试温度STC)

例：
  η_ref = 19.0% (STC额定效率)
  T_cell = 50°C (实际运行)
  γ = -0.005 /°C

  η(50°C) = 0.19 × [1 + (-0.005) × (50-25)]
          = 0.19 × [1 - 0.125]
          = 0.19 × 0.875
          = 0.1663 = 16.63%
          → 相比STC下降2.37%
```

#### 7. 积尘和污垢损失

```
积尘因子(Soiling Factor):
  f_soiling ≈ 0.95-0.98

影响因素：
- 地理位置和气候(灰尘/污染程度)
- 降雨频率(自然清洁)
- 倾角(>30°自清洁能力好)
- 维护频率

意大利平均：
  f_soiling ≈ 0.97 (年平均约3%损失)
```

#### 8. 最终输出功率

```
完整PV模型：

P_pv,t = P_rated × η_temp(T_cell(t)) × f_soiling × f_inverter
         × [POA(t) / 1000]

步骤示例(某时刻t)：

  输入：
  - GHI(t) = 600 W/m²
  - T_amb(t) = 20°C
  - η_ref = 19%
  - 倾角=35°, 方位=0°
  - P_rated = 10 kW
  - f_soiling = 0.97
  - f_inverter = 0.96

  计算：
  1. POA = GHI × cos(θ_inc) ≈ 600 × 0.85 = 510 W/m²

  2. T_cell = 20 + (45-20) × 510/800
            = 20 + 25 × 0.6375
            = 20 + 15.9 = 35.9°C

  3. η_temp = 1 + (-0.005)×(35.9-25)
            = 1 - 0.055 = 0.945

  4. P_pv = 10 × 0.945 × 0.97 × 0.96 × (510/1000)
          = 10 × 0.945 × 0.97 × 0.96 × 0.51
          = 4.55 kW
```

---

### 能源匹配模块

#### 差值计算

```
E_diff,t = P_pv,t - E_load,t

分类统计：
  E_surplus,annual = Σ max(0, E_diff,t)    [全年余电]
  E_deficit,annual = Σ |min(0, E_diff,t)|  [全年缺电]

  覆盖率(%) = Σ min(P_pv,t, E_load,t) / Σ E_load,t × 100%
```

---

## Streamlit 框架

### 核心代码结构

```python
# app.py - 主入口

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============ 页面配置 ============
st.set_page_config(
    page_title="建筑原型电能模拟演示",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ 侧边栏参数输入 ============
st.sidebar.header("⚙️ 参数配置")

# 加载数据
regions_df = pd.read_csv("data/regions_italy.csv")
region_list = regions_df['Region_Name_IT'].tolist()

# 地区选择
selected_region = st.sidebar.selectbox(
    "📍 选择意大利地区",
    region_list,
    index=0,
    help="选择建筑所在地区以获取对应的气象数据"
)

# 年代选择
age_periods = [
    "<1919", "1919-1945", "1946-1960", "1961-1970",
    "1971-1980", "1981-1990", "1991-2005", ">2005"
]
selected_age = st.sidebar.selectbox(
    "📅 选择建筑建造年代",
    age_periods,
    index=3,
    help="年代越新，建筑能效越高"
)

# 类型选择
building_types = ["住宅", "办公", "商业", "教育"]
selected_type = st.sidebar.selectbox(
    "🏢 选择建筑类型",
    building_types,
    index=0,
    help="不同类型的使用时间表和功率特性不同"
)

# 建筑面积(可选自定义)
building_area = st.sidebar.slider(
    "📐 建筑面积 (m²)",
    min_value=50,
    max_value=500,
    value=100,
    step=10
)

# 计算按钮
calculate_btn = st.sidebar.button(
    "🔄 更新计算",
    key="calc_button",
    use_container_width=True
)

# ============ 主内容区 ============
st.title("🌞 意大利建筑原型电能模拟演示系统")
st.markdown("**教育性工具**：展示不同建筑参数对能耗与发电的影响")

# 当前选择显示
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📍 地区", selected_region)
with col2:
    st.metric("📅 年代", selected_age)
with col3:
    st.metric("🏢 类型", selected_type)
with col4:
    st.metric("📐 面积", f"{building_area} m²")

st.divider()

# ============ 数据查询和计算 ============
@st.cache_data
def get_archetype_params(region, age, btype):
    """查询建筑原型参数"""
    df = pd.read_csv("data/archetype_matrix.csv")
    params = df[
        (df['Region'] == region) &
        (df['Age_Period'] == age) &
        (df['BuildingType'] == btype)
    ].iloc[0]
    return params.to_dict()

@st.cache_data
def get_weather_data(region):
    """加载气象数据"""
    # 首先查询地区坐标
    regions = pd.read_csv("data/regions_italy.csv")
    point_id = regions[regions['Region_Name_IT']==region]['PVGIS_Point_ID'].values[0]

    weather_file = f"data/weather/{point_id}.csv"
    df = pd.read_csv(weather_file)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

@st.cache_data
def get_schedule(btype, day_type):
    """加载使用时间表"""
    schedule_file = f"data/schedules/schedule_{btype.lower()}_{day_type}.csv"
    df = pd.read_csv(schedule_file)
    return df

# 如果点击计算按钮，执行计算
if calculate_btn:
    with st.spinner("正在加载数据..."):
        # 获取参数
        archetype = get_archetype_params(selected_region, selected_age, selected_type)
        weather = get_weather_data(selected_region)

        st.success("✅ 数据加载完成！开始计算...")

# ============ TAB 页面 ============
tab1, tab2, tab3 = st.tabs(["⚡ 耗电量计算", "☀️ 生产量计算", "📊 差值分析"])

with tab1:
    st.header("⚡ 建筑耗电量计算")
    # ... 后续实现

with tab2:
    st.header("☀️ 光伏生产量计算")
    # ... 后续实现

with tab3:
    st.header("📊 电量余缺分析")
    # ... 后续实现
```

---

## 文件结构

```
Thesis_Agent/single building electrical energy sitimulation-demo/
│
├── README.md                              # 项目说明与快速开始
├── PROJECT_SPECIFICATION.md              # 本文档
│
├── app.py                                # Streamlit主应用
├── requirements.txt                      # Python依赖
│
├── data/
│   ├── regions_italy.csv                # 20个意大利地区信息表
│   ├── archetype_matrix.csv             # 640×建筑参数矩阵
│   │
│   ├── schedules/
│   │   ├── schedule_residential_weekday.csv
│   │   ├── schedule_residential_weekend.csv
│   │   ├── schedule_office_weekday.csv
│   │   ├── schedule_office_weekend.csv
│   │   ├── schedule_commercial_weekday.csv
│   │   ├── schedule_commercial_weekend.csv
│   │   ├── schedule_educational_schoolday.csv
│   │   └── schedule_educational_holiday.csv
│   │
│   └── weather/
│       ├── piemonte_2024.csv            # 20个地区的气象数据
│       ├── lazio_2024.csv
│       ├── sicilia_2024.csv
│       └── ... (共20个)
│
├── backend/
│   ├── __init__.py
│   ├── load_model.py                   # 能耗计算模块
│   ├── pv_model.py                     # 光伏计算模块(Pvlib)
│   ├── data_loader.py                  # 数据库查询函数
│   └── utils.py                        # 工具函数
│
├── assets/
│   └── logo.png                         # 项目标志(可选)
│
└── tests/
    ├── test_load_model.py              # 单元测试
    ├── test_pv_model.py
    └── test_data_loader.py

```

---

## 部署指南

### 本地运行

```

其中：
- H_env = 围护结构传热热损失系数
- H_vent = 通风换气热损失系数
- H_total = 建筑总热损失系数（围护结构 + 通风）
- U_env = 围护结构平均传热系数
- A_env = 围护结构总面积
- n = 换气次数(ACH)
- V = 建筑净体积
- θ_H = 供暖基准温度
- θ_C = 制冷基准温度
- g_occ,h = 占用/运行因子
- COP/EER = 设备能效参数
# 1. 克隆仓库或下载文件
# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
streamlit run app.py

# 5. 本地访问
# 浏览器打开：http://localhost:8501
```

### Streamlit Cloud 部署

```bash
# 1. 推送到GitHub
git init
git add .
git commit -m "Initial commit"
git push origin main

# 2. 访问 https://share.streamlit.io
# 连接GitHub账号并选择仓库
# 设置入口文件为 app.py

# 3. 点击"Deploy"
# 等待部署完成，获得公网URL
```

**部署后的URL格式**：

```
https://[your-username]-[repo-name]-[random-id].streamlit.app
```

---

## 关键依赖

```txt
streamlit>=1.30.0
pandas>=1.5.0
numpy>=1.23.0
plotly>=5.13.0
pvlib>=0.10.0
scikit-learn>=1.2.0
```

---

## 使用示例

### 场景 1：教师讲授建筑能耗基础

```
讲师操作：
1. 选择"北部" → "1950年代" → "住宅"
2. 点击"更新计算"
3. TAB1中展示U值为0.85 W/m²·K的战后住宅的能耗特性
4. 对比"新建(>2005)" → TAB1显示U值降至0.18 W/m²·K，
   年耗电量从16,198 MWh降至4,850 MWh
5. 讲解能效改进的重要性

学生理解：
✓ 建筑年代对能耗的决定性影响
✓ 隔热(U值)的作用机制
✓ 公式-参数-结果的因果关系
```

### 场景 2：设计师评估节能潜力

```
设计师需求：
评估在撒丁岛加装10 kW光伏系统，对既有商业建筑能源平衡的影响

操作流程：
1. 选择"撒丁岛" → "1980年代" → "商业"
2. TAB1观察冬季缺电情况(撒丁岛冬季供暖需求低)
3. TAB2查看夏季发电高峰(南部地中海气候优势)
4. TAB3分析全年电量盈余
5. 结论：该建筑夏季可出售电量，冬季需网购补充

决策支持：
✓ 该项目经济可行性较好
✓ 预计年度覆盖率约75-80%
```

---

## 常见问题 (FAQ)

**Q: 为什么冬季耗电量那么高？**
A: 北方冬季寒冷(0°C以下)，供暖需求占总耗电的70-80%。供暖需热量与室内外温差成正比：Q = U×A×ΔT，所以冬季能耗是夏季的2-3倍。

**Q: 为什么夏季发电也降低了？**
A: 不对！夏季发电是全年最高的。但夏季制冷也消耗电力，所以净余电量(覆盖率)仍低于冬季。

**Q: 如何改善年度覆盖率？**
A:

- 增加PV装机容量
- 安装储能电池(缓冲冬季缺电)
- 改善建筑保温(减少冬季耗电)
- 与邻居组建能源社区(分享发电)

---

## 技术支持与反馈

- **作者**：[您的名字]
- **机构**：[学校/研究机构]
- **邮件**：[contact@example.com]
- **GitHub Issues**：[项目GitHub链接]

---

## 许可证

本项目采用 **Creative Commons Attribution 4.0** 开源许可，欢迎学术引用与教学使用。

---

**文档版本**：1.0  
**最后更新**：2026年5月14日  
**维护状态**：✅ 持续更新
