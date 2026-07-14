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
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from matplotlib.patches import Wedge
import numpy as np
from matplotlib.patches import Patch
import plotly.graph_objects as go

import seaborn as sns
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
    'Bulk carriers': '#8da0cb',          # 保留
    'Chemical tankers': '#9ecae1',       # 稍微偏绿一点
    'Container ships': '#ef8a62',        # 保留为唯一主暖色
    'Crude oil tankers': '#969696',      # 比现在更深一点（区分灰）
    'Gas tankers': '#fddbc7',            # 保留
    'General cargo ships': '#bcbddc',    # 蓝→紫灰，拉开和地图
    'Oil product tankers': '#f4a582',    # 保留
    'Refrigerated cargo ships': '#d9d9d9',# 保留
    'Ro-Ro cargo ships': '#e0f3f8'       # 偏青而非蓝
}

#################### Sankey diagram ############################

# 1.调色板

NPG_PALETTE = [
    '#1f78b4',  # 强蓝（Build 1）
    '#33a02c',  # 强绿（Build 2）
    '#e31a1c',  # 强红（Build 3）
    '#ff7f00',  # 强橙
    '#6a3d9a',  # 深紫
    '#b15928',  # 棕（工业/材料感）
    '#a6cee3',  # 浅蓝（次要）
    '#b2df8a',  # 浅绿
    '#fb9a99',  # 浅红
    '#fdbf6f'   # 浅橙
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

# 3. 节点构建（顺序 = 颜色稳定性的生命线）

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

# Owner → Flag（仍然用 Source 的颜色）
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

    # 节点字体控制
    textfont=dict(
        size=38,
        family='Helvetica',
        color='black'
    )

))


# 列标题
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
    # paper_bgcolor='white',
    # plot_bgcolor='white',
    margin=dict(l=0, r=0, t=0, b=60),
    annotations=annotations
)

# 6. 导出
safe_output_path = os.path.abspath(os.path.join(add, '04-figures', 'sankey.jpg'))
os.makedirs(os.path.dirname(safe_output_path), exist_ok=True)
fig_sankey.write_image(safe_output_path, scale=4)
# fig_sankey.write_image(add + '/04-figures/sankey.jpg', scale=4)
fig_sankey.show()


#################### Global governance fragmentation ############################

# ===== 字体风格设置 =====
mpl.rcParams.update({
    'font.family': 'sans-serif',       # 无衬线字体
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],  # 可选
    'font.size': 8,                     # 主字体大小
    'axes.titlesize': 9,                # 标题
    'axes.labelsize': 8,                # 坐标轴标签
    'xtick.labelsize': 7,               # x刻度字体
    'ytick.labelsize': 7,               # y刻度字体
    'legend.fontsize': 7,               # 图例
    'legend.title_fontsize': 8,
    'figure.titlesize': 10,             # 整体 figure 标题
    'axes.linewidth': 0.5,              # 坐标轴线宽
    'xtick.direction': 'out',           # 刻度向外
    'ytick.direction': 'out',
    'axes.edgecolor': '0.3',            # 坐标轴颜色稍浅
    'text.color': '0.1',                # 黑色文本
})


from matplotlib.gridspec import GridSpec
fig = plt.figure(figsize=(10, 10))

gs = GridSpec(
    nrows=2,      # 两行
    ncols=2,      # 两列
    height_ratios=[1.5, 1],
    width_ratios=[1.7, 1],
    hspace=-0.02,  # 行间距
    wspace=0.07   # 列间距
)

# 第一行：1 列，横跨两列
ax1 = fig.add_subplot(gs[0, :])

# 第二行：2 列
ax2 = fig.add_subplot(gs[1, 0])
ax3 = fig.add_subplot(gs[1, 1])

pos = ax2.get_position()   # [x0, y0, width, height]
ax2.set_position([
    pos.x0,
    pos.y0-0.045,   # ↓ 向下移动（0.02–0.08 之间微调）
    pos.width,
    pos.height*1.1
])

ax1.set_title(r"$\bf{a.}$ Global distribution of ship ownership", fontsize=12, color='black', loc='left', pad=10)
ax2.set_title(r"$\bf{b.}$ Material flows along the ship governance chain", fontsize=12, color='black', loc='left', pad=13)
ax3.set_title(r"$\bf{c.}$ Owner–flag ship tonnage", fontsize=12, color='black', loc='left', pad=0)

############# ax1 ###############################################################

# data
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
df['LDT']=df['LDT']/1e6 # To million LDT

gdf2['LDT'] = 0.0
for i in df.Owner_code.unique():
    if i in gdf2.SOC.unique():
        gdf2.loc[gdf2.SOC==i,'LDT']=df.loc[df.Owner_code==i ,'LDT'].sum()

# Ten-dash line
gdf1.plot(
    ax=ax1,
    color='black',
    edgecolor='#2f2f2f',
    linewidth=0.2,
    linestyle=(0, (5, 2)),
    zorder=5
)

# Owner map

