"""Batch calculate HDD/CDD for all weather stations.

This script scans the weather data tree, reads each station's EPW file,
computes heating and cooling degree days using hourly dry-bulb temperature,
and overwrites the summary CSV at data/HDD_CDD_Summary.csv.

Formula:
    HDD = sum(max(0, T_base_h - T_out,h)) / 24
    CDD = sum(max(0, T_out,h - T_base_c)) / 24

The output is station-level by default, with a region-level aggregate section
also written to a Markdown summary file.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.epw_parser import EPWParser
from backend.weather_station_manager import WeatherStationManager


BASE_HEATING_TEMP = 20.0
BASE_COOLING_TEMP = 26.0


def compute_degree_days(weather_df: pd.DataFrame) -> Dict[str, float]:
    """Compute HDD/CDD from hourly dry-bulb temperature data."""
    if 'T_Drybulb' not in weather_df.columns:
        raise KeyError('Missing T_Drybulb column in EPW data frame')

    dry_bulb = pd.to_numeric(weather_df['T_Drybulb'], errors='coerce').ffill().bfill()

    hdd_degree_hours = (BASE_HEATING_TEMP - dry_bulb).clip(lower=0).sum()
    cdd_degree_hours = (dry_bulb - BASE_COOLING_TEMP).clip(lower=0).sum()

    return {
        'HDD_base20': float(hdd_degree_hours / 24.0),
        'CDD_base26': float(cdd_degree_hours / 24.0),
        'HDD_degree_hours': float(hdd_degree_hours),
        'CDD_degree_hours': float(cdd_degree_hours),
    }


def build_station_summary(weather_root: Path) -> pd.DataFrame:
    """Build a station-level HDD/CDD summary for every EPW file."""
    manager = WeatherStationManager(weather_root)
    rows: List[Dict[str, object]] = []

    for station in sorted(manager.list_all_stations(), key=lambda item: (item.region_code, item.station_name, item.display_name)):
        if not station.epw_file_path:
            continue

        metadata, weather_df = EPWParser.read_epw(str(station.epw_file_path))
        degree_days = compute_degree_days(weather_df)

        rows.append(
            {
                'Region_Code': station.region_code,
                'Region_Name': station.region_name,
                'Station_Name': station.station_name,
                'Station_Local_Name': station.station_local_name,
                'Display_Name': station.display_name,
                'EPW_File': station.epw_file_path.name,
                'Latitude': metadata.get('Latitude'),
                'Longitude': metadata.get('Longitude'),
                'Altitude': metadata.get('Altitude'),
                **degree_days,
            }
        )

    summary_df = pd.DataFrame(rows)
    if summary_df.empty:
        raise RuntimeError(f'No EPW files were found under {weather_root}')

    summary_df = summary_df.sort_values(['Region_Code', 'Station_Name', 'Display_Name']).reset_index(drop=True)
    return summary_df


def build_region_summary(station_summary: pd.DataFrame) -> pd.DataFrame:
    """Aggregate station-level HDD/CDD to region-level statistics."""
    grouped = (
        station_summary.groupby(['Region_Code', 'Region_Name'], as_index=False)
        .agg(
            Station_Count=('Display_Name', 'count'),
            HDD_mean=('HDD_base20', 'mean'),
            HDD_min=('HDD_base20', 'min'),
            HDD_max=('HDD_base20', 'max'),
            CDD_mean=('CDD_base26', 'mean'),
            CDD_min=('CDD_base26', 'min'),
            CDD_max=('CDD_base26', 'max'),
        )
    )

    return grouped.sort_values(['Region_Code']).reset_index(drop=True)


def write_markdown_summary(station_summary: pd.DataFrame, region_summary: pd.DataFrame, output_path: Path) -> None:
    """Write a human-readable summary document."""
    total_stations = len(station_summary)
    total_regions = len(region_summary)

    hottest_station = station_summary.sort_values('CDD_base26', ascending=False).iloc[0]
    coldest_station = station_summary.sort_values('HDD_base20', ascending=False).iloc[0]
    warmest_region = region_summary.sort_values('CDD_mean', ascending=False).iloc[0]
    coldest_region = region_summary.sort_values('HDD_mean', ascending=False).iloc[0]

    def render_markdown_table(df: pd.DataFrame) -> List[str]:
        headers = list(df.columns)
        rows = [headers, ['---' for _ in headers]]
        for _, row in df.iterrows():
            rows.append([str(row[col]) for col in headers])
        return ['| ' + ' | '.join(row) + ' |' for row in rows]

    lines = [
        '# HDD/CDD Summary',
        '',
        'This document summarizes the batch calculation results for all EPW weather stations under data/weather.',
        '',
        '## Method',
        '',
        f'- Heating base temperature: {BASE_HEATING_TEMP:.1f} °C',
        f'- Cooling base temperature: {BASE_COOLING_TEMP:.1f} °C',
        '- Formula: HDD = sum(max(0, T_base_h - T_out,h)) / 24',
        '- Formula: CDD = sum(max(0, T_out,h - T_base_c)) / 24',
        '- Input data: hourly dry-bulb temperature from each station EPW file',
        '',
        '## Coverage',
        '',
        f'- Regions processed: {total_regions}',
        f'- Stations processed: {total_stations}',
        '',
        '## Extremes',
        '',
        f'- Highest HDD station: {coldest_station["Display_Name"]} ({coldest_station["HDD_base20"]:.2f})',
        f'- Highest CDD station: {hottest_station["Display_Name"]} ({hottest_station["CDD_base26"]:.2f})',
        f'- Coldest region by mean HDD: {coldest_region["Region_Code"]} ({coldest_region["HDD_mean"]:.2f})',
        f'- Warmest region by mean CDD: {warmest_region["Region_Code"]} ({warmest_region["CDD_mean"]:.2f})',
        '',
        '## Region Aggregate Preview',
        '',
    ] + render_markdown_table(region_summary) + [
        '',
    ]

    output_path.write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    project_root = PROJECT_ROOT
    weather_root = project_root / 'data' / 'weather'
    output_csv = project_root / 'data' / 'HDD_CDD_Summary.csv'
    output_md = project_root / 'data' / 'HDD_CDD_Summary.md'
    output_region_csv = project_root / 'data' / 'HDD_CDD_Region_Summary.csv'

    station_summary = build_station_summary(weather_root)
    region_summary = build_region_summary(station_summary)

    station_summary.to_csv(output_csv, index=False, encoding='utf-8-sig')
    region_summary.to_csv(output_region_csv, index=False, encoding='utf-8-sig')
    write_markdown_summary(station_summary, region_summary, output_md)

    print(f'Wrote station summary: {output_csv}')
    print(f'Wrote region summary: {output_region_csv}')
    print(f'Wrote markdown summary: {output_md}')


if __name__ == '__main__':
    main()