# -*- coding: utf-8 -*-
"""
Created on Fri May  8 09:51:25 2026

@author: Xining Yang
"""

import os
add=str(os.getcwd()).replace('\\', '/').replace('01-script', '')
print(add)

import pandas as pd
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
import numpy as np


scenario_data=pd.read_excel(add + '02-data sources/ship_stock_yxn/SSP-based_demand_v08012026_yxn.xlsx')
ship_type_list=list(scenario_data['Ship_type'].unique())

sd=pd.read_csv(add + '/03-results/sd_0.csv')

years = sd['Year'].sort_values(ascending=True).unique()

MIC_ecoinvent=pd.read_excel(add + '02-data sources/MIC_yxn/ecoinvent_mic.xlsx', sheet_name='final')
MIC_ecoinvent.set_index('Diogo_scenario_types', inplace=True, drop=True)
material_type_list=MIC_ecoinvent.columns.tolist()

carbon_factor_Primary=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Primary')
carbon_factor_Primary.set_index('Material', inplace=True, drop=True)
        
        
# Annual finished LDT
df=pd.DataFrame(np.zeros((len(years), len(ship_type_list))), columns=ship_type_list)
df['Year']=years
df.set_index('Year', inplace=True, drop=True)

for i in years:
    for j in ship_type_list:
        
        df.loc[i,j]=sd.loc[(sd.Year==i) & (sd.Type_Diogo==j),'LDT'].sum()
        
df.to_csv(add + '/03-results/current_stock_LDT.csv')


# Annual finished Number
df=pd.DataFrame(np.zeros((len(years), len(ship_type_list))), columns=ship_type_list)
df['Year']=years
df.set_index('Year', inplace=True, drop=True)

for i in years:
    for j in ship_type_list:
        
        df.loc[i,j]=sd.loc[(sd.Year==i) & (sd.Type_Diogo==j)].shape[0]

df.to_csv(add + '/03-results/current_stock_Number.csv')
print(df[ship_type_list].sum().astype(int))
print(np.sum(df[ship_type_list].sum()))
print(sd['DWT'].sum()/1e9)
print(sd['LDT'].sum()/1e6)


# Annual GHG
df=pd.DataFrame(np.zeros((len(years), len(material_type_list))), columns=material_type_list)
df['Year']=years
df.set_index('Year', inplace=True, drop=True)

for i in years:
    df.loc[i,material_type_list]=sd.loc[(sd.Year==i),material_type_list].sum(axis=0)
    
df.loc[:,'Total']=df[material_type_list].sum(axis=1)
df.to_csv(add + '/03-results/current_stock_material.csv')        

for i in years:
    for j in material_type_list:
        df.loc[i,j]=df.loc[i,j]*carbon_factor_Primary.loc[j,2025]

df.loc[:,'Total']=df[material_type_list].sum(axis=1)
df.to_csv(add + '/03-results/current_stock_GHG.csv')




