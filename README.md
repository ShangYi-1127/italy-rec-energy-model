
# 🌞 Italian Prototype Electrical Energy Simulation Demonstration System for Architecture
**You can view it on the website：https://italy-rec-energy-model.streamlit.app/**
---
## 📋 Project Overview

An **educational interactive tool** that allows users to select architectural parameters (region, era, type), and displays:
- ⚡ **Building Energy Consumption Calculation** - Hourly energy breakdown and formula derivation
- ☀️ **Photovoltaic Production Calculation** - Power generation model based on meteorological data
- 📊 **Energy Supply and Demand Analysis** - Dynamic changes in supply and demand relationship

## 🎯 Core Features

✅ **Complete Formula Display** - Each calculation step has its corresponding mathematical formula
✅ **Detailed Parameter Library** - 20 Italian regions × 8 architectural eras × 4 types = 640 combinations
✅ **Interactive Interface** - Real-time visualization using Streamlit + Plotly
✅ **Open Source Deployment** - Supports local running and Streamlit Cloud cloud deployment

---

## 🚀 QUICK START

### Locally-run

#### 1. Environmental Preparation

```bash
# Clone or enter the project directory
cd single\ building\ electrical\ energy\ sitimulation-demo

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Run the application

```bash
streamlit run app.py
```

#### 4. Accessing the Application

Open the browser at: `http://localhost:8501`

### 5.Streamlit Cloud Cloud Deployment

1. Push the project to GitHub
2. Visit https://share.streamlit.io
3. Connect your GitHub account and select the repository
4. Set the entry file as `app.py`
5. Click "Deploy"
---

## 📁 Project Structure

```
.
├── app.py                           # Streamlit
├── requirements.txt                 # Python dependencies
├── README.md                        # this document
│
├── backend/                         # Backend
│   ├── __init__.py
│   ├── load_model.py               # PV power generation calculation module
│   ├── pv_model.py                 # PV power generation calculation module
│   ├── matching_algorithm.py       # Economic Assessment module
│   ├── economic_model.py           # Economic Assessment module(CACI/CACV/RID)
│   └── archetype_data.py           # Architectural Prototype library
│
├── data/                            # Data Directory
│   ├── archetypes.csv              # Building Parameter Matrix (scalable)
│   ├── regions.csv                 # Information on the Italian region
│   ├── schedules/                  # Time Schedule
│   │   ├── schedule_residential_weekday.csv
│   │   ├── schedule_residential_weekend.csv
│   │   ├── schedule_office_weekday.csv
│   │   ├── schedule_office_weekend.csv
│   │   ├── schedule_commercial_weekday.csv
│   │   ├── schedule_commercial_weekend.csv
│   │   ├── schedule_educational_schoolday.csv
│   │   └── schedule_educational_holiday.csv
│   │
│   └── weather/                    # Meteorological data cache (optional)
│       ├── piemonte_2024.csv
│       ├── lazio_2024.csv
│       ├── sicilia_2024.csv
│       └── ... (20个地区)
│
└── tests/                           # Unit Test(optional)
    ├── test_load_model.py
    ├── test_pv_model.py
    └── test_matching.py
```

---

## 🔧 Building load calculation

### 1. LoadModel (Building load calculation)

**Formula**：

```
E_light,t = P_light × A × S_light(t)
E_appl,t = P_appl × A × S_appl(t)
P_vent,t = ρ × c_p × V_vent × ΔT / 3600
E_hvac,t = Q_demand / COP(T)
E_total,t = E_light + E_appl + E_vent + E_hvac
```

  **Key Parameters**:
- U value: Building heat transfer coefficient [W/(m²·K)]
- P_light, P_appl: Power density [W/m²]
- COP: System performance coefficient (varies with temperature)

### 2. PVModel (Photovoltaic power generation)

**Core Algorithm(Pvlib)**：

```
T_cell = T_amb + (NOCT - 20) × POA / 800
η_temp = 1 + γ × (T_cell - 25)  ; γ = -0.005/°C
P_pv = P_rated × η_temp × η_soiling × η_inverter × (POA / 1000)
```

  **Characteristics**:
  
- Temperature correction factor
- Dust accumulation loss modeling
- Inverter efficiency

### 3. MatchingAlgorithm


**Core Metrics**: 
```
E_diff,t = P_pv(t) - E_load(t)
Coverage = min(P_pv, E_load).sum() / E_load.sum() 
```