cmap = mcolors.LinearSegmentedColormap.from_list(
    "NatureBlue_separated_plus",
    [
        "#f5f7fb",  # 1️⃣ 更亮的起点
        "#e3edf7",  # 2️⃣ 低值
        "#c6dbef",  # 3️⃣ 中低
        "#6baed6",  # 4️⃣ 中值
        "#3182bd",  # 5️⃣ 中高
        "#08519c",  # 6️⃣ 高值
        "#08306b"   # 7️⃣ 深值，保留蓝调，不至于过黑
    ]
)


# 绘制地图，不显示 legend

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

leg.get_frame().set_linewidth(0.25)     # 0.2–0.4 很 Nature
leg.get_frame().set_edgecolor('0.7')   # 深灰，比纯黑柔和

# ax1.set_axis_off()
ax1.set_xticks([])  # 隐藏 x 轴刻度
ax1.set_yticks([])  # 隐藏 y 轴刻度

xmin, ymin, xmax, ymax = gdf2.total_bounds
ax1.set_xlim(xmin, xmax)
ax1.set_ylim(ymin, ymax*1.1)

# top owners

country_ship_owner=pd.read_excel(add + '/03-results/country_ship_Owner.xlsx').set_index('Owner_code')
top_LDT_countries = (country_ship_owner.sort_values('Total', ascending=False).head(10)).index

def safe_centroid(gdf, projected_crs="EPSG:6933"):
    gdf_proj = gdf.to_crs(projected_crs)
    return gdf_proj.geometry.centroid.to_crs(gdf.crs)

gdf2['centroid'] = safe_centroid(gdf2)

# 固定饼图半径
xmin, ymin, xmax, ymax = ax1.get_xlim()[0], ax1.get_ylim()[0], ax1.get_xlim()[1], ax1.get_ylim()[1]
map_width = xmax - xmin
fixed_radius = map_width * 0.035

# 单独调整偏移（单位与 fixed_radius 一致）
def get_offset(ct, fixed_radius):
    if ct == 'CHN':  # 中国
        dx = fixed_radius * 0.1  # 向左
        dy = fixed_radius * 1.8     # 向上
    elif ct == 'SGP':  # 新加坡
        dx = fixed_radius * -1.5   # 向右
        dy = fixed_radius * -1    # 向下
    elif ct == 'MHL':  # 马绍尔群岛
        dx = fixed_radius * -1.3     # 向右
        dy = fixed_radius * -2.3     # 向上
    elif ct == 'JPN':  # 日本
        dx = fixed_radius * 1.5   # 向右
        dy = fixed_radius * 1     # 向上
    elif ct == 'LBR':  # 利比里亚
        dx = fixed_radius * -1    # 向左
        dy = fixed_radius * -1    # 向下
    elif ct == 'GRC':  # 希腊
        dx = fixed_radius * 1.5     # 向右
        dy = fixed_radius * -1  # 向下
    elif ct == 'DEU':  # 德国
        dx = fixed_radius * 1.5     # 向右
        dy = fixed_radius * 0.8   # 向上
    elif ct == 'KOR':  # 韩国
        dx = fixed_radius * 2   # 向右
        dy = fixed_radius * (-1.5)   # 向上
    elif ct == 'PAN':  # 巴拿马
        dx = fixed_radius * -1.5  # 向左
        dy = fixed_radius * -0.5  # 向下
    elif ct == 'GBR':  # 英国
        dx = fixed_radius * (-1)     # 向右
        dy = fixed_radius * 1   # 向上
    else:
        dx = 0
        dy = 0
    return dx, dy


for ct in top_LDT_countries:
    centroid = gdf2.loc[gdf2['SOC'] == ct, 'centroid'].values[0]
    cx, cy = centroid.x, centroid.y
         
    dx, dy = get_offset(ct, fixed_radius)
    x, y = cx + dx, cy + dy  # 饼图位置
    
    # 绘制连接线
    ax1.plot([cx, x], [cy, y], color='0.6', linewidth=0.4, zorder=4)
    
    # 绘制饼图
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
        x+text_x, y + fixed_radius*1.1,  # 饼图上方一点
        coco.convert(names=ct, to='name_short'),
        ha='center', va='bottom',
        fontsize=8.5,
        color='0.15',
        zorder=3
    )

# legend

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

ship_legend._legend_box.align = "left"   # 整体左对齐
ship_legend.get_title().set_ha('left')   # 标题文本左对齐

frame = ship_legend.get_frame()
frame.set_linewidth(0.25)   # 控制边框粗细（Nature 常用 0.2–0.4）
frame.set_edgecolor('0.7') # 浅灰，不抢视觉
frame.set_facecolor((1, 1, 1, 0.85))  # 半透明白底

# 保留原来的 LDT 图例
if orig_legend is not None:
    ax1.add_artist(orig_legend)


############# ax2 : bar for build country ###############################################################

sankey_fig=add + '/04-figures/sankey.jpg'

import matplotlib.image as mpimg

img = mpimg.imread(sankey_fig)

ax2.imshow(img)

ax2.axis('off')

ax2.imshow(img, extent=[0, 1, 0, 1])
ax2.imshow(img, aspect='auto')  # 根据 ax2 伸缩

