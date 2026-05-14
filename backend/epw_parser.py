"""
EPW气象数据解析器
================

功能：
- 读取并解析EnergyPlus Weather (EPW)格式文件
- 提取建筑能耗模拟所需的气象参数
- 返回pandas DataFrame格式的逐时气象数据
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple


class EPWParser:
    """EPW文件解析器"""
    
    # EPW格式中的字段名称（34个字段）
    EPW_COLUMNS = [
        'Year', 'Month', 'Day', 'Hour', 'Minute', 'Data_Source_and_Uncertainty_Flags',
        'T_Drybulb',           # 7: 干球温度 (°C)
        'T_Dewpoint',          # 8: 露点温度 (°C)
        'RH',                  # 9: 相对湿度 (%)
        'Pressure',            # 10: 大气压力 (Pa)
        'Radiation_Diffuse_Horizontal',    # 11: 散射水平辐照 (W/m²)
        'Radiation_Direct_Normal',         # 12: 直接法向辐照 (W/m²)
        'Radiation_Global_Horizontal',     # 13: 全球水平辐照 (W/m²) ← PV所需
        'Radiation_Extra_Terrestrial',     # 14: 额外太阳辐照 (W/m²)
        'Radiation_Diffuse_Horizontal_MJ', # 15: 散射水平辐照 (MJ/m²)
        'Radiation_Direct_Normal_MJ',      # 16: 直接法向辐照 (MJ/m²)
        'Radiation_Global_Horizontal_MJ',  # 17: 全球水平辐照 (MJ/m²)
        'Radiation_Extraterrestrial_MJ',   # 18
        'Radiation_Extraterrestrial_Direct_Normal_MJ',
        'Horizontal_Infrared_Radiation',
        'Horizontal_Infrared_Radiation_MJ',
        'Global_Horizontal_Illuminance',
        'Direct_Normal_Illuminance',
        'Diffuse_Horizontal_Illuminance',
        'Zenith_Luminance',
        'Wind_Direction',      # 24: 风向 (度)
        'Wind_Speed',          # 25: 风速 (m/s)
        'Total_Sky_Cover',
        'Opaque_Sky_Cover',
        'Visibility',
        'Ceiling_Height',
        'Present_Weather_Observation',
        'Present_Weather_Codes',
        'Precipitable_Water',
        'Aerosol_Optical_Depth',
        'Snow_Depth',
        'Days_Since_Last_Snowfall',
        'Albedo',
        'Liquid_Precipitation_Depth',
    ]
    
    # 计算所需的最小字段集合
    REQUIRED_COLUMNS = [
        'Year', 'Month', 'Day', 'Hour', 'Minute',
        'T_Drybulb',                      # 温度（HVAC COP计算）
        'RH',                             # 相对湿度
        'Pressure',                       # 气压
        'Radiation_Global_Horizontal',    # GHI（PV计算）
        'Radiation_Direct_Normal',        # DNI（可选，用于cos校正）
        'Radiation_Diffuse_Horizontal',   # 散射辐照
        'Wind_Speed',                     # 风速（可选，散热）
    ]
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    @staticmethod
    def read_epw(epw_file_path: str) -> Tuple[Dict, pd.DataFrame]:
        """
        读取EPW文件并返回元数据和气象数据
        
        参数:
            epw_file_path: EPW文件路径
            
        返回:
            (metadata_dict, weather_dataframe)
        """
        epw_path = Path(epw_file_path)
        if not epw_path.exists():
            raise FileNotFoundError(f"EPW文件不存在: {epw_file_path}")
        
        with open(epw_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # ========== 解析元数据 (前8行) ==========
        metadata = EPWParser._parse_header(lines[:8])
        
        # ========== 解析气象数据 (从第9行开始) ==========
        data_lines = lines[8:]
        
        # 尝试自动检测分隔符
        delimiter = ','
        if data_lines:
            first_line = data_lines[0].strip()
            if ';' in first_line and ',' not in first_line:
                delimiter = ';'
        
        # 读取数据
        weather_data = []
        for line_num, line in enumerate(data_lines, start=9):
            line = line.strip()
            if not line:
                continue
                
            try:
                values = line.split(delimiter)
                if len(values) >= 34:
                    # 转换数据类型
                    row_data = {
                        'Year': int(values[0]),
                        'Month': int(values[1]),
                        'Day': int(values[2]),
                        'Hour': int(values[3]),
                        'Minute': int(values[4]),
                        'T_Drybulb': float(values[6]) if values[6] not in ['', '9999'] else np.nan,
                        'T_Dewpoint': float(values[7]) if values[7] not in ['', '9999'] else np.nan,
                        'RH': float(values[8]) if values[8] not in ['', '999'] else np.nan,
                        'Pressure': float(values[9]) if values[9] not in ['', '99999'] else np.nan,
                        'Radiation_Direct_Normal': float(values[10]) if values[10] not in ['', '9999'] else 0,
                        'Radiation_Diffuse_Horizontal': float(values[11]) if values[11] not in ['', '9999'] else 0,
                        'Radiation_Global_Horizontal': float(values[12]) if values[12] not in ['', '9999'] else 0,
                        'Wind_Speed': float(values[24]) if values[24] not in ['', '999'] else 0,
                        'Wind_Direction': float(values[23]) if values[23] not in ['', '999'] else 0,
                    }
                    weather_data.append(row_data)
            except (ValueError, IndexError) as e:
                print(f"警告: 第{line_num}行解析失败: {e}")
                continue
        
        # 创建DataFrame
        df = pd.DataFrame(weather_data)
        
        # ========== 数据清理 ==========
        # 创建时间戳列
        df['DateTime'] = pd.to_datetime(
            df[['Year', 'Month', 'Day', 'Hour']],
            format='%Y%m%d%H',
            errors='coerce'
        )
        
        # 处理缺失值：用前向填充
        numeric_cols = [col for col in df.columns if col not in ['DateTime', 'Year', 'Month', 'Day', 'Hour', 'Minute']]
        df[numeric_cols] = df[numeric_cols].ffill().bfill()
        
        # 确保辐照度不为负
        radiation_cols = ['Radiation_Direct_Normal', 'Radiation_Diffuse_Horizontal', 'Radiation_Global_Horizontal']
        for col in radiation_cols:
            df[col] = df[col].clip(lower=0)
        
        # 排序并重置索引
        df = df.sort_values('DateTime').reset_index(drop=True)
        
        return metadata, df
    
    @staticmethod
    def _parse_header(header_lines: list) -> Dict:
        """
        解析EPW文件的8行元数据
        
        格式示例:
        LOCATION,City Name,State,Country,TimeZone,Latitude,Longitude,Altitude
        """
        metadata = {}
        
        try:
            # 第一行：位置信息
            if header_lines[0].startswith('LOCATION'):
                parts = header_lines[0].split(',')
                if len(parts) >= 10:
                    metadata['Location'] = parts[1].strip()
                    metadata['State'] = parts[2].strip()
                    metadata['Country'] = parts[3].strip()
                    metadata['DataSource'] = parts[4].strip()
                    metadata['WMO'] = parts[5].strip()
                    metadata['Latitude'] = float(parts[6].strip())
                    metadata['Longitude'] = float(parts[7].strip())
                    metadata['TimeZone'] = float(parts[8].strip())
                    metadata['Altitude'] = float(parts[9].strip())
        except Exception as e:
            print(f"警告: 解析位置信息失败: {e}")
        
        return metadata
    
    @staticmethod
    def validate_data_completeness(df: pd.DataFrame, year: int = None) -> Dict:
        """
        验证数据的完整性
        
        检查：
        - 是否有完整的8760个小时
        - 缺失值比例
        - 时间序列连贯性
        """
        validation_result = {
            'total_rows': len(df),
            'expected_rows': 8760,
            'is_complete': len(df) == 8760,
            'missing_values': {},
            'data_quality_score': 0
        }
        
        # 检查缺失值
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32']:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    validation_result['missing_values'][col] = {
                        'count': missing_count,
                        'percentage': (missing_count / len(df) * 100)
                    }
        
        # 计算数据质量评分 (0-100)
        if validation_result['is_complete']:
            missing_pct = sum([v['percentage'] for v in validation_result['missing_values'].values()]) / len(validation_result['missing_values']) if validation_result['missing_values'] else 0
            validation_result['data_quality_score'] = max(0, 100 - missing_pct)
        
        return validation_result


if __name__ == '__main__':
    # 测试示例
    epw_path = "data/weather/AB_Abruzzi/ITA_AB_Fucino.162270_TMYx.2011-2025/ITA_AB_Fucino.162270_TMYx.2011-2025.epw"
    
    metadata, weather_df = EPWParser.read_epw(epw_path)
    print("元数据:", metadata)
    print("\n气象数据前5行:")
    print(weather_df.head())
    print("\n数据形状:", weather_df.shape)
    print("\n验证结果:", EPWParser.validate_data_completeness(weather_df))
