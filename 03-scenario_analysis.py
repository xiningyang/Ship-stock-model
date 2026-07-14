# -*- coding: utf-8 -*-
"""
The model was developed by Dr. Xining Yang

"""

import os
add=str(os.getcwd()).replace('\\', '/').replace('01-script', '')
print(add)

import pandas as pd
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
import numpy as np
import time as tm

import ship_stock_model as ssm

start = tm.perf_counter()

############# load ship data ###########################################################################################################################################################################################

scenario_data=pd.read_excel(add + '02-data sources/ship_stock_yxn/SSP-based_demand_v08012026_yxn.xlsx')

ship_type_list=list(scenario_data['Ship_type'].unique())

############# Scenarios and strategies ###########################################################################################################################################################################################

start_year=2025
end_year=2100

scenario_list=sorted(scenario_data.Scenario.unique())
print('\nDiogo SSP scenarios:',scenario_list)

scenario_list_SSP1345_baseline=[i for i in scenario_list if 'Baseline' in i and 'SSP2' not in i]
scenario_list_SSP2_baseline=[i for i in scenario_list if 'SSP2' in i and 'Baseline' in i]
scenario_list_SSP2_26_19=[i for i in scenario_list if 'SSP2' in i and ('26' in i or '19' in i)]

print(scenario_list_SSP2_26_19)

strategy_template_SSP1345_baseline = {
                      'Reference': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
                      'Reference_Low': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
                      'Reference_High': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0}
                      }

strategy_template_SSP2_baseline = {
    'Reference': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
    'Reference_Low': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
    'Reference_High': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
    'Electricity_decarbonization': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':1, 'Green_steel':0},
    'Green_steel': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':1}, 
    'Supply_side': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':1, 'Green_steel':1}, 
    'Lifetime_extension': {'Lifetime_extension': 1, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
    'Material_recovery': {'Lifetime_extension': 0, 'Material_recovery': 1, 'Electricity_decarbonization':0, 'Green_steel':0}, 
    'Demand_side': {'Lifetime_extension': 1,'Material_recovery': 1,'Electricity_decarbonization': 0, 'Green_steel':0}, # Material circularity refers to the combined implementation of lifetime extension and material recovery strategies, without changes in energy-related emission factors.
    'Integrated_strategies': {'Lifetime_extension': 1, 'Material_recovery': 1, 'Electricity_decarbonization':1, 'Green_steel':1} # The combined scenario represents the simultaneous implementation of material circularity and energy transition.
    }

strategy_template_SSP2_26_19 = {
    'Reference': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
    'Electricity_decarbonization': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':1, 'Green_steel':0},
    'Green_steel': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':1}, 
    'Supply_side': {'Lifetime_extension': 0, 'Material_recovery': 0, 'Electricity_decarbonization':1, 'Green_steel':1}, 
    'Lifetime_extension': {'Lifetime_extension': 1, 'Material_recovery': 0, 'Electricity_decarbonization':0, 'Green_steel':0},
    'Material_recovery': {'Lifetime_extension': 0, 'Material_recovery': 1, 'Electricity_decarbonization':0, 'Green_steel':0}, 
    'Demand_side': {'Lifetime_extension': 1,'Material_recovery': 1,'Electricity_decarbonization': 0, 'Green_steel':0}, # Material circularity refers to the combined implementation of lifetime extension and material recovery strategies, without changes in energy-related emission factors.
    'Integrated_strategies': {'Lifetime_extension': 1, 'Material_recovery': 1, 'Electricity_decarbonization':1, 'Green_steel':1} # The combined scenario represents the simultaneous implementation of material circularity and energy transition.
    }

Scenarios = {
    **{ssp: strategy_template_SSP1345_baseline for ssp in scenario_list_SSP1345_baseline},
    **{ssp: strategy_template_SSP2_baseline for ssp in scenario_list_SSP2_baseline},
    **{ssp: strategy_template_SSP2_26_19 for ssp in scenario_list_SSP2_26_19},
}

for i in Scenarios:
    for j in Scenarios[i]:
        print('\n')
        print(i,j,Scenarios[i][j])

############################### dynamic ship stock model ###########################################################################################

# prepare ship datasets
sd=pd.read_csv(add + '/03-results/sd_0.csv')
ship_columns=[
    'IMO', 'Type_Diogo', 'Year',
    'LDT', 'DWT', 'Period', 'Lifetime', 'Steel', 'Glass_wool', 
    'Paint', 'HDPE', 'PP', 'EPS', 'PU', 'PVDC', 'Ceramics', 
    'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood'
]
ship_sample_new=sd.loc[sd.Period=='2019-'].copy()

for scenario_name in list(Scenarios.keys()):
    
    for strategy in list(Scenarios[scenario_name].keys()):
        
        print('\nScenario:', scenario_name, strategy)
        
        folder_path = os.path.join(add, '03-results', scenario_name, strategy)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' has been created successfully！")
        else:
            print(f"Folder '{folder_path}' already exists!")        
        

        
        ssm.dynamic_stock_model(start_year, end_year, Scenarios[scenario_name], scenario_name, strategy, sd, ship_sample_new, ship_type_list, folder_path)
        
        
end = tm.perf_counter()
print(f"Execution Duration: {end - start:.6f} seconds")




