from ismn.interface import ISMN_Interface
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import xarray as xr
ISMN_stack = ISMN_Interface('/home/ddkovacs/shares/climers/Projects/CCIplus_Soil_Moisture/07_data/LPRM/debug/daytime_retrieval/ismn_data/SCAN.zip',
                    parallel=True)
sat_sm = xr.open_dataset("/home/ddkovacs/Desktop/personal/daytime_retrievals/datasets/US_2024.nc")

subset = [
    -97.53240268817623,
    35.08715998253409,
    -94.7909204023861,
    37.798177765461276
  ]

station_name = "Adobe"
sm_sensor_name = "Hydraprobe-Sdi-12-A_soil_moisture_1.016000_1.016000"
t_sensor_name = "Hydraprobe-Sdi-12-A_soil_temperature_1.016000_1.016000"

ismn_station = ISMN_stack["SCAN"][station_name]
ismn_sm = ismn_station['Hydraprobe-Sdi-12-A_soil_moisture_1.016000_1.016000'].to_xarray()["soil_moisture"]
ismn_t = ismn_station['Hydraprobe-Sdi-12-A_soil_temperature_1.016000_1.016000'].to_xarray()["soil_temperature"]

data =  sat_sm.sel(
    LAT =ismn_station.lat,
    LON =ismn_station.lon,
    method = "nearest"
)

sm_adj = data["SM_ADJ"]
sat_sm = data["SM_X"]
sat_t_soil = data["T_soil_hull"]-273.15
sat_t_canopy = data["T_canopy_hull"] -273.15
sat_t = data["TSURF"] -273.15


def temp_plot(ismn_t,
              sat_t,
              sat_t_soil,
              sat_t_canopy):

    plt.figure()

    ismn_t.plot(label = "ISMN T_Soil")
    sat_t.plot(label = "TSURF")
    sat_t_soil.plot(label = "T_soil_hull")
    sat_t_canopy.plot(label = "T_canopy_hull")

    t = sat_t.indexes["time"]
    plt.xlim(t.min(), t.max())
    plt.legend()
    plt.show()

def sm_plot(ismn_sm,
            sat_sm,
            sat_adj
            ):
    plt.figure()

    ismn_sm.plot(label="ISMN SM")
    sat_sm.plot(label="LPRM SM (normal)")
    sat_adj.plot(label="LPRM SM (Adjusted!)")

    t = sat_sm.indexes["time"]
    plt.xlim(t.min(), t.max())
    plt.legend()
    plt.show()


def temp_sm_plot(
    ismn_t, sat_t, sat_t_soil, sat_t_canopy,
    ismn_sm, sat_sm, sat_adj
):
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # --- Temperature subplot ---
    ax = axes[0]
    ismn_t.plot(ax=ax, label="ISMN T_Soil")
    sat_t.plot(ax=ax, label="TSURF")
    sat_t_soil.plot(ax=ax, label="T_soil_hull")
    sat_t_canopy.plot(ax=ax, label="T_canopy_hull")
    ax.set_title("Temperature")
    ax.legend()

    # --- Soil moisture subplot ---
    ax = axes[1]
    ismn_sm.plot(ax=ax, label="ISMN SM")
    sat_sm.plot(ax=ax, label="LPRM SM (normal)")
    sat_adj.plot(ax=ax, label="LPRM SM (Adjusted!)")
    ax.set_title("Soil Moisture")
    ax.legend()

    # Shared x-axis limits
    t = sat_sm.indexes["time"]
    axes[1].set_xlim(t.min(), t.max())

    plt.tight_layout()
    plt.show()
temp_sm_plot(
    ismn_t,
    sat_t,
    sat_t_soil,
    sat_t_canopy,
    ismn_sm,
    sat_sm,
    sm_adj
)

# temp_plot(ismn_t,sat_t, sat_t_soil ,sat_t_canopy)
# sm_plot(ismn_sm,sat_sm, sm_adj)