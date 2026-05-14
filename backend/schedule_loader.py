"""
Standard schedule loader.

This module reads data/ScheduleV2.csv and expands the selected building type
into an annual 8760-hour schedule aligned to weather timestamps.
"""

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


SCHEDULE_FILE = Path(__file__).resolve().parent.parent / "data" / "ScheduleV2.csv"

# 英文 UI 类型到标准 schedule profile 的映射
PROFILE_MAP = {
    "Residential": "ReApart",
    "Office": "OfficeSingle",
    "Commercial": "DepStore",
    "Educational": "Sch",
}


class ScheduleLoader:
    """Load and expand the standard schedule library."""

    def __init__(self, schedule_path: Path = SCHEDULE_FILE):
        self.schedule_path = Path(schedule_path)
        self._raw = None

    def load_raw(self) -> pd.DataFrame:
        """读取原始 ScheduleV2.csv 表格。"""
        if self._raw is None:
            if not self.schedule_path.exists():
                raise FileNotFoundError(f"Schedule file not found: {self.schedule_path}")
            self._raw = pd.read_csv(self.schedule_path, header=[0, 1, 2])
        return self._raw.copy()

    def available_profiles(self) -> List[str]:
        """返回可用 profile 名称。"""
        raw = self.load_raw()
        profiles = []
        for profile in raw.columns.get_level_values(0):
            if profile != "h" and profile not in profiles:
                profiles.append(profile)
        return profiles

    def _extract_profile_table(self, profile_name: str, day_type: str) -> pd.DataFrame:
        """提取单个 profile 的工作日或周末表。"""
        raw = self.load_raw()
        if (profile_name, day_type, "Occupants") not in raw.columns:
            raise KeyError(f"Profile not found in schedule library: {profile_name} / {day_type}")

        hour_series = raw.iloc[:, 0].astype(int)
        table = pd.DataFrame({
            "Hour": hour_series,
            "Occupancy": raw[(profile_name, day_type, "Occupants")].astype(float).values,
            "Appliance": raw[(profile_name, day_type, "Appliances")].astype(float).values,
            "Lighting": raw[(profile_name, day_type, "Lighting")].astype(float).values,
        })
        table["DayType"] = day_type
        table["Ventilation"] = table["Occupancy"]
        return table

    def get_daily_tables(self, building_type: str) -> Dict[str, pd.DataFrame]:
        """获取某建筑类型的工作日/周末 24 小时表。"""
        profile_name = PROFILE_MAP.get(building_type, PROFILE_MAP["Residential"])
        return {
            "Weekdays": self._extract_profile_table(profile_name, "Weekdays"),
            "Weekends": self._extract_profile_table(profile_name, "Weekends"),
        }

    def build_annual_schedule(self, building_type: str, timestamps: pd.Series) -> pd.DataFrame:
        """根据时间戳展开年时序 schedule。"""
        timestamp_series = pd.to_datetime(pd.Series(timestamps)).reset_index(drop=True)
        base = pd.DataFrame({"Timestamp": timestamp_series})
        base["Hour"] = base["Timestamp"].dt.hour + 1
        base["DayType"] = np.where(base["Timestamp"].dt.dayofweek < 5, "Weekdays", "Weekends")

        tables = self.get_daily_tables(building_type)
        lookup = pd.concat(tables.values(), ignore_index=True)

        merged = base.merge(lookup, on=["DayType", "Hour"], how="left")
        merged["Occupancy"] = merged["Occupancy"].fillna(0.0)
        merged["Appliance"] = merged["Appliance"].fillna(0.0)
        merged["Lighting"] = merged["Lighting"].fillna(0.0)
        merged["Ventilation"] = merged["Ventilation"].fillna(merged["Occupancy"])

        return merged[["Timestamp", "Hour", "DayType", "Occupancy", "Appliance", "Lighting", "Ventilation"]]


if __name__ == "__main__":
    loader = ScheduleLoader()
    print(loader.available_profiles())
    annual = loader.build_annual_schedule("Residential", pd.date_range("2024-01-01", periods=8760, freq="h"))
    print(annual.head())
