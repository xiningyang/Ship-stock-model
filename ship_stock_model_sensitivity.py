# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 15:45:31 2026

@author: Xining Yang
"""

import os
add=str(os.getcwd()).replace('\\', '/').replace('01-script', '')

import pandas as pd
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
import numpy as np
import time as tm
import gc


def dynamic_stock_model(start_year, end_year, sd, ship_sample_new, strategy, lifetime_value, strategy_rate):
    
    years_2030_2100=list(range(start_year+5,end_year+1,5))
    years_2025_2100=[start_year] + years_2030_2100
    
    diogo_scenario_data  =pd.read_excel(add + '02-data sources/ship_stock_yxn/SSP-based_demand_v08012026_yxn.xlsx')
    diogo_scenario_data = diogo_scenario_data.loc[diogo_scenario_data['Scenario']=='SSP2-Baseline']
    ship_type_list=list(diogo_scenario_data['Ship_type'].unique())
    
    MIC_ecoinvent=pd.read_excel(add + '02-data sources/MIC_yxn/ecoinvent_mic.xlsx', sheet_name='final')
    MIC_ecoinvent.set_index('Diogo_scenario_types', inplace=True, drop=True)
    material_type_list=MIC_ecoinvent.columns.tolist()

    # ship stock dynamics
    ship_outflow=pd.DataFrame(np.zeros((len(years_2030_2100), len(ship_type_list)+1)), columns=['year']+ship_type_list)
    ship_outflow.loc[:,'year']=years_2030_2100
    ship_outflow.set_index('year', inplace=True, drop=True)
    
    ship_inflow=pd.DataFrame(np.zeros((len(years_2030_2100), len(ship_type_list)+1)), columns=['year']+ship_type_list)
    ship_inflow.loc[:,'year']=years_2030_2100
    ship_inflow.set_index('year', inplace=True, drop=True)
    
    ship_stock=pd.DataFrame(np.zeros((len(years_2025_2100), len(ship_type_list)+1)), columns=['year']+ship_type_list)
    ship_stock.loc[:,'year']=years_2025_2100
    ship_stock.set_index('year', inplace=True, drop=True)
    
    # material stock and flows
    material_outflow=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    material_outflow.loc[:,'year']=years_2030_2100
    material_outflow.set_index('year', inplace=True, drop=True)
    
    material_inflow=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    material_inflow.loc[:,'year']=years_2030_2100
    material_inflow.set_index('year', inplace=True, drop=True)
    
    material_stock=pd.DataFrame(np.zeros((len(years_2025_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    material_stock.loc[:,'year']=years_2025_2100
    material_stock.set_index('year', inplace=True, drop=True)
    
    # material demand and supply
    material_primary=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    material_primary.loc[:,'year']=years_2030_2100
    material_primary.set_index('year', inplace=True, drop=True)
    
    material_reuse=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    material_reuse.loc[:,'year']=years_2030_2100
    material_reuse.set_index('year', inplace=True, drop=True)
    
    material_recycle=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    material_recycle.loc[:,'year']=years_2030_2100
    material_recycle.set_index('year', inplace=True, drop=True)
    
    material_waste=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    material_waste.loc[:,'year']=years_2030_2100
    material_waste.set_index('year', inplace=True, drop=True)
    
    # carbon emissions
    carbon_primary=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    carbon_primary.loc[:,'year']=years_2030_2100
    carbon_primary.set_index('year', inplace=True, drop=True)
    
    carbon_reuse=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    carbon_reuse.loc[:,'year']=years_2030_2100
    carbon_reuse.set_index('year', inplace=True, drop=True)
    
    carbon_recycle=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    carbon_recycle.loc[:,'year']=years_2030_2100
    carbon_recycle.set_index('year', inplace=True, drop=True)
    
    carbon_waste=pd.DataFrame(np.zeros((len(years_2030_2100), len(material_type_list)+1)), columns=['year']+material_type_list)
    carbon_waste.loc[:,'year']=years_2030_2100
    carbon_waste.set_index('year', inplace=True, drop=True)
    
    carbon_total=pd.DataFrame(carbon_primary)*0.0

    carbon_factor_Primary=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Primary')
    carbon_factor_Primary.set_index('Material', inplace=True, drop=True)
    carbon_factor_Recycle=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Secondary')
    carbon_factor_Recycle.set_index('Material', inplace=True, drop=True)
    carbon_factor_Waste=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Waste')
    carbon_factor_Waste.set_index('Material', inplace=True, drop=True)
    for col in carbon_factor_Primary.columns:
        carbon_factor_Primary.loc[:, col] = carbon_factor_Primary[start_year]
        carbon_factor_Recycle.loc[:, col] = carbon_factor_Recycle[start_year]
        carbon_factor_Waste.loc[:, col] = carbon_factor_Waste[start_year]

    lifetime_data=pd.read_excel(add + '02-data sources/lifetime_distribution_yxn/lifetime.xlsx', sheet_name='final')
    lifetime_data.set_index(keys='Diogo_scenario_types', inplace=True, drop=True)
    
    
    # Material recovery
    if strategy=='Material_recovery':
        Recovery=pd.read_excel(add + '02-data sources/Recycling/Recovery_rate.xlsx', sheet_name='Sheet1')
        Recovery.set_index('Material', inplace=True, drop=True)
        
        Recovery.loc[:,['Reuse_rate', 'Recycle_rate']] = Recovery.loc[:,['Reuse_rate', 'Recycle_rate']] * strategy_rate
        Recovery.loc[:,'Waste_rate'] = 1.0 - (Recovery['Reuse_rate'] + Recovery['Recycle_rate'])
        
    else:
        Recovery=pd.read_excel(add + '02-data sources/Recycling/Recovery_rate.xlsx', sheet_name='Sheet1')
        Recovery.set_index('Material', inplace=True, drop=True)
        Recovery.loc[:,['Reuse_rate', 'Recycle_rate']]=0.0
        Recovery.loc[:,['Waste_rate']]=1.0
        
    # Energy transition
    if strategy=='Electricity_decarbonization':

        carbon_factor_Primary_high=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Primary')
        carbon_factor_Primary_high.set_index('Material', inplace=True, drop=True)
        carbon_factor_Recycle_high=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Secondary')
        carbon_factor_Recycle_high.set_index('Material', inplace=True, drop=True)
        carbon_factor_Waste_high=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Waste')
        carbon_factor_Waste_high.set_index('Material', inplace=True, drop=True)

        carbon_factor_Primary_low=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Primary')
        carbon_factor_Primary_low.set_index('Material', inplace=True, drop=True)
        carbon_factor_Recycle_low=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Secondary')
        carbon_factor_Recycle_low.set_index('Material', inplace=True, drop=True)
        carbon_factor_Waste_low=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Waste')
        carbon_factor_Waste_low.set_index('Material', inplace=True, drop=True)
        
        carbon_factor_Primary=carbon_factor_Primary_high.copy()
        for mt in carbon_factor_Primary.index:
            ef_2025=carbon_factor_Primary_high.loc[mt, start_year]
            ef_2060=carbon_factor_Primary_low.loc[mt, 2060]
            ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
            years_2025_2060 = np.arange(2025, 2061, 5)
            carbon_factor_Primary.loc[mt,years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
            carbon_factor_Primary.loc[mt,2065:2100]=ef_2060
        
        carbon_factor_Recycle=carbon_factor_Recycle_high.copy()
        for mt in carbon_factor_Recycle.index:
            ef_2025=carbon_factor_Recycle_high.loc[mt, start_year]
            ef_2060=carbon_factor_Recycle_low.loc[mt, 2060]
            ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
            years_2025_2060 = np.arange(2025, 2061, 5)
            carbon_factor_Recycle.loc[mt,years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
            carbon_factor_Recycle.loc[mt,2065:2100]=ef_2060

        carbon_factor_Waste=carbon_factor_Waste_high.copy()
        for mt in carbon_factor_Waste.index:
            ef_2025=carbon_factor_Waste_high.loc[mt, start_year]
            ef_2060=carbon_factor_Waste_low.loc[mt, 2060]
            ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
            years_2025_2060 = np.arange(2025, 2061, 5)
            carbon_factor_Waste.loc[mt,years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
            carbon_factor_Waste.loc[mt,2065:2100]=ef_2060

    # Green_steel
    if strategy=='Green_steel':
        carbon_factor_Primary_high=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Primary')
        carbon_factor_Primary_high.set_index('Material', inplace=True, drop=True)
        carbon_factor_Primary_low=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Primary_Steel')
        carbon_factor_Primary_low.set_index('Material', inplace=True, drop=True)

        ef_2025=carbon_factor_Primary_high.loc['Steel', start_year]
        ef_2060=carbon_factor_Primary_low.loc['Steel', 2060]
        ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
        years_2025_2060 = np.arange(2025, 2061, 5)
        carbon_factor_Primary.loc['Steel',years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
        carbon_factor_Primary.loc['Steel',2065:2100]=ef_2060

    # Integrated strategies
    if strategy=='Integrated_strategies':
        
        # Material_recovery
        Recovery=pd.read_excel(add + '02-data sources/Recycling/Recovery_rate.xlsx', sheet_name='Sheet1')
        Recovery.set_index('Material', inplace=True, drop=True)
        Recovery.loc[:,['Reuse_rate', 'Recycle_rate']] = Recovery.loc[:,['Reuse_rate', 'Recycle_rate']] * strategy_rate
        Recovery.loc[:,'Waste_rate'] = 1.0 - (Recovery['Reuse_rate'] + Recovery['Recycle_rate'])
        
        # Electricity_decarbonization
        carbon_factor_Primary_high=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Primary')
        carbon_factor_Primary_high.set_index('Material', inplace=True, drop=True)
        carbon_factor_Recycle_high=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Secondary')
        carbon_factor_Recycle_high.set_index('Material', inplace=True, drop=True)
        carbon_factor_Waste_high=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Waste')
        carbon_factor_Waste_high.set_index('Material', inplace=True, drop=True)

        carbon_factor_Primary_low=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Primary')
        carbon_factor_Primary_low.set_index('Material', inplace=True, drop=True)
        carbon_factor_Recycle_low=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Secondary')
        carbon_factor_Recycle_low.set_index('Material', inplace=True, drop=True)
        carbon_factor_Waste_low=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Waste')
        carbon_factor_Waste_low.set_index('Material', inplace=True, drop=True)
        
        carbon_factor_Primary=carbon_factor_Primary_high.copy()
        for mt in carbon_factor_Primary.index:
            ef_2025=carbon_factor_Primary_high.loc[mt, start_year]
            ef_2060=carbon_factor_Primary_low.loc[mt, 2060]
            ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
            years_2025_2060 = np.arange(2025, 2061, 5)
            carbon_factor_Primary.loc[mt,years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
            carbon_factor_Primary.loc[mt,2065:2100]=ef_2060
        
        carbon_factor_Recycle=carbon_factor_Recycle_high.copy()
        for mt in carbon_factor_Recycle.index:
            ef_2025=carbon_factor_Recycle_high.loc[mt, start_year]
            ef_2060=carbon_factor_Recycle_low.loc[mt, 2060]
            ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
            years_2025_2060 = np.arange(2025, 2061, 5)
            carbon_factor_Recycle.loc[mt,years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
            carbon_factor_Recycle.loc[mt,2065:2100]=ef_2060

        carbon_factor_Waste=carbon_factor_Waste_high.copy()
        for mt in carbon_factor_Waste.index:
            ef_2025=carbon_factor_Waste_high.loc[mt, start_year]
            ef_2060=carbon_factor_Waste_low.loc[mt, 2060]
            ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
            years_2025_2060 = np.arange(2025, 2061, 5)
            carbon_factor_Waste.loc[mt,years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
            carbon_factor_Waste.loc[mt,2065:2100]=ef_2060            
        
        # Green_steel
        carbon_factor_Primary_low_steel=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Primary_Steel')
        carbon_factor_Primary_low_steel.set_index('Material', inplace=True, drop=True)
        ef_2025=carbon_factor_Primary_high.loc['Steel', start_year]
        ef_2060=carbon_factor_Primary_low_steel.loc['Steel', 2060]
        ef_2060 = ef_2025 - (ef_2025 - ef_2060 ) * strategy_rate
        years_2025_2060 = np.arange(2025, 2061, 5)
        carbon_factor_Primary.loc['Steel',years_2025_2060]=np.linspace(ef_2025, ef_2060, len(years_2025_2060))
        carbon_factor_Primary.loc['Steel',2065:2100]=ef_2060
    
    print(carbon_factor_Primary.loc['Steel',:])
    
    # initialize dfs
    ship_outflow=ship_outflow*0.0
    ship_inflow=ship_inflow*0.0
    ship_stock.loc[years_2030_2100,:]=ship_stock.loc[years_2030_2100,:]*0.0
    for st in ship_type_list:
        ship_stock.loc[start_year,st]=sd.loc[sd.Type_Diogo==st,'DWT'].sum()
    
    material_outflow=material_outflow*0.0
    material_inflow=material_inflow*0.0
    material_stock.loc[years_2030_2100,:]=material_stock.loc[years_2030_2100,:]*0.0
    material_stock.loc[start_year,material_type_list]=sd[material_type_list].sum(axis=0)
    
    material_primary=material_primary*0.0
    material_reuse=material_reuse*0.0
    material_recycle=material_recycle*0.0
    material_waste=material_waste*0.0
    
    carbon_primary=carbon_primary*0.0
    carbon_reuse=carbon_reuse*0.0
    carbon_recycle=carbon_recycle*0.0
    carbon_waste=carbon_waste*0.0
    carbon_total=carbon_total*0.0
    
    # dynamic loops
    for step_year in years_2030_2100:
        
        #ship stock evolution
        for ship_type in ship_type_list:
            
            #outflow
            sd_dem_index=sd.loc[(sd.Type_Diogo==ship_type) & (sd.Year+sd.Lifetime>step_year-5) & (sd.Year+sd.Lifetime<=step_year)].index
            sd_dem=sd.loc[sd_dem_index, :].copy()
            sd = sd.loc[~sd.index.isin(sd_dem_index)].reset_index(drop=True)
            
            #inflow
            ship_demand=ship_stock.loc[start_year,ship_type] * diogo_scenario_data.loc[diogo_scenario_data['Ship_type']==ship_type][step_year].to_list()[0]
            stock_ship_type=sd.loc[(sd.Type_Diogo==ship_type)]['DWT'].sum()
            
            if stock_ship_type < ship_demand:
                sd_new=pd.DataFrame(np.zeros((0, sd.shape[1])), columns=sd.columns)
                while (sd_new['DWT'].sum() < ship_demand - stock_ship_type):
                    df=ship_sample_new.loc[ship_sample_new.Type_Diogo==ship_type].sample(n=1, replace=True)
                    sd_new = pd.concat([sd_new, df], ignore_index=True)
                
                random_Year=np.arange(step_year-4,step_year+1)
                sd_new.loc[:,'Year']=np.random.choice(random_Year, sd_new.shape[0], replace=True)
                sd_new.loc[:,'Lifetime']=lifetime_value
                
                if strategy=='Lifetime_extension' or strategy=='Integrated_strategies':
                    sd_new.loc[:,'Lifetime']= (sd_new.loc[:,'Lifetime'] + (40-sd_new.loc[:,'Lifetime'])*strategy_rate).astype(int)
                
                sd_new.loc[:,'IMO']=sd_new.loc[:,'Year']*1000 + np.arange(len(sd_new))
                sd_new.loc[:, material_type_list] = sd_new.loc[:, 'LDT'].values[:, None] * MIC_ecoinvent.loc[ship_type, material_type_list].values
                
            elif stock_ship_type >= ship_demand:
                sd_new=pd.DataFrame(np.zeros((0, sd.shape[1])), columns=sd.columns)
            
            #stock
            sd=pd.concat([sd, sd_new], ignore_index=True)            
            
            #summary
            ship_outflow.loc[step_year,ship_type]=sd_dem.loc[sd_dem.Type_Diogo==ship_type, 'DWT'].sum()
            material_outflow.loc[step_year,material_type_list] += sd_dem[material_type_list].sum(axis=0)
            
            ship_inflow.loc[step_year,ship_type]=sd_new.loc[(sd_new.Type_Diogo==ship_type) & (sd_new.Year>step_year-5) & (sd_new.Year<=step_year)]['DWT'].sum()
            material_inflow.loc[step_year,material_type_list] += sd_new[material_type_list].sum(axis=0)
                        
            ship_stock.loc[step_year,ship_type]=sd.loc[sd.Type_Diogo==ship_type, 'DWT'].sum()
        material_stock.loc[step_year,material_type_list]=material_stock.loc[step_year-5,material_type_list] - material_outflow.loc[step_year,material_type_list] + material_inflow.loc[step_year,material_type_list]
        
        #material recovery and carbon emissions
        material_outflow.loc[step_year,'Zinc']=0.0 # Zinc is assumed to disappear during ship operation
        
        for mm in material_type_list:
            if material_inflow.loc[step_year, mm] <= material_outflow.loc[step_year, mm]*Recovery.loc[mm, 'Reuse_rate']:
                material_reuse.loc[step_year,mm]=material_inflow.loc[step_year, mm]
                material_recycle.loc[step_year,mm]=0.0
                material_waste.loc[step_year,mm]=material_outflow.loc[step_year,mm]-material_reuse.loc[step_year,mm]-material_recycle.loc[step_year,mm]
                material_primary.loc[step_year,mm]=0.0
            elif (material_inflow.loc[step_year, mm] > material_outflow.loc[step_year, mm]*Recovery.loc[mm, 'Reuse_rate']) & (material_inflow.loc[step_year, mm] <= material_outflow.loc[step_year, mm]*(Recovery.loc[mm, 'Reuse_rate']+Recovery.loc[mm, 'Recycle_rate'])):                    
                material_reuse.loc[step_year,mm]=material_outflow.loc[step_year, mm]*Recovery.loc[mm, 'Reuse_rate']
                material_recycle.loc[step_year,mm]=material_inflow.loc[step_year, mm]-material_reuse.loc[step_year,mm]
                material_waste.loc[step_year,mm]=material_outflow.loc[step_year,mm]-material_reuse.loc[step_year,mm]-material_recycle.loc[step_year,mm]
                material_primary.loc[step_year,mm]=0.0
            elif material_inflow.loc[step_year, mm] > material_outflow.loc[step_year, mm]*(Recovery.loc[mm, 'Reuse_rate']+Recovery.loc[mm, 'Recycle_rate']):                       
                material_reuse.loc[step_year,mm]=material_outflow.loc[step_year, mm]*Recovery.loc[mm, 'Reuse_rate']
                material_recycle.loc[step_year,mm]=material_outflow.loc[step_year, mm]*Recovery.loc[mm, 'Recycle_rate']
                material_waste.loc[step_year,mm]=material_outflow.loc[step_year,mm]-material_reuse.loc[step_year,mm]-material_recycle.loc[step_year,mm]
                material_primary.loc[step_year,mm]=material_inflow.loc[step_year, mm]-material_reuse.loc[step_year,mm]-material_recycle.loc[step_year,mm]
        
        #material recovery and carbon emissions
        carbon_reuse.loc[step_year,material_type_list]=material_reuse.loc[step_year,material_type_list]*0.0
        carbon_reuse.loc[step_year,'Steel']=material_reuse.loc[step_year,'Steel']*carbon_factor_Primary.loc['Steel',step_year] * (0.23+0.31)/2 #23-31% of primary steel production, source: SSI, 2021, Exploring shipping's transition to a circular industry
        carbon_recycle.loc[step_year,material_type_list]=material_recycle.loc[step_year,material_type_list]*carbon_factor_Recycle.loc[material_type_list,step_year]
        carbon_primary.loc[step_year,material_type_list]=material_primary.loc[step_year,material_type_list]*carbon_factor_Primary.loc[material_type_list,step_year]
        carbon_waste.loc[step_year,material_type_list]=material_waste.loc[step_year,material_type_list]*(carbon_factor_Waste.loc[material_type_list,step_year])
        
    # results
    return np.sum(carbon_reuse.sum(axis=1) + carbon_recycle.sum(axis=1) + carbon_primary.sum(axis=1) + carbon_waste.sum(axis=1))

            

            
