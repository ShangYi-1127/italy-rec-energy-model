"""
气象站数据管理系统
==============

功能：
- 自动扫描所有天气数据文件夹
- 规范化长文件夹名称为简化显示名称
- 管理地区-气象站映射关系
- 获取特定地区的所有可用气象站
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class WeatherStation:
    """气象站数据类"""
    region_code: str          # 如 'AB'
    region_name: str          # 如 'Abruzzi'
    station_name: str         # 如 'Fucino', 'Pescara'
    station_local_name: str   # 本地名称
    latitude: float           # 纬度
    longitude: float          # 经度
    altitude: float           # 海拔
    folder_path: Path         # 文件夹完整路径
    epw_file_path: Optional[Path] = None  # EPW文件路径
    
    @property
    def display_name(self) -> str:
        """页面展示名称: ITA_AB_Pescara.Abruzzo"""
        return f"ITA_{self.region_code}_{self.station_name}.{self.region_name}"
    
    @property
    def short_name(self) -> str:
        """简短名称: Pescara"""
        return self.station_name


class WeatherStationManager:
    """气象站管理器"""
    
    # 意大利地区编码映射
    REGION_MAPPING = {
        'AB': ('Abruzzi', 'Abruzzo'),
        'BC': ('Basilicata', 'Basilicata'),
        'CM': ('Campania', 'Campania'),
        'ER': ('Emilia-Romagna', 'Emilia-Romagna'),
        'FV': ('Friuli-Venezia_Giulia', 'Friuli-Venezia Giulia'),
        'LB': ('Calabria', 'Calabria'),
        'LG': ('Liguria', 'Liguria'),
        'LM': ('Lombardy', 'Lombardy'),
        'LZ': ('Lazio', 'Lazio'),
        'MH': ('Marche', 'Marche'),
        'ML': ('Molise', 'Molise'),
        'PM': ('Piedmont', 'Piedmont'),
        'PU': ('Apulia', 'Apulia'),
        'SC': ('Sicily', 'Sicily'),
        'SD': ('Sardinia', 'Sardinia'),
        'TC': ('Tuscany', 'Tuscany'),
        'TT': ('Trentino-Alto_Adige', 'Trentino-Alto Adige'),
        'UM': ('Umbria', 'Umbria'),
        'VD': ('Valle_d-Aosta', "Valle d'Aosta"),
        'VN': ('Veneto', 'Veneto'),
    }
    
    def __init__(self, weather_data_root: str = None):
        """
        初始化气象站管理器
        
        参数:
            weather_data_root: 天气数据根目录路径
        """
        if weather_data_root is None:
            # 默认路径
            weather_data_root = Path(__file__).parent.parent / 'data' / 'weather'
        
        self.weather_root = Path(weather_data_root)
        self.stations: Dict[str, WeatherStation] = {}  # 按display_name索引
        self.region_stations: Dict[str, List[WeatherStation]] = {}  # 按地区索引
        
        # 初始化：扫描所有气象站
        self._scan_stations()
    
    def _scan_stations(self):
        """扫描weather_root下的所有气象站文件夹"""
        
        if not self.weather_root.exists():
            print(f"Warning: weather data path does not exist: {self.weather_root}")
            return
        
        # 遍历所有地区文件夹
        for region_folder in sorted(self.weather_root.iterdir()):
            if not region_folder.is_dir():
                continue
            
            region_folder_name = region_folder.name  # 如 'AB_Abruzzi'
            
            # 提取地区代码
            region_code = self._extract_region_code(region_folder_name)
            if not region_code:
                continue
            
            # 获取地区英文名称
            if region_code not in self.REGION_MAPPING:
                print(f"Warning: unknown region code: {region_code}")
                continue
            
            _, region_name_en = self.REGION_MAPPING[region_code]
            
            # 遍历该地区下的所有气象站文件夹
            station_list = []
            for station_folder in sorted(region_folder.iterdir()):
                if not station_folder.is_dir():
                    continue
                
                # 解析气象站名称
                station_info = self._parse_station_folder(
                    station_folder,
                    region_code,
                    region_name_en
                )
                
                if station_info:
                    self.stations[station_info.display_name] = station_info
                    station_list.append(station_info)
            
            if station_list:
                self.region_stations[region_code] = station_list
    
    @staticmethod
    def _extract_region_code(folder_name: str) -> Optional[str]:
        """
        从文件夹名称中提取地区代码
        
        例: 'AB_Abruzzi' -> 'AB'
        """
        match = re.match(r'^([A-Z]{2})', folder_name)
        return match.group(1) if match else None
    
    @staticmethod
    def _parse_station_folder(station_folder: Path, region_code: str, region_name: str) -> Optional[WeatherStation]:
        """
        解析气象站文件夹
        
        文件夹名称格式:
        - ITA_AB_Fucino.162270_TMYx.2011-2025
        - ITA_AB_Pescara.Abruzzo.AP.162300_TMYx.2011-2025 (1)
        """
        folder_name = station_folder.name
        
        # 规范化名称（移除后缀如 " (1)", " (2)" 等）
        clean_name = re.sub(r'\s+\(\d+\)$', '', folder_name)
        
        # 兼容更复杂的站点命名：
        # ITA_AB_Pescara.Abruzzo.AP.162300_TMYx.2011-2025
        # ITA_FV_Trieste-Friuli.Venezia.Guilia.AP.161080_TMYx.2011-2025
        match = re.match(r'^ITA_[A-Z]{2}_(?P<station_part>.+?)\.(?P<station_code>\d+)_TMYx(?:\..+)?$', clean_name)
        if not match:
            print(f"Warning: unable to parse station folder name: {clean_name}")
            return None

        station_part = match.group('station_part')
        station_code = match.group('station_code')
        station_name = station_part.split('.')[0]
        station_local_name = station_part
        
        # 查找EPW文件
        epw_files = list(station_folder.glob('*.epw'))
        if not epw_files:
            print(f"Warning: no EPW file found in {station_folder}")
            return None
        
        epw_file = epw_files[0]
        
        # 创建WeatherStation对象
        station = WeatherStation(
            region_code=region_code,
            region_name=region_name,
            station_name=station_name,
            station_local_name=station_local_name,
            latitude=0.0,  # 从EPW元数据中提取
            longitude=0.0,
            altitude=0.0,
            folder_path=station_folder,
            epw_file_path=epw_file
        )
        
        return station
    
    def get_regions(self) -> List[str]:
        """获取所有可用的地区代码"""
        return sorted(self.region_stations.keys())
    
    def get_regions_with_names(self) -> Dict[str, str]:
        """获取所有地区的代码和英文名称"""
        result = {}
        for code in self.get_regions():
            if code in self.REGION_MAPPING:
                _, name = self.REGION_MAPPING[code]
                result[code] = name
        return result
    
    def get_stations_by_region(self, region_code: str) -> List[WeatherStation]:
        """获取指定地区的所有气象站"""
        return self.region_stations.get(region_code, [])
    
    def get_station_display_names_by_region(self, region_code: str) -> List[str]:
        """获取指定地区的所有气象站显示名称"""
        stations = self.get_stations_by_region(region_code)
        return [s.display_name for s in stations]
    
    def get_station_by_display_name(self, display_name: str) -> Optional[WeatherStation]:
        """通过显示名称获取气象站"""
        return self.stations.get(display_name)
    
    def get_epw_file_path(self, display_name: str) -> Optional[Path]:
        """获取指定气象站的EPW文件路径"""
        station = self.get_station_by_display_name(display_name)
        return station.epw_file_path if station else None
    
    def list_all_stations(self) -> List[WeatherStation]:
        """列出所有气象站"""
        return list(self.stations.values())
    
    def export_station_catalog(self) -> pd.DataFrame:
        """导出气象站目录为DataFrame"""
        data = []
        for station in self.list_all_stations():
            data.append({
                'Region_Code': station.region_code,
                'Region_Name': station.region_name,
                'Station_Name': station.station_name,
                'Display_Name': station.display_name,
                'EPW_File': station.epw_file_path.name if station.epw_file_path else None,
                'Folder_Path': str(station.folder_path)
            })
        
        return pd.DataFrame(data).sort_values(['Region_Code', 'Station_Name'])


if __name__ == '__main__':
    # 测试示例
    manager = WeatherStationManager()
    
    print("=== 可用的地区 ===")
    regions = manager.get_regions_with_names()
    for code, name in regions.items():
        print(f"{code}: {name}")
    
    print("\n=== AB地区的气象站 ===")
    ab_stations = manager.get_stations_by_region('AB')
    for station in ab_stations:
        print(f"  - {station.display_name}")
    
    print("\n=== 气象站目录 ===")
    catalog = manager.export_station_catalog()
    print(catalog.to_string())
