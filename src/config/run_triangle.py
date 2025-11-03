from readers.Sat import BTData, LPRMData
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from scipy.stats import gaussian_kde
import pandas as pd
from utilities.utils import bbox, calc_surface_temperature, mpdi
import mpl_scatter_density # adds projection='scatter_density'
from utilities.plotting import scatter_density



list =[
    -70.27302575366366,
    -38.441971436609485,
    -57.055616768820755,
    -26.843915254949074
  ]

path_sat = r"G:\My Drive\Munka\CLIMERS\ER2_validation\AMSR2\passive_input\medium_resolution"
sat_freq = '18.7'
sat_sensor = "amsr2"
overpass = "day"
target_res = "10"


datelist = [
    # "2023-08-28",
    # "2023-08-29",
    # "2023-08-30",
    "2024-10-24",
            "2024-10-25",
            "2024-10-26",
            "2024-10-27",]

# for d in datelist:
d = "2024-10-24"
KA = BTData(path = path_sat,
               date = d,
               sat_freq = '36.5',
               overpass = overpass,
               sat_sensor = sat_sensor,
               target_res = target_res,
               )

dfKA = KA.to_pandas()
dfKA = bbox(dfKA, list)
dfKA["TSURF"] = calc_surface_temperature(dfKA["bt_V"])

BT = BTData(path = path_sat,
               date = d,
               sat_freq = sat_freq,
               overpass = overpass,
               sat_sensor = sat_sensor,
               target_res = target_res,
               )

BT = BT.to_pandas()
BT = bbox(BT, list)

BT["MPDI"] =  mpdi(BT["bt_V"], BT["bt_H"])


LPRM = LPRMData(path = r"G:\My Drive\Munka\CLIMERS\ER2_validation\AMSR2\lprm_output\medium_resolution",
               date = d,
               sat_freq = sat_freq,
               overpass = overpass,
               sat_sensor = sat_sensor,
               target_res = target_res,
               )

LPRM = LPRM.to_pandas()
LPRM = bbox(LPRM, list)

plt.ion()
scatter_density(
    BT["MPDI"],
    dfKA["TSURF"],
    xlabel= "18.7 GHz MPDI",
    ylabel="Ka T surface",
    )
