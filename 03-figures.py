# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 07:36:24 2026

@author: Xining Yang
"""

import os
add=str(os.getcwd()).replace('\\', '/').replace('01-script', '')
print(add)

import pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib as mpl
import matplotlib.colors as mcolors
from matplotlib.patches import Wedge
from matplotlib.patches import Patch
import plotly.graph_objects as go
import country_converter as coco

scenario_data=pd.read_excel(add + '02-data sources/ship_stock_yxn/SSP-based_demand_v08012026_yxn.xlsx')
ship_type_list=list(scenario_data['Ship_type'].unique())
print(ship_type_list)

MIC_ecoinvent=pd.read_excel(add + '02-data sources/MIC_yxn/ecoinvent_mic.xlsx', sheet_name='final')
MIC_ecoinvent.set_index('Diogo_scenario_types', inplace=True, drop=True)
material_list=MIC_ecoinvent.columns.tolist()

material_list_final=['Steel', 'Glass_wool', 'Paint', 'Plastic', 'Ceramics', 'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood']

start_year=2025
end_year=2100

year_list=list(range(start_year+5,2101,5))
year_list2=[start_year] + year_list

# ==================================================================================================
# Figure 1 | Global ship stock distribution, transnational governance chain and owner-flag mismatch
# ==================================================================================================

ship_type_colors = {
    'Bulk carriers': '#8da0cb',          
    'Chemical tankers': '#9ecae1',       
    'Container ships': '#ef8a62',        
    'Crude oil tankers': '#969696',      
    'Gas tankers': '#fddbc7',            
    'General cargo ships': '#bcbddc',    
    'Oil product tankers': '#f4a582',    
    'Refrigerated cargo ships': '#d9d9d9',
    'Ro-Ro cargo ships': '#e0f3f8'       
}

#################### Sankey diagram ############################

# 1.调色板

NPG_PALETTE = [
    '#1f78b4',
    '#33a02c',
    '#e31a1c',
    '#ff7f00',
    '#6a3d9a',
    '#b15928',
    '#a6cee3',
    '#b2df8a',
    '#fb9a99',
    '#fdbf6f'
]


def hex_to_rgba(hex_color, alpha=0.4):
    hex_color = hex_color.lstrip('#')
    r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    return f'rgba({r},{g},{b},{alpha})'

# 2. 数据读取与整理

df_raw = pd.read_csv(add + '/03-results/sd_0.csv')
df = df_raw[['Build', 'Owner', 'Flag', 'LDT']].copy()

def simplify(df, col, top_n, other='Others'):
    top = df.groupby(col)['LDT'].sum().nlargest(top_n).index
    return df[col].where(df[col].isin(top), other)

df['Source'] = simplify(df, 'Build', 6)
df['Middle'] = simplify(df, 'Owner', 6)
df['Target'] = simplify(df, 'Flag', 6)

# 3. 节点构建

src_nodes = sorted(df['Source'].unique())
mid_nodes = sorted(df['Middle'].unique())
tgt_nodes = sorted(df['Target'].unique())

assert len(src_nodes) <= len(NPG_PALETTE), "Nature 调色板不够长"

SRC_COLOR = dict(zip(src_nodes, NPG_PALETTE[:len(src_nodes)]))

all_nodes = (
    [f'{s} (Build)' for s in src_nodes] +
    [f'{m} (Owner)' for m in mid_nodes] +
    [f'{t} (Flag)'  for t in tgt_nodes]
)

node_id = {n: i for i, n in enumerate(all_nodes)}

node_colors = (
    [SRC_COLOR[s] for s in src_nodes] +
    ['#E0E0E0'] * len(mid_nodes) +
    ['#E0E0E0'] * len(tgt_nodes)
)

# 4. 连线（颜色只追踪 Source）

links = dict(source=[], target=[], value=[], color=[])

# Build → Owner
g1 = df.groupby(['Source', 'Middle'])['LDT'].sum().reset_index()
for _, r in g1.iterrows():
    links['source'].append(node_id[f"{r.Source} (Build)"])
    links['target'].append(node_id[f"{r.Middle} (Owner)"])
    links['value'].append(r.LDT)
    links['color'].append(hex_to_rgba(SRC_COLOR[r.Source], 0.45))

print(g1)
g1.to_csv(add + '/04-figures/Fig1b1.csv')

g2 = df.groupby(['Source', 'Middle', 'Target'])['LDT'].sum().reset_index()
for _, r in g2.iterrows():
    links['source'].append(node_id[f"{r.Middle} (Owner)"])
    links['target'].append(node_id[f"{r.Target} (Flag)"])
    links['value'].append(r.LDT)
    links['color'].append(hex_to_rgba(SRC_COLOR[r.Source], 0.40))

print(g2)
g2.to_csv(add + '/04-figures/Fig1b2.csv')

# 5. 绘图
fig_sankey = go.Figure(go.Sankey(
    node=dict(
        pad=28,
        thickness=11,
        line=dict(width=0),
        label=[n.split('(')[0] for n in all_nodes],
        color=node_colors
    ),
    link=links,

    textfont=dict(
        size=38,
        family='Helvetica',
        color='black'
    )

))


annotations = [
    dict(x=0.0, y=-0.06, text='Build country', xref='paper', yref='paper',
         showarrow=False, font=dict(size=38, family='Helvetica', color='black', weight='bold')),
    dict(x=0.5, y=-0.06, text='Owner country', xref='paper', yref='paper',
         showarrow=False, font=dict(size=38, family='Helvetica', color='black', weight='bold')),
    dict(x=1.0, y=-0.06, text='Flag country', xref='paper', yref='paper',
         showarrow=False, font=dict(size=38, family='Helvetica', color='black', weight='bold'))
]

fig_sankey.update_layout(
    font=dict(size=24, family='Helvetica'),
    width=1500,
    height=1000,
    margin=dict(l=0, r=0, t=0, b=60),
    annotations=annotations
)

# 6. 导出
safe_output_path = os.path.abspath(os.path.join(add, '04-figures', 'sankey.jpg'))
os.makedirs(os.path.dirname(safe_output_path), exist_ok=True)
fig_sankey.write_image(safe_output_path, scale=4)
fig_sankey.show()


#################### Global governance fragmentation ############################

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 8,                     
    'axes.titlesize': 9,                
    'axes.labelsize': 8,                
    'xtick.labelsize': 7,               
    'ytick.labelsize': 7,               
    'legend.fontsize': 7,               
    'legend.title_fontsize': 8,
    'figure.titlesize': 10,             
    'axes.linewidth': 0.5,              
    'xtick.direction': 'out',           
    'ytick.direction': 'out',
    'axes.edgecolor': '0.3',            
    'text.color': '0.1',                
})


from matplotlib.gridspec import GridSpec
fig = plt.figure(figsize=(10, 10))

gs = GridSpec(
    nrows=2,
    ncols=2,
    height_ratios=[1.5, 1],
    width_ratios=[1.7, 1],
    hspace=-0.02,
    wspace=0.07
)

ax1 = fig.add_subplot(gs[0, :])
ax2 = fig.add_subplot(gs[1, 0])
ax3 = fig.add_subplot(gs[1, 1])

pos = ax2.get_position()
ax2.set_position([
    pos.x0,
    pos.y0-0.045,
    pos.width,
    pos.height*1.1
])

ax1.set_title(r"$\bf{a.}$ Global distribution of ship ownership", fontsize=12, color='black', loc='left', pad=10)
ax2.set_title(r"$\bf{b.}$ Material flows along the ship governance chain", fontsize=12, color='black', loc='left', pad=13)
ax3.set_title(r"$\bf{c.}$ Owner–flag ship tonnage", fontsize=12, color='black', loc='left', pad=0)

############# ax1 ###############################################################

gdf1 = gpd.read_file(add + '02-data sources/Map/十段线.shp')
gdf2 = gpd.read_file(add + '02-data sources/Map/世界各国行政区划.shp')

gdf1 = gdf1.to_crs(epsg=4326)
gdf2 = gdf2.to_crs(epsg=4326)

df = pd.read_csv(add + '/03-results/sd_0.csv')
print(df.shape)
df=df[df.Owner_code!='not found']
print(df.shape)

print(df['DWT'].sum()/1e9)
print(df['LDT'].sum()/1e6)
df['LDT']=df['LDT']/1e6

gdf2['LDT'] = 0.0
for i in df.Owner_code.unique():
    if i in gdf2.SOC.unique():
        gdf2.loc[gdf2.SOC==i,'LDT']=df.loc[df.Owner_code==i ,'LDT'].sum()

gdf1.plot(
    ax=ax1,
    color='black',
    edgecolor='#2f2f2f',
    linewidth=0.2,
    linestyle=(0, (5, 2)),
    zorder=5
)

cmap = mcolors.LinearSegmentedColormap.from_list(
    "NatureBlue_separated_plus",
    [
        "#f5f7fb",
        "#e3edf7",
        "#c6dbef",
        "#6baed6",
        "#3182bd",
        "#08519c",
        "#08306b"
    ]
)

gdf2.plot(
    ax=ax1,
    scheme='natural_breaks',
    column="LDT",
    cmap=cmap,
    alpha=0.90,
    legend=True,
    edgecolor="black",
    linewidth=0.02,
    legend_kwds={
        'title': 'Million LDT',
        'loc': 'center left',
        'fontsize': 7,
        'title_fontsize': 8,
        'frameon': True
    }
)

leg = ax1.get_legend()
leg.set_bbox_to_anchor((0.006, 0.53))
leg._legend_box.align = "left"
leg.get_title().set_ha('left')

leg.get_frame().set_linewidth(0.25)
leg.get_frame().set_edgecolor('0.7')

ax1.set_xticks([])
ax1.set_yticks([])

xmin, ymin, xmax, ymax = gdf2.total_bounds
ax1.set_xlim(xmin, xmax)
ax1.set_ylim(ymin, ymax*1.1)

country_ship_owner=pd.read_excel(add + '/03-results/country_ship_Owner.xlsx').set_index('Owner_code')
top_LDT_countries = (country_ship_owner.sort_values('Total', ascending=False).head(10)).index

def safe_centroid(gdf, projected_crs="EPSG:6933"):
    gdf_proj = gdf.to_crs(projected_crs)
    return gdf_proj.geometry.centroid.to_crs(gdf.crs)

gdf2['centroid'] = safe_centroid(gdf2)

xmin, ymin, xmax, ymax = ax1.get_xlim()[0], ax1.get_ylim()[0], ax1.get_xlim()[1], ax1.get_ylim()[1]
map_width = xmax - xmin
fixed_radius = map_width * 0.035

def get_offset(ct, fixed_radius):
    if ct == 'CHN':  # 中国
        dx = fixed_radius * 0.1
        dy = fixed_radius * 1.8
    elif ct == 'SGP':  # 新加坡
        dx = fixed_radius * -1.5
        dy = fixed_radius * -1 
    elif ct == 'MHL':  # 马绍尔群岛
        dx = fixed_radius * -1.3     
        dy = fixed_radius * -2.3     
    elif ct == 'JPN':  # 日本
        dx = fixed_radius * 1.5   
        dy = fixed_radius * 1     
    elif ct == 'LBR':  # 利比里亚
        dx = fixed_radius * -1    
        dy = fixed_radius * -1    
    elif ct == 'GRC':  # 希腊
        dx = fixed_radius * 1.5     
        dy = fixed_radius * -1  
    elif ct == 'DEU':  # 德国
        dx = fixed_radius * 1.5     
        dy = fixed_radius * 0.8   
    elif ct == 'KOR':  # 韩国
        dx = fixed_radius * 2   
        dy = fixed_radius * (-1.5)   
    elif ct == 'PAN':  # 巴拿马
        dx = fixed_radius * -1.5  
        dy = fixed_radius * -0.5  
    elif ct == 'GBR':  # 英国
        dx = fixed_radius * (-1)     
        dy = fixed_radius * 1   
    else:
        dx = 0
        dy = 0
    return dx, dy


for ct in top_LDT_countries:
    centroid = gdf2.loc[gdf2['SOC'] == ct, 'centroid'].values[0]
    cx, cy = centroid.x, centroid.y
         
    dx, dy = get_offset(ct, fixed_radius)
    x, y = cx + dx, cy + dy 
    
    ax1.plot([cx, x], [cy, y], color='0.6', linewidth=0.4, zorder=4)
    
    values = country_ship_owner.loc[ct, ship_type_list].values
    total = values.sum()
    start_angle = 0
    for v, ship_type in zip(values, ship_type_list):
        if v <= 0:
            continue
        angle = 360 * v / total
        wedge = Wedge(
            (x, y),
            fixed_radius,
            start_angle,
            start_angle + angle,
            facecolor=ship_type_colors[ship_type],
            linewidth=0.25,
            zorder=3
        )
        ax1.add_patch(wedge)
        start_angle += angle
    
    if ct=='MHL':
        text_x=fixed_radius*-1
    else:
        text_x=0
        
    ax1.text(
        x+text_x, y + fixed_radius*1.1,
        coco.convert(names=ct, to='name_short'),
        ha='center', va='bottom',
        fontsize=8.5,
        color='0.15',
        zorder=3
    )

orig_legend = ax1.get_legend()

ship_handles = [Patch(facecolor=color, edgecolor='white', label=name)
                for name, color in ship_type_colors.items()]

ship_legend = ax1.legend(
    handles=ship_handles,
    title='Ship types',
    title_fontsize=8,
    loc='lower left',
    bbox_to_anchor=(0.005, 0.02),
    ncol=1,
    frameon=True,
    fontsize=7
)

ship_legend._legend_box.align = "left" 
ship_legend.get_title().set_ha('left') 

frame = ship_legend.get_frame()
frame.set_linewidth(0.25)
frame.set_edgecolor('0.7')
frame.set_facecolor((1, 1, 1, 0.85))

if orig_legend is not None:
    ax1.add_artist(orig_legend)


############# ax2 : bar for build country ###############################################################

sankey_fig=add + '/04-figures/sankey.jpg'

import matplotlib.image as mpimg

img = mpimg.imread(sankey_fig)

ax2.imshow(img)

ax2.axis('off')

ax2.imshow(img, extent=[0, 1, 0, 1])
ax2.imshow(img, aspect='auto')

############# ax3 : bar for build country ###############################################################

# ==========================
# 1. 数据读取与处理
# ==========================
df_raw = pd.read_csv(add + '/03-results/sd_0.csv')
df_raw['LDT'] = df_raw['LDT'] / 1e6
df_raw['Type'] = df_raw['Type_Diogo']
df_raw = df_raw[['Build', 'Owner', 'Flag', 'Type', 'LDT']]

owner_ldt = df_raw.groupby('Owner')['LDT'].sum()
flag_ldt  = df_raw.groupby('Flag')['LDT'].sum()

comparison_df = (
    pd.DataFrame({'Owner': owner_ldt, 'Flag': flag_ldt})
    .fillna(0)
    .sort_values('Owner', ascending=True)
    .tail(10)
)

countries = comparison_df.index.to_numpy()
owner_vals = comparison_df['Owner'].to_numpy()
flag_vals  = comparison_df['Flag'].to_numpy()

print(comparison_df)
comparison_df.to_csv(add + '/04-figures/Fig1c.csv')

# ==========================
# 2. 绘图设置
# ==========================

COLOR_OWNER = '#2b6ca3'
COLOR_FLAG  = '#e67e22'

y_pos = np.arange(len(countries))

ax3.barh(y_pos, -owner_vals, color=COLOR_OWNER, height=0.6, alpha=0.7, label='Owner')
ax3.barh(y_pos,  flag_vals, color=COLOR_FLAG,  height=0.6, alpha=0.7, label='Flag')

ax3.legend(
    loc='upper center',
    bbox_to_anchor=(0.3, -0.06),
    ncol=2,                      
    frameon=False,               
    fontsize=9
)

ax3.text(0.67, -0.127, 'Unit: Million LDT', transform=ax3.transAxes, fontsize=9)

ax3.spines['left'].set_visible(False)

ax3.axvline(0, color='0.2', linewidth=0.25)

for y, country in zip(y_pos, countries):
    ax3.text(
        0-120, y, country,
        ha='left', va='center',
        fontsize=9, zorder=5
    )

ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.spines['bottom'].set_linewidth(0.3)

ax3.tick_params(axis='y', left=False)
ax3.set_yticks([])
ax3.tick_params(axis='x', labelsize=8)

max_val = max(owner_vals.max(), flag_vals.max())
margin = max_val * 0.1
ax3.set_xlim(-120, 80)

output_path = add + '/04-figures/Fig-1-Ship stock and governance chain.jpg'
plt.savefig(output_path, dpi=600, bbox_inches='tight')
plt.show()


# ==================================================================================================
# Figure 2 | Cumulative GHG emissions of SSP1-5 Base
# ==================================================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

# =====================================
# Figure 1 | SSP1-5 Baseline cumulative GHG with in-between shading
# =====================================

fig = plt.figure(figsize=(12, 6))

gs = fig.add_gridspec(2, 4, width_ratios=[2.0, 1, 1, 1])

ax1 = fig.add_subplot(gs[0:2, 0])
ax1.set_title('Cumulative emissions', fontsize=13)

ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])
ax4 = fig.add_subplot(gs[0, 3])

ax5 = fig.add_subplot(gs[1, 1])
ax6 = fig.add_subplot(gs[1, 2])
ax7 = fig.add_subplot(gs[1, 3])


########## cumulative emissions ##########

scenario_list_Baseline = ['SSP1-Baseline', 'SSP2-Baseline', 'SSP3-Baseline', 
                          'SSP4-Baseline', 'SSP5-Baseline']
years = range(2030, 2101, 5)

material_list_final = ['Steel', 'Glass_wool', 'Paint', 'Plastic', 'Ceramics', 'Copper', 
                       'Bronze', 'Aluminium', 'Zinc', 'Wood']

GHG_SSPs_Baseline_Reference = pd.DataFrame(0, index=years, columns=scenario_list_Baseline)
GHG_SSPs_Baseline_Reference_Low = pd.DataFrame(0, index=years, columns=scenario_list_Baseline)
GHG_SSPs_Baseline_Reference_High = pd.DataFrame(0, index=years, columns=scenario_list_Baseline)

for scr in scenario_list_Baseline:
    df = pd.read_csv(f"{add}/03-results/{scr}/Reference/carbon_total.csv").set_index('year')
    GHG_SSPs_Baseline_Reference[scr] = df.loc[years, material_list_final].sum(axis=1)/1e9  # Mt
    
    df = pd.read_csv(f"{add}/03-results/{scr}/Reference_Low/carbon_total.csv").set_index('year')
    GHG_SSPs_Baseline_Reference_Low[scr] = df.loc[years, material_list_final].sum(axis=1)/1e9  # Mt    
    
    df = pd.read_csv(f"{add}/03-results/{scr}/Reference_High/carbon_total.csv").set_index('year')
    GHG_SSPs_Baseline_Reference_High[scr] = df.loc[years, material_list_final].sum(axis=1)/1e9  # Mt     
    

GHG_SSPs_Baseline_Reference.columns = GHG_SSPs_Baseline_Reference.columns.str.replace('-Baseline','',regex=False)
GHG_SSPs_Baseline_Reference_Low.columns = GHG_SSPs_Baseline_Reference_Low.columns.str.replace('-Baseline','',regex=False)
GHG_SSPs_Baseline_Reference_High.columns = GHG_SSPs_Baseline_Reference_High.columns.str.replace('-Baseline','',regex=False)

df_5y = GHG_SSPs_Baseline_Reference.copy()
years_full = np.arange(2025, 2101)
df_yearly = pd.DataFrame(index=years_full,columns=df_5y.columns,dtype=float)
df_yearly.loc[2025] = 0
for y in df_5y.index:
    start_year = y - 4   
    end_year = y         
    df_yearly.loc[start_year:end_year] = df_5y.loc[y].values/5

GHG_SSPs_Baseline_Reference=df_yearly.cumsum()
print(GHG_SSPs_Baseline_Reference)

df_5y = GHG_SSPs_Baseline_Reference_Low.copy()
years_full = np.arange(2025, 2101)
df_yearly = pd.DataFrame(index=years_full,columns=df_5y.columns,dtype=float)
df_yearly.loc[2025] = 0
for y in df_5y.index:
    start_year = y - 4   
    end_year = y         
    df_yearly.loc[start_year:end_year] = df_5y.loc[y].values/5
GHG_SSPs_Baseline_Reference_Low=df_yearly.cumsum()

df_5y = GHG_SSPs_Baseline_Reference_High.copy()
years_full = np.arange(2025, 2101)
df_yearly = pd.DataFrame(index=years_full,columns=df_5y.columns,dtype=float)
df_yearly.loc[2025] = 0
for y in df_5y.index:
    start_year = y - 4   
    end_year = y         
    df_yearly.loc[start_year:end_year] = df_5y.loc[y].values/5
GHG_SSPs_Baseline_Reference_High=df_yearly.cumsum()

SSP_COLORS = {
    'SSP1': '#1b9e77',  
    'SSP2': '#4d4d4d',  
    'SSP3': '#d95f02',  
    'SSP4': '#7570b3',  
    'SSP5': '#e7298a'   
}

# ===================== 不确定性区间（in-between shading） =====================

GHG_SSPs_Baseline_Reference.to_csv(add + '/04-figures/Fig2a.csv')

for col in GHG_SSPs_Baseline_Reference.columns:

    color = SSP_COLORS[col]
    y_ref  = GHG_SSPs_Baseline_Reference[col]
    y_low  = GHG_SSPs_Baseline_Reference_Low[col]
    y_high = GHG_SSPs_Baseline_Reference_High[col]

    ax1.fill_between(
        GHG_SSPs_Baseline_Reference.index,
        y_low,
        y_high,
        color=color,
        alpha=0.15,
        linewidth=0,
        zorder=1
    )

    ax1.plot(
        GHG_SSPs_Baseline_Reference.index,
        y_low,
        color=color,
        linestyle='-',
        linewidth=0.1,
        alpha=0.6,
        label='_nolegend_',
        zorder=2
    )

    ax1.plot(
        GHG_SSPs_Baseline_Reference.index,
        y_high,
        color=color,
        linestyle='-',
        linewidth=0.1,
        alpha=0.6,
        label='_nolegend_',
        zorder=2
    )

# ===================== Reference 主线 =====================
for col in GHG_SSPs_Baseline_Reference.columns:
    lw = 2.4 if col == 'SSP2' else 1.6
    ax1.plot(
        GHG_SSPs_Baseline_Reference.index,
        GHG_SSPs_Baseline_Reference[col],
        label=col,
        color=SSP_COLORS[col],
        linewidth=lw,
        zorder=3
    )

# ===================== 坐标轴与风格 =====================

ax1.set_ylabel('GHG emissions (Mt CO$_2$-eq)', fontsize=11)

ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_linewidth(0.9)
ax1.spines['bottom'].set_linewidth(0.9)

ax1.tick_params(axis='both', which='major', length=4, width=0.8, labelsize=10)
ax1.tick_params(axis='both', which='minor', length=2, width=0.5)

ax1.set_xlim(2025, 2100)
xticks = list(range(2030, 2101, 10))
ax1.set_xticks(xticks)
ax1.set_xticklabels(xticks, rotation=0)

ax1.yaxis.set_minor_locator(AutoMinorLocator())
ax1.margins(x=0.02)

ax1.set_ylim(0, GHG_SSPs_Baseline_Reference_High['SSP5'].max()*1.1)
ax1.set_xlabel('')

ax1.legend(
    frameon=False,
    fontsize=9,
    loc='upper left',
    handlelength=2.8
)


########## 子图 2-7 ##########

scenario_data=pd.read_excel(add + '02-data sources/ship_stock_yxn/SSP-based_demand_v08012026_yxn.xlsx')
ship_type_list=list(scenario_data['Ship_type'].unique())

ship_type_colors = {
    'Bulk carriers': '#8da0cb',  
    'Chemical tankers': '#9ecae1',       
    'Container ships': '#ef8a62',        
    'Crude oil tankers': '#969696',      
    'Gas tankers': '#fddbc7',            
    'General cargo ships': '#bcbddc',    
    'Oil product tankers': '#f4a582',    
    'Refrigerated cargo ships': '#d9d9d9',
    'Ro-Ro cargo ships': '#e0f3f8'       
}
colors = [ship_type_colors[ship] for ship in ship_type_list]

plot_axes = [ax2, ax3, ax4, ax5, ax6]

for scr, ax_sub in zip(scenario_list_Baseline[:5], plot_axes):
    
    df = pd.read_csv(f"{add}/03-results/{scr}/Reference/carbon_by_ship_all_primary.csv").astype(int).set_index('year')
    df[ship_type_list] = df[ship_type_list] / 1e9 / 5.0
    
    df.to_csv(add + '/04-figures/Fig2b_'+scr+'.csv')
    
    df.loc[:, ship_type_list].plot(
    kind='bar', 
    stacked=True, 
    ax=ax_sub, 
    width=0.8, 
    edgecolor='white',
    linewidth=0.3,
    legend=False,
    alpha=1,
    color=colors)
    
    ax_sub.set_title(scr.replace('-Baseline',''), fontsize=12, pad=10) 
    ax_sub.set_ylabel('GHG emissions (Mt CO$_2$-eq)', fontsize=10)
    ax_sub.set_xlabel('') 
    ax_sub.tick_params(direction='in', labelsize=7)
    ax_sub.tick_params(axis='x', rotation=90)

handles, labels = ax_sub.get_legend_handles_labels()

ax7.axis('off')

ax7.legend(
    handles[::-1],                  
    labels[::-1],                   
    loc='center',
    title='Ship types',             
    title_fontsize=12,             
    frameon=False,
    fontsize=10,
    handletextpad=0.8,             
    labelspacing=0.5               
)

plt.tight_layout()

output_path = add + '/04-figures/Fig2-SSP1-5 Cumualtive emissions.jpg'
plt.savefig(output_path, dpi=600, bbox_inches='tight')
plt.show()


# ==================================================================================================
# Figure 3 | SSP2 Baseline / 26 / 19 + Circular strategies
# ==================================================================================================

material_list_final = ['Steel', 'Glass_wool', 'Paint', 'Plastic', 'Ceramics', 
                       'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood']

scenarios = ['Reference',
             'Lifetime_extension', 'Material_recovery', 'Demand_side',
             'Electricity_decarbonization', 'Green_steel', 'Supply_side',
             'Integrated_strategies']

energy_scenarios = ['SSP2-Baseline', 'SSP2-26', 'SSP2-19']
display_names = ['Baseline', 'RCP2.6', 'RCP1.9']

strategy_colors = {
    # --- 基础/弱化基准 ---
    'Reference':             '#D3D3D3',

    # --- 供应侧技术簇 (Supply-side) ---
    'Electricity_decarbonization':     '#E69F00', 
    'Green_steel':           '#F0E442',  
    'Supply_side':           '#D55E00',  

    # --- 需求侧资源簇 (Demand-side) ---
    'Lifetime_extension':    '#56B4E9', 
    'Material_recovery':     '#0072B2',  
    'Demand_side':           '#009E73',  

    # --- 终极系统集成 ---
    'Integrated_strategies': '#332288'  
}

# ============================ 读取数据 ============================
df_total = pd.DataFrame(0.0, index=[f'{e}_{s}' for e in energy_scenarios for s in scenarios],
                        columns=['Total'])

for e in energy_scenarios:
    for s in scenarios:
        path_total = f"{add}/03-results/{e}/{s}/carbon_total.csv"
        df_total.loc[f'{e}_{s}','Total'] = pd.read_csv(path_total).set_index('year')[material_list_final].sum().sum()/1e9

df_total.to_csv(add + '/04-figures/RCPs-strategies-GHG.csv')

df_total.to_csv(add + '/04-figures/Fig3.csv')

# ============================ 绘图 ============================
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'Arial'
})

fig, ax = plt.subplots(figsize=(14, 7), dpi=300) 
bar_width = 0.105
x_group = np.arange(len(energy_scenarios))

for g, e in enumerate(energy_scenarios):

    n = len(scenarios)
    offsets = (np.arange(n) - (n-1)/2) * bar_width  

    for i, s in enumerate(scenarios):
        val = df_total.loc[f'{e}_{s}', 'Total']
        color = strategy_colors[s]

        bar = ax.bar(
            x_group[g] + offsets[i],
            val,
            width=bar_width,
            color=color,
            edgecolor='none'
        )

        ax.text(
            x_group[g] + offsets[i],
            val + 0.005*df_total['Total'].max(),  
            f'{val:.0f}',
            ha='center', va='bottom',
            fontsize=10.5
        )

ax.set_xticks(x_group)
ax.set_xticklabels(display_names, fontsize=12)

ax.tick_params(axis='y', labelsize=11)
ax.set_ylabel('Cumulative emissions (Mt CO$_2$-eq)', fontsize=14)
ax.set_ylim(0, df_total['Total'].max()*1.10)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.spines['left'].set_linewidth(0.8)
ax.spines['bottom'].set_linewidth(0.8)

ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.5)

legend_scenarios = scenarios
handles = [
    plt.Rectangle((0,0), 1, 1,
                  facecolor=strategy_colors[s],
                  edgecolor='none')
    for s in legend_scenarios
]

legend_scenarios=[s.replace('_', ' ') for s in scenarios]
ax.legend(handles, legend_scenarios, frameon=False, fontsize=11, loc='upper right')

plt.tight_layout()

plt.savefig(add + '/04-figures/Fig-3-SSP2-RCPs-strategies.jpg', dpi=600, bbox_inches='tight')
plt.show()


# ==================================================================================================
# Figure S1 | ship stock development under SSP1-5 Baseline
# ==================================================================================================

import matplotlib.patches as mpatches
import matplotlib.ticker as mtick

cmap = plt.get_cmap('Set3')
colors = [cmap(i) for i in range(cmap.N)]

colors = [ship_type_colors[ship_type] for ship_type in ship_type_list]

scenarios = [ 'SSP1-Baseline', 'SSP2-Baseline', 'SSP3-Baseline', 'SSP4-Baseline', 'SSP5-Baseline']

fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(10, 6))
axes_flat = axes.flatten()

for i in range(5):
    ax = axes_flat[i]
    
    ship_stock=pd.read_csv(add + '/03-results/' + scenarios[i] + '/Reference/ship_stock.csv')
    ship_stock.loc[:,ship_type_list]=ship_stock.loc[:,ship_type_list] 
    ship_stock.set_index('year',drop=True,inplace=True)
    ship_stock.loc[:, ship_type_list] = ship_stock.loc[:, ship_type_list]/1e9
    
    ship_stock.to_csv(add + '04-figures/Fig.S1_'+scenarios[i]+'.csv')
    
    print(scenarios[i])
    print(ship_stock)
    
    ax.stackplot(
    ship_stock.index,
    ship_stock[ship_type_list].T,
    labels=ship_type_list,
    alpha=0.7,
    colors=colors)
    
    ax.tick_params(axis='x', labelsize=8, rotation=45)
    ax.tick_params(axis='y', labelsize=10)

    ax.set_xlim(2025, 2100)
    ax.set_ylim(0, np.sum(ship_stock.loc[end_year,ship_type_list])*1.1)

    target_ticks = np.arange(2025, 2101, 5)
    ax.set_xticks(target_ticks)
    ax.set_xticklabels(target_ticks, rotation=90, fontsize=7)
    
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))

    ax.set_xlabel("") 
    ax.set_ylabel("Billion DWT", fontsize=8) 
    
    ax.set_title("SSP" + str(i+1), loc='center', fontsize=10, weight="bold", pad=10)


ax_legend = axes_flat[5] 
ax_legend.axis('off')

legend_handles = [
    mpatches.Patch(color=colors[i], label=ship_type_list[i]) 
    for i in range(len(ship_type_list))
][::-1]

ax_legend.legend(
    handles=legend_handles, 
    loc="center left",
    ncol=1, 
    frameon=False, 
    fontsize=11,
    title="Ship Types",
    title_fontsize=13
)

plt.tight_layout()

fig_s2_out_path = os.path.abspath(os.path.join(add, '04-figures', 'Fig-S1-Prospective_ship_stock_under_RCPs.jpg'))
os.makedirs(os.path.dirname(fig_s2_out_path), exist_ok=True)
fig.savefig(fig_s2_out_path, dpi=600, bbox_inches='tight')
plt.show()



# ==================================================================================================
# Figure S2 | Ship stock and flows under RCPs
# ==================================================================================================


import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np

colors = [ship_type_colors[ship_type] for ship_type in ship_type_list]

scenarios = ['SSP2-26', 'SSP2-19']
end_year = 2100

fig, axes = plt.subplots(
    nrows=2, 
    ncols=2, 
    figsize=(9.0, 6.5),
)
axes_flat = axes.flatten()

max_inflow = 0
min_outflow = 0

for i in range(2):
    ax = axes_flat[i]
    
    ship_stock = pd.read_csv(add + '/03-results/' + scenarios[i] + '/Reference/ship_stock.csv')
    ship_stock.set_index('year', drop=True, inplace=True)
    ship_stock.loc[:, ship_type_list] = ship_stock.loc[:, ship_type_list] / 1e9
    
    ship_stock.to_csv(add + '04-figures/Fig.S2_'+scenarios[i]+'_stock'+'.csv')
    
    ax.stackplot(
        ship_stock.index,
        ship_stock[ship_type_list].T,
        labels=ship_type_list,
        alpha=0.85, 
        colors=colors,
        edgecolor='white',
        linewidth=0.3
    )
    
    target_ticks = np.arange(2025, 2101, 15)  
    ax.set_xticks(target_ticks)
    ax.set_xticklabels(target_ticks, rotation=45, fontsize=8)
    ax.set_xlim(2025, 2100)
    
    max_y = np.sum(ship_stock.loc[end_year, ship_type_list]) * 1.1
    ax.set_ylim(0, max_y)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2f'))
    ax.tick_params(axis='both', which='major', labelsize=8)
    
    if i == 0:
        ax.set_ylabel("Ship stock (Billion DWT)", fontsize=9, weight="bold") 
    
    title_dict = {'SSP2-26': 'SSP2-RCP2.6', 'SSP2-19': 'SSP2-RCP1.9'}
    ax.set_title(title_dict.get(scenarios[i], scenarios[i]), loc='center', fontsize=10, weight="bold", pad=12)
    ax.set_xlabel("") 

inflow_data_list = []
outflow_data_list = []

for i in range(2, 4):
    scen = scenarios[i-2]
    inflow = pd.read_csv(add + '/03-results/' + scen + '/Reference/ship_inflow.csv').set_index('year', drop=True) / 1e6 / 5
    outflow = pd.read_csv(add + '/03-results/' + scen + '/Reference/ship_outflow.csv').set_index('year', drop=True) * (-1) / 1e6 / 5
    inflow_data_list.append(inflow)
    outflow_data_list.append(outflow)
    
    max_inflow = max(max_inflow, inflow[ship_type_list].sum(axis=1).max())
    min_outflow = min(min_outflow, outflow[ship_type_list].sum(axis=1).min())

global_y_max = max_inflow * 1.2
global_y_min = min_outflow * 1.2

for i in range(2, 4):
    ax = axes_flat[i]
    scen = scenarios[i-2]
    
    ship_inflow = pd.read_csv(add + '/03-results/' + scen + '/Reference/ship_inflow.csv').set_index('year', drop=True) / 1e6 / 5
    ship_outflow = pd.read_csv(add + '/03-results/' + scen + '/Reference/ship_outflow.csv').set_index('year', drop=True) * (-1) / 1e6 / 5
    
    ship_inflow.to_csv(add + '04-figures/Fig.S2_'+scen+'_inflow'+'.csv')
    ship_outflow.to_csv(add + '04-figures/Fig.S2_'+scen+'_outflow'+'.csv')
    
    print(scen)
    print(ship_inflow[ship_type_list].sum(axis=1) + ship_outflow[ship_type_list].sum(axis=1))
    
    ship_inflow[ship_type_list].plot(kind="bar", stacked=True, ax=ax, color=colors, width=0.7, alpha=0.85, legend=False)
    ship_outflow[ship_type_list].plot(kind="bar", stacked=True, ax=ax, color=colors, width=0.7, alpha=0.85, legend=False)
    
    ax.axhline(y=0, color='black', linewidth=0.6)
    ax.set_xlabel("")
    
    all_years = ship_inflow.index.astype(int).tolist()
    ticks = [all_years.index(y) for y in range(2030, 2101, 10) if y in all_years]
    labels = [int(y) for y in range(2030, 2101, 10) if y in all_years]
    ax.set_xticks(ticks) 
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8) 
    
    ax.set_xlim(-0.5, len(ship_inflow) - 0.5)
    
    ax.set_ylim(global_y_min, global_y_max)
    ax.tick_params(axis='y', labelsize=8)
    
legend_handles = [
    mpatches.Patch(color=colors[k], label=ship_type_list[k]) 
    for k in range(len(ship_type_list))
][::-1]

fig.legend(
    handles=legend_handles, 
    loc="center right", 
    bbox_to_anchor=(1.06, 0.75), 
    ncol=1, 
    frameon=False, 
    fontsize=9,
    title="Ship Types",
    title_fontsize=10,
    alignment='left'
)

plt.tight_layout()
fig.subplots_adjust(right=0.82, hspace=0.2) 

fig.savefig(add + '04-figures/FigS2-Prospective_ship_stock_under_RCPs.jpg', dpi=600, bbox_inches='tight')
plt.show()


# ==================================================================================================
# Figure S3 | Annual GHG emissions under SSP2-based pathways
# ==================================================================================================

SSP_scenarios = ['SSP2-Baseline', 'SSP2-26', 'SSP2-19']
SSP_scenarios_name = ['SSP2-Baseline', 'SSP2-RCP2.6', 'SSP2-RCP1.9']
Strategies = ['Reference',
             'Lifetime_extension', 'Material_recovery', 'Demand_side',
             'Electricity_decarbonization', 'Green_steel', 'Supply_side',
             'Integrated_strategies']

material_list=['Steel', 'Glass_wool', 'Paint', 'Plastic', 'Ceramics', 'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood']

strategy_colors =  {
    # --- 基础/弱化基准 ---
    'Reference':             '#D3D3D3',

    # --- 供应侧技术簇 (Supply-side) ---
    'Electricity_decarbonization':     '#E69F00',
    'Green_steel':           '#F0E442',  
    'Supply_side':           '#D55E00',  

    # --- 需求侧资源簇 (Demand-side) ---
    'Lifetime_extension':    '#56B4E9',
    'Material_recovery':     '#0072B2', 
    'Demand_side':           '#009E73', 

    # --- 终极系统集成 ---
    'Integrated_strategies': '#332288'
}

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 6))
axes_flat = axes.flatten()

for i in range(3):
    ax = axes_flat[i]
    
    print(SSP_scenarios[i])
    year_list=range(2030,2101,5)
    df_sc=pd.DataFrame(np.zeros((len(year_list),len(Strategies))), columns=Strategies)
    df_sc['year']=year_list
    df_sc.set_index('year', inplace=True, drop=True)
    
    for st in Strategies:
       df= pd.read_csv(add + '/03-results/' + SSP_scenarios[i] + '/' + str(st) + '/carbon_total.csv')
       df['Total']=df[material_list].sum(axis=1)/1e9/5
       df_sc[st]=df['Total'].tolist()
       
       full_years = pd.DataFrame({'year': range(2026, 2101)})
       df = pd.merge(full_years, df, on='year', how='left')
       df = df.bfill()
       df=df.loc[df.year.isin([2026]+list(range(2030,2101,5)))]
       
       ax.plot(df['year'], df['Total'], color=strategy_colors[st], linewidth=1.5, alpha=0.65)
    
    print(df_sc)
    df_sc.to_csv(add + '04-figures/Fig.S3_'+SSP_scenarios[i]+'.csv')
    
    target_ticks = np.arange(2025, 2101, 10)
    ax.set_xticks(target_ticks)
    ax.set_xticklabels(target_ticks, rotation=45, fontsize=9)
    ax.set_xlim(2025, 2100)
    
    ax.set_ylim(0, 100)

    ax.tick_params(axis='x', labelsize=8, rotation=0)
    ax.tick_params(axis='y', labelsize=10)

    ax.set_xlabel("") 
    ax.set_ylabel("Mt CO$_2$-eq", fontsize=9) 
    
    ax.set_title(SSP_scenarios_name[i], loc='center', fontsize=10, weight="bold", pad=10)       
       
       
ax_legend = axes_flat[3] 
ax_legend.axis('off')
legend_handles = [mpatches.Patch(color=strategy_colors[Strategies[i]], label=Strategies[i]) 
                  for i in range(len(Strategies))]

ax_legend.legend(
    handles=legend_handles, 
    loc="center left", 
    ncol=1, 
    frameon=False, 
    fontsize=10,
    title="Scenarios",
    title_fontsize=12
)        

plt.tight_layout()
fig.savefig(add + '04-figures/FigS3-Annual GHG under SSP2-based pathways.jpg', dpi=600, bbox_inches='tight')
plt.show()    


# ==================================================================================================
# Figure S4 | Annual GHG emissions under SSP2-based pathways
# ==================================================================================================

from matplotlib.ticker import MaxNLocator

strategies = ['Lifetime_extension', 'Material_recovery', 'Electricity_decarbonization', 'Green_steel']
labels = ['a.', 'b.', 'c.', 'd.']
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

v_min, v_max = 2, 8
fixed_levels = np.linspace(v_min, v_max, 10)

for i, strategy in enumerate(strategies):
    ax = axes[i]

    full_save_path = os.path.join(add, '03-results', 'Sensitivity', f"{strategy}.csv")
    df = pd.read_csv(full_save_path)
    df = df.set_index('Lifetime')
    
    (df / 1e12).to_csv(add + '04-figures/Fig.S4_'+strategy+'.csv')
    
    x_coords = df.index.astype(int)          
    y_coords = df.columns.astype(float)*100  
    X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
    
    Z = (df.values / 1e12).T 
    
    cp = ax.contourf(X_grid, Y_grid, Z, levels=fixed_levels, cmap='RdYlGn_r', alpha=0.9, extend='both')
    
    cbar = fig.colorbar(cp, ax=ax, pad=0.02, shrink=1.0, aspect=15)
    cbar.set_label('$\mathrm{Gt\ CO_2}$-eq', rotation=90, labelpad=6, fontsize=9)
    
    cbar.set_ticks(fixed_levels)
    cbar.set_ticklabels([f"{x:.1f}" for x in fixed_levels])
    
    ax.set_title(strategy.replace('_', ' '), pad=16, loc='left')
    ax.text(-0.08, 1.105, labels[i], transform=ax.transAxes, 
            fontsize=15, fontweight='bold', va='top')
    
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel('Lifetime (Years)')
    ax.set_ylabel('Strategy intensity (%)', labelpad=0)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

fig.savefig(add + '04-figures/FigS4-Sensitivity.jpg', dpi=600, bbox_inches='tight')
plt.show()  
    

# ==================================================================================================
# Figure S5 | Material decarbonization potential per strategy
# ==================================================================================================


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, PercentFormatter

plt.style.use("default")
plt.rcParams.update({
    'font.family': 'Arial',
    'axes.linewidth': 1.0,
    'axes.edgecolor': 'black',
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'figure.dpi': 300,
    'savefig.dpi': 600,
    'axes.facecolor': 'white',
    'figure.facecolor': 'white',
})


scenarios = [ 'Electricity_decarbonization', 'Lifetime_extension', 'Material_recovery', 'Integrated_strategies']
material_list=['Steel', 'Glass_wool', 'Paint', 'Plastic', 'Ceramics', 'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood']

color_list = [
    "#1b9e77", "#66a61e", "#7570b3", "#e6ab02",
    "#a6761d", "#d95f02", "#666666", "#8dd3c7", "#b3de69"
]

df0 = pd.read_csv(add + '/03-results/SSP2-26/Reference/carbon_total.csv').set_index('year')

fig, axes = plt.subplots(2, 2, figsize=(18, 12), dpi=300)
axes = axes.flatten()  

subplot_labels = ['a', 'b', 'c', 'd']

df_material_strategy=pd.DataFrame(np.zeros((len(material_list), len(scenarios))), columns=scenarios)
df_material_strategy['Material']=material_list
df_material_strategy.set_index('Material', inplace=True, drop=True)

for i, sc in enumerate(scenarios):
    
    ax = axes[i]
    
    ax.text(
        -0.09, 1.07,                        
        subplot_labels[i],                   
        transform=ax.transAxes,              
        fontsize=20,
        fontweight='bold',
        va='top', ha='left'
    )
    
    df = pd.read_csv(add + f'/03-results/SSP2-26/{sc}/carbon_total.csv').set_index('year')
    
    df_reduction = (df0[material_list].sum(axis=0) - df[material_list].sum(axis=0)) / df0[material_list].sum(axis=0)
    print(df_reduction)
    df_material_strategy[sc]=df_reduction
    
    x = np.arange(len(material_list))
    
    bars = ax.bar(
        x, 
        df_reduction, 
        color=color_list[:len(material_list)], 
        width=0.65, 
        edgecolor='black', 
        alpha=0.85
    )
    
    ax.set_xticks(x)
    ax.set_xticklabels(material_list, rotation=45, ha='right', fontsize=14)
    
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2, 
            height + 0.02,       
            f"{height*100:.0f}%", 
            ha='center', va='bottom', fontsize=14
        )
    
    ax.set_title(sc.replace("_", " "), fontsize=18, pad=10)
    ax.tick_params(axis='y', labelsize=12)
    ax.set_ylabel("GHG Reduction Potential", fontsize=14, labelpad=-2)
    ax.grid(False)

plt.tight_layout(rect=[0, 0.03, 1, 0.97])

df_material_strategy.to_csv(add + '/04-figures/Fig.S5_Strategy potential by material.csv')

plt.savefig(add + '/04-figures/FigS5-Decarbonization potential by material.jpg', dpi=600, bbox_inches='tight')
plt.show()



# ==================================================================================================
# Figure S6 | primary vs. secondary supply
# ==================================================================================================


plt.style.use("default")
plt.rcParams.update({
    'font.family': 'Arial',       
    'axes.linewidth': 1.0,
    'axes.edgecolor': 'black',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'figure.dpi': 400,
    'savefig.dpi': 600,
    'axes.facecolor': 'white',
    'figure.facecolor': 'white',
})

fig, axes = plt.subplots(2, 4, figsize=(14, 8), constrained_layout=False)

scenarios = ['Material_recovery', 'Demand_side']
material_list = ['Steel', 'Copper', 'Bronze', 'Aluminium']

color_list = [
    '#3182BD',  
    '#FD8D3C'   
]

line_color = '#333333'


Recovery=pd.read_excel(add + '02-data sources/Recycling/Recovery_rate.xlsx', sheet_name='Sheet1')
Recovery.set_index('Material', inplace=True, drop=True)
            
material_max = {}

for mat in material_list:
    max_val = 0
    for sc in scenarios:
        df1 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{sc}/material_primary.csv')[material_list]/1e9
        df2 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{sc}/material_recycle.csv')[material_list]/1e9
        df3 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{sc}/material_reuse.csv')[material_list]/1e9
        total = df1[mat] + df2[mat] + df3[mat]
        max_val = max(max_val, total.max())
    material_max[mat] = max_val * 1.15

for i, scen in enumerate(scenarios):
    df1 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{scen}/material_primary.csv').set_index('year')
    df2 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{scen}/material_recycle.csv').set_index('year')
    df3 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{scen}/material_reuse.csv').set_index('year')

    for j, mat in enumerate(material_list):
        ax = axes[i, j]
        
        df_total = pd.DataFrame({
            'Primary': df1[mat] / 1e9,
            'Secondary': (df2[mat] + df3[mat]) / 1e9
        })
        df_total['Share'] = df_total['Secondary'] / (df_total['Primary'] + df_total['Secondary'])
        df_total['Cumulative_Share'] = df_total['Secondary'].cumsum() / (df_total['Primary'].cumsum() + df_total['Secondary'].cumsum())
        df_total['Theoretical_Share']=Recovery.loc[mat, 'Reuse_rate']+Recovery.loc[mat, 'Recycle_rate']
        
        df_total.to_csv(add + '04-figures/Fig.S6_'+scen+'_'+mat+'.csv')
        
        bars = df_total[['Secondary', 'Primary']].plot(
            kind='bar',
            stacked=True,
            ax=ax,
            color=color_list,
            width=0.75,
            edgecolor='none',
            legend=False,
            alpha=0.8
        )
        
        x = np.arange(len(df_total))
        ax.set_xticks(x)
        ax.set_xticklabels(df_total.index.astype(int), rotation=80, fontsize=8)

        x = np.arange(len(df_total))
        
        ax2 = ax.twinx()
        ax2.plot(
            x,
            df_total['Share'],
            color='black',
            marker='o',
            markersize=3,
            linewidth=1.1,
            zorder=5,
            label='Secondary share'
        )
        ax2.set_ylim(0, 1)  
        ax2.set_yticks(np.linspace(0, 1, 5))
        ax2.set_yticklabels([f'{int(v*100)}%' for v in np.linspace(0, 1, 5)], fontsize=9)
        ax2.tick_params(axis='y', labelsize=9, width=0.8)
        
        ax.set_ylim(0, material_max[mat])
        ax.tick_params(axis='x', rotation=90, labelsize=8)
        ax.tick_params(axis='y', labelsize=9, width=0.8)
        ax.set_xlabel("")
        
        if j > 0:
            ax.set_ylabel("")
        else:
            ax.set_ylabel("")  
        
            ax.text(
                -0.27, 0.5+0.01,          
                scen.replace("_", " "),
                transform=ax.transAxes,
                va="center",
                ha="center",
                fontsize=14,
                rotation=90  
            )
        
            ax.text(
                -0.16, 0.5,          
                "Mass (Mt)",
                transform=ax.transAxes,
                va="center",
                ha="center",
                fontsize=12,
                rotation=90  
            )
        
        if i==0:
            ax.set_title(mat, fontsize=14, pad=6)
        
        ax.grid(False)
        ax2.grid(False)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)
        ax.yaxis.set_minor_locator(AutoMinorLocator())


handles = [
    plt.matplotlib.patches.Patch(color=color_list[0], label='Secondary'),
    plt.matplotlib.patches.Patch(color=color_list[1], label='Primary'),
    plt.Line2D([], [], color='black', marker='o', linestyle='-', label='Secondary share')
]
fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False, fontsize=13, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout(rect=[0, 0.03, 1, 0.98])
plt.savefig(add + '04-figures/FigS6-Primary_vs_Secondary_supply.jpg', dpi=600, bbox_inches='tight')
plt.show()
