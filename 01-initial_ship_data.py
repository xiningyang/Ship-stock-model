# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 14:56:27 2025

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
from scipy.special import gamma
import country_converter as coco

start = tm.perf_counter()

############# timeframe ###########################################################################################################################################################################################

start_year=2025
end_year=2100

############# load ship data from Diogo ###########################################################################################################################################################################################

sd=pd.read_excel(add + '02-data sources/ship_stock_yxn/ship_data_v2026Jan_yxn.xlsx')
sd=sd.loc[sd.Status=='In Service/Commission']
sd=sd.loc[:, ['IMO', 'Type', 'Year', 'Breadth', 'Length', 'Draught', 'LDT', 'DWT', 'GT', 'Build Location', 'Flag', 'Operator Domicile', 'Registered Owner Domicile', 'Shipmanager Domicile']]

sd.rename(columns={'Build Location': 'Build', 'Registered Owner Domicile': 'Owner', 'Operator Domicile': 'Operator', 'Shipmanager Domicile': 'Shipmanager'}, inplace=True)

scenario_data=pd.read_excel(add + '02-data sources/ship_stock_yxn/SSP-based_demand_v08012026_yxn.xlsx')
ship_type_list=list(scenario_data['Ship_type'].unique())

print('Number of ships before filter:', sd.shape)

############# ship classification ###########################################################################################################################################################################################

sd = sd.rename(columns={'Type': 'Type_Diogo'})

sd=sd.loc[(sd.Type_Diogo.isin(scenario_data['Ship_type'].unique()))] 
print('After filter types:', sd.shape)

# periods source: Steel stocks and flows of global merchant fleets as material base of international trade from 1980 to 2050
for i in sd.index:
    if (sd.loc[i,'Year']<=1979):
        sd.loc[i,'Period']='-1979'
    elif (sd.loc[i,'Year']>=1980) and (sd.loc[i,'Year']<=1984):
        sd.loc[i,'Period']='1980-1984'
    elif (sd.loc[i,'Year']>=1985) and (sd.loc[i,'Year']<=1989):
        sd.loc[i,'Period']='1985-1989'        
    elif (sd.loc[i,'Year']>=1990) and (sd.loc[i,'Year']<=1994):
        sd.loc[i,'Period']='1990-1994' 
    elif (sd.loc[i,'Year']>=1995) and (sd.loc[i,'Year']<=1999):
        sd.loc[i,'Period']='1995-1999' 
    elif (sd.loc[i,'Year']>=2000) and (sd.loc[i,'Year']<=2004):
        sd.loc[i,'Period']='2000-2004'
    elif (sd.loc[i,'Year']>=2005) and (sd.loc[i,'Year']<=2009):
        sd.loc[i,'Period']='2005-2009'
    elif (sd.loc[i,'Year']>=2010) and (sd.loc[i,'Year']<=2014):
        sd.loc[i,'Period']='2010-2014'
    elif (sd.loc[i,'Year']>=2015) and (sd.loc[i,'Year']<=2018):
        sd.loc[i,'Period']='2015-2018'
    elif (sd.loc[i,'Year']>=2019):
        sd.loc[i,'Period']='2019-'
    else:
        print(666)

sd.sort_values(by=['Year'], ascending=True, inplace=True)
sd.reset_index(drop='True', inplace=True)
print('Number of ship datastes:', len(sd)) # totaling 45,891 vessels. source: Global Shipping Emissions from a Well-to-Wake Perspective: The MariTEAM Model

############################### expected lifetime ###########################################################################################

def existing_ship_lifetime(lifetime_distribution, a, b, build_year, initial_year, number_ships):
    if lifetime_distribution=='normal':
        mean=a
        std=b
        random_lifetime=np.random.normal(mean, std, 1000000).round(0).astype(int)       
        lifetime_list=np.random.choice(random_lifetime[random_lifetime>initial_year-build_year], number_ships, replace=True)
        return lifetime_list

lifetime_data=pd.read_excel(add + '02-data sources/lifetime_distribution_yxn/lifetime.xlsx', sheet_name='final')
lifetime_data.set_index(keys='Diogo_scenario_types', inplace=True, drop=True)

sd1=sd.loc[sd.Year>1980].copy()
for i in range(1980, start_year+1):
    for j in sd1.Type_Diogo.unique():
        sd_index=sd1.loc[(sd1.Year==i) & (sd1.Type_Diogo==j)].index
        sd1.loc[sd_index,'Lifetime']=existing_ship_lifetime('normal', lifetime_data.loc[j, 'mean'], lifetime_data.loc[j, 'std'], i, start_year, len(sd_index))


sd2=sd.loc[sd.Year<=1980].copy()
remaining_life = np.random.uniform(0, 10, size=len(sd2))
sd2['Lifetime'] = (start_year - sd2['Year'] + remaining_life).round(0).astype(int)

sd=pd.concat([sd1,sd2],ignore_index=True)

