# Base Parameter Registry   -- Source from UNI EN 16798-1 ANNEX C
# Unit - W/m² (Conversion result based on ASHRAE 90.1 )

BASE_PARAMS = {
    "Educational building": {
        "name": "Sch",
        "components": {
            "Lighting": 7.75,     # ASHRAE School/university 0.72 W/ft2
            "Appliances": 8.0,
            "Occ_Total": 21.7,  # W/m2 (Occupants Total)
            "Occ_Dry": 13.8,  # W/m2 (Occupants Dry)
            "Density": 5.4  # m2/pers
        },
    },
    "Commercial building": {
        "name": "DepStore",
        "components": {
            "Lighting": 9.04,     # ASHRAE Retail 0.84
            "Appliances": 8.0,  # 1.0 in EN 16798-1-2019
            "Occ_Total": 9.3,
            "Occ_Dry": 4.5,
            "Density": 17.0
        },
    },
    "Office building": {
        "name": "OfficeSingle",
        "components": {
            "Lighting": 6.89,     # ASHRAE Office 0.64
            "Appliances": 12.0,
            "Occ_Total": 11.8,
            "Occ_Dry": 8.0,
            "Density": 10.0
        },
    },
    "ResidentialApartment": {
        "name": "ReApart",
        "components": {
            "Lighting": 4.84,     # ASHRAE Multifamily 0.45
            "Appliances": 3.0,
            "Occ_Total": 4.2,
            "Occ_Dry": 2.8,
            "Density": 28.3
        },
    },
}


