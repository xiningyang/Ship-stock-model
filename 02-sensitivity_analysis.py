# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 07:36:24 2026

@author: Xining Yang
"""

import os
add=str(os.getcwd()).replace('\\', '/').replace('01-script', '')
print(add)

import pandas as pd
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
import numpy as np
import time as tm
import ship_stock_model_sensitivity as ssms

start = tm.perf_counter()

start_year=2025
end_year=2100

############################### dynamic ship stock model ###########################################################################################

sd=pd.read_csv(add + '/03-results/sd_0.csv')

ship_columns=[
    'IMO', 'Type_Diogo', 'Year',
    'LDT', 'DWT', 'Period', 'Lifetime', 'Steel', 'Glass_wool', 
    'Paint', 'HDPE', 'PP', 'EPS', 'PU', 'PVDC', 'Ceramics', 
    'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood'
]

sd=sd[ship_columns]

ship_sample_new=sd.loc[sd.Period=='2019-'].copy()

strategies=['Lifetime_extension', 'Material_recovery', 'Electricity_decarbonization', 'Green_steel', 'Integrated_strategies']

lifetime_values=list(range(20 ,41, 2))
strategy_step=0.10
strategy_rates = [round(x, 4) for x in np.arange(0.0, 1.0 +strategy_step, strategy_step)]

for strategy in strategies:
    
    df=pd.DataFrame(np.zeros((len(lifetime_values), len(strategy_rates))), columns=strategy_rates)
    df['Lifetime']=lifetime_values
    df.set_index('Lifetime', inplace=True, drop=True)
    
    for lifetime_value in lifetime_values:
        for strategy_rate in strategy_rates:
            
            df.loc[lifetime_value,strategy_rate] = ssms.dynamic_stock_model(start_year, end_year, sd, ship_sample_new, strategy, lifetime_value, strategy_rate)
            print('\nScenario:', strategy, lifetime_value, strategy_rate)
            print(df)
            
    folder_path = os.path.join(add, '03-results', 'Sensitivity')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        print(f"Folder '{folder_path}' already exists!")
    
    file_name = f"{strategy}.csv"
    full_save_path = os.path.join(folder_path, file_name)
    df.to_csv(full_save_path)
    
end = tm.perf_counter()
print(f"Execution Duration: {end - start:.6f} seconds")




