"""
Italian Building Energy Simulation Demo
======================================

English-only Streamlit interface aligned with the thesis workflow.
Code comments are intentionally kept brief and can remain Chinese when needed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 让 backend 目录可直接导入
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from load_model import LoadModel
from matching_algorithm import MatchingAlgorithm
from pv_model import PVModel
from schedule_loader import ScheduleLoader
from weather_station_manager import WeatherStationManager
from epw_parser import EPWParser
from italian_building_code_db import get_research_uenv_from_year
from data.params import BASE_PARAMS


APP_ROOT = Path(__file__).resolve().parent
HDD_CDD_FILE = APP_ROOT / "data" / "HDD_CDD_Summary.csv"

BUILDING_TYPE_LABELS = ["Residential", "Office", "Commercial", "Educational"]
BUILDING_TYPE_TO_BASE_KEY = {
    "Residential": "ResidentialApartment",
    "Office": "Office building",
    "Commercial": "Commercial building",
    "Educational": "Educational building",
}
WINDOW_RATIO_BY_TYPE = {
    "Residential": 0.25,
    "Office": 0.35,
    "Commercial": 0.45,
    "Educational": 0.30,
}
PV_ROOF_RATIO = 0.40        # PV panel area = 40% of roof (≈ floor) area
PV_ETA_STC = 0.19           # mono-Si panel efficiency at STC
DEFAULT_PV_TILT_DEG = 35
CLIMATE_ZONE_THRESHOLDS = [
    (600, "A"),
    (900, "B"),
    (1400, "C"),
    (2100, "D"),
    (3000, "E"),
    (float("inf"), "F"),
]


st.set_page_config(
    page_title="Italian Building Energy Simulation Demo",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container { padding-top: 1.4rem; }
        .stMetric { border: 1px solid rgba(120,120,120,0.18); border-radius: 14px; padding: 0.3rem 0.6rem; }
        .hero {
            padding: 1.1rem 1.2rem;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(18,34,64,0.95), rgba(31,60,105,0.9));
            color: white;
            margin-bottom: 1rem;
        }
        .hero h1 { color: white; margin-bottom: 0.2rem; }
        .hero p { color: rgba(255,255,255,0.88); margin-bottom: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource

def get_weather_manager() -> WeatherStationManager:
    return WeatherStationManager()


@st.cache_resource

def get_schedule_loader() -> ScheduleLoader:
    return ScheduleLoader()


@st.cache_data

def load_hdd_cdd_summary() -> pd.DataFrame:
    if not HDD_CDD_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(HDD_CDD_FILE)


@st.cache_data

def load_epw_weather(epw_path: str):
    metadata, weather_df = EPWParser.read_epw(epw_path)
    weather_df = weather_df.copy()
    weather_df["Timestamp"] = pd.to_datetime(weather_df["DateTime"])
    weather_df = weather_df.rename(
        columns={
            "T_Drybulb": "T_amb",
            "Radiation_Global_Horizontal": "GHI",
            "Radiation_Diffuse_Horizontal": "Diffuse",
        }
    )
    for column in ["T_amb", "GHI", "Diffuse"]:
        if column not in weather_df.columns:
            weather_df[column] = 0.0
    return metadata, weather_df[["Timestamp", "T_amb", "GHI", "Diffuse"]]


@st.cache_data

def load_station_summary(display_name: str) -> dict:
    summary_df = load_hdd_cdd_summary()
    if summary_df.empty:
        return {}
    match = summary_df[summary_df["Display_Name"] == display_name]
    if match.empty:
        return {}
    row = match.iloc[0]
    return row.to_dict()


@st.cache_data

def build_schedule(building_type: str, timestamps: pd.Series) -> pd.DataFrame:
    loader = get_schedule_loader()
    return loader.build_annual_schedule(building_type, timestamps)


@st.cache_data

def get_schedule_preview(building_type: str) -> dict:
    loader = get_schedule_loader()
    tables = loader.get_daily_tables(building_type)
    return {key: value.copy() for key, value in tables.items()}


@st.cache_data

def get_station_options() -> list[str]:
    manager = get_weather_manager()
    return [station.display_name for station in manager.list_all_stations()]


@st.cache_data

def get_station_by_display_name(display_name: str):
    manager = get_weather_manager()
    return manager.get_station_by_display_name(display_name)


@st.cache_data

def determine_climate_zone(hdd: float) -> str:
    for threshold, zone in CLIMATE_ZONE_THRESHOLDS:
        if hdd < threshold:
            return zone
    return "F"


@st.cache_data

def parse_age_to_year(age_label: str) -> int:
    age_label = str(age_label).strip()
    if age_label == "<1900":
        return 1899
    if age_label == "1901-1945":
        return 1925
    if age_label == "1946-1975":
        return 1960
    if age_label == "1976-1990":
        return 1983
    if age_label == "1991-2005":
        return 1998
    return 2015


@st.cache_data

def resolve_building_params(building_type: str, age_label: str, electric_heating: bool, electric_cooling: bool, electric_ventilation: bool, height: float) -> dict:
    age_year = parse_age_to_year(age_label)
    age_rule = get_research_uenv_from_year(age_year)
    base_key = BUILDING_TYPE_TO_BASE_KEY[building_type]
    base_components = BASE_PARAMS[base_key]["components"]

    params = {
        "P_light": float(base_components["Lighting"]),
        "P_appl": float(base_components["Appliances"]),
        "U_value": float(age_rule["Uenv"]),
        "Uenv": float(age_rule["Uenv"]),
        "Uwall_ref": float(age_rule["Uwall"]),
        "Uwindow_ref": float(age_rule["Uwindow"]),
        "Window_Ratio": WINDOW_RATIO_BY_TYPE[building_type],
        "Height": float(height),
        "Levels": 1,
        "Net_Volume_Factor": 0.9,
        "Perimeter_Factor": 4.08,
        "Heating_Setpoint": 20.0,
        "Cooling_Setpoint": 26.0,
        "COP_heat": 3.0,
        "COP_cool": 2.8,
        "ACH_occ": 0.5,
        "ACH_unocc": 0.1,
        "SFP": 1.5,
        "f_fan": 1 if electric_ventilation else 0,
        "Electric_Heating": electric_heating,
        "Electric_Cooling": electric_cooling,
        "Electric_Ventilation": electric_ventilation,
        "Renovated": False,
        "BuildingYear": age_year,
        "PeriodLabel": age_label,
    }
    return params


def add_continuous_year_axis(frame: pd.DataFrame) -> pd.DataFrame:
    """为逐时结果添加连续年的显示轴，避免日期年份跳变。"""
    display_frame = frame.copy()
    display_frame["HourOfYear"] = np.arange(1, len(display_frame) + 1)
    display_frame["Month"] = display_frame["Timestamp"].dt.month
    display_frame["DayOfYear"] = display_frame["Timestamp"].dt.dayofyear
    display_frame["ClockLabel"] = display_frame["Timestamp"].dt.strftime("%m-%d %H:00")
    return display_frame


def to_daily_display(frame: pd.DataFrame, sum_columns: list[str], mean_columns: list[str] | None = None) -> pd.DataFrame:
    """把逐时序列汇总成逐日序列，每天只保留一个显示值。"""
    mean_columns = mean_columns or []
    daily = frame.copy()
    daily["Date"] = pd.to_datetime(daily["Timestamp"]).dt.floor("D")

    aggregation = {column: "sum" for column in sum_columns}
    aggregation.update({column: "mean" for column in mean_columns})
    aggregation["Timestamp"] = "first"

    daily = daily.groupby("Date", as_index=False).agg(aggregation)
    daily = daily.rename(columns={"Date": "Timestamp"})
    daily["DayOfYear"] = np.arange(1, len(daily) + 1)
    daily["DateLabel"] = daily["Timestamp"].dt.strftime("%m-%d")
    return daily


if "run_ready" not in st.session_state:
    st.session_state.run_ready = False

if "load_results" not in st.session_state:
    st.session_state.load_results = None

if "pv_results" not in st.session_state:
    st.session_state.pv_results = None

if "matching_results" not in st.session_state:
    st.session_state.matching_results = None

if "summary" not in st.session_state:
    st.session_state.summary = {}


st.markdown(
    """
    <div class="hero">
        <h1>Italian Building Energy Simulation Demo</h1>
        <p>
            A thesis-aligned Streamlit prototype for a single building.
            The user selects only GIS-available inputs: floor area, height, building age, weather station proxy, ventilation/heating electrification, and building type.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "The calculation pipeline uses the standard weather station EPW files, the research degree-day anchoring method, and the standard schedule library from data/ScheduleV2.csv."
)

