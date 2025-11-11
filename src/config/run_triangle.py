from readers.Sat import BTData, LPRMData
import matplotlib
import numpy as np
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull, convex_hull_plot_2d
from shapely.geometry import Polygon
import pandas as pd
from utilities.utils import (bbox,
                             soil_canopy_temperatures,
                             mpdi,
                             extreme_hull_vals,
                             find_common_coords,
                             normalize)
from utilities.plotting import scatter_density,create_scatter_plot
from config.paths import path_lprm, path_bt

list =  [
    15.975491129711514,
    -33.34587460190708,
    20.811738889215945,
    68.07067886548683
  ]

# Frequencies(AMSR2):
AMSR2_bands = ['6.9', '7.3', '10.7', '18.7', '23.8', '36.5', '89.0']
_path_bt = path_bt
_path_lprm = path_lprm
sat_freq = '18.7'
sat_sensor = "amsr2"
overpass = "day"
target_res = "10"

composite_start = "2024-10-01"
composite_end = "2024-11-01"

datelist = pd.date_range(start=composite_start, end=composite_end, freq="ME")
datelist = [s.strftime("%Y-%m-%d") for s in datelist]

ref_compound = pd.DataFrame({})
test_compound = pd.DataFrame({})


for d in datelist:
#     d = composite_end
    BT = BTData(path = _path_bt,
                   date = d,
                   sat_freq = sat_freq,
                   overpass = overpass,
                   sat_sensor = sat_sensor,
                   target_res = target_res,
                   )

    BT = BT.to_pandas()
    BT = bbox(BT, list)

    BT["MPDI"] =  mpdi(BT["BT_V"], BT["BT_H"])


    LPRM = LPRMData(path =_path_lprm,
                   date = d,
                   sat_freq = sat_freq,
                   overpass = overpass,
                   sat_sensor = sat_sensor,
                   target_res = target_res,
                   )

    LPRM = LPRM.to_pandas()
    LPRM = bbox(LPRM, list)

    # ref_compound = pd.concat([ref_compound,LPRM])
    # test_compound = pd.concat([test_compound,BT])
    print(f"{d} read")

    plt.ion()
    common_data = find_common_coords(LPRM,BT)

    x_var = "VOD_KU"
    y_var = "TSURF"
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

    point_cloud = common_data.dropna(how = "any")

    _x = point_cloud[x_var]
    _y = point_cloud[y_var]

    points = np.array([_x,_y]).T
    hull = ConvexHull(points, )

    vertices = extreme_hull_vals(points[hull.vertices, 0],
                                 points[hull.vertices, 1],
                                 x_variable= x_var,
                                 y_variable= y_var, )

    plt.plot(points[hull.vertices, 0], points[hull.vertices, 1], 'r--', lw=2)

    # plt.scatter(vertices[:,0],
    #             vertices[:,1],
    #             color = "b")

    plt.show()

    # Gradient of warm edge (y2-y1) / (x2-x1)
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


    # Arbitrary point P
    p = [0.6, 300] # x and y coords

    T_soil, T_canopy = soil_canopy_temperatures(p[0],
                                                p[1],
                                                cold_edge,
                                                grad_warm_edge,
                                                intercept_warm_edge,
                                                full_veg_cover
                                                )



# create_scatter_plot(
#     ref=common_data["VOD_KU"],
#     test=common_data["TSURF"],
#     # test_colour=common_data["SM_C1"],
#     xlabel= "VOD_KU",
#     ylabel="TSURF",
#     # cbar_label= "SM_C1",
#     # xlim = (0,1.4),
#     # ylim = (270,320),
#     # cbar_scale = (250,280),
#     stat_text=False
#     )