############# ax3 : bar for build country ###############################################################

# ==========================
# 1. 数据读取与处理
# ==========================
df_raw = pd.read_csv(add + '/03-results/sd_0.csv')
df_raw['LDT'] = df_raw['LDT'] / 1e6  # Million LDT
df_raw['Type'] = df_raw['Type_Diogo']
df_raw = df_raw[['Build', 'Owner', 'Flag', 'Type', 'LDT']]

# 按 Owner / Flag 汇总
owner_ldt = df_raw.groupby('Owner')['LDT'].sum()
flag_ldt  = df_raw.groupby('Flag')['LDT'].sum()

# Top 10 by Owner
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

# 绘制横向条形图
ax3.barh(y_pos, -owner_vals, color=COLOR_OWNER, height=0.6, alpha=0.7, label='Owner')
ax3.barh(y_pos,  flag_vals, color=COLOR_FLAG,  height=0.6, alpha=0.7, label='Flag')

# 添加图例，放在子图下方
ax3.legend(
    loc='upper center',          # 上方居中
    bbox_to_anchor=(0.3, -0.06),# 下移到子图下方
    ncol=2,                      # 两列
    frameon=False,               # 无边框
    fontsize=9
)

ax3.text(0.67, -0.127, 'Unit: Million LDT', transform=ax3.transAxes, fontsize=9)



# 隐藏左侧 spine
ax3.spines['left'].set_visible(False)

# 绘制中轴线（零线）
ax3.axvline(0, color='0.2', linewidth=0.25)

# 设置国家名在中轴上
for y, country in zip(y_pos, countries):
    ax3.text(
        0-120, y, country,
        ha='left', va='center',
        fontsize=9, zorder=5
    )

# 隐藏其他多余 spines
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.spines['bottom'].set_linewidth(0.3)

ax3.tick_params(axis='y', left=False)
ax3.set_yticks([])  # 隐藏所有 y 轴刻度
ax3.tick_params(axis='x', labelsize=8)

max_val = max(owner_vals.max(), flag_vals.max())  # 取绝对值最大
margin = max_val * 0.1  # 留一点空白
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

# 设置画布大小，4列的布局建议增加宽度
fig = plt.figure(figsize=(12, 6))

# 创建一个 2行 4列 的网格布局
gs = fig.add_gridspec(2, 4, width_ratios=[2.0, 1, 1, 1])

# 1. ax1：占据第 0 到 1 行（全两行），第 0 列
ax1 = fig.add_subplot(gs[0:2, 0])
ax1.set_title('Cumulative emissions', fontsize=13)

# 2. 剩下的 6 个子图，分布在第 1, 2, 3 列
# 第一行（剩下的三个）
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])
ax4 = fig.add_subplot(gs[0, 3])

# 第二行（剩下的三个）
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
    start_year = y - 4   # 2030 -> 2026
    end_year = y         # 2030 -> 2030
    df_yearly.loc[start_year:end_year] = df_5y.loc[y].values/5

# print(df_yearly)
GHG_SSPs_Baseline_Reference=df_yearly.cumsum()
print(GHG_SSPs_Baseline_Reference)
# print(GHG_SSPs_Baseline_Reference)

df_5y = GHG_SSPs_Baseline_Reference_Low.copy()
years_full = np.arange(2025, 2101)
df_yearly = pd.DataFrame(index=years_full,columns=df_5y.columns,dtype=float)
df_yearly.loc[2025] = 0
for y in df_5y.index:
    start_year = y - 4   # 2030 -> 2026
    end_year = y         # 2030 -> 2030
    df_yearly.loc[start_year:end_year] = df_5y.loc[y].values/5
GHG_SSPs_Baseline_Reference_Low=df_yearly.cumsum()

df_5y = GHG_SSPs_Baseline_Reference_High.copy()
years_full = np.arange(2025, 2101)
df_yearly = pd.DataFrame(index=years_full,columns=df_5y.columns,dtype=float)
df_yearly.loc[2025] = 0
for y in df_5y.index:
    start_year = y - 4   # 2030 -> 2026
    end_year = y         # 2030 -> 2030
    df_yearly.loc[start_year:end_year] = df_5y.loc[y].values/5
GHG_SSPs_Baseline_Reference_High=df_yearly.cumsum()


SSP_COLORS = {
    'SSP1': '#1b9e77',  # 绿
    'SSP2': '#4d4d4d',  # 暗灰，替代黑色，更柔和
    'SSP3': '#d95f02',  # 橙
    'SSP4': '#7570b3',  # 紫
    'SSP5': '#e7298a'   # 红
}

# ===================== 不确定性区间（in-between shading） =====================

GHG_SSPs_Baseline_Reference.to_csv(add + '/04-figures/Fig2a.csv')

