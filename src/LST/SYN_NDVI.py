from LST.NDVI_utils import snow_filtering
from config.paths import SLSTR_path, path_bt
import xarray as xr
import numpy as np
from NDVI_utils import (open_sltsr,
                        open_amsr2,
                        filter_empty_var,
                        crop2roi,
                        threshold_ndvi,
                        cloud_filtering,
                        slstr_pixels_in_amsr2)
from plot_functions import plot_lst, plot_amsr2, boxplot_soil_veg
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")


if __name__=="__main__":

    NDVI = open_sltsr(path=SLSTR_path,
                   subdir_pattern=f"S3A_SL_2_LST____*",
                   date_pattern=r'___(\d{8})T(\d{4})',
                   variable_file="LST_ancillary_ds.nc",
                   # bbox= bbox
                        )

    LST= open_sltsr(path=SLSTR_path,
                   subdir_pattern=f"S3A_SL_2_LST____*",
                   date_pattern=r'___(\d{8})T(\d{4})',
                   variable_file="LST_in.nc",
                   # bbox= bbox
                        )

    AMSR2 = open_amsr2(path=path_bt,
                       sensor="AMSR2",
                       overpass="day",
                       subdir_pattern=f"20*",
                       file_pattern="amsr2_l1bt_*.nc",
                       date_pattern=r"_(\d{8})_",
                       time_start="2024-05-01",
                       time_stop="2025-07-01",
                       )

    _SLSTR = xr.merge([NDVI,LST])[["LST","NDVI"]]

    _SLSTR = cloud_filtering(_SLSTR) # Mask clouds (strict)
    _SLSTR = snow_filtering(_SLSTR) # Mask clouds (strict)

    SLSTR = filter_empty_var(_SLSTR, "NDVI") # Filter empty NDVI obs

    ##
    date = "2024-08-25"

    bbox =   [
    -98.14778655230879,
    35.62525958403951,
    -97.3774255778045,
    36.13940216587241
  ]
    ndvi_thres =0.5

    SLSTR_obs = SLSTR.sel(time=date, method="nearest")
    SLSTR_obs = crop2roi(SLSTR_obs.compute(),bbox)

    AMSR2_obs = AMSR2.sortby('time').sel(time=date, method="nearest")
    AMSR2_obs = crop2roi(AMSR2_obs.compute(),bbox)
    TSURF = AMSR2_obs["bt_36.5V"] * 0.893 + 44.8

    soil_temp, veg_temp = threshold_ndvi(lst = SLSTR_obs["LST"], ndvi = SLSTR_obs["NDVI"] ,ndvi_thres = ndvi_thres)

    LST_plot_params = {"x": "lon",
                       "y":"lat",
                       "cmap":"coolwarm",
                       "cbar_kwargs":{'label': 'LST [K]'},
                       "vmin":290,
                       "title": "LST"
                       }
    NDVI_plot_params = {
                        "x":"lon",
                        "y":"lat",
                        "cmap":"YlGn",
                        "cbar_kwargs":{'label':"NDVI [-]"},
                        "vmin" : 0,
                        "vmax" : 0.6,
                        "title" :"NDVI"
                       }
    AMSR2_plot_params = {
                        "cmap":"coolwarm",
                        "cbar_kwargs":{'label': 'LST [K]'},
                        "vmin": 290,
                        "vmax": 320,
        "title" : np.datetime_as_string(AMSR2_obs.time.values, unit='D')
                       }

    plot_lst(left_da = SLSTR_obs["LST"],
             right_da = SLSTR_obs["NDVI"],
             left_params=LST_plot_params,
             right_params= NDVI_plot_params)

    plot_amsr2(TSURF,AMSR2_plot_params)

##
    target_lat_bin = 2
    target_lon_bin = 2

    soil_subset = slstr_pixels_in_amsr2(soil_temp,
                          TSURF,
                          target_lat_bin,
                          target_lon_bin)

    veg_subset =  slstr_pixels_in_amsr2(veg_temp,
                          TSURF,
                          target_lat_bin,
                          target_lon_bin)

    plt.figure()
    soil_subset.plot(x="lon", y = "lat")
    plt.title("Soil")
    plt.show()
    plt.figure()
    veg_subset.plot(x="lon", y = "lat")
    plt.title("Vegetation")
    plt.show()

    boxplot_soil_veg(soil_subset,veg_subset,ndvi_thres)

##
    # soil_plot_params = {"x": "lon",
    #                    "y":"lat",
    #                    "cmap":"coolwarm",
    #                    "cbar_kwargs":{'label': 'Soil LST [K]'},
    #                    "vmin":290,
    #                     "vmax": 320,
    #                     "title": "Soil (NDVI<0.3) LST"
    #                    }
    # veg_plot_params = {
    #                     "x":"lon",
    #                     "y":"lat",
    #                     "cmap":"coolwarm",
    #                     "cbar_kwargs":{'label':"NDVI [-]"},
    #                     "vmin" : 290,
    #                     "vmax" : 320,
    #                     "title" :"Veg. (NDVI>0.3) LST"
    #                    }
    #
    # plot_lst(left_da = veg_temp,
    #          right_da = soil_temp,
    #          left_params=veg_plot_params,
    #          right_params= soil_plot_params)

##
