"""
PV generation model
===================

P_pv(t) = P_rated × η_temp(T_cell) × η_soiling × η_inverter × [POA(t)/1000]

where:
  T_cell  = T_amb + (NOCT-20) × POA/800
  η_temp  = 1 + γ×(T_cell - 25),  γ ≈ -0.005 /°C
  η_soiling ≈ 0.97
  P_rated = PV_area × η_STC  [kW]   (area-based sizing)
  POA     = DNI×cos(θ_i) + Diffuse×(1+cos(tilt))/2   (isotropic model)
"""

import numpy as np
import pandas as pd
from typing import Dict


# Panel STC efficiency for rated-power derivation
ETA_STC = 0.19          # 19 % mono-Si
NOCT = 45.0             # °C
GAMMA = -0.005          # temperature coefficient  [1/°C]
ETA_SOILING = 0.97
ETA_INVERTER = 0.96
MIN_SIN_ALT = 0.087     # ≈ 5° above horizon – below this angle DNI extraction is unreliable
MAX_DNI = 1100.0         # physical upper bound for clear-sky DNI [W/m²]


class PVModel:
    """Area-based PV generation model with corrected POA."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        p_rated: float = 10.0,
        tilt: float = 35.0,
        azimuth: float = 180.0,
        altitude: float = 0.0,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.p_rated = p_rated          # kW (DC nameplate)
        self.tilt = tilt                # degrees from horizontal
        self.azimuth = azimuth          # degrees, 180 = south
        self.altitude = altitude        # site elevation [m]

        self.results: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------
    def calculate_hourly_generation(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        results = pd.DataFrame({
            "Timestamp": weather_df["Timestamp"].values,
            "GHI": weather_df["GHI"].values.astype(float),
            "Diffuse": weather_df["Diffuse"].values.astype(float),
            "T_amb": weather_df["T_amb"].values.astype(float),
        })

        ts = pd.to_datetime(results["Timestamp"])
        doy = ts.dt.dayofyear.values.astype(float)
        hour = ts.dt.hour.values.astype(float)

        # --- 1. solar position -------------------------------------------
        decl_rad = np.deg2rad(23.45 * np.sin(np.deg2rad(360.0 * (doy - 81) / 365.0)))
        ha_rad = np.deg2rad(15.0 * (hour - 12.0))
        lat_rad = np.deg2rad(self.latitude)

        sin_alt = (
            np.sin(lat_rad) * np.sin(decl_rad)
            + np.cos(lat_rad) * np.cos(decl_rad) * np.cos(ha_rad)
        )
        sin_alt = np.maximum(sin_alt, 0.0)
        cos_alt = np.sqrt(np.maximum(1.0 - sin_alt ** 2, 0.0))

        # solar azimuth measured FROM NORTH (0°=N, 90°=E, 180°=S, 270°=W)
        safe_cos_alt = np.maximum(cos_alt, 1e-6)
        cos_az_north = np.clip(
            (np.sin(decl_rad) * np.cos(lat_rad)
             - np.cos(decl_rad) * np.sin(lat_rad) * np.cos(ha_rad))
            / safe_cos_alt,
            -1.0, 1.0,
        )
        az_north = np.arccos(cos_az_north)                       # 0 … π
        az_north = np.where(ha_rad > 0, 2 * np.pi - az_north, az_north)  # afternoon → west

        # --- 2. incidence angle on tilted surface ------------------------
        tilt_rad = np.deg2rad(self.tilt)
        panel_az_north = np.deg2rad(self.azimuth)                 # 180° for south-facing

        cos_incidence = (
            sin_alt * np.cos(tilt_rad)
            + cos_alt * np.sin(tilt_rad) * np.cos(az_north - panel_az_north)
        )
        cos_incidence = np.maximum(cos_incidence, 0.0)

        # --- 3. POA (isotropic diffuse model) ----------------------------
        ghi = results["GHI"].values
        dhi = results["Diffuse"].values

        sun_up = sin_alt > MIN_SIN_ALT
        safe_sin_alt = np.where(sun_up, sin_alt, 1.0)
        dni = np.where(
            sun_up,
            np.clip((ghi - dhi) / safe_sin_alt, 0.0, MAX_DNI),
            0.0,
        )

        poa_beam = dni * cos_incidence
        poa_diffuse = dhi * (1.0 + np.cos(tilt_rad)) / 2.0
        poa = np.maximum(poa_beam + poa_diffuse, 0.0)

        results["POA"] = poa

        # --- 4. cell temperature (NOCT model) ----------------------------
        results["T_cell"] = results["T_amb"] + (NOCT - 20.0) * poa / 800.0

        # --- 5. temperature de-rating ------------------------------------
        eta_temp = 1.0 + GAMMA * (results["T_cell"].values - 25.0)
        eta_temp = np.maximum(eta_temp, 0.5)
        results["eta_temp"] = eta_temp

        # --- 6. output power ---------------------------------------------
        results["P_pv"] = np.maximum(
            self.p_rated * eta_temp * ETA_SOILING * ETA_INVERTER * (poa / 1000.0),
            0.0,
        )

        self.results = results
        return results

    def get_summary_statistics(self) -> Dict:
        if self.results is None:
            raise ValueError("Run calculate_hourly_generation() first.")

        r = self.results
        annual_kwh = r["P_pv"].sum()
        ghi_sum = r["GHI"].sum()
        peak = r["P_pv"].max()

        return {
            "annual_total_kwh": annual_kwh,
            "annual_avg_kw": r["P_pv"].mean(),
            "utilization_hours": annual_kwh / self.p_rated if self.p_rated > 0 else 0,
            "peak_power_kw": peak,
            "system_efficiency": (annual_kwh / (ghi_sum * self.p_rated / 1000.0) * 100.0) if ghi_sum > 0 and self.p_rated > 0 else 0,
            "monthly_avg": r.groupby(r["Timestamp"].dt.month)["P_pv"].mean(),
        }

    def get_seasonal_generation(self) -> Dict:
        if self.results is None:
            raise ValueError("Run calculate_hourly_generation() first.")
        month = self.results["Timestamp"].dt.month
        return {
            "winter_kwh": self.results[month.isin([12, 1, 2])]["P_pv"].sum(),
            "spring_kwh": self.results[month.isin([3, 4, 5])]["P_pv"].sum(),
            "summer_kwh": self.results[month.isin([6, 7, 8])]["P_pv"].sum(),
            "autumn_kwh": self.results[month.isin([9, 10, 11])]["P_pv"].sum(),
        }