for col in GHG_SSPs_Baseline_Reference.columns:

    color = SSP_COLORS[col]
    y_ref  = GHG_SSPs_Baseline_Reference[col]
    y_low  = GHG_SSPs_Baseline_Reference_Low[col]
    y_high = GHG_SSPs_Baseline_Reference_High[col]

    # 阴影
    ax1.fill_between(
        GHG_SSPs_Baseline_Reference.index,
        y_low,
        y_high,
        color=color,
        alpha=0.15,
        linewidth=0,
        zorder=1
    )

    # 上下限虚线（不进图例）
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
# ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('GHG emissions (Mt CO$_2$-eq)', fontsize=11)

ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_linewidth(0.9)
ax1.spines['bottom'].set_linewidth(0.9)

ax1.tick_params(axis='both', which='major', length=4, width=0.8, labelsize=10)
ax1.tick_params(axis='both', which='minor', length=2, width=0.5)

ax1.set_xlim(2025, 2100)
# xticks = [2025] + list(range(2030, 2101, 10))
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
    'Bulk carriers': '#8da0cb',          # 保留
    'Chemical tankers': '#9ecae1',       # 稍微偏绿一点
    'Container ships': '#ef8a62',        # 保留为唯一主暖色
    'Crude oil tankers': '#969696',      # 比现在更深一点（区分灰）
    'Gas tankers': '#fddbc7',            # 保留
    'General cargo ships': '#bcbddc',    # 蓝→紫灰，拉开和地图
    'Oil product tankers': '#f4a582',    # 保留
    'Refrigerated cargo ships': '#d9d9d9',# 保留
    'Ro-Ro cargo ships': '#e0f3f8'       # 偏青而非蓝
}
colors = [ship_type_colors[ship] for ship in ship_type_list]

# 1. 明确子图分配
# ax2-ax6 用于画图 (共5个情境)
plot_axes = [ax2, ax3, ax4, ax5, ax6]
# ax7 专门留出做图例

# 2. 循环绘制 ax2-ax6
for scr, ax_sub in zip(scenario_list_Baseline[:5], plot_axes):
    # 读取与数据处理
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
    
    # df.loc[:, ship_type_list].plot(
    # kind='area', 
    # stacked=True, 
    # ax=ax_sub, 
    # legend=False,
    # alpha=0.85, 
    # color=colors,
    # linewidth=0)


    # 子图细节设置
    ax_sub.set_title(scr.replace('-Baseline',''), fontsize=12, pad=10) # 使用情境名作为标题
    ax_sub.set_ylabel('GHG emissions (Mt CO$_2$-eq)', fontsize=10)
    ax_sub.set_xlabel('') # 移除 X 轴标题 Year，保持简洁
    ax_sub.tick_params(direction='in', labelsize=7)
    ax_sub.tick_params(axis='x', rotation=90)

handles, labels = ax_sub.get_legend_handles_labels()

ax7.axis('off')

ax7.legend(
    handles[::-1],                  # <-- 逆序传入 handles
    labels[::-1],                   # <-- 逆序传入 labels
    loc='center',
    title='Ship types',             # 标题文本
    title_fontsize=12,             # 标题字体大小
    # title_fontweight='bold',       # 标题字体粗细 ('normal', 'bold', 'light')
    # title_alignment='center',      # 标题对齐 ('center', 'left', 'right')
    frameon=False,
    fontsize=10,
    handletextpad=0.8,             # 图例符号与标签间距
    labelspacing=0.5               # 标签之间的间距
)
########## 子图 ##########

plt.tight_layout()

output_path = add + '/04-figures/Fig2-SSP1-5 Cumualtive emissions.jpg'
plt.savefig(output_path, dpi=600, bbox_inches='tight')
plt.show()


# ==================================================================================================
# Figure 3 | SSP2 Baseline / 26 / 19 + Circular strategies
# ==================================================================================================

# ============================ 设置参数 ============================
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
    'Reference':             '#D3D3D3',  # 浅灰（保持弱化）

    # --- 供应侧技术簇 (Supply-side): 统一为暖色调 ---
    'Electricity_decarbonization':     '#E69F00',  # 暗橙（能源转型）
    'Green_steel':           '#F0E442',  # 亮金黄（绿钢/新技术，与暗橙天然属于一个色族）
    'Supply_side':           '#D55E00',  # 朱红/红棕（供应侧总体 = 橙 + 黄的渐进聚变）

    # --- 需求侧资源簇 (Demand-side): 统一为冷色调 ---
    'Lifetime_extension':    '#56B4E9',  # 天蓝（时间/延长寿命）
    'Material_recovery':     '#0072B2',  # 深蓝（空间/物质循环）
    'Demand_side':           '#009E73',  # 纯绿（需求侧总体 = 天蓝 + 深蓝合流后的生命绿）

    # --- 终极系统集成 ---
    'Integrated_strategies': '#332288'   # 深紫蓝（冷暖交融的系统终点）
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

fig, ax = plt.subplots(figsize=(14, 7), dpi=300)  # 大画布 & 高分辨率
bar_width = 0.105  # 每个柱宽
x_group = np.arange(len(energy_scenarios))