weather_manager = get_weather_manager()
station_options = get_station_options()
summary_df = load_hdd_cdd_summary()

with st.sidebar:
    st.header("Simulation Inputs")

    selected_station = st.selectbox(
        "Climate zone / weather station",
        station_options,
        help="A weather station acts as the climate-zone proxy for this demo.",
    )

    building_type = st.selectbox(
        "Building type",
        BUILDING_TYPE_LABELS,
        index=0,
    )

    age_options = ["<1900", "1901-1945", "1946-1975", "1976-1990", "1991-2005", "After 2005"]
    building_age = st.selectbox(
        "Construction period",
        age_options,
        index=5,
    )

    floor_area = st.slider(
        "Floor area (m²)",
        min_value=30,
        max_value=2000,
        value=120,
        step=10,
    )

    building_height = st.slider(
        "Building height (m)",
        min_value=2.0,
        max_value=20.0,
        value=3.0,
        step=0.1,
    )

    electric_ventilation = st.checkbox("Electric ventilation", value=True)
    electric_heating = st.checkbox("Electric heating", value=True)
    electric_cooling = st.checkbox("Electric cooling", value=True)

    st.subheader("PV assumptions")
    pv_area = floor_area * PV_ROOF_RATIO
    pv_capacity = pv_area * PV_ETA_STC       # kW rated (DC nameplate)
    pv_tilt = DEFAULT_PV_TILT_DEG
    st.caption(
        f"PV area = {pv_area:.1f} m² (roof × {PV_ROOF_RATIO:.0%}), "
        f"rated power = {pv_capacity:.2f} kW (η_STC={PV_ETA_STC:.0%}), "
        f"tilt {pv_tilt}°, south-facing."
    )

    run_button = st.button("Run simulation", type="primary", use_container_width=True)


