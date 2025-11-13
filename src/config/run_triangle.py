from readers.Sat import BTData, LPRMData
import matplotlib
import numpy as np
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull, convex_hull_plot_2d
from shapely import LineString, wkt
import pandas as pd
from utilities.utils import (bbox,
                             soil_canopy_temperatures,
                             mpdi,
                             extreme_hull_vals,
                             find_common_coords,
                             normalize)
from utilities.plotting import scatter_density,create_scatter_plot
from config.paths import path_lprm, path_bt

list = [
    -120.1714086676526,
    35.70104219505507,
    125.27052940556717,
    40.98135188828232
  ]

# Frequencies(AMSR2):
AMSR2_bands = ['6.9', '7.3', '10.7', '18.7', '23.8', '36.5', '89.0']
_path_bt = path_bt
_path_lprm = path_lprm
sat_freq = '18.7'
sat_sensor = "amsr2"
overpass = "day"
target_res = "10"

composite_start = "2024-06-01"
composite_end = "2024-07-01"

datelist = pd.date_range(start=composite_start, end=composite_end, freq="ME")
datelist = [s.strftime("%Y-%m-%d") for s in datelist]

ref_compound = pd.DataFrame({})
test_compound = pd.DataFrame({})

def checkIntersection2(polyX, polyY, gradient, intercept):

    linePtX = np.linspace(0, 5, 10000)
    linePtY = gradient * linePtX + intercept

    poly = LineString([(x, y) for x, y in zip(polyX, polyY)])
    line = LineString([(x, y) for x, y in zip(linePtX, linePtY)])
    intPoints = poly.intersection(line)
    points = [p for p in intPoints.geoms]
    return points

for d in datelist:

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

    ds_LPRM = LPRM.to_xarray(bbox=list)
    ds_LPRM = ds_LPRM.assign_coords({"lon": ds_LPRM["LON"],
                                     "lat": ds_LPRM["LAT"]})

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

    points =  checkIntersection2(points[hull.vertices, 0],points[hull.vertices, 1],
                                 grad_warm_edge,intercept_warm_edge)

    point_cloud["T_SOIL"], point_cloud["T_CANOPY"] = soil_canopy_temperatures(_x,
                                                _y,
                                                cold_edge,
                                                grad_warm_edge,
                                                intercept_warm_edge,
                                                full_veg_cover
                                                )
    arb = [0.6, 287]
    arb_ts, arb_tc = soil_canopy_temperatures(arb[0],
                                                arb[1],
                                                cold_edge,
                                                grad_warm_edge,
                                                intercept_warm_edge,
                                                full_veg_cover
                                                )
    print(arb_ts,arb_tc)
    plt.plot(arb[0], arb[1], marker = "D", color  ="r")
    plt.plot(full_veg_cover, arb_tc, marker="D", color="r")
    plt.plot(0, arb_ts, marker="D", color="r")
    plt.plot(0, arb_ts, marker="D", color="r")

    cordinates = [point_cloud["LAT"].values , point_cloud["LON"].values]
    mi_array = zip(*cordinates)
    point_cloud.index = pd.MultiIndex.from_tuples(mi_array, names=["LAT", "LON"])

    ds_point_cloud = point_cloud.to_xarray()

    variables = ["T_SOIL", "T_CANOPY", "TSURF"]
    vmin, vmax = 270, 330

    fig, axes = plt.subplots(3, 1, figsize=(15, 5))

    for ax, var in zip(axes, variables):
        data = ds_point_cloud[var]
        im = ax.imshow(np.flipud(data), vmin=vmin, vmax=vmax)
        ax.set_title(var)
        ax.axis('off')  # optional, remove axes for cleaner look

    # fig.colorbar(im, ax=axes, orientation='horizontal', fraction=0.02, pad=0.04)
    plt.tight_layout()
    plt.show()