### 4. Economic Model (Economic Assessment)  
**Italian REC Subsidy**:  
- **CACI**: Shared electricity subsidy ~80–120 €/MWh  
- **CACV**: Grid fee refund ~30 €/MWh  
- **RID**: Grid sale (market price)

---

## 📊 Parameter Configuration

### Region(20)

| North | Central | South + Islands |
| -------- | -------- | --------- |
| Piedmont | Tuscany | Campania |
| Lombardy | Lazio   | Puglia    |
| Veneto   | Umbria  | Sicily    |
| ...      | ...      | Sardinia   |

### Building Age(8个)

```
<1919  →  1919-1945  →  1946-1960  →  1961-1970  →
1971-1980  →  1981-1990  →  1991-2005  →  >2005
```

U value range：2.0 W/(m²·K) ... 0.12 W/(m²·K)

### Building types (4)

- ** Residential ** : Bimodal (morning/night)
- ** Office ** : Single-peak mode (working hours)
- ** Business ** : Extended business hours
- ** Education ** : Class schedule + Seasonality

---

## 💡 EXAMPLES

### Scene 1: Understanding the evolution of building energy efficiency

` ` `
Select "North" → "Piemonte"
2. Compare the same type of buildings in "<1919" vs. ">2005"
3. Observe the impact of the difference in U values (1.8 → 0.18) on energy consumption
```

### Scene 1: Understanding the evolution of building energy efficiency

` ` `
Select "North" → "Piemonte"
2. Compare the same type of buildings in "<1919" vs. ">2005"
3. Observe the impact of the difference in U values (1.8 → 0.18) on energy consumption

```
Select "South" → "Sicilia"
2. The fixed building type is "residential"
3. Gradually increase the installed capacity of PV: 5kW → 10kW → 20kW
4. Observe the coverage rate changes in TAB3
Result: In the south, it can reach over 100% in summer, but supplementation is still needed in winter
```

---

## 📈 Energy consumption calculation

- ✅ annual total power consumption [MWh]
- ✅ energy consumption breakdown ratio (lighting/equipment /HVAC/ ventilation)
- ✅ monthly peak-valley value [kW]
- ✅ annual 8,760 hour curve

### TAB 1 Energy consumption calculation

- ✅ annual total power consumption [MWh]
- ✅ energy consumption breakdown ratio (lighting/equipment /HVAC/ ventilation)
- ✅ monthly peak-valley value [kW]
- ✅ annual 8,760 hour curve

### TAB 2 Matching Analysis

- ✅ annual coverage rate [%]
- ✅ annual power shortage/surplus [MWh]
- ✅ monthly summary table
- ✅ seasonal analysis

  
### TAB 3 Matching Analysis

- ✅ annual coverage rate [%]
- ✅ annual power shortage/surplus [MWh]
- ✅ monthly summary table
- ✅ seasonal analysis

---

## 🔌 技术栈

| Module     | Version  | 
| ---------- | -------- | 
| Python     | 3.9+     | 
| Streamlit  | ≥1.30    | 
| Pandas     | ≥1.5     | 
| Plotly     | ≥5.13    | 
| Pvlib      | ≥0.10    | 
| NumPy      | ≥1.23    | 

---

## 📝 Main API

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

## 🤝 Contribution Guide

Welcome to submit issues or PRS to improve this project
- 🐛 bug report
- ✨ new building prototype
- 🌍 new regional data
- 📚 document optimization

---

## 📖 Reference

### Standards and Specifications

- **BS EN 16798-1:2019** - Design conditions for architectural interior environment
- **ISO 52016-1:2017** - Design conditions for architectural interior environment
- **UNI/TS 11300-2:2019** - Italian building energy efficiency standards

### Data Sources

- **PVGIS** - European Photovoltaic Geographic Information System
- **DPR 412/93** - Italian building classification standards
- **DECRETO CACER** - Italian building classification standards

### Python Library Documentation

- [Pvlib Documentation](https://pvlib-python.readthedocs.io/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)

---

## ⚖️ 许可证

This project is licensed under **Creative Commons Attribution 4.0 (CC-BY-4.0)** license

Welcome for academic citation and teaching use

---

## 👤 Contact Information

- **Author**：[Shang Yi]
- **Institution**：[Politecnico di Torino]
- **Email**：[s339753@studenti.polito.it]

---

**最后更新**：2026-05-14
**项目版本**：v1.0.0  
**维护状态**：updating