for g, e in enumerate(energy_scenarios):

    # Baseline 不包含 Electricity_decarbonization
    # if e == 'SSP2-Baseline':
    #     valid_scenarios = [s for s in scenarios if s != 'Electricity_decarbonization']
    # else:
    #     valid_scenarios = scenarios

    n = len(scenarios)
    offsets = (np.arange(n) - (n-1)/2) * bar_width  # 居中排列

    for i, s in enumerate(scenarios):
        val = df_total.loc[f'{e}_{s}', 'Total']
        color = strategy_colors[s]

        bar = ax.bar(
            x_group[g] + offsets[i],
            val,
            width=bar_width,
            color=color,
            # edgecolor='black',
            # linewidth=0.8,
            edgecolor='none'
        )

        # ------------------- 在柱子顶端添加数字 -------------------
        ax.text(
            x_group[g] + offsets[i],
            val + 0.005*df_total['Total'].max(),  # 顶端偏移
            f'{val:.0f}',
            ha='center', va='bottom',
            fontsize=10.5
        )

# ============================ X轴 & Y轴 ============================
ax.set_xticks(x_group)
ax.set_xticklabels(display_names, fontsize=12)

ax.tick_params(axis='y', labelsize=11)
ax.set_ylabel('Cumulative emissions (Mt CO$_2$-eq)', fontsize=14)
ax.set_ylim(0, df_total['Total'].max()*1.10)

# ============================ 样式 ============================
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.spines['left'].set_linewidth(0.8)
ax.spines['bottom'].set_linewidth(0.8)

# ax.yaxis.set_minor_locator(AutoMinorLocator())
ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.5)

# ============================ 图例 ============================
# 只显示每种策略一次
legend_scenarios = scenarios
# handles = [plt.Rectangle((0,0),1,1, color=strategy_colors[s], ec='black') for s in legend_scenarios]
handles = [
    plt.Rectangle((0,0), 1, 1,
                  facecolor=strategy_colors[s],
                  edgecolor='none')
    for s in legend_scenarios
]

legend_scenarios=[s.replace('_', ' ') for s in scenarios]
ax.legend(handles, legend_scenarios, frameon=False, fontsize=11, loc='upper right')

plt.tight_layout()

# ============================ 保存 ============================
# plt.savefig(add + '/04-figures/Fig-3-SSP2-RCPs-strategies.tiff', dpi=300, bbox_inches='tight')  # 高分辨率位图
plt.savefig(add + '/04-figures/Fig-3-SSP2-RCPs-strategies.jpg', dpi=600, bbox_inches='tight')  # 高分辨率位图
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
][::-1]  # <--- 在这里加一个切片，一键倒序

ax_legend.legend(
    handles=legend_handles, 
    loc="center left",     # 改为居中左侧，在空位中更好看
    ncol=1, 
    frameon=False, 
    fontsize=11,
    title="Ship Types",    # 可选：给图例加个标题
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

# --- 1. 顶刊色彩与参数配置 ---
# 请确保此前已定义好 ship_type_list 和 ship_type_colors 字典
colors = [ship_type_colors[ship_type] for ship_type in ship_type_list]

scenarios = ['SSP2-26', 'SSP2-19']
end_year = 2100

# 画布微调：移除全局 sharey=True 避免一二行纵轴强行统一而无法看清
fig, axes = plt.subplots(
    nrows=2, 
    ncols=2, 
    figsize=(9.0, 6.5),  # 稍微放高一点，给两行不同类型的图更充足的垂直空间
)
axes_flat = axes.flatten()

# 创建用于后两行统一纵轴的边界变量
max_inflow = 0
min_outflow = 0

# --- 2. 第一行：绘制 Ship Stock (堆叠面积图) ---
for i in range(2):
    ax = axes_flat[i]
    
    # 读取并归一化数据
    ship_stock = pd.read_csv(add + '/03-results/' + scenarios[i] + '/Reference/ship_stock.csv')
    ship_stock.set_index('year', drop=True, inplace=True)
    ship_stock.loc[:, ship_type_list] = ship_stock.loc[:, ship_type_list] / 1e9
    
    ship_stock.to_csv(add + '04-figures/Fig.S2_'+scenarios[i]+'_stock'+'.csv')
    
    # 绘制堆叠面积图
    ax.stackplot(
        ship_stock.index,
        ship_stock[ship_type_list].T,
        labels=ship_type_list,
        alpha=0.85, 
        colors=colors,
        edgecolor='white',
        linewidth=0.3
    )
    
    # X 轴精细化设置：确保 2025 刻度完美显现并对齐
    target_ticks = np.arange(2025, 2101, 15)  
    ax.set_xticks(target_ticks)
    ax.set_xticklabels(target_ticks, rotation=45, fontsize=8)
    ax.set_xlim(2025, 2100)
    
    # Y 轴格式化 (纠正单位为学术严谨的 LDT)
    max_y = np.sum(ship_stock.loc[end_year, ship_type_list]) * 1.1
    ax.set_ylim(0, max_y)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2f'))
    ax.tick_params(axis='both', which='major', labelsize=8)
    
    if i == 0:
        ax.set_ylabel("Ship stock (Billion DWT)", fontsize=9, weight="bold") 
    
    title_dict = {'SSP2-26': 'SSP2-RCP2.6', 'SSP2-19': 'SSP2-RCP1.9'}
    ax.set_title(title_dict.get(scenarios[i], scenarios[i]), loc='center', fontsize=10, weight="bold", pad=12)
    ax.set_xlabel("") 

# --- 3. 第二行：绘制 Ship Inflow & Outflow (双向条形图) ---
# 预读数据，提前统一第二行两个子图的 Y 轴范围，确保可比性
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

# 正式绘制第二行
for i in range(2, 4):
    ax = axes_flat[i]
    scen = scenarios[i-2]
    
    # 1. 干净利落地读取数据
    ship_inflow = pd.read_csv(add + '/03-results/' + scen + '/Reference/ship_inflow.csv').set_index('year', drop=True) / 1e6 / 5
    ship_outflow = pd.read_csv(add + '/03-results/' + scen + '/Reference/ship_outflow.csv').set_index('year', drop=True) * (-1) / 1e6 / 5
    
    ship_inflow.to_csv(add + '04-figures/Fig.S2_'+scen+'_inflow'+'.csv')
    ship_outflow.to_csv(add + '04-figures/Fig.S2_'+scen+'_outflow'+'.csv')
    
    print(scen)
    print(ship_inflow[ship_type_list].sum(axis=1) + ship_outflow[ship_type_list].sum(axis=1))
    
    # 2. 【核心减负】用 Pandas 优雅的一行流直接画完堆叠柱状图！
    ship_inflow[ship_type_list].plot(kind="bar", stacked=True, ax=ax, color=colors, width=0.7, alpha=0.85, legend=False)
    ship_outflow[ship_type_list].plot(kind="bar", stacked=True, ax=ax, color=colors, width=0.7, alpha=0.85, legend=False)
    
    # 3. 规整界面与基准线
    ax.axhline(y=0, color='black', linewidth=0.6)
    ax.set_xlabel("")
    
    # 3. 规整界面与基准线
    all_years = ship_inflow.index.astype(int).tolist()
    ticks = [all_years.index(y) for y in range(2030, 2101, 10) if y in all_years]
    labels = [int(y) for y in range(2030, 2101, 10) if y in all_years] # 强转 int
    ax.set_xticks(ticks) 
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8) # ha='right' 让斜体对齐更美观
    
    ax.set_xlim(-0.5, len(ship_inflow) - 0.5)
    
    # 5. 轴范围控制
    ax.set_ylim(global_y_min, global_y_max)
    ax.tick_params(axis='y', labelsize=8)
    
    # title_dict = {'SSP2-26': 'SSP2-RCP2.6', 'SSP2-19': 'SSP2-RCP1.9'}
    # ax.set_title(title_dict.get(scen, scen) + " Dynamics", loc='center', fontsize=10, weight="bold", pad=12)

