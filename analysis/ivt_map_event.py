# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------
import os
import sys
import string
from pathlib import Path
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import cmocean.cm as cmo
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Local modules
sys.path.append('../modules/')
import globalvars
from plotter import set_font


# --- IVT Data ---
ivt_file = '/cw3e/mead/projects/cwp162/data/downloads/ERA5_sfc/ivt/6hr/era5_namerica_025dg_6hr_ivt_2015.nc'
ivt = xr.open_dataset(ivt_file)
# print(ivt['p72.162'].attrs)

rename_dict = {'p71.162': 'uIVT', 'p72.162': 'vIVT', 
               'longitude': 'lon', 'latitude':'lat'}
ivt = ivt.rename(rename_dict)
ivt['IVT'] = np.sqrt(ivt['uIVT']**2 + ivt['vIVT']**2)

# ivt = ivt.sel(time='2023-01-01 06:00')
ivt = ivt.sel(time='2015-04-26 00:00')
print(ivt)

# ---------------------------------------------------------------------
# Setup Figure
# ---------------------------------------------------------------------
current_dpi = 300
base_dpi = 100
scaling_factor = (current_dpi / base_dpi) ** 0.3
set_font(current_dpi, scaling_factor)

fig = plt.figure(figsize=(10, 6), dpi=current_dpi)
gs = gridspec.GridSpec(
    nrows=1, ncols=2,
    width_ratios=[1, 0.05],
    height_ratios=[1],
    wspace=0.05, hspace=0.08
)
cax = fig.add_subplot(gs[0, -1])  # colorbar axis

datacrs = ccrs.PlateCarree()
mapcrs = ccrs.Mercator()

# ---------------------------------------------------------------------
# (2) IVT Map Panel
# ---------------------------------------------------------------------
ax_ivt = fig.add_subplot(gs[0, 0], projection=mapcrs)
ax_ivt.set_extent([-135, -100, 23, 42], crs=datacrs)

for feat in [cfeature.COASTLINE, cfeature.BORDERS]:
    ax_ivt.add_feature(feat, lw=0.8)
ax_ivt.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0)
ax_ivt.add_feature(cfeature.OCEAN, facecolor='white', zorder=0)
ax_ivt.add_feature(cfeature.STATES.with_scale('50m'), edgecolor='gray', facecolor='none')


levels_ivt = np.arange(150, 850, 100)
cf_ivt = ax_ivt.contourf(
    ivt['lon'], ivt['lat'], ivt['IVT'],
    levels=levels_ivt, cmap=cmo.deep,
    transform=datacrs, extend='neither'
)

# IVT vectors
uvec = ivt['uIVT']
vvec = ivt['vIVT']
mask = ivt['IVT'] >= 250

Q = ax_ivt.quiver(
    ivt['lon'], ivt['lat'],
    uvec.where(mask).values, vvec.where(mask).values,
    transform=datacrs,
    color='k',
    regrid_shape=16,
    scale=7000  # bigger = shorter arrows
)
ax_ivt.quiverkey(Q, X=0.85, Y=0.03, U=250, label='250 kg m$^{-1}$ s$^{-1}$',
                 labelpos='E', coordinates='axes', fontproperties={'size':6})

# ---------------------------------------------------------------------
# Colorbar & Save
# ---------------------------------------------------------------------
cb = fig.colorbar(cf_ivt, cax=cax, orientation='vertical')
cb.set_label('IVT (kg m$^{-1}$ s$^{-1}$)', fontsize=11)
cb.ax.tick_params(labelsize=10)

output_path = Path('../figs/ivt_case.png')
fig.savefig(output_path, bbox_inches='tight', dpi=fig.dpi)
print(f"✅ Saved figure to: {output_path.resolve()}")