station_info = get_station_by_display_name(selected_station)
station_summary = load_station_summary(selected_station)

if station_info is not None:
    st.subheader("Selected weather station")
    station_meta_cols = st.columns(4)
    with station_meta_cols[0]:
        st.metric("Station", station_info.display_name)
    with station_meta_cols[1]:
        st.metric("Region", station_info.region_name)
    with station_meta_cols[2]:
        st.metric("Latitude", f"{station_summary.get('Latitude', 0.0):.3f}")
    with station_meta_cols[3]:
        st.metric("Longitude", f"{station_summary.get('Longitude', 0.0):.3f}")

    if station_summary:
        climate_zone = determine_climate_zone(float(station_summary.get("HDD_base20", 0.0)))
        st.info(
            f"Derived climate zone: {climate_zone} | HDD(base20): {station_summary.get('HDD_base20', 0.0):.1f} | CDD(base26): {station_summary.get('CDD_base26', 0.0):.1f}"
        )
else:
    climate_zone = "D"
    st.warning("No weather station metadata could be loaded.")

st.divider()

if run_button:
    try:
        with st.spinner("Loading weather data and running the simulation..."):
            if station_info is None or station_info.epw_file_path is None:
                raise FileNotFoundError("Selected weather station does not have an EPW file.")

            metadata, weather_df = load_epw_weather(str(station_info.epw_file_path))
            schedule_df = build_schedule(building_type, weather_df["Timestamp"])
            params = resolve_building_params(building_type, building_age, electric_heating, electric_cooling, electric_ventilation, building_height)

            load_model = LoadModel(params, floor_area)
            load_results = load_model.calculate_hourly_load(weather_df, schedule_df)
            load_results = add_continuous_year_axis(load_results)
            load_summary = load_model.get_summary_statistics()

            latitude = float(metadata.get("Latitude", station_summary.get("Latitude", 0.0) or 0.0))
            longitude = float(metadata.get("Longitude", station_summary.get("Longitude", 0.0) or 0.0))
            altitude = float(metadata.get("Altitude", station_summary.get("Altitude", 0.0) or 0.0))
            pv_model = PVModel(latitude, longitude, p_rated=float(pv_capacity), tilt=float(pv_tilt), altitude=altitude)
            pv_results = pv_model.calculate_hourly_generation(weather_df)
            pv_results = add_continuous_year_axis(pv_results)
            pv_summary = pv_model.get_summary_statistics()

            matching = MatchingAlgorithm()
            matching_results = matching.calculate_matching(load_results, pv_results)
            matching_results = add_continuous_year_axis(matching_results)
            matching_summary = matching.get_annual_statistics()

            st.session_state.run_ready = True
            st.session_state.load_results = load_results
            st.session_state.pv_results = pv_results
            st.session_state.matching_results = matching_results
            st.session_state.summary = {
                "load": load_summary,
                "pv": pv_summary,
                "matching": matching_summary,
                "climate_zone": climate_zone,
                "weather_metadata": metadata,
                "params": params,
                "station": station_info.display_name,
                "station_region": station_info.region_name,
            }

        st.success("Simulation completed successfully.")
    except Exception as exc:
        st.session_state.run_ready = False
        st.error(f"Simulation failed: {exc}")