# --- 4. 全局唯一公共图例（结合色彩一键倒序） ---
# 使用 [::-1] 倒序排列，保证图例自上而下的颜色顺序与堆叠图在视觉上的“由上至下”高度吻合
legend_handles = [
    mpatches.Patch(color=colors[k], label=ship_type_list[k]) 
    for k in range(len(ship_type_list))
][::-1]

fig.legend(
    handles=legend_handles, 
    loc="center right", 
    bbox_to_anchor=(1.06, 0.75), # 1.16 将图例稳妥推至子图最右侧边缘外，杜绝遮挡
    ncol=1, 
    frameon=False, 
    fontsize=9,
    title="Ship Types",
    title_fontsize=10,
    alignment='left'
)

# --- 5. 布局优化与高质量导出 ---
plt.tight_layout()
fig.subplots_adjust(right=0.82, hspace=0.2) # 预留18%的右侧空间给公用图例，并拉开上下两行间距

# 导出符合 Nature 子刊审稿标准的高清大图
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
    'Reference':             '#D3D3D3',  # 浅灰（保持弱化）

    # --- 供应侧技术簇 (Supply-side): 统一为暖色调 ---
    'Electricity_decarbonization':     '#E69F00',  # 暗橙（能源转型）
    'Green_steel':           '#F0E442',  # 亮金黄（绿钢/新技术，与暗橙天然属于一个色族）
    'Supply_side':           '#D55E00',  # 朱红/红棕（供应侧总体 = 橙 + 黄的渐进聚变）

    # --- 需求侧资源簇 (Demand-side): 统一为冷色调 ---
    'Lifetime_extension':    '#56B4E9',  # 天蓝（时间/延长寿命）
    'Material_recovery':     '#0072B2',  # 深蓝（空间/物质循环）
    'Demand_side':           '#009E73',  # 纯绿（需求侧总体 = 天蓝 + 深蓝合流后的生命绿）

    # --- 终极系统集成 ---
    'Integrated_strategies': '#332288'   # 深紫蓝（冷暖交融的系统终点）
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
       # df.set_index('year',drop=True,inplace=True)
       df['Total']=df[material_list].sum(axis=1)/1e9/5 #average to per year
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
    loc="center left",     # 改为居中左侧，在空位中更好看
    ncol=1, 
    frameon=False, 
    fontsize=10,
    title="Scenarios",    # 可选：给图例加个标题
    title_fontsize=12
)        