############# material composition ###########################################################################################################################################################################################

MIC_ecoinvent=pd.read_excel(add + '02-data sources/MIC_yxn/ecoinvent_mic.xlsx', sheet_name='final')
MIC_ecoinvent.set_index('Diogo_scenario_types', inplace=True, drop=True)

material_list=MIC_ecoinvent.columns.tolist()

for i in sd.Type_Diogo.unique():
    index_tem=sd.loc[(sd.Type_Diogo==i)].index
    sd.loc[index_tem, material_list]=(np.tile(sd.loc[index_tem, 'LDT'].tolist(), (len(material_list), 1)).T) * (np.tile(MIC_ecoinvent.loc[i,material_list], (len(index_tem), 1))) # assuming LWT=LDT


############# One China ###########################################################################################################################################################################################

cols = ['Operator', 'Owner', 'Shipmanager', 'Flag', 'Build']
pattern = r"(?i)\b(china|chinese|taiwan|taipei|macao|hong\s*kong|china,\s*people's\s*republic\s*of)\b"

sd[cols] = sd[cols].replace(
    pattern,
    "China",
    regex=True
)

############# ship country ###########################################################################################################################################################################################

country_map = {
    # 欧洲历史国家
    'Irish Republic': 'IRL',
    'U.S.S.R.': 'RUS',                     # successor state
    'Yugoslavia': 'SRB',                   # successor state
    'German Democratic Republic': 'DEU',   # East Germany
    'Serbia & Montenegro': 'SRB',          # successor state
    'Czechoslovakia': 'CZE',               # successor state

    # 葡萄牙自治地区
    'Madeira': 'PRT',
    'Azores': 'PRT',

    # 西班牙自治地区
    'Canary Islands': 'ESP',

    # 中国相关地区
    'Taiwan': 'CHN',
    'Taipei': 'CHN',
    'Macao': 'CHN',
    'Hong Kong': 'CHN',
    'Chinese Mainland': 'CHN',
    "China, People's Republic Of": 'CHN',

    # 北美/海外领土示例
    'Greenland': 'DNK',       # Denmark
    'Faroe Islands': 'DNK',   # Denmark
    'Bermuda': 'GBR',         # UK
    'Cayman Islands': 'GBR',  # UK
    'Gibraltar': 'GBR',       # UK
}


sd['Flag_code'] = coco.convert(names=sd['Flag'], to='ISO3')
sd['Flag_code'] = sd['Flag'].map(country_map).fillna(sd['Flag_code'])

sd['Build_code'] = coco.convert(names=sd['Build'], to='ISO3')  
sd['Build_code'] = sd['Build'].map(country_map).fillna(sd['Build_code'])

sd['Owner_code'] = coco.convert(names=sd['Owner'], to='ISO3')  
sd['Owner_code'] = sd['Owner'].map(country_map).fillna(sd['Owner_code'])

sd.loc[:, 'Flag'] = coco.convert(names=sd['Flag_code'], to='name_short')
sd.loc[:, 'Build'] = coco.convert(names=sd['Build_code'], to='name_short')
sd.loc[:, 'Owner'] = coco.convert(names=sd['Owner_code'], to='name_short')

############# save ship dataset ###########################################################################################################################################################################################

print('Ship number:', sd.shape)
print('Final ship number:', sd.shape)
sd.set_index('IMO', inplace=True, drop=True)
sd.to_csv(add + '/03-results/sd_0.csv')

############# ships by country flag ###########################################################################################################################################################################################

sd = pd.read_csv(add + '/03-results/sd_0.csv')

countries=sd.loc[:, 'Flag_code'].unique().tolist()
countries.sort(key=str.lower)
country_ship_flag=pd.DataFrame(np.zeros((len(countries), len(ship_type_list))), columns=ship_type_list)
country_ship_flag.loc[:,'Flag_code']=countries
country_ship_flag.set_index('Flag_code', inplace=True, drop=True)
country_material_flag=pd.DataFrame(country_ship_flag*0.0)

for i in countries:
    for j in ship_type_list:
        country_ship_flag.loc[i,j]=sd.loc[(sd.Flag_code==i) & (sd.Type_Diogo==j)]['LDT'].sum()
        country_material_flag.loc[i,j]=np.sum(sd.loc[(sd.Flag_code==i) & (sd.Type_Diogo==j)][material_list].sum())

country_ship_flag.loc[:,'Total']=country_ship_flag.loc[:,ship_type_list].sum(axis=1)
country_ship_flag = country_ship_flag.sort_values(by='Total', ascending=False)
country_ship_flag.loc[:,'Share']=country_ship_flag.loc[:,'Total']/country_ship_flag.loc[:,'Total'].sum()

country_material_flag.loc[:,'Total']=country_material_flag.loc[:,ship_type_list].sum(axis=1)
country_material_flag = country_material_flag.sort_values(by='Total', ascending=False)
country_material_flag.loc[:,'Share']=country_material_flag.loc[:,'Total']/country_material_flag.loc[:,'Total'].sum()