if st.session_state.run_ready:
    load_results = st.session_state.load_results
    pv_results = st.session_state.pv_results
    matching_results = st.session_state.matching_results
    load_summary = st.session_state.summary["load"]
    pv_summary = st.session_state.summary["pv"]
    matching_summary = st.session_state.summary["matching"]
    params = st.session_state.summary["params"]

    st.subheader("Key results")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Annual load (kWh)", f"{load_summary['annual_total_kwh']:.1f}")
    with c2:
        st.metric("Annual PV generation (kWh)", f"{pv_summary['annual_total_kwh']:.1f}")
    with c3:
        st.metric("Coverage rate", f"{matching_summary['coverage_rate_percent']:.1f}%")
    with c4:
        st.metric("Annual surplus (kWh)", f"{matching_summary['annual_surplus_kwh']:.1f}")
    with c5:
        st.metric("Annual deficit (kWh)", f"{matching_summary['annual_deficit_kwh']:.1f}")

    tab_load, tab_pv, tab_balance, tab_inputs = st.tabs(["Load", "PV", "Balance", "Inputs"])

    with tab_load:
        st.markdown("### Building load breakdown")
        load_cols = st.columns(6)
        with load_cols[0]:
            st.metric("Lighting", f"{load_summary.get('lighting_total_kwh', 0):.1f} kWh", f"{load_summary.get('lighting_ratio', 0):.1f}%")
        with load_cols[1]:
            st.metric("Appliances", f"{load_summary.get('appliance_total_kwh', 0):.1f} kWh", f"{load_summary.get('appliance_ratio', 0):.1f}%")
        with load_cols[2]:
            st.metric("Ventilation", f"{load_summary.get('ventilation_total_kwh', 0):.1f} kWh", f"{load_summary.get('ventilation_ratio', 0):.1f}%")
        with load_cols[3]:
            st.metric("HVAC total", f"{load_summary.get('hvac_total_kwh', 0):.1f} kWh", f"{load_summary.get('hvac_ratio', 0):.1f}%")
        with load_cols[4]:
            st.metric("- Heating", f"{load_summary.get('heating_total_kwh', 0):.1f} kWh", f"{load_summary.get('heating_ratio', 0):.1f}%")
        with load_cols[5]:
            st.metric("- Cooling", f"{load_summary.get('cooling_total_kwh', 0):.1f} kWh", f"{load_summary.get('cooling_ratio', 0):.1f}%")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=load_results["HourOfYear"], y=load_results["E_total"], mode="lines", name="Total load", line=dict(color="#1f77b4", width=1.5), customdata=load_results[["ClockLabel"]], hovertemplate="Hour %{x}<br>%{customdata[0]}<br>Load: %{y:.3f} kW<extra></extra>"))
        fig.add_trace(go.Scatter(x=load_results["HourOfYear"], y=load_results["E_hvac"], mode="lines", name="HVAC", line=dict(color="#d62728", width=1.0, dash="dot"), customdata=load_results[["ClockLabel"]], hovertemplate="Hour %{x}<br>%{customdata[0]}<br>HVAC: %{y:.3f} kW<extra></extra>"))
        fig.add_trace(go.Scatter(x=load_results["HourOfYear"], y=load_results["E_vent"], mode="lines", name="Ventilation", line=dict(color="#9467bd", width=1.0, dash="dash"), customdata=load_results[["ClockLabel"]], hovertemplate="Hour %{x}<br>%{customdata[0]}<br>Ventilation: %{y:.3f} kW<extra></extra>"))
        fig.update_layout(height=420, xaxis_title="Hour of year (1-8760)", yaxis_title="kW", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        monthly_load = load_results.groupby(load_results["Timestamp"].dt.month.rename("Month"))[["E_light", "E_appl", "E_vent", "E_hvac"]].sum().reset_index()
        monthly_fig = go.Figure()
        monthly_fig.add_trace(go.Bar(x=monthly_load["Month"], y=monthly_load["E_light"], name="Lighting"))
        monthly_fig.add_trace(go.Bar(x=monthly_load["Month"], y=monthly_load["E_appl"], name="Appliances"))
        monthly_fig.add_trace(go.Bar(x=monthly_load["Month"], y=monthly_load["E_vent"], name="Ventilation"))
        monthly_fig.add_trace(go.Bar(x=monthly_load["Month"], y=monthly_load["E_hvac"], name="HVAC"))
        monthly_fig.update_layout(barmode="stack", height=360, xaxis_title="Month", yaxis_title="kWh")
        st.plotly_chart(monthly_fig, use_container_width=True)

    with tab_pv:
        st.markdown("### PV generation")
        pv_cols = st.columns(5)
        with pv_cols[0]:
            st.metric("Panel area", f"{pv_area:.1f} m²")
        with pv_cols[1]:
            st.metric("Rated power", f"{pv_capacity:.2f} kW")
        with pv_cols[2]:
            st.metric("Tilt", f"{pv_tilt}°")
        with pv_cols[3]:
            st.metric("Peak power", f"{pv_summary['peak_power_kw']:.2f} kW")
        with pv_cols[4]:
            st.metric("Utilization hours", f"{pv_summary['utilization_hours']:.0f} h")

        pv_fig = go.Figure()
        pv_fig.add_trace(go.Scatter(x=pv_results["HourOfYear"], y=pv_results["P_pv"], mode="lines", name="PV generation", line=dict(color="#f2b01e", width=1.5), customdata=pv_results[["ClockLabel"]], hovertemplate="Hour %{x}<br>%{customdata[0]}<br>PV: %{y:.3f} kW<extra></extra>"))
        pv_fig.update_layout(height=420, xaxis_title="Hour of year (1-8760)", yaxis_title="kW", hovermode="x unified")
        st.plotly_chart(pv_fig, use_container_width=True)

        monthly_pv = pv_results.groupby(pv_results["Timestamp"].dt.month.rename("Month"))["P_pv"].sum().reset_index(name="PV")
        pv_month_fig = go.Figure()
        pv_month_fig.add_trace(go.Bar(x=monthly_pv["Month"], y=monthly_pv["PV"], name="PV generation", marker_color="#f2b01e"))
        pv_month_fig.update_layout(height=360, xaxis_title="Month", yaxis_title="kWh")
        st.plotly_chart(pv_month_fig, use_container_width=True)

    with tab_balance:
        st.markdown("### Load-generation balance")
        bal_cols = st.columns(4)
        with bal_cols[0]:
            st.metric("Self-consumed energy", f"{matching_results['E_shared'].sum():.1f} kWh")
        with bal_cols[1]:
            st.metric("Load / generation ratio", f"{matching_summary['load_generation_ratio']:.2f}")
        with bal_cols[2]:
            st.metric("Peak load", f"{matching_summary['peak_load_kw']:.2f} kW")
        with bal_cols[3]:
            st.metric("Peak PV", f"{matching_summary['peak_generation_kw']:.2f} kW")

        balance_fig = make_subplots(specs=[[{"secondary_y": True}]])
        balance_fig.add_trace(go.Scatter(x=matching_results["HourOfYear"], y=matching_results["E_load"], name="Load", line=dict(color="#1f77b4", width=1), customdata=matching_results[["ClockLabel"]], hovertemplate="Hour %{x}<br>%{customdata[0]}<br>Load: %{y:.3f} kW<extra></extra>"), secondary_y=False)
        balance_fig.add_trace(go.Scatter(x=matching_results["HourOfYear"], y=matching_results["P_pv"], name="PV", line=dict(color="#f2b01e", width=1), customdata=matching_results[["ClockLabel"]], hovertemplate="Hour %{x}<br>%{customdata[0]}<br>PV: %{y:.3f} kW<extra></extra>"), secondary_y=False)
        balance_fig.add_trace(go.Scatter(x=matching_results["HourOfYear"], y=matching_results["E_diff"], name="Balance", line=dict(color="#2ca02c", width=1, dash="dash"), customdata=matching_results[["ClockLabel"]], hovertemplate="Hour %{x}<br>%{customdata[0]}<br>Balance: %{y:.3f} kW<extra></extra>"), secondary_y=True)
        balance_fig.update_layout(height=460, xaxis_title="Hour of year (1-8760)", hovermode="x unified")
        balance_fig.update_yaxes(title_text="kW", secondary_y=False)
        balance_fig.update_yaxes(title_text="Net balance (kW)", secondary_y=True)
        st.plotly_chart(balance_fig, use_container_width=True)

        st.markdown("### Monthly balance")
        monthly_balance = matching_results.groupby(matching_results["Timestamp"].dt.month.rename("Month"))[["E_load", "P_pv", "E_shared"]].sum().reset_index()
        monthly_balance.columns = ["Month", "Load", "PV", "Shared"]
        balance_month_fig = go.Figure()
        balance_month_fig.add_trace(go.Bar(x=monthly_balance["Month"], y=monthly_balance["Load"], name="Load"))
        balance_month_fig.add_trace(go.Bar(x=monthly_balance["Month"], y=monthly_balance["PV"], name="PV"))
        balance_month_fig.add_trace(go.Bar(x=monthly_balance["Month"], y=monthly_balance["Shared"], name="Shared"))
        balance_month_fig.update_layout(barmode="group", height=360, xaxis_title="Month", yaxis_title="kWh")
        st.plotly_chart(balance_month_fig, use_container_width=True)

    with tab_inputs:
        st.markdown("### Simulation inputs")
        input_cols = st.columns(2)
        with input_cols[0]:
            st.json(
                {
                    "station": st.session_state.summary["station"],
                    "climate_zone": st.session_state.summary["climate_zone"],
                    "building_type": building_type,
                    "construction_period": building_age,
                    "floor_area_m2": floor_area,
                    "height_m": building_height,
                },
                expanded=False,
            )
        with input_cols[1]:
            st.json(
                {
                    "electric_heating": electric_heating,
                    "electric_ventilation": electric_ventilation,
                    "pv_rated_power_kw": pv_capacity,
                    "pv_tilt_deg": pv_tilt,
                    "u_env": params["Uenv"],
                    "lighting_w_m2": params["P_light"],
                    "appliance_w_m2": params["P_appl"],
                },
                expanded=False,
            )

        preview_tables = get_schedule_preview(building_type)
        weekday_table = preview_tables["Weekdays"].copy()
        weekend_table = preview_tables["Weekends"].copy()
        preview_fig = go.Figure()
        preview_fig.add_trace(go.Scatter(x=weekday_table["Hour"], y=weekday_table["Occupancy"], name="Weekday occupancy", line=dict(color="#1f77b4")))
        preview_fig.add_trace(go.Scatter(x=weekday_table["Hour"], y=weekday_table["Lighting"], name="Weekday lighting", line=dict(color="#ff7f0e")))
        preview_fig.add_trace(go.Scatter(x=weekday_table["Hour"], y=weekday_table["Appliance"], name="Weekday appliance", line=dict(color="#2ca02c")))
        preview_fig.add_trace(go.Scatter(x=weekend_table["Hour"], y=weekend_table["Occupancy"], name="Weekend occupancy", line=dict(color="#1f77b4", dash="dash")))
        preview_fig.add_trace(go.Scatter(x=weekend_table["Hour"], y=weekend_table["Lighting"], name="Weekend lighting", line=dict(color="#ff7f0e", dash="dash")))
        preview_fig.add_trace(go.Scatter(x=weekend_table["Hour"], y=weekend_table["Appliance"], name="Weekend appliance", line=dict(color="#2ca02c", dash="dash")))
        preview_fig.update_layout(height=420, xaxis_title="Hour", yaxis_title="Schedule factor", hovermode="x unified")
        st.plotly_chart(preview_fig, use_container_width=True)

    st.download_button(
        "Download load results as CSV",
        data=load_results.to_csv(index=False).encode("utf-8"),
        file_name="load_results.csv",
        mime="text/csv",
    )

    st.divider()
    st.subheader("Computation parameter summary")
    st.caption("All key parameters and intermediate values used in this simulation run.")

    geo_data = {
        "Parameter": [
            "Floor area (A_zone)",
            "Building height",
            "Net volume (V = A × h × 0.9)",
            "Perimeter",
            "Total wall area",
            "Window area (wall × WR)",
            "Opaque wall area",
            "Roof area",
            "Floor area (envelope)",
            "Total envelope area (A_env)",
            "Window-to-wall ratio (WR)",
        ],
        "Value": [
            f"{floor_area} m²",
            f"{building_height:.1f} m",
            f"{load_summary.get('volume_m3', 0):.1f} m³",
            f"{params.get('Perimeter_Factor', 4.08) * np.sqrt(floor_area):.2f} m",
            f"{load_summary.get('area_wall_m2', 0):.1f} m²",
            f"{load_summary.get('area_window_m2', 0):.1f} m²",
            f"{load_summary.get('area_opaque_wall_m2', 0):.1f} m²",
            f"{load_summary.get('area_roof_m2', 0):.1f} m²",
            f"{load_summary.get('area_floor_m2', 0):.1f} m²",
            f"{load_summary.get('area_env_m2', 0):.1f} m²",
            f"{load_summary.get('window_ratio', 0):.2f}",
        ],
    }

    thermal_data = {
        "Parameter": [
            "U_env (blended envelope U-value)",
            "U_wall (reference wall)",
            "U_window (reference window)",
            "H_env = U_env × A_env",
            "H_total (mean, incl. ventilation)",
            "Heating setpoint (θ_H)",
            "Cooling setpoint (θ_C)",
            "COP_heating",
            "COP_cooling (EER)",
            "ACH occupied",
            "ACH unoccupied",
            "SFP (specific fan power)",
            "f_fan (mechanical ventilation)",
            "Electric heating enabled",
            "Electric cooling enabled",
            "Electric ventilation enabled",
        ],
        "Value": [
            f"{params.get('Uenv', 0):.3f} W/(m²·K)",
            f"{params.get('Uwall_ref', 0):.3f} W/(m²·K)",
            f"{params.get('Uwindow_ref', 0):.3f} W/(m²·K)",
            f"{load_summary.get('h_env_wk', 0):.1f} W/K",
            f"{load_summary.get('h_total_ref_wk', 0):.1f} W/K",
            f"{load_summary.get('heating_setpoint_c', 20):.1f} °C",
            f"{load_summary.get('cooling_setpoint_c', 26):.1f} °C",
            f"{load_summary.get('cop_heat_ref', 0):.2f}",
            f"{load_summary.get('cop_cool_ref', 0):.2f}",
            f"{params.get('ACH_occ', 0):.2f} h⁻¹",
            f"{params.get('ACH_unocc', 0):.2f} h⁻¹",
            f"{params.get('SFP', 0):.2f} kW/(m³/s)",
            f"{params.get('f_fan', 0)}",
            f"{'Yes' if params.get('Electric_Heating') else 'No'}",
            f"{'Yes' if params.get('Electric_Cooling') else 'No'}",
            f"{'Yes' if params.get('Electric_Ventilation') else 'No'}",
        ],
    }

    energy_data = {
        "Parameter": [
            "P_light (lighting power density)",
            "P_appl (appliance power density)",
            "HDD (annual, base 20 °C)",
            "CDD (annual, base 26 °C)",
            "Q_H,annual (thermal heating demand)",
            "Q_C,annual (thermal cooling demand)",
            "E_lighting (annual electricity)",
            "E_appliances (annual electricity)",
            "E_ventilation (annual electricity)",
            "E_heating (annual electricity)",
            "E_cooling (annual electricity)",
            "E_HVAC (heating + cooling)",
            "E_total (annual electricity)",
        ],
        "Value": [
            f"{params.get('P_light', 0):.2f} W/m²",
            f"{params.get('P_appl', 0):.2f} W/m²",
            f"{load_summary.get('hdd_annual', 0):.1f} °C·day",
            f"{load_summary.get('cdd_annual', 0):.1f} °C·day",
            f"{load_summary.get('q_h_annual_kwh', 0):.1f} kWh",
            f"{load_summary.get('q_c_annual_kwh', 0):.1f} kWh",
            f"{load_summary.get('lighting_total_kwh', 0):.1f} kWh",
            f"{load_summary.get('appliance_total_kwh', 0):.1f} kWh",
            f"{load_summary.get('ventilation_total_kwh', 0):.1f} kWh",
            f"{load_summary.get('heating_total_kwh', 0):.1f} kWh",
            f"{load_summary.get('cooling_total_kwh', 0):.1f} kWh",
            f"{load_summary.get('hvac_total_kwh', 0):.1f} kWh",
            f"{load_summary.get('annual_total_kwh', 0):.1f} kWh",
        ],
    }

    pv_param_data = {
        "Parameter": [
            "Roof area (= floor area)",
            "PV roof ratio",
            "PV panel area",
            "η_STC (panel efficiency)",
            "Rated power (P_rated = area × η_STC)",
            "Tilt angle",
            "Azimuth",
            "Annual PV generation",
            "Peak PV power",
            "Utilization hours",
            "Annual surplus",
            "Annual deficit",
            "Coverage rate",
        ],
        "Value": [
            f"{floor_area} m²",
            f"{PV_ROOF_RATIO:.0%}",
            f"{pv_area:.1f} m²",
            f"{PV_ETA_STC:.0%}",
            f"{pv_capacity:.2f} kW",
            f"{pv_tilt}°",
            "180° (south-facing)",
            f"{pv_summary.get('annual_total_kwh', 0):.1f} kWh",
            f"{pv_summary.get('peak_power_kw', 0):.2f} kW",
            f"{pv_summary.get('utilization_hours', 0):.0f} h",
            f"{matching_summary.get('annual_surplus_kwh', 0):.1f} kWh",
            f"{matching_summary.get('annual_deficit_kwh', 0):.1f} kWh",
            f"{matching_summary.get('coverage_rate_percent', 0):.1f}%",
        ],
    }

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### Geometry")
        st.dataframe(pd.DataFrame(geo_data), hide_index=True, use_container_width=True)
        st.markdown("#### Energy results")
        st.dataframe(pd.DataFrame(energy_data), hide_index=True, use_container_width=True)
    with col_right:
        st.markdown("#### Thermal & HVAC parameters")
        st.dataframe(pd.DataFrame(thermal_data), hide_index=True, use_container_width=True)
        st.markdown("#### PV & matching")
        st.dataframe(pd.DataFrame(pv_param_data), hide_index=True, use_container_width=True)

else:
    st.info("Select the inputs in the sidebar and run the simulation to generate the results.")