plt.tight_layout()
# fig.savefig(add + '04-figures/Fig-S2-Annual GHG under SSP2-based pathways.tiff', dpi=600, bbox_inches='tight')
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

# --- 1. 统一色阶设置 ---
# 根据你的数据范围（约 3.8 到 6.9 Gt），手动设定统一的色标尺
v_min, v_max = 2, 8
fixed_levels = np.linspace(v_min, v_max, 10)

for i, strategy in enumerate(strategies):
    ax = axes[i]

    # 读取数据
    full_save_path = os.path.join(add, '03-results', 'Sensitivity', f"{strategy}.csv")
    df = pd.read_csv(full_save_path)
    df = df.set_index('Lifetime')
    
    (df / 1e12).to_csv(add + '04-figures/Fig.S4_'+strategy+'.csv')
    
    x_coords = df.index.astype(int)          # Lifetime
    y_coords = df.columns.astype(float)*100  # Intensity %
    X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
    
    # 转换为 Gt 并转置以匹配 meshgrid
    Z = (df.values / 1e12).T 
    
    # --- 2. 核心：强制所有子图使用相同的 levels 和范围 ---
    # extend='both' 确保万一数据超出 3.5-7.5 范围也能正常显示颜色
    cp = ax.contourf(X_grid, Y_grid, Z, levels=fixed_levels, cmap='RdYlGn_r', alpha=0.9, extend='both')
    
    # --- 3. 统一 Colorbar 设置 ---
    cbar = fig.colorbar(cp, ax=ax, pad=0.02, shrink=1.0, aspect=15)
    cbar.set_label('$\mathrm{Gt\ CO_2}$-eq', rotation=90, labelpad=6, fontsize=9)
    # 强制 colorbar 的刻度显示我们定义的 fixed_levels
    cbar.set_ticks(fixed_levels)
    cbar.set_ticklabels([f"{x:.1f}" for x in fixed_levels])
    
    # 标题与标签设置
    ax.set_title(strategy.replace('_', ' '), pad=16, loc='left')
    ax.text(-0.08, 1.105, labels[i], transform=ax.transAxes, 
            fontsize=15, fontweight='bold', va='top')
    
    # 坐标轴美化
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel('Lifetime (Years)')
    ax.set_ylabel('Strategy intensity (%)', labelpad=0)

# 5. 整体布局优化

plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # 为总标题留出空间

fig.savefig(add + '04-figures/FigS4-Sensitivity.jpg', dpi=600, bbox_inches='tight')
plt.show()  
    

# ==================================================================================================
# Figure S5 | Material decarbonization potential per strategy
# ==================================================================================================


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, PercentFormatter

# ===== 全局参数设置 =====
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

# ===== 数据与变量 =====
scenarios = [ 'Electricity_decarbonization', 'Lifetime_extension', 'Material_recovery', 'Integrated_strategies']
material_list=['Steel', 'Glass_wool', 'Paint', 'Plastic', 'Ceramics', 'Copper', 'Bronze', 'Aluminium', 'Zinc', 'Wood']

# 颜色列表（柔和明亮，避免过多重复）
color_list = [
    "#1b9e77", "#66a61e", "#7570b3", "#e6ab02",
    "#a6761d", "#d95f02", "#666666", "#8dd3c7", "#b3de69"
]

# ===== 基础数据：Base scenario =====
df0 = pd.read_csv(add + '/03-results/SSP2-26/Reference/carbon_total.csv').set_index('year')

# ===== 创建子图 =====
fig, axes = plt.subplots(2, 2, figsize=(18, 12), dpi=300)
axes = axes.flatten()  # 扁平化便于索引

subplot_labels = ['a', 'b', 'c', 'd']

df_material_strategy=pd.DataFrame(np.zeros((len(material_list), len(scenarios))), columns=scenarios)
df_material_strategy['Material']=material_list
df_material_strategy.set_index('Material', inplace=True, drop=True)

for i, sc in enumerate(scenarios):
    
    ax = axes[i]
    
    # 左上角添加子图编号
    ax.text(
        -0.09, 1.07,                        # 位置：相对坐标
        subplot_labels[i],                   # a/b/c/d
        transform=ax.transAxes,              # 相对坐标
        fontsize=20,
        fontweight='bold',
        va='top', ha='left'
    )
    
    # 读取场景数据
    df = pd.read_csv(add + f'/03-results/SSP2-26/{sc}/carbon_total.csv').set_index('year')
    
    # 计算减碳潜力（比例，小数）
    df_reduction = (df0[material_list].sum(axis=0) - df[material_list].sum(axis=0)) / df0[material_list].sum(axis=0)
    print(df_reduction)
    df_material_strategy[sc]=df_reduction
    
    # 横坐标位置
    x = np.arange(len(material_list))
    
    # 柱状图
    bars = ax.bar(
        x, 
        df_reduction, 
        color=color_list[:len(material_list)], 
        width=0.65, 
        edgecolor='black', 
        alpha=0.85
    )
    
    # x轴标签
    ax.set_xticks(x)
    ax.set_xticklabels(material_list, rotation=45, ha='right', fontsize=14)
    
    # y轴百分比
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    
    # 添加柱顶百分比标签
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2, 
            height + 0.02,                  # 顶端稍偏移
            f"{height*100:.0f}%", 
            ha='center', va='bottom', fontsize=14
        )
    
    # 子图样式
    ax.set_title(sc.replace("_", " "), fontsize=18, pad=10)
    ax.tick_params(axis='y', labelsize=12)
    ax.set_ylabel("GHG Reduction Potential", fontsize=14, labelpad=-2)
    ax.grid(False)

