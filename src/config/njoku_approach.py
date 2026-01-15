import sys
import os

# Get the absolute path of the directory containing this script (src/config)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory (src)
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to sys.path if it's not there
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
import datetime
import os
import pandas as pd
from scipy.stats import pearsonr
from readers.Sat import BTData, LPRMData
import matplotlib
import numpy as np
matplotlib.use("Qt5Agg")
import xarray as xr
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import pandas as pd
import dask.array as da
from utilities.utils import (
    bbox,
    mpdi,
    extreme_hull_vals,
    find_common_coords,
    get_dates,
    convex_hull,
    pearson_corr,
    save_nc,
)
from utilities.retrieval_helpers import (
    soil_canopy_temperatures,
    interceptor,
    dummy_line, retrieve_LPRM,tiff_df
)
from utilities.plotting import scatter_density, plot_maps_LPRM, plot_maps_day_night, plot_timeseries
from config.paths import path_lprm, path_bt, path_aux
import lprm.retrieval.lprm_v6_1.par100m_v6_1 as par100
from lprm.retrieval.lprm_general import load_aux_file
from lprm.retrieval.lprm_v6_1.parameters import get_lprm_parameters_for_frequency
from lprm.satellite_specs import get_specs
from utilities.run_lprm import run_band


bt_path = "/home/ddkovacs/shares/climers/Projects/CCIplus_Soil_Moisture/07_data/LPRM/passive_input/coarse_resolution/"
overpass = "day"
sensor = "AMSR2"
# sat_band = "C1"
frequencies={'C1': 6.9, 'C2': 7.3, 'X': 10.7,'KU': 18.7, 'K': 23.8, 'Ka': 36.5}

start_date = "2024-06-01"
end_date = "2024-06-01"
# soil_only, canopy_only
pixel_type = "canopy_only"

datelist = get_dates(start_date, end_date, freq = "D")
avg_dict= {}
std_dict = {}

for sat_band in list(frequencies.keys())[0:1]: # Set this to the index which Freq. u want
    avg_list = []
    std_list = []
    for d in datelist:

        pattern = f"{sensor}_l1bt_{overpass}_{d.strftime("%Y%m%d")}_{25}km.nc"
        bt_filepath = os.path.join(bt_path,sensor,overpass, d.strftime("%Y%m"),pattern)

        bt_data = xr.open_dataset(bt_filepath).isel(time = 0)
        Tbv = bt_data[f"bt_{frequencies[sat_band]}V"]
        Tbh = bt_data[f"bt_{frequencies[sat_band]}H"]

        Teff  = (0.893 * bt_data[f"bt_36.5V"]) + 44.8

        SND = load_aux_file(0.25,"SND")
        CLY = load_aux_file(0.25,"CLY")
        BLD = load_aux_file(0.25,"BLD")

        specs = get_specs(sensor.upper())
        params = get_lprm_parameters_for_frequency(sat_band, specs.incidence_angle)
        freq = get_specs(sensor.upper()).frequencies[sat_band.upper()]

        sm, vod,_,_= run_band(
            Tbv.values.astype('double'),
            Tbh.values.astype('double'),
            Teff.values.astype('double'),
            SND,
            CLY,
            BLD,
            params.Q,
            params.w,
            0,
            specs.incidence_angle[0],
            params.h1,
            params.h2,
            params.vod_Av,
            params.vod_Bv,
            float(freq),
            params.temp_freeze,
            False,
            None,
        )
        # smrun = np.array(smrun)
        # opt_run = np.array(opt_run)
        sm  = xr.where(sm>0,sm,np.nan)
        dataset = xr.DataArray(
            data=sm,
            dims=Tbv.dims,
            coords=Tbv.coords,
            name='sm'
        ).to_dataset()

        vod  = np.where(vod>0,vod,np.nan)

        dataset["vod"] = (("lat", "lon"),vod )

        plt.figure()
        ax = plt.gca()
        dataset["sm"].plot(ax=ax,vmin=0, vmax=1)
        def format_coord(x, y):
            try:
                val = dataset["sm"].sel(lon=x, lat=y, method="nearest").values
                return f"x={x:.4f}, y={y:.4f}, value={val:.4f}"
            except:
                return f"x={x:.4f}, y={y:.4f}"
        ax.format_coord = format_coord
        plt.show()

    avg_dict[sat_band] = avg_list
    std_dict[sat_band] = std_list




##
# x = np.array(datelist)
#
# plt.figure(figsize=(12, 7))
#
# for band in avg_dict.keys():
#     y = np.array(avg_dict[band])
#     std = np.array(std_dict[band])
#
#     p = plt.plot(x, y, label=band, linewidth=2)
#     color = p[0].get_color()
#
#     plt.fill_between(
#         x,
#         y - (std / 2),
#         y + (std / 2),
#         color=color,
#         alpha=0.2,  # Lower alpha for overlap visibility
#         edgecolor=None  # Removes border around the shade for a cleaner look
#     )
#
# plt.title(f"Time Series delta T {pixel_type}")
# plt.ylabel("$T_{Ka}$ - $T_{theory}$")  # Assuming dB based on typical backscatter data
# plt.legend(loc='best')  # Automatically finds the best spot for the legend
# plt.grid(True, alpha=0.3)
#
# # Rotate dates
# plt.xticks(rotation=45, ha='right')
#
# plt.tight_layout()
# plt.show()