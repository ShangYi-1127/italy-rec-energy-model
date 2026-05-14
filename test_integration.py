"""
集成测试脚本
===========

验证气象数据提取、加载、计算的完整流程

运行方法:
python test_integration.py
"""

import sys
from pathlib import Path

# 添加后端模块路径
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import pandas as pd
from epw_parser import EPWParser
from weather_station_manager import WeatherStationManager
from archetype_data import ArchetypeDataManager
from load_model import LoadModel
from pv_model import PVModel
from matching_algorithm import MatchingAlgorithm


def print_section(title):
    """打印带下划线的标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_weather_station_manager():
    """测试气象站管理系统"""
    print_section("1. 气象站管理系统测试")
    
    manager = WeatherStationManager()
    
    # 获取所有可用地区
    regions = manager.get_regions_with_names()
    print(f"\n✓ 找到 {len(regions)} 个地区:")
    for code, name in list(regions.items())[:5]:
        print(f"  - {code}: {name}")
    print(f"  ... 等等")
    
    # 获取AB地区的气象站
    ab_stations = manager.get_stations_by_region('AB')
    print(f"\n✓ AB (Abruzzi) 地区有 {len(ab_stations)} 个气象站:")
    for station in ab_stations:
        print(f"  - {station.display_name}")
    
    # 导出目录
    catalog = manager.export_station_catalog()
    print(f"\n✓ 气象站目录:")
    print(catalog.head(10).to_string())
    print(f"... 共 {len(catalog)} 个气象站")
    
    return manager


def test_epw_parser(manager):
    """测试EPW文件解析"""
    print_section("2. EPW文件解析测试")
    
    # 选择第一个可用的气象站
    all_stations = manager.list_all_stations()
    if not all_stations:
        print("❌ 未找到任何气象站")
        return None
    
    station = all_stations[0]
    print(f"\n选择气象站: {station.display_name}")
    print(f"EPW文件: {station.epw_file_path}")
    
    try:
        # 解析EPW文件
        metadata, weather_df = EPWParser.read_epw(str(station.epw_file_path))
        
        print(f"\n✓ 元数据:")
        for key, value in metadata.items():
            print(f"  - {key}: {value}")
        
        # 数据质量检查
        validation = EPWParser.validate_data_completeness(weather_df)
        print(f"\n✓ 数据质量检查:")
        print(f"  - 总行数: {validation['total_rows']} (期望: {validation['expected_rows']})")
        print(f"  - 数据完整: {'✓' if validation['is_complete'] else '✗'}")
        print(f"  - 质量评分: {validation['data_quality_score']:.1f}/100")
        
        # 显示数据摘要
        print(f"\n✓ 气象数据摘要:")
        for col in ['T_Drybulb', 'RH', 'Radiation_Global_Horizontal', 'Wind_Speed']:
            if col in weather_df.columns:
                print(f"  - {col}:")
                print(f"      均值: {weather_df[col].mean():.2f}")
                print(f"      最小: {weather_df[col].min():.2f}")
                print(f"      最大: {weather_df[col].max():.2f}")
        
        print(f"\n✓ 数据前5行:")
        print(weather_df.head().to_string())
        
        return weather_df
        
    except Exception as e:
        print(f"❌ EPW解析失败: {str(e)}")
        return None


def test_archetype_data():
    """测试建筑原型库"""
    print_section("3. 建筑原型库测试")
    
    manager = ArchetypeDataManager()
    
    regions = manager.list_available_regions()
    ages = manager.list_available_ages()
    types = manager.list_available_types()
    
    print(f"\n✓ 可用地区: {len(regions)}")
    for region in list(regions)[:3]:
        print(f"  - {region}")
    print(f"  ... 等等")
    
    print(f"\n✓ 可用年代: {len(ages)}")
    for age in ages:
        print(f"  - {age}")
    
    print(f"\n✓ 可用类型: {len(types)}")
    for btype in types:
        print(f"  - {btype}")
    
    # 获取示例参数
    params = manager.get_archetype_params('Piemonte', '<1919', '住宅')
    print(f"\n✓ Piemonte <1919 住宅 的参数:")
    for key, value in params.items():
        print(f"  - {key}: {value}")
    
    return manager


def test_calculation(weather_df, archetype_manager):
    """测试完整的能耗和发电计算"""
    print_section("4. 能耗和发电计算测试")
    
    # 建筑参数
    params = archetype_manager.get_archetype_params('Piemonte', '>2005', '办公')
    building_area = 100.0  # m²
    
    # 时间表 (简化示例)
    schedule_df = pd.DataFrame({
        'Hour': list(range(24)),
        'Occupancy': [0]*8 + [1]*9 + [0]*7,
        'Lighting': [0]*8 + [0.8]*9 + [0.2]*7,
        'Appliance': [0.1]*8 + [0.8]*9 + [0.1]*7
    })
    
    print(f"\n建筑参数:")
    print(f"  - 地区: Piemonte")
    print(f"  - 年代: >2005")
    print(f"  - 类型: 办公")
    print(f"  - 面积: {building_area} m²")
    
    # 1. 能耗计算
    print(f"\n计算耗电量...")
    load_model = LoadModel(params, building_area)
    
    # 确保天气数据有正确的列名
    weather_calc = weather_df.rename(columns={
        'T_Drybulb': 'T_amb' if 'T_Drybulb' in weather_df.columns else 'T_amb',
        'Radiation_Global_Horizontal': 'GHI' if 'Radiation_Global_Horizontal' in weather_df.columns else 'GHI',
        'Radiation_Diffuse_Horizontal': 'Diffuse' if 'Radiation_Diffuse_Horizontal' in weather_df.columns else 'Diffuse'
    })
    
    # 确保有Timestamp列
    if 'Timestamp' not in weather_calc.columns and 'DateTime' in weather_calc.columns:
        weather_calc['Timestamp'] = weather_calc['DateTime']
    elif 'Timestamp' not in weather_calc.columns:
        print("⚠️ 警告: Timestamp列不存在")
    
    load_results = load_model.calculate_hourly_load(weather_calc, schedule_df)
    load_summary = load_model.get_summary_statistics()
    
    print(f"✓ 能耗计算完成:")
    print(f"  - 年总耗电量: {load_summary['annual_total_kwh']:.1f} kWh")
    print(f"  - 年平均功率: {load_summary['annual_avg_kw']:.2f} kW")
    print(f"  - 峰值功率: {load_summary['peak_load_kw']:.2f} kW")
    print(f"  - 谷值功率: {load_summary['min_load_kw']:.2f} kW")
    
    # 2. PV发电计算
    print(f"\n计算光伏发电...")
    pv_capacity = 10.0  # kW
    pv_tilt = 35.0  # 度
    latitude = 45.2  # Piemonte
    longitude = 7.7
    
    pv_model = PVModel(latitude, longitude, pv_capacity, pv_tilt)
    pv_results = pv_model.calculate_hourly_generation(weather_calc)
    pv_summary = pv_model.get_summary_statistics()
    
    print(f"✓ 发电计算完成:")
    print(f"  - 年发电量: {pv_summary['annual_total_kwh']:.1f} kWh")
    print(f"  - 利用小时数: {pv_summary['utilization_hours']:.0f} h")
    print(f"  - 系统效率: {pv_summary['system_efficiency']:.2f} %")
    
    # 3. 匹配分析
    print(f"\n计算能量匹配...")
    matching = MatchingAlgorithm()
    matching_results = matching.calculate_matching(load_results, pv_results)
    matching_summary = matching.get_annual_statistics()
    
    print(f"✓ 匹配分析完成:")
    print(f"  - 覆盖率: {matching_summary['coverage_rate_percent']:.1f} %")
    print(f"  - 年剩余电量: {matching_summary['annual_surplus_kwh']:.1f} kWh")
    print(f"  - 年缺电量: {matching_summary['annual_deficit_kwh']:.1f} kWh")
    
    return load_results, pv_results, matching_results


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  气象数据集成测试")
    print("="*60)
    
    # 1. 测试气象站管理器
    try:
        weather_manager = test_weather_station_manager()
    except Exception as e:
        print(f"❌ 气象站管理器测试失败: {str(e)}")
        return
    
    # 2. 测试EPW解析
    try:
        weather_df = test_epw_parser(weather_manager)
        if weather_df is None:
            print("⚠️ 跳过后续测试")
            return
    except Exception as e:
        print(f"❌ EPW解析测试失败: {str(e)}")
        return
    
    # 3. 测试原型库
    try:
        archetype_manager = test_archetype_data()
    except Exception as e:
        print(f"❌ 原型库测试失败: {str(e)}")
        return
    
    # 4. 测试计算
    try:
        load_results, pv_results, matching_results = test_calculation(weather_df, archetype_manager)
    except Exception as e:
        print(f"❌ 计算测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 完成
    print_section("测试总结")
    print("\n✓ 所有测试完成！")
    print("\n接下来:")
    print("  1. 运行 Streamlit 应用: streamlit run app.py")
    print("  2. 在浏览器中打开应用界面")
    print("  3. 选择气象地区和建筑参数进行模拟")


if __name__ == '__main__':
    main()