# ===== 调整布局 =====
plt.tight_layout(rect=[0, 0.03, 1, 0.97])

# ===== 保存图形 =====
df_material_strategy.to_csv(add + '/04-figures/Fig.S5_Strategy potential by material.csv')

plt.savefig(add + '/04-figures/FigS5-Decarbonization potential by material.jpg', dpi=600, bbox_inches='tight')
plt.show()



# ==================================================================================================
# Figure S6 | primary vs. secondary supply
# ==================================================================================================


# ===== 全局参数设置 =====
plt.style.use("default")
plt.rcParams.update({
    'font.family': 'Arial',       # Nature/Science 常用字体
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

# ===== 数据与变量 =====
fig, axes = plt.subplots(2, 4, figsize=(14, 8), constrained_layout=False)

scenarios = ['Material_recovery', 'Demand_side']
material_list = ['Steel', 'Copper', 'Bronze', 'Aluminium']

color_list = [
    '#3182BD',  # 蓝色，沉稳、材料/基础
    '#FD8D3C'   # 橙色，强调、策略/能源
]

line_color = '#333333'


Recovery=pd.read_excel(add + '02-data sources/Recycling/Recovery_rate.xlsx', sheet_name='Sheet1')
Recovery.set_index('Material', inplace=True, drop=True)
            
# === 计算每种材料最大值（统一y轴范围） ===
material_max = {}

for mat in material_list:
    max_val = 0
    for sc in scenarios:
        df1 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{sc}/material_primary.csv')[material_list]/1e9
        df2 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{sc}/material_recycle.csv')[material_list]/1e9
        df3 = pd.read_csv(add + f'/03-results/SSP2-Baseline/{sc}/material_reuse.csv')[material_list]/1e9
        total = df1[mat] + df2[mat] + df3[mat]
        max_val = max(max_val, total.max())
    material_max[mat] = max_val * 1.15  # 略放大 15%

# ===== 主循环绘图 =====
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
        
        # === 主图堆叠柱 ===
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
        
        # 横坐标显示整数
        x = np.arange(len(df_total))
        ax.set_xticks(x)
        ax.set_xticklabels(df_total.index.astype(int), rotation=80, fontsize=8)

        # === 次轴曲线（关键修复）===
        
        x = np.arange(len(df_total))  # 与柱状图的横坐标对齐
        
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
        ax2.set_ylim(0, 1)  # 比例固定在 0–1
        ax2.set_yticks(np.linspace(0, 1, 5))
        ax2.set_yticklabels([f'{int(v*100)}%' for v in np.linspace(0, 1, 5)], fontsize=9)
        ax2.tick_params(axis='y', labelsize=9, width=0.8)
        
        # === y轴统一范围 ===
        ax.set_ylim(0, material_max[mat])
        ax.tick_params(axis='x', rotation=90, labelsize=8)
        ax.tick_params(axis='y', labelsize=9, width=0.8)
        ax.set_xlabel("")
        
        # ax.set_ylabel("" if j > 0 else scen, fontsize=14)
        if j > 0:
            ax.set_ylabel("")
        else:
            ax.set_ylabel("")  # 去掉默认的 ylabel
        
            # 第一列：scen（大字体）
            ax.text(
                -0.27, 0.5+0.01,          # x 更靠左（控制整体位置）
                scen.replace("_", " "),
                transform=ax.transAxes,
                va="center",
                ha="center",
                fontsize=14,
                rotation=90  # 旋转 90 度
            )
        
            # 第二列：mass (Mt)（小字体）
            ax.text(
                -0.16, 0.5,          # x 右移 → 变成第二列
                "Mass (Mt)",
                transform=ax.transAxes,
                va="center",
                ha="center",
                fontsize=12,
                rotation=90  # 旋转 90 度
            )
        
        if i==0:
            ax.set_title(mat, fontsize=14, pad=6)
        
        # === 细节优化 ===
        ax.grid(False)
        ax2.grid(False)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)
        ax.yaxis.set_minor_locator(AutoMinorLocator())


# ===== 全局图例与标题 =====
handles = [
    plt.matplotlib.patches.Patch(color=color_list[0], label='Secondary'),
    plt.matplotlib.patches.Patch(color=color_list[1], label='Primary'),
    plt.Line2D([], [], color='black', marker='o', linestyle='-', label='Secondary share')
]
fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False, fontsize=13, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout(rect=[0, 0.03, 1, 0.98])
plt.savefig(add + '04-figures/FigS6-Primary_vs_Secondary_supply.jpg', dpi=600, bbox_inches='tight')
plt.show()
