"""
Filename:    plotter.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for plotting
"""

# Import Python modules

import os, sys
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import colorsys
import cmocean.cm as cmo
from matplotlib.colors import LinearSegmentedColormap # Linear interpolation for color maps
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib import cm, colors as clr
from matplotlib.colorbar import Colorbar # different way to handle colorbar
import matplotlib.animation as animation
import pandas as pd
import matplotlib.gridspec as gridspec
import seaborn as sns
## import personal modules
import globalvars

class FixPointNormalize(mcolors.Normalize):
    """ 
    Inspired by https://stackoverflow.com/questions/20144529/shifted-colorbar-matplotlib
    Subclassing Normalize to obtain a colormap with a fixpoint 
    somewhere in the middle of the colormap.

    This may be useful for a `terrain` map, to set the "sea level" 
    to a color in the blue/turquise range. 
    """
    def __init__(self, vmin=None, vmax=None, sealevel=0, col_val = 0.21875, clip=False):
        # sealevel is the fix point of the colormap (in data units)
        self.sealevel = sealevel
        # col_val is the color value in the range [0,1] that should represent the sealevel.
        self.col_val = col_val
        mcolors.Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        x, y = [self.vmin, self.sealevel, self.vmax], [0, self.col_val, 1]
        return np.ma.masked_array(np.interp(value, x, y))

def terrain_cmap(vmax=3000):
    # make a colormap that has land and ocean clearly delineated and of the
    # same length (256 + 256)
    colors_undersea = plt.cm.terrain(np.linspace(0, 0.17, 256))
    colors_land = plt.cm.terrain(np.linspace(0.25, 1, 256))
    all_colors = np.vstack((colors_undersea, colors_land))
    terrain_map = mcolors.LinearSegmentedColormap.from_list(
        'terrain_map', all_colors)
    # make the norm:  Note the center is offset so that the land has more
    # dynamic range:
    divnorm = mcolors.TwoSlopeNorm(vmin=-0.25, vcenter=1, vmax=vmax)

    return terrain_map, divnorm

def plot_terrain(ax, ext, vmax, greyscale=True, zorder=100):
    fname = '/cw3e/mead/projects/cwp162/data/downloads/ETOPO1_Bed_c_gmt4.grd'
    datacrs = ccrs.PlateCarree()
    grid = xr.open_dataset(fname, engine='netcdf4')
    grid = grid.where(grid.z > 0) # mask below sea level
    grid = grid.sel(x=slice(ext[0], ext[1]), y=slice(ext[2], ext[3]))
    if greyscale == True:
        cmap = cmo.gray_r
        bnds = np.arange(0, vmax, 250)
        norm = mcolors.BoundaryNorm(bnds, cmap.N)
        cs = ax.pcolormesh(grid.x, grid.y, grid.z, vmin=0, vmax=vmax,
                            cmap=cmo.gray_r, transform=datacrs, alpha=0.7, zorder=zorder)
    # else:
    #     terrain_map, divnorm = terrain_cmap(vmax)
    #     cs = ax.pcolormesh(grid.x, grid.y, grid.z, rasterized=True, norm=divnorm,
    #                         cmap=terrain_map, shading='auto', transform=datacrs, alpha=0.6, zorder=zorder)

    else:
        norm = FixPointNormalize(sealevel=0, vmax=vmax)
        cs = ax.pcolormesh(grid.x, grid.y, grid.z, rasterized=True, norm=norm,
                           cmap=plt.cm.terrain, shading='auto', transform=datacrs, alpha=0.6, zorder=zorder)
    
    return ax, cs

def set_font(current_dpi, scaling_factor):
    fm.fontManager.addfont(globalvars.path_to_repo+'modules/helvetica.ttc')

    plt.rcParams.update({
                    'font.family' : 'Helvetica',
                    'figure.dpi': current_dpi,
                    'font.size': 8 * scaling_factor, #changes axes tick label
                    'axes.labelsize': 8 * scaling_factor,
                    'axes.titlesize': 8 * scaling_factor,
                    'xtick.labelsize': 8 * scaling_factor,#do nothing
                    'ytick.labelsize': 8 * scaling_factor, #do nothing
                    'legend.fontsize': 5 * scaling_factor,
                    'lines.linewidth': 0.7 * scaling_factor,
                    'axes.linewidth': 0.2 * scaling_factor,
                    'legend.fontsize': 12 * scaling_factor,
                    'xtick.major.width': 0.8 * scaling_factor,
                    'ytick.major.width': 0.8 * scaling_factor,
                    'xtick.minor.width': 0.6 * scaling_factor,
                    'ytick.minor.width': 0.6 * scaling_factor,
                    'lines.markersize': 6 * scaling_factor
                })
    
