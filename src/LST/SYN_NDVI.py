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
                        slstr_pixels_in_amsr2,
                        subset_statistics,
                        binning_smaller_pixels)
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
    # szerintem ebbol csinaljak majd egy functiont hetfon

    veg_mean_list = []
    veg_std_list = []

    soil_mean_list = []
    soil_std_list = []

    TSURF_list = []

    bin_dict = binning_smaller_pixels(SLSTR_obs["NDVI"], TSURF)

    for targetlon in np.unique(bin_dict["lons"]):
        for targetlat in np.unique(bin_dict["lats"]):

            soil_subset = slstr_pixels_in_amsr2(soil_temp,
                                  bin_dict,
                                  targetlat,
                                  targetlon)

            veg_subset =  slstr_pixels_in_amsr2(veg_temp,
                                  bin_dict,
                                  targetlat,
                                  targetlon)


            soil_mean_list.append(subset_statistics(soil_subset)[1]["mean"])
            soil_std_list.append(subset_statistics(soil_subset)[1]["std"])

            veg_mean_list.append(subset_statistics(veg_subset)[1]["mean"])
            veg_std_list.append(subset_statistics(veg_subset)[1]["std"])

            x = np.arange(len(veg_mean_list))

    veg_mean_list = sorted(veg_mean_list)
    veg_std_list = sorted(veg_std_list)
    soil_mean_list = sorted(soil_mean_list)
    soil_std_list = sorted(soil_std_list)

    plt.figure()
    plt.plot(x, veg_mean_list, label='Vegetation Mean', color='forestgreen', linewidth=2)
    plt.fill_between(x,
                     np.array(veg_mean_list) - np.array(veg_std_list),
                     np.array(veg_mean_list) + np.array(veg_std_list),
                     color='forestgreen', alpha=0.2, label='Veg $\pm 1 \sigma$')

    # Plot Soil Data
    plt.plot(x, soil_mean_list, label='Soil Mean', color='saddlebrown', linewidth=2)
    plt.fill_between(x,
                     np.array(soil_mean_list) - np.array(soil_std_list),
                     np.array(soil_mean_list) + np.array(soil_std_list),
                     color='saddlebrown', alpha=0.2, label='Soil $\pm 1 \sigma$')

    plt.ylabel('Land Surface Temperature [K]')
    plt.title('Sub-pixel LST Statistics per Coarse Pixel')
    plt.legend(loc='upper left', frameon=True)

    plt.tight_layout()
    plt.show()
            # boxplot_soil_veg(soil_subset,veg_subset,ndvi_thres,  bins =100)

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
