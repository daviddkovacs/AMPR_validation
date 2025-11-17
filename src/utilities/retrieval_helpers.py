from cartopy.mpl.clip_path import bbox_to_path
from shapely.geometry import LineString,  Point
from lprm.retrieval.lprm_v6_1.run_lprmv6 import load_band_from_ds
import rioxarray
from utilities.utils import bbox

def soil_canopy_temperatures(point_x,
                             point_y,
                             cold_edge,
                             grad_warm_edge,
                             intercept_warm_edge,
                             full_veg_cover
                             ):
    # equation of line: Tsoil = grad_warm_edge * point_x + intercept_warm_edge
    a = point_y - cold_edge
    b = (grad_warm_edge * point_x + intercept_warm_edge) - point_y

    A = cold_edge
    D = intercept_warm_edge
    T_soil_extreme = ((a / (a+b)) * (D - A) + A)

    B = cold_edge
    C = (grad_warm_edge * full_veg_cover + intercept_warm_edge)
    T_canopy_extreme = ((a / (a + b)) * (C -B ) + B)

    # these gradients and intercepts are needed to find the intersection for every line for every point with the hull
    # yes, I know I define multiple variables to be the same, but (for now) it is better to understand..
    gradient_of_point =  (( T_soil_extreme - T_canopy_extreme) / (0 - full_veg_cover))
    intercept_of_point = T_soil_extreme

    t_dict = {"T_soil_extreme" : T_soil_extreme,
              "T_canopy_extreme": T_canopy_extreme,
              "gradient_of_point" : gradient_of_point,
              "intercept_of_point" : intercept_of_point}

    return t_dict


def dummy_line(gradient, intercept):

    # We need to get two arbitrary points of the line
    # To find the intersection with the hull
    # y_0 = intercept
    p_5 = (gradient * 5) + intercept
    p_0 = intercept

    return p_0, p_5


def interceptor(poly, p_0, p_5, TSURF):

    line = LineString([(0,p_0) ,(5, p_5)])

    intersection = poly.intersection(line)
    if isinstance(intersection, LineString) and not intersection.is_empty:
        t_soil, t_canopy = [list(intersection.coords)[i][1] for i in range(0,2)]
    if isinstance(intersection, Point):
        t_soil = t_canopy = list(intersection.coords)[0][1]
    if intersection.is_empty:
        t_soil = t_canopy= TSURF

    return t_soil, t_canopy


def tiff_aux(path,lista):

    dataset = rioxarray.open_rasterio(path)[0,:,:]
    dataset = dataset.assign_coords(
        x=((dataset.x + 180) % 360) - 180,
        y=((dataset.y + 90) % 180) - 90,
    )
    dataarray = dataset.rename({"x" : "LON",
                                "y" : "LAT"})
    dataarray = dataarray.drop_vars(["band", "spatial_ref"])
    panda = dataarray.to_dataframe("var").reset_index()

    subset_panda = bbox(panda,lista)

    return subset_panda


x = tiff_aux("/home/ddkovacs/shares/climers/Projects/CCIplus_Soil_Moisture/07_data/LPRM/aux_data/coarse_resolution/lprm_v6/soil_content/auxiliary_data_BLD_25km",
             [
                 -123.68616150473056,
                 42.853690174978794,
                 -95.746707235368,
                 48.80496307433518
             ]
             )

