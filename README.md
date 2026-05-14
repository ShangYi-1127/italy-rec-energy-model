# 🌞 意大利建筑原型电能模拟演示系统

**Italian Building Archetype Single-Unit Electrical Energy Simulation Demo**

---

## 📋 项目概述

一个**教育性交互式工具**，通过选择建筑参数(地区、年代、类型)，展示：

- ⚡ **建筑耗电量计算** - 逐时能耗分解与公式推导
- ☀️ **光伏生产量计算** - 基于气象数据的发电模型
- 📊 **电量匹配分析** - 供需关系动态变化

## 🎯 核心特性

✅ **完整公式展示** - 每个计算步骤都有对应的数学公式  
✅ **细致参数库** - 20个意大利地区 × 8个建筑年代 × 4种类型 = 640种组合  
✅ **交互式界面** - Streamlit + Plotly实时可视化  
✅ **开源部署** - 支持本地运行和Streamlit Cloud云部署

---

## 🚀 快速开始

### 本地运行

#### 1. 环境准备

```bash
# 克隆或进入项目目录
cd single\ building\ electrical\ energy\ sitimulation-demo

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 运行应用

```bash
streamlit run app.py
```

#### 4. 访问应用

浏览器打开：`http://localhost:8501`

### Streamlit Cloud 云部署

1. 将项目推送到GitHub
2. 访问 https://share.streamlit.io
3. 连接GitHub账号，选择仓库
4. 设置入口文件为 `app.py`
5. 点击"Deploy"

---

## 📁 项目结构

```
.
├── app.py                           # Streamlit主应用
├── requirements.txt                 # Python依赖
├── README.md                        # 本文件
│
├── backend/                         # 后端模块
│   ├── __init__.py
│   ├── load_model.py               # 建筑负荷计算模块
│   ├── pv_model.py                 # PV发电计算模块
│   ├── matching_algorithm.py       # 能源匹配算法
│   ├── economic_model.py           # 经济评估模块(CACI/CACV/RID)
│   └── archetype_data.py           # 建筑原型库
│
├── data/                            # 数据目录
│   ├── archetypes.csv              # 建筑参数矩阵(可扩展)
│   ├── regions.csv                 # 意大利地区信息
│   ├── schedules/                  # 使用时间表
│   │   ├── schedule_residential_weekday.csv
│   │   ├── schedule_residential_weekend.csv
│   │   ├── schedule_office_weekday.csv
│   │   ├── schedule_office_weekend.csv
│   │   ├── schedule_commercial_weekday.csv
│   │   ├── schedule_commercial_weekend.csv
│   │   ├── schedule_educational_schoolday.csv
│   │   └── schedule_educational_holiday.csv
│   │
│   └── weather/                    # 气象数据缓存(可选)
│       ├── piemonte_2024.csv
│       ├── lazio_2024.csv
│       ├── sicilia_2024.csv
│       └── ... (20个地区)
│
└── tests/                           # 单元测试(可选)
    ├── test_load_model.py
    ├── test_pv_model.py
    └── test_matching.py
```

---

## 🔧 核心模块说明

### 1. LoadModel (建筑负荷计算)

**公式**：

```
E_light,t = P_light × A × S_light(t)
E_appl,t = P_appl × A × S_appl(t)
P_vent,t = ρ × c_p × V_vent × ΔT / 3600
E_hvac,t = Q_demand / COP(T)
E_total,t = E_light + E_appl + E_vent + E_hvac
```

**关键参数**：

- U值：建筑传热系数 [W/(m²·K)]
- P_light, P_appl：功率密度 [W/m²]
- COP：系统性能系数(随温度变化)

### 2. PVModel (光伏发电)

**核心算法(Pvlib)**：

```
T_cell = T_amb + (NOCT - 20) × POA / 800
η_temp = 1 + γ × (T_cell - 25)  ; γ = -0.005/°C
P_pv = P_rated × η_temp × η_soiling × η_inverter × (POA / 1000)
```

**特性**：

- 温度修正系数
- 积尘损失建模
- 逆变器效率

### 3. MatchingAlgorithm (能源匹配)

**核心指标**：

```
E_diff,t = P_pv(t) - E_load(t)
覆盖率 = min(P_pv, E_load).sum() / E_load.sum()
```

### 4. EconomicModel (经济评估)

**意大利REC补贴**：

- **CACI**：共享电量补贴 ~80-120 €/MWh
- **CACV**：网费返还 ~30 €/MWh
- **RID**：电网出售 (市场价格)

---

## 📊 参数配置

