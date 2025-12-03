from ismn.interface import ISMN_Interface
from ismn.meta import Depth
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import xarray as xr
import numpy as np
from pandas import Timestamp,Timedelta
from utilities.plotting import temp_sm_plot
from config.paths import sat_stack_path,ismn_data_path, path_aux
from utilities.retrieval_helpers import retrieve_LPRM,tiff_df

sat_data = xr.open_dataset(sat_stack_path)
ISMN_stack = ISMN_Interface(ismn_data_path, parallel=True)
NETWORK_stack = ISMN_stack["SCAN"]

station_user = "Abrams"
ts_cutoff = Timestamp("2015-01-01")
depth_selection = Depth(0., 0.1)


stat_list = [ 'Lind#1']
for i in stat_list:
    STATION = NETWORK_stack[i]
    print(i)
    try:
        for  _, _sensor_sm in NETWORK_stack.iter_sensors(variable='soil_moisture',
                                                         depth=depth_selection,
                                                         filter_meta_dict={
                                                             'station': [i],
                                                         }):

            if _sensor_sm.metadata["timerange_from"][1] > ts_cutoff:
                ismn_sm = _sensor_sm.read_data()

            for _, _sensor_t in NETWORK_stack.iter_sensors(variable='soil_temperature',
                                                           depth=depth_selection,
                                                           filter_meta_dict={
                                                               'station': [i],
                                                           }):
                if _sensor_t.metadata["timerange_from"][1] > ts_cutoff:

                    ismn_t = _sensor_t.read_data()



        data =  sat_data.sel(
            LAT =STATION.lat,
            LON =STATION.lon,
            method = "nearest"
        )

        sm_adj = data["SM_ADJ"]
        sm_x = data["SM_X"]
        sat_t_soil = data["T_soil_hull"]-273.15
        sat_t_canopy = data["T_canopy_hull"] -273.15
        sat_t = data["TSURF"] -273.15

        temp_sm_plot(
            ismn_t,
            sat_t,
            sat_t_soil,
            sat_t_canopy,
            ismn_sm,
            sm_x,
            sm_adj,
            **{
            "name" : STATION.name,
            "lat" : np.round(STATION.lat,2),
            "lon" : np.round(STATION.lon,2),
        }
        )
    except:
        continue


##
SINGLE_STATION = NETWORK_stack[station_user]

_sat_data = sat_data.sel(
            LAT =SINGLE_STATION.lat,
            LON =SINGLE_STATION.lon,
            method = "nearest"
        ).expand_dims(['LAT','LON']).to_dataframe()


_sat_data = _sat_data.drop(columns = ["SM_ADJ"])

doy = Timestamp("2024-06-15")
sat_day = _sat_data.xs(doy, level="time")
aux_df = tiff_df(path_aux)

lprm_day = retrieve_LPRM(sat_day,
                         aux_df,
                         "AMSR2",
                         "X"
                         ).to_dataframe()

lprm_day = lprm_day.drop(columns = ["BLD","SND","CLY","DIF_SMX-ADJ"])

conditions_sm = (ISMN_stack.metadata['variable'].val == 'soil_moisture') & \
             (ISMN_stack.metadata['instrument'].depth_to < 0.1) & \
             (ISMN_stack.metadata['instrument'].depth_from >= 0) & \
             (ISMN_stack.metadata["timerange_to"].val > doy + Timedelta(days=1)) & \
             (ISMN_stack.metadata['station'].val == station_user)

ids = ISMN_stack.metadata[conditions_sm].index.to_list()
ts, meta = ISMN_stack.read(ids, return_meta=True)