country_ship_flag.to_csv(add + '/03-results/country_ship_Flag.csv')     
country_material_flag.to_csv(add + '/03-results/country_material_Flag.csv')

############# ships by country build ###########################################################################################################################################################################################

sd = pd.read_csv(add + '/03-results/sd_0.csv')

countries=sd.loc[:, 'Build_code'].unique().tolist()
countries.sort(key=str.lower)
country_ship_build=pd.DataFrame(np.zeros((len(countries), len(ship_type_list))), columns=ship_type_list)
country_ship_build.loc[:,'Build_code']=countries
country_ship_build.set_index('Build_code', inplace=True, drop=True)
country_material_build=pd.DataFrame(country_ship_build*0.0)

for i in countries:
    for j in ship_type_list:
        country_ship_build.loc[i,j]=sd.loc[(sd.Build_code==i) & (sd.Type_Diogo==j)]['LDT'].sum()
        country_material_build.loc[i,j]=np.sum(sd.loc[(sd.Build_code==i) & (sd.Type_Diogo==j)][material_list].sum())

country_ship_build.loc[:,'Total']=country_ship_build.loc[:,ship_type_list].sum(axis=1)
country_ship_build = country_ship_build.sort_values(by='Total', ascending=False)
country_ship_build.loc[:,'Share']=country_ship_build.loc[:,'Total']/country_ship_build.loc[:,'Total'].sum()

country_material_build.loc[:,'Total']=country_material_build.loc[:,ship_type_list].sum(axis=1)
country_material_build = country_material_build.sort_values(by='Total', ascending=False)
country_material_build.loc[:,'Share']=country_material_build.loc[:,'Total']/country_material_build.loc[:,'Total'].sum()

country_ship_build.to_excel(add + '/03-results/country_ship_Build.xlsx')     
country_material_build.to_excel(add + '/03-results/country_material_Build.xlsx')

############# ships by country Owner ###########################################################################################################################################################################################

sd = pd.read_csv(add + '/03-results/sd_0.csv')

countries=sd.loc[:, 'Owner_code'].unique().tolist()
countries.sort(key=str.lower)
country_ship_Owner=pd.DataFrame(np.zeros((len(countries), len(ship_type_list))), columns=ship_type_list)
country_ship_Owner.loc[:,'Owner_code']=countries
country_ship_Owner.set_index('Owner_code', inplace=True, drop=True)
country_material_Owner=pd.DataFrame(country_ship_Owner*0.0)

for i in countries:
    for j in ship_type_list:
        country_ship_Owner.loc[i,j]=sd.loc[(sd.Owner_code==i) & (sd.Type_Diogo==j)]['LDT'].sum()
        country_material_Owner.loc[i,j]=np.sum(sd.loc[(sd.Owner_code==i) & (sd.Type_Diogo==j)][material_list].sum())

country_ship_Owner.loc[:,'Total']=country_ship_Owner.loc[:,ship_type_list].sum(axis=1)
country_ship_Owner = country_ship_Owner.sort_values(by='Total', ascending=False)
country_ship_Owner.loc[:,'Share']=country_ship_Owner.loc[:,'Total']/country_ship_Owner.loc[:,'Total'].sum()

country_material_Owner.loc[:,'Total']=country_material_Owner.loc[:,ship_type_list].sum(axis=1)
country_material_Owner = country_material_Owner.sort_values(by='Total', ascending=False)
country_material_Owner.loc[:,'Share']=country_material_Owner.loc[:,'Total']/country_material_Owner.loc[:,'Total'].sum()

country_ship_Owner.to_excel(add + '/03-results/country_ship_Owner.xlsx')     
country_material_Owner.to_excel(add + '/03-results/country_material_Owner.xlsx')

############# ships by period ###########################################################################################################################################################################################

sd = pd.read_csv(add + '/03-results/sd_0.csv')

periods=sd.loc[:, 'Period'].unique().tolist()
periods.sort(key=str.lower)
periods_ship=pd.DataFrame(np.zeros((len(periods), len(ship_type_list))), columns=ship_type_list)
periods_ship.loc[:,'Period']=periods
periods_ship.set_index('Period', inplace=True, drop=True)
periods_material=pd.DataFrame(periods_ship*0.0)

for i in periods:
    for j in ship_type_list:
        periods_ship.loc[i,j]=sd.loc[(sd.Period==i) & (sd.Type_Diogo==j)]['LDT'].sum()
        periods_material.loc[i,j] = np.sum(sd.loc[(sd.Period==i) & (sd.Type_Diogo==j)][material_list].sum())

periods_ship.to_excel(add + '/03-results/period_ship.xlsx')     
periods_material.to_excel(add + '/03-results/period_material.xlsx')

end = tm.perf_counter()  # 记录结束时间
print(f"代码执行时间: {end - start:.6f} 秒")