### 地区(20个)

| 北部     | 中部     | 南部+岛屿 |
| -------- | -------- | --------- |
| 皮埃蒙特 | 托斯卡纳 | 坎帕尼亚  |
| 伦巴第   | 拉齐奥   | 普利亚    |
| 威尼托   | 翁布里亚 | 西西里    |
| ...      | ...      | 撒丁岛    |

### 建筑年代(8个)

```
<1919  →  1919-1945  →  1946-1960  →  1961-1970  →
1971-1980  →  1981-1990  →  1991-2005  →  >2005
```

U值范围：2.0 W/(m²·K) ... 0.12 W/(m²·K)

### 建筑类型(4种)

- **住宅**：双峰模式(晨间/夜间)
- **办公**：单峰模式(工作时间)
- **商业**：扩展营业时间
- **教育**：课时表+季节性

---

## 💡 使用示例

### 场景1：理解建筑能效演变

```
1. 选择"北部" → "Piemonte"
2. 比较 "<1919" vs ">2005" 的同类型建筑
3. 观察U值差异(1.8 → 0.18)对能耗的影响
   结果：新建筑年耗电量下降80%以上
```

### 场景2：评估光伏补偿潜力

```
1. 选择"南部" → "Sicilia"
2. 固定建筑类型为"住宅"
3. 逐步增加PV装机容量：5kW → 10kW → 20kW
4. 在TAB3观察覆盖率变化
   结果：南部夏季可达100%+，冬季仍需补充
```

---

## 📈 关键输出指标

### TAB 1 (能耗计算)

- ✅ 年总耗电量 [MWh]
- ✅ 能耗分解占比 (照明/设备/HVAC/通风)
- ✅ 月度峰谷值 [kW]
- ✅ 全年8760小时曲线

### TAB 2 (生产量)

- ✅ 年总发电量 [MWh]
- ✅ 利用小时数 [h]
- ✅ 系统效率 [%]
- ✅ 季节性分布

### TAB 3 (匹配分析)

- ✅ 年度覆盖率 [%]
- ✅ 年缺电/余电量 [MWh]
- ✅ 月度汇总表
- ✅ 季节性分析

---

## 🔌 技术栈

| 组件      | 版本  | 说明       |
| --------- | ----- | ---------- |
| Python    | 3.9+  | 编程语言   |
| Streamlit | ≥1.30 | Web框架    |
| Pandas    | ≥1.5  | 数据处理   |
| Plotly    | ≥5.13 | 交互可视化 |
| Pvlib     | ≥0.10 | PV计算库   |
| NumPy     | ≥1.23 | 数值计算   |

---

## 📝 主要函数API

### LoadModel

```python
load_model = LoadModel(archetype_params, building_area=100)
results = load_model.calculate_hourly_load(weather_df, schedule_df)
stats = load_model.get_summary_statistics()
```

### PVModel

```python
pv_model = PVModel(latitude, longitude, p_rated=10, tilt=35)
results = pv_model.calculate_hourly_generation(weather_df)
stats = pv_model.get_summary_statistics()
```

### MatchingAlgorithm

```python
matching = MatchingAlgorithm()
results = matching.calculate_matching(load_df, pv_df)
annual_stats = matching.get_annual_statistics()
monthly_stats = matching.get_monthly_statistics()
```

---

## 🤝 贡献指南

欢迎提交Issue或PR来改进本项目：

- 🐛 bug报告
- ✨ 新建筑原型
- 🌍 新地区数据
- 📚 文档优化

---

## 📖 参考资源

### 标准与规范

- **BS EN 16798-1:2019** - 建筑室内环境设计条件
- **ISO 52016-1:2017** - 建筑能耗计算程序
- **UNI/TS 11300-2:2019** - 意大利建筑能效标准

### 数据来源

- **PVGIS** - 欧洲光伏地理信息系统
- **DPR 412/93** - 意大利建筑分类标准
- **DECRETO CACER** - 意大利能源社区激励框架

### Python库文档

- [Pvlib Documentation](https://pvlib-python.readthedocs.io/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)

---

## ⚖️ 许可证

本项目采用 **Creative Commons Attribution 4.0 (CC-BY-4.0)** 许可

欢迎学术引用与教学使用

---

## 👤 联系方式

- **作者**：[学生姓名]
- **机构**：[学校/研究机构]
- **邮件**：[contact@example.com]
- **GitHub Issues**：[项目GitHub链接]

---

**最后更新**：2026年5月14日  
**项目版本**：v1.0.0  
**维护状态**：✅ 持续更新