def make_brgr_white_cmap(cflevs, white_range):
    """
    Create a 'BrGr'-style diverging colormap with white at the center.

    Parameters
    ----------
    cflevs : array-like
        Contour levels (e.g., np.arange(-10, 11, 2)).
    white_range : tuple (low, high)
        Range of values to make white (e.g., (-2, 2)).

    Returns
    -------
    cmap : matplotlib.colors.ListedColormap
        Custom colormap with white center.
    norm : matplotlib.colors.BoundaryNorm
        Normalization for use in contourf/pcolormesh.
    """

    # Use Brewer "BrBG" diverging colormap
    base_cmap = plt.get_cmap('BrBG', len(cflevs) - 1)
    colors = base_cmap(np.arange(len(cflevs) - 1))

    # Identify color bins that fall inside the white range
    mask = (cflevs[:-1] >= white_range[0]) & (cflevs[1:] <= white_range[1])

    # Set those bins to white
    colors[mask] = [1, 1, 1, 1]

    # Build new colormap and norm
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(cflevs, ncolors=cmap.N, clip=True)

    return cmap, norm
    
def draw_basemap(ax, datacrs=ccrs.PlateCarree(), extent=None, xticks=None, yticks=None, grid=False, left_lats=True, right_lats=False, bottom_lons=True, mask_ocean=False, coastline=True):
    """
    Creates and returns a background map on which to plot data. 
    
    Map features include continents and country borders.
    Option to set lat/lon tickmarks and draw gridlines.
    
    Parameters
    ----------
    ax : 
        plot Axes on which to draw the basemap
    
    datacrs : 
        crs that the data comes in (usually ccrs.PlateCarree())
        
    extent : float
        Set map extent to [lonmin, lonmax, latmin, latmax] 
        Default: None (uses global extent)
        
    grid : bool
        Whether to draw grid lines. Default: False
        
    xticks : float
        array of xtick locations (longitude tick marks)
    
    yticks : float
        array of ytick locations (latitude tick marks)
        
    left_lats : bool
        Whether to add latitude labels on the left side. Default: True
        
    right_lats : bool
        Whether to add latitude labels on the right side. Default: False
        
    Returns
    -------
    ax :
        plot Axes with Basemap
    
    Notes
    -----
    - Grayscale colors can be set using 0 (black) to 1 (white)
    - Alpha sets transparency (0 is transparent, 1 is solid)
    
    """
    ## some style dictionaries
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    kw_grid = {'linewidth': .5, 'color': 'k', 'linestyle': '--', 'alpha': 0.4}
    kw_ticks = {'length': 4, 'width': 0.5, 'pad': 2, 'color': 'black',
                         'labelsize': 10, 'labelcolor': 'dimgray'}

    # Use map projection (CRS) of the given Axes
    mapcrs = ax.projection
    
    if extent is None:
        ax.set_global()
    else:
        ax.set_extent(extent, crs=datacrs)
    
    # Add map features (continents and country borders)
    ax.add_feature(cfeature.LAND, facecolor='0.9')      
    ax.add_feature(cfeature.BORDERS, edgecolor='0.5', linewidth=0.4, zorder=199)
    if coastline == True:
        ax.add_feature(cfeature.COASTLINE, edgecolor='0.4', linewidth=0.4)
    if mask_ocean == True:
        ocean = cfeature.NaturalEarthFeature('physical', 'ocean', \
        scale='50m', edgecolor='none', facecolor='#89C2D9')
        ax.add_feature(ocean)
        
    ## Tickmarks/Labels
    ## Add in meridian and parallels
    if mapcrs == ccrs.NorthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
    elif mapcrs == ccrs.SouthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
        
    else:
        gl = ax.gridlines(crs=datacrs, draw_labels=True, **kw_grid)
        gl.top_labels = False
        gl.left_labels = left_lats
        gl.right_labels = right_lats
        gl.bottom_labels = bottom_lons
        gl.xlocator = mticker.FixedLocator(xticks)
        gl.ylocator = mticker.FixedLocator(yticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = kw_ticklabels
        gl.ylabel_style = kw_ticklabels
    
    
    # Gridlines
    if grid:
        gl.xlines = True
        gl.ylines = True
    else:
        gl.xlines = False
        gl.ylines = False
    
    # Add tick marks (no labels)
    ax.set_xticks(xticks, crs=datacrs)
    ax.set_yticks(yticks, crs=datacrs)
    ax.tick_params(labelbottom=False, labelleft=False, length=3, width=0.3, color='k')

    return ax
