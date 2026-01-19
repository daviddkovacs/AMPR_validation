import os
import glob
from config.paths import path_bt, path_lprm
import pandas as pd

from readers.Sat import BTData, LPRMData
from scipy.stats import gaussian_kde
import matplotlib
import numpy as np
matplotlib.use("Qt5Agg")
import xarray as xr
import matplotlib.pyplot as plt
from lprm.retrieval.lprm_v6_1.parameters import get_lprm_parameters_for_frequency
from lprm.satellite_specs import get_specs
import lprm.retrieval.lprm_v6_1.par100m_v6_1 as par100
from shapely.geometry import LineString,  Point
from lprm.retrieval.lprm_v6_1.run_lprmv6 import load_band_from_ds

year = "2024"
sat_band = "C1"
sat_sensor = "amsr2"
bbox = [
    -10.085077598814223,
    7.702018665435389,
    25.48544779340702,
    15.553781844242934
  ]

bt_path = os.path.join(path_bt,"day",f"{year}*", f"*day_{year}*.nc")
bt_files = glob.glob(bt_path)


bt_data = xr.open_dataset(bt_files[0], decode_timedelta=False)
bt_data = bt_data.sel(lat = slice(bbox[3],bbox[1]),
                      lon = slice(bbox[0], bbox[2]))


BTV = bt_data["bt_6.9V"].isel(time = 0,drop=True).values.flatten()
BTH = bt_data["bt_6.9H"].isel(time = 0,drop=True).values.flatten()

KuH = bt_data["bt_18.7H"].isel(time = 0,drop=True).values.flatten()
KaV = bt_data["bt_36.5V"].isel(time = 0,drop=True).values.flatten()

df = pd.DataFrame({"BTV" : BTV,
                  "BTH" : BTH,
                  "KuH" : KuH,
                  "KaV" : KaV})

df["kuka"] = df["KuH"] / df["KaV"]
df["mpdi"] = ((df["BTV"] - df["BTH"]) / (df["BTV"] + df["BTH"]))
df["TeffKa"] = df["KaV"] *0.893 +44.8
df["Teff"] = ((0.893*df["KuH"]) / (1- (df["mpdi"]/0.58))) + 44.8
df = df.dropna(how="any")

def hexbin_plot(x, y,
                plot_TeffKa = False,
                xlabel = None,
                ylabel = None,
                xlim=None,
                ylim=None,
                type = None,

                ):

    fig, ax = plt.subplots()
    hb = ax.hexbin(
        x,
        y,
        gridsize=100,
        bins= type,
    )
    m, c = np.polyfit(x, y,1)
    # ax.axline((0,0),slope=1)
    if plot_TeffKa:
        ax.hexbin(
            x,
            df["TeffKa"],
            gridsize=100,
            bins=type,
        )

    fig.colorbar(hb, ax=ax, label="log10(N)")
    fig.suptitle(f"slope: {np.round(m,2)}, intercept: {np.round(c,2)}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    offsets = hb.get_offsets()
    values = hb.get_array()

    def on_move(event):
        if event.inaxes != ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        dx = offsets[:, 0] - event.xdata
        dy = offsets[:, 1] - event.ydata
        d2 = dx*dx + dy*dy
        i = np.argmin(d2)

        val = values[i]
        if np.ma.is_masked(val):
            ax.set_title("density = NaN")
        else:
            ax.set_title(f"density = {val:.2f}")

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)

    plt.show()


hexbin_plot(df["TeffKa"].values, df["mpdi"].values, type = "log",xlabel = "TeffKa" , ylabel = "mpdi C1")
# hexbin_plot(df["TeffKa"].values, df["Teff"].values,type = "log", xlabel = "Teff Ka" , ylabel = "Teff analytic", xlim = [270,330], ylim = [270,330],plot_TeffKa=False)
# hexbin_plot(((0.893*df["KuH"]) / (1- (df["mpdi"]/0.58))) + 44.8,df["Teff"].values,type="log", xlabel = "B" , ylabel = "teff analytic" ,plot_TeffKa=False)
# hexbin_plot(((0.893*df["KuH"]) / (1- (df["mpdi"]/0.58))) + 44.8,df["mpdi"].values,type="log", xlabel = "B" , ylabel = "mpdi C1" ,plot_TeffKa=False)
