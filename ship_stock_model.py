# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 15:45:31 2026

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
import gc


def dynamic_stock_model(start_year, end_year, scenario, scenario_name, strategy, sd, ship_sample_new, ship_type_list, folder_path):
    
    years_2030_2100=list(range(start_year+5,end_year+1,5))
    # print('\nTimeframe:', years_2030_2100)
    years_2025_2100=[start_year] + years_2030_2100
    
    diogo_scenario_data=pd.read_excel(add + '02-data sources/ship_stock_yxn/SSP-based_demand_v08012026_yxn.xlsx')
    
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
    
    carbon_by_ship_all_primary=pd.DataFrame(np.zeros((len(years_2030_2100), len(ship_type_list)+1)), columns=['year']+ship_type_list)
    carbon_by_ship_all_primary.loc[:,'year']=years_2030_2100
    carbon_by_ship_all_primary.set_index('year', inplace=True, drop=True)    
    
    
    # Lifetime extension
    if scenario[strategy]['Lifetime_extension']==0:
        lifetime_data=pd.read_excel(add + '02-data sources/lifetime_distribution_yxn/lifetime.xlsx', sheet_name='final')
        lifetime_data.set_index(keys='Diogo_scenario_types', inplace=True, drop=True)
    elif scenario[strategy]['Lifetime_extension']==1:
        lifetime_data=pd.read_excel(add + '02-data sources/lifetime_distribution_yxn/lifetime.xlsx', sheet_name='final')
        lifetime_data.set_index(keys='Diogo_scenario_types', inplace=True, drop=True)
        lifetime_data.loc[:,'mean']=lifetime_data.loc[:,'mean']*1.20 #Shimotsuura, T., 2024. Environmental consequences in lifecycle changes of container shipping vessels. Journal of Environmental Management 365, 121558. https://doi.org/10.1016/j.jenvman.2024.121558
    
    # Material recovery
    if scenario[strategy]['Material_recovery']==0:
        Recovery=pd.read_excel(add + '02-data sources/Recycling/Recovery_rate.xlsx', sheet_name='Sheet1')
        Recovery.set_index('Material', inplace=True, drop=True)
        Recovery.loc[:,['Reuse_rate', 'Recycle_rate']]=0.0
        Recovery.loc[:,['Waste_rate']]=1.0
    elif scenario[strategy]['Material_recovery']==1:
        Recovery=pd.read_excel(add + '02-data sources/Recycling/Recovery_rate.xlsx', sheet_name='Sheet1')
        Recovery.set_index('Material', inplace=True, drop=True)
    
    # Energy transition
    if 'SSP2' not in scenario_name:
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
            
    elif scenario_name=='SSP2-Baseline':
        if scenario[strategy]['Electricity_decarbonization']==0:
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
        elif scenario[strategy]['Electricity_decarbonization']==1:
            carbon_factor_Primary=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Primary')
            carbon_factor_Primary.set_index('Material', inplace=True, drop=True)
            carbon_factor_Recycle=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Secondary')
            carbon_factor_Recycle.set_index('Material', inplace=True, drop=True)
            carbon_factor_Waste=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Waste')
            carbon_factor_Waste.set_index('Material', inplace=True, drop=True)
    
    elif scenario_name=='SSP2-26':
        if scenario[strategy]['Electricity_decarbonization']==0:
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
        elif scenario[strategy]['Electricity_decarbonization']==1:
            carbon_factor_Primary=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP26_Primary')
            carbon_factor_Primary.set_index('Material', inplace=True, drop=True)
            carbon_factor_Recycle=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP26_Secondary')
            carbon_factor_Recycle.set_index('Material', inplace=True, drop=True)
            carbon_factor_Waste=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP26_Waste')
            carbon_factor_Waste.set_index('Material', inplace=True, drop=True)
    
    elif scenario_name=='SSP2-19':
        if scenario[strategy]['Electricity_decarbonization']==0:
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
        elif scenario[strategy]['Electricity_decarbonization']==1:
            carbon_factor_Primary=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Primary')
            carbon_factor_Primary.set_index('Material', inplace=True, drop=True)
            carbon_factor_Recycle=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Secondary')
            carbon_factor_Recycle.set_index('Material', inplace=True, drop=True)
            carbon_factor_Waste=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Waste')
            carbon_factor_Waste.set_index('Material', inplace=True, drop=True)

    # Green steel
    if scenario_name=='SSP2-Baseline':  
        if scenario[strategy]['Green_steel']==1:
            carbon_factor_Primary_Steel=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_Base_Primary_Steel')
            carbon_factor_Primary_Steel.set_index('Material', inplace=True, drop=True)
            carbon_factor_Primary.loc['Steel',:]=carbon_factor_Primary_Steel.loc['Steel',:]
    elif scenario_name=='SSP2-26':  
        if scenario[strategy]['Green_steel']==1:
            carbon_factor_Primary_Steel=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP26_Primary_Steel')
            carbon_factor_Primary_Steel.set_index('Material', inplace=True, drop=True)
            carbon_factor_Primary.loc['Steel',:]=carbon_factor_Primary_Steel.loc['Steel',:]
    elif scenario_name=='SSP2-19':  
        if scenario[strategy]['Green_steel']==1:
            carbon_factor_Primary_Steel=pd.read_excel(add + '02-data sources/Carbon_factor/Carbon_factor.xlsx', sheet_name='SSP2_RCP19_Primary_Steel')
            carbon_factor_Primary_Steel.set_index('Material', inplace=True, drop=True)
            carbon_factor_Primary.loc['Steel',:]=carbon_factor_Primary_Steel.loc['Steel',:]

    
    # Low and high bound
    uncertainty_rate=0.05
    if 'Baseline' in scenario_name:
        if strategy =='Reference_Low':
            #existing ships
            sd.loc[:, 'Lifetime']=sd['Lifetime'] + ((sd['Year'] + sd['Lifetime']-start_year)*uncertainty_rate).round(0).astype(int)
            sd=sd.loc[sd['Year'] + sd['Lifetime']>start_year]
            #new ships
            lifetime_data['mean']=lifetime_data['mean']*(1.0+uncertainty_rate) #Shimotsuura, T., 2024. Environmental consequences in lifecycle changes of container shipping vessels. Journal of Environmental Management 365, 121558. https://doi.org/10.1016/j.jenvman.2024.121558
            
            #MIC
            sd.loc[:, material_type_list]=sd[material_type_list]*(1.0-uncertainty_rate)
            MIC_ecoinvent=pd.read_excel(add + '02-data sources/MIC_yxn/ecoinvent_mic.xlsx', sheet_name='final')
            MIC_ecoinvent.set_index('Diogo_scenario_types', inplace=True, drop=True)
            MIC_ecoinvent.loc[ship_type_list,material_type_list]=MIC_ecoinvent.loc[ship_type_list,material_type_list]*(1.0-uncertainty_rate)
            
            # Carbon factor
            carbon_factor_Primary.loc[material_type_list, years_2025_2100]=carbon_factor_Primary.loc[material_type_list, years_2025_2100]*(1.0-uncertainty_rate)
            carbon_factor_Recycle.loc[material_type_list, years_2025_2100]=carbon_factor_Recycle.loc[material_type_list, years_2025_2100]*(1.0-uncertainty_rate)
            carbon_factor_Waste.loc[material_type_list, years_2025_2100]=carbon_factor_Waste.loc[material_type_list, years_2025_2100]*(1.0-uncertainty_rate)
            
        elif strategy =='Reference_High':
            #existing ships
            sd.loc[:, 'Lifetime']=sd['Lifetime'] - ((sd['Year'] + sd['Lifetime']-start_year)*uncertainty_rate).round(0).astype(int)
            sd=sd.loc[sd['Year'] + sd['Lifetime']>start_year]
            #new ships
            lifetime_data['mean']=lifetime_data['mean']*(1.0-uncertainty_rate) #Shimotsuura, T., 2024. Environmental consequences in lifecycle changes of container shipping vessels. Journal of Environmental Management 365, 121558. https://doi.org/10.1016/j.jenvman.2024.121558
            
            #MIC
            sd.loc[:, material_type_list]=sd[material_type_list]*(1.0+uncertainty_rate)
            MIC_ecoinvent=pd.read_excel(add + '02-data sources/MIC_yxn/ecoinvent_mic.xlsx', sheet_name='final')
            MIC_ecoinvent.set_index('Diogo_scenario_types', inplace=True, drop=True)
            MIC_ecoinvent.loc[ship_type_list,material_type_list]=MIC_ecoinvent.loc[ship_type_list,material_type_list]*(1.0+uncertainty_rate)
            
            # Carbon factor
            carbon_factor_Primary.loc[material_type_list, years_2025_2100]=carbon_factor_Primary.loc[material_type_list, years_2025_2100]*(1+uncertainty_rate)
            carbon_factor_Recycle.loc[material_type_list, years_2025_2100]=carbon_factor_Recycle.loc[material_type_list, years_2025_2100]*(1+uncertainty_rate)
            carbon_factor_Waste.loc[material_type_list, years_2025_2100]=carbon_factor_Waste.loc[material_type_list, years_2025_2100]*(1+uncertainty_rate)

        
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
            ship_demand=ship_stock.loc[start_year,ship_type] * diogo_scenario_data.loc[(diogo_scenario_data['Scenario']==scenario_name) & (diogo_scenario_data['Ship_type']==ship_type)][step_year].to_list()[0]
            stock_ship_type=sd.loc[(sd.Type_Diogo==ship_type)]['DWT'].sum()
            
            if stock_ship_type < ship_demand:
                sd_new=pd.DataFrame(np.zeros((0, sd.shape[1])), columns=sd.columns)
                while (sd_new['DWT'].sum() < ship_demand - stock_ship_type):
                    df=ship_sample_new.loc[ship_sample_new.Type_Diogo==ship_type].sample(n=1, replace=True)
                    sd_new = pd.concat([sd_new, df], ignore_index=True)
                
                random_Year=np.arange(step_year-4,step_year+1)
                sd_new.loc[:,'Year']=np.random.choice(random_Year, sd_new.shape[0], replace=True)
                sd_new.loc[:,'IMO']=sd_new.loc[:,'Year']*1000 + np.arange(len(sd_new))
                sd_new.loc[:, material_type_list] = sd_new.loc[:, 'LDT'].values[:, None] * MIC_ecoinvent.loc[ship_type, material_type_list].values
                
                for tt in sd_new['Type_Diogo'].unique():
                    random_lifetime=np.random.normal(lifetime_data.loc[tt, 'mean'], lifetime_data.loc[tt, 'std'], 10000000).round(0).astype(int)
                    random_lifetime=random_lifetime[(random_lifetime>=lifetime_data.loc[tt, 'mean']-1.5*lifetime_data.loc[tt, 'std']) & (random_lifetime<=lifetime_data.loc[tt, 'mean']+1.5*lifetime_data.loc[tt, 'std'])] # 1.5 std, [1] B. Müller D. Stock dynamics for forecasting material flows—Case study for housing in The Netherlands. Ecol Econ 2006;59:142–56. doi:https://doi.org/10.1016/j.ecolecon.2005.09.025.        
                    tt_index=sd_new.loc[sd_new.Type_Diogo==tt].index
                    sd_new.loc[tt_index,'Lifetime']=np.random.choice(random_lifetime, len(tt_index), replace=True).astype(int)
            elif stock_ship_type >= ship_demand:
                sd_new=pd.DataFrame(np.zeros((0, sd.shape[1])), columns=sd.columns)
            
            factor_series = carbon_factor_Primary.loc[material_type_list, step_year]
            carbon_by_ship_all_primary.loc[step_year, ship_type] = sd_new[material_type_list].sum().dot(factor_series)
            
            factor_series = carbon_factor_Waste.loc[material_type_list, step_year]
            carbon_by_ship_all_primary.loc[step_year, ship_type] +=  sd_dem[material_type_list].sum().dot(factor_series)

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
        
        # save results
        if step_year==end_year:

            #ship#
            
            # sd.to_csv(os.path.join(folder_path, 'sd_final.csv'))
            ship_outflow.to_csv(os.path.join(folder_path, 'ship_outflow.csv'))
            ship_inflow.to_csv(os.path.join(folder_path, 'ship_inflow.csv'))
            ship_stock.to_csv(os.path.join(folder_path, 'ship_stock.csv'))
            
            #materials#

            material_type_list_final=['Steel', 'Glass_wool', 'Paint', 'Plastic', 'Ceramics', 'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood']
            material_type_list_plastic=['HDPE', 'PP', 'EPS', 'PU', 'PVDC']
            
            material_outflow.to_csv(os.path.join(folder_path, 'material_outflow_full_material_type_list.csv'))
            material_inflow.to_csv(os.path.join(folder_path, 'material_inflow_full_material_type_list.csv'))
            material_stock.to_csv(os.path.join(folder_path, 'material_stock_full_material_type_list.csv'))  
            
            material_outflow.loc[:,'Plastic']=material_outflow[material_type_list_plastic].sum(axis=1)
            material_inflow.loc[:,'Plastic']=material_inflow[material_type_list_plastic].sum(axis=1)
            material_stock.loc[:,'Plastic']=material_stock[material_type_list_plastic].sum(axis=1)
            material_outflow[material_type_list_final].to_csv(os.path.join(folder_path, 'material_outflow.csv'))
            material_inflow[material_type_list_final].to_csv(os.path.join(folder_path, 'material_inflow.csv'))
            material_stock[material_type_list_final].to_csv(os.path.join(folder_path, 'material_stock.csv'))                

            material_reuse.to_csv(os.path.join(folder_path, 'material_reuse_full_material_type_list.csv'))
            material_recycle.to_csv(os.path.join(folder_path, 'material_recycle_full_material_type_list.csv'))
            material_waste.to_csv(os.path.join(folder_path, 'material_waste_full_material_type_list.csv'))  
            material_primary.to_csv(os.path.join(folder_path, 'material_primary_full_material_type_list.csv'))  
            
            material_reuse.loc[:,'Plastic']=material_reuse[material_type_list_plastic].sum(axis=1)
            material_recycle.loc[:,'Plastic']=material_recycle[material_type_list_plastic].sum(axis=1)
            material_waste.loc[:,'Plastic']=material_waste[material_type_list_plastic].sum(axis=1)
            material_primary.loc[:,'Plastic']=material_primary[material_type_list_plastic].sum(axis=1)
            material_reuse[material_type_list_final].to_csv(os.path.join(folder_path, 'material_reuse.csv'))
            material_recycle[material_type_list_final].to_csv(os.path.join(folder_path, 'material_recycle.csv'))
            material_waste[material_type_list_final].to_csv(os.path.join(folder_path, 'material_waste.csv'))
            material_primary[material_type_list_final].to_csv(os.path.join(folder_path, 'material_primary.csv'))                
            
            #GHG#

            carbon_primary.to_csv(os.path.join(folder_path, 'carbon_primary_full_material_type_list.csv'))
            carbon_recycle.to_csv(os.path.join(folder_path, 'carbon_recycle_full_material_type_list.csv'))
            carbon_waste.to_csv(os.path.join(folder_path, 'carbon_waste_full_material_type_list.csv'))                
            
            carbon_primary.loc[:,'Plastic']=carbon_primary[material_type_list_plastic].sum(axis=1)
            carbon_reuse.loc[:,'Plastic']=carbon_reuse[material_type_list_plastic].sum(axis=1)
            carbon_recycle.loc[:,'Plastic']=carbon_recycle[material_type_list_plastic].sum(axis=1)
            carbon_waste.loc[:,'Plastic']=carbon_waste[material_type_list_plastic].sum(axis=1)
            carbon_primary[material_type_list_final].to_csv(os.path.join(folder_path, 'carbon_primary.csv'))
            carbon_reuse[material_type_list_final].to_csv(os.path.join(folder_path, 'carbon_reuse.csv'))
            carbon_recycle[material_type_list_final].to_csv(os.path.join(folder_path, 'carbon_recycle.csv'))
            carbon_waste[material_type_list_final].to_csv(os.path.join(folder_path, 'carbon_waste.csv'))
            
            carbon_total=carbon_primary[material_type_list_final]+carbon_reuse[material_type_list_final]+carbon_recycle[material_type_list_final]+carbon_waste[material_type_list_final]
            carbon_total.to_csv(os.path.join(folder_path, 'carbon_total.csv'))    
            
            carbon_by_ship_all_primary.to_csv(os.path.join(folder_path, 'carbon_by_ship_all_primary.csv'))   

