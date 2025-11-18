import datetime
from readers.Sat import BTData, LPRMData
import matplotlib
import numpy as np
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon
import pandas as pd

from utilities.utils import (
    bbox,
    mpdi,
    extreme_hull_vals,
    find_common_coords,
)

from utilities.retrieval_helpers import (
    soil_canopy_temperatures,
    interceptor,
    dummy_line, tiff_df,
)

from utilities.plotting import scatter_density,plot_maps
from config.paths import path_lprm, path_bt, path_aux

from lprm.retrieval.lprm_v6_1.run_lprmv6 import calc_lprm
from lprm.retrieval.lprm_v6_1.parameters import get_lprm_parameters_for_frequency
from lprm.satellite_specs import get_specs
import lprm.retrieval.lprm_v6_1.par100m_v6_1 as par100

list_bbox= [
    -123.68616150473056,
    42.853690174978794,
    -95.746707235368,
    48.80496307433518
  ]

# Frequencies(AMSR2):
AMSR2_bands = ['6.9', '7.3', '10.7', '18.7', '23.8', '36.5', '89.0']
_path_bt = path_bt
_path_lprm = path_lprm
sat_freq = 'KU'
sat_sensor = "amsr2"
overpass = "day"
target_res = "25"

composite_start = "2024-01-01"
composite_end = "2024-02-01"

datelist = pd.date_range(start=composite_start, end=composite_end, freq="ME")
datelist = [s.strftime("%Y-%m-%d") for s in datelist]


for d in datelist:

    BT_object = BTData(path = _path_bt,
                   date = d,
                   sat_freq = sat_freq,
                   overpass = overpass,
                   sat_sensor = sat_sensor,
                   target_res = target_res,
                   )

    BT = BT_object.to_pandas()
    BT = bbox(BT, list_bbox)
    BT["MPDI"] =  mpdi(BT["BT_V"], BT["BT_H"])


    LPRM_object = LPRMData(path =_path_lprm,
                   date = d,
                   sat_freq = sat_freq,
                   overpass = overpass,
                   sat_sensor = sat_sensor,
                   target_res = target_res,
                   )

    LPRM = LPRM_object.to_pandas()
    LPRM = bbox(LPRM, list_bbox)

    print(f"{d} read")

    plt.ion()
    common_data = find_common_coords(BT,LPRM,target_res)

    x_var = "VOD_KU"
    y_var = "TSURF"
    common_data = common_data.dropna(how = "any")

    x = common_data[x_var]
    y = common_data[y_var]

    scatter_density(
        ref=x,
        test=y,
        test_colour=common_data["SM_C1"],
        xlabel= x_var,
        ylabel=y_var,
        cbar_label= "SM_C1",
        # cbar_type = "jet",
        xlim = (0,1.4),
        ylim = (273,330),
        # cbar_scale = (0,0.5),
        # dpi =5
        )

    points = np.array([x,y]).T
    hull = ConvexHull(points)

    vertices = extreme_hull_vals(points[hull.vertices, 0],
                                 points[hull.vertices, 1],
                                 x_variable= x_var,
                                 y_variable= y_var, )
    plt.plot(points[hull.vertices, 0], points[hull.vertices, 1], 'r--', lw=2)

    # Gradient of warm edge (y2-y1) / (x2-x1)
    # 0th is x and 1st index is y coord
    grad_warm_edge = ((vertices[f"max_{y_var}"][1] - vertices[f"max_{x_var}"][1]) /
                 (vertices[f"max_{y_var}"][0] - vertices[f"max_{x_var}"][0]))

    # Intercept of warm edge on y-axis
    intercept_warm_edge = ((grad_warm_edge * vertices[f"max_{x_var}"][0]) * -1) + vertices[f"max_{x_var}"][1]
    plt.plot(x, grad_warm_edge * x + intercept_warm_edge, label = "Warm edge")

    # Cold edge
    cold_edge = vertices[f"min_{y_var}"][1]
    plt.axhline(cold_edge)

    # full vegetation cover edge
    full_veg_cover = vertices[f"max_{x_var}"][0]
    plt.axvline(full_veg_cover)

    temperatures_data = soil_canopy_temperatures(x,
                                                y,
                                                cold_edge,
                                                grad_warm_edge,
                                                intercept_warm_edge,
                                                full_veg_cover
                                                )

    common_data["T_SOIL"] = temperatures_data["T_soil_extreme"]
    common_data["T_CANOPY"] = temperatures_data["T_canopy_extreme"]

    # Grad and intercept for ALL points!
    common_data["gradient"] = temperatures_data["gradient_of_point"].values
    common_data["intercept"] = temperatures_data["intercept_of_point"].values

    common_data["p_o"], common_data["p_5"] = dummy_line(
        common_data["gradient"],common_data["intercept"])

    hull_x = points[hull.vertices, 0]
    hull_y = points[hull.vertices, 1]
    poly = Polygon((x, y) for x, y in zip(hull_x, hull_y))

    results = list(map(lambda p: interceptor(poly=poly, p_0 = p[0], p_5 = p[1], TSURF =p[2]),
                       zip(common_data["p_o"], common_data["p_5"], common_data["TSURF"])))

    common_data["T_soil_hull"], common_data["T_canopy_hull"] = zip(*results)


    # Retrieve LPRM here
    aux_df  = tiff_df(path_aux,list_bbox, target_res)

    merged = common_data.join(aux_df, how="inner")

    specs = get_specs(sat_sensor.upper())
    params = get_lprm_parameters_for_frequency(sat_freq, specs.incidence_angle)

    merged_geo = merged.to_xarray()

    sm, vod = par100.run_band(
        merged_geo["BT_V"].values.astype('double'),
        merged_geo["BT_H"].values.astype('double'),
        merged_geo["TSURF"].values.astype('double'),
        merged_geo["SND"].values.astype('double'),
        merged_geo["CLY"].values.astype('double'),
        merged_geo["BLD"].values.astype('double'),
        params.Q,
        params.w,
        params.opt_atm,
        specs.incidence_angle[0],
        params.h1,
        params.h2,
        params.vod_Av,
        params.vod_Bv,
        float(LPRM_object.sat_freq),
        params.temp_freeze,
        False,    # apply VOD correction if mean is passed
        None,                # pass mean VOD of backwards window
    )

    merged_geo[f"SM_ADJ"] = (merged_geo.dims, sm)
    merged_geo[f"VOD_ADJ"]= (merged_geo.dims, vod)

    cbar_lut = {"T_soil_hull": (270, 330),
                "T_canopy_hull": (270, 330),
                "SM_ADJ": (0, 0.5),
                "SM_KU": (0, 0.5)
                }

    plot_maps(merged_geo, cbar_lut)

