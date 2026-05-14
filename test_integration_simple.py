"""
集成测试脚本 (简化版)
====================

验证气象数据提取、加载、计算的完整流程

运行: python test_integration_simple.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import pandas as pd
from epw_parser import EPWParser
from weather_station_manager import WeatherStationManager
from archetype_data import ArchetypeDataManager
from load_model import LoadModel
from pv_model import PVModel
from matching_algorithm import MatchingAlgorithm


def main():
    print("\n" + "="*60)
    print("  Weather Data Integration Test")
    print("="*60)
    
    # 1. Test weather station manager
    print("\n[1] Testing Weather Station Manager...")
    try:
        manager = WeatherStationManager()
        regions = manager.get_regions_with_names()
        print(f"    - Found {len(regions)} regions")
        
        ab_stations = manager.get_stations_by_region('AB')
        print(f"    - AB region has {len(ab_stations)} weather stations:")
        for st in ab_stations:
            print(f"      * {st.display_name}")
        
        catalog = manager.export_station_catalog()
        print(f"    - Total stations in catalog: {len(catalog)}")
        
    except Exception as e:
        print(f"    ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Test EPW parsing
    print("\n[2] Testing EPW Parser...")
    try:
        all_stations = manager.list_all_stations()
        station = all_stations[0]
        print(f"    - Parsing: {station.display_name}")
        
        metadata, weather_df = EPWParser.read_epw(str(station.epw_file_path))
        print(f"    - Data shape: {weather_df.shape}")
        print(f"    - Columns: {list(weather_df.columns)[:5]}...")
        
        validation = EPWParser.validate_data_completeness(weather_df)
        print(f"    - Total rows: {validation['total_rows']} (expected: {validation['expected_rows']})")
        print(f"    - Complete: {'YES' if validation['is_complete'] else 'NO'}")
        print(f"    - Quality score: {validation['data_quality_score']:.1f}/100")
        
        # Show sample data
        print(f"    - Sample data:")
        for col in ['T_Drybulb', 'RH', 'Radiation_Global_Horizontal']:
            if col in weather_df.columns:
                print(f"      {col}: mean={weather_df[col].mean():.2f}, min={weather_df[col].min():.2f}, max={weather_df[col].max():.2f}")
        
    except Exception as e:
        print(f"    ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Test archetype data
    print("\n[3] Testing Archetype Data...")
    try:
        arch_manager = ArchetypeDataManager()
        regions = arch_manager.list_available_regions()
        ages = arch_manager.list_available_ages()
        types = arch_manager.list_available_types()
        
        print(f"    - Regions: {len(regions)} total")
        print(f"    - Ages: {len(ages)} total")
        print(f"    - Types: {len(types)} total")
        
        params = arch_manager.get_archetype_params('Piemonte', '>2005', 'Office' if 'Office' in types else types[0])
        print(f"    - Loaded parameters for Piemonte >2005")
        print(f"      U_value: {params['U_value']}")
        print(f"      P_light: {params['P_light']}")
        print(f"      COP_heat: {params['COP_heat']}")
        
    except Exception as e:
        print(f"    ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Test calculation
    print("\n[4] Testing Calculation Pipeline...")
    try:
        # Building parameters
        params = arch_manager.get_archetype_params('Piemonte', '>2005', types[0])
        building_area = 100.0
        
        # Schedule
        schedule_df = pd.DataFrame({
            'Hour': list(range(24)),
            'Occupancy': [0]*8 + [1]*9 + [0]*7,
            'Lighting': [0]*8 + [0.8]*9 + [0.2]*7,
            'Appliance': [0.1]*8 + [0.8]*9 + [0.1]*7
        })
        
        # Prepare weather data
        weather_calc = weather_df.rename(columns={
            'T_Drybulb': 'T_amb',
            'Radiation_Global_Horizontal': 'GHI',
            'Radiation_Diffuse_Horizontal': 'Diffuse'
        })
        if 'DateTime' in weather_calc.columns and 'Timestamp' not in weather_calc.columns:
            weather_calc['Timestamp'] = weather_calc['DateTime']
        
        # Calculate load
        print("    - Calculating building load...")
        load_model = LoadModel(params, building_area)
        load_results = load_model.calculate_hourly_load(weather_calc, schedule_df)
        load_summary = load_model.get_summary_statistics()
        
        print(f"      Annual consumption: {load_summary['annual_total_kwh']:.1f} kWh")
        print(f"      Average power: {load_summary['annual_avg_kw']:.2f} kW")
        print(f"      Peak power: {load_summary['peak_load_kw']:.2f} kW")
        
        # Calculate PV generation
        print("    - Calculating PV generation...")
        pv_model = PVModel(45.2, 7.7, 10.0, 35.0)
        pv_results = pv_model.calculate_hourly_generation(weather_calc)
        pv_summary = pv_model.get_summary_statistics()
        
        print(f"      Annual generation: {pv_summary['annual_total_kwh']:.1f} kWh")
        print(f"      Utilization hours: {pv_summary['utilization_hours']:.0f} h")
        print(f"      System efficiency: {pv_summary['system_efficiency']:.2f}%")
        
        # Calculate matching
        print("    - Calculating energy matching...")
        matching = MatchingAlgorithm()
        matching_results = matching.calculate_matching(load_results, pv_results)
        matching_summary = matching.get_annual_statistics()
        
        print(f"      Coverage rate: {matching_summary['coverage_rate_percent']:.1f}%")
        print(f"      Annual surplus: {matching_summary['annual_surplus_kwh']:.1f} kWh")
        print(f"      Annual deficit: {matching_summary['annual_deficit_kwh']:.1f} kWh")
        
    except Exception as e:
        print(f"    ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Success
    print("\n" + "="*60)
    print("  ALL TESTS PASSED!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Run: streamlit run app.py")
    print("  2. Open browser and select weather stations")
    print("  3. Configure building parameters")
    print("  4. Click 'Update Calculation' button")


if __name__ == '__main__':
    main()
