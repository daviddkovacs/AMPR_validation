import os.path
import rioxarray
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from datetime import datetime
import xarray as xr
import pandas as pd
import os

class Bio:
    def __init__(self,
                 path,
                 date,
                 bio_var,
                 time="1200"):

        self.path = path
        self.date = date
        self.bio_var = bio_var

        year = datetime.strptime(date, "%Y-%m-%d").strftime("%Y")
        ddd = datetime.strptime(date, "%Y-%m-%d").strftime("%j")
        fulldate = datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m%d")

        pattern = f"ERA5-LAND_AN_{fulldate}_{time}.nc"
        self.bio_file = os.path.join(path,year,ddd,pattern)

    def era5_coords_converter(self,longitude):
        """
        Converting ERA5 longitudes from its grid to range b/w -180 and 180 deg
        """
        array = (longitude + 180) % 360 - 180

        return array

    def to_pandas(self, bbox=None):

        if bbox is None:
            bbox = list([-120.66213,32.3257314,-88.03080,41.79186])

        dataset = self.to_xarray(bbox)
        pandas = dataset.to_dataframe()
        pandas = pandas.dropna(subset=[self.bio_var]).reset_index()

        pandas = pandas[["lon", "lat", f"{self.bio_var}"]]

        return pandas

    def to_xarray(self,bbox):

        dataset = xr.open_dataset(self.bio_file, chunks="auto",
                                  decode_timedelta=False)

        if "longitude" in dataset.coords:
            dataset = dataset.rename({"longitude": "lon",
                                            "latitude": "lat", })
            dataset["lon"] = self.era5_coords_converter(dataset["lon"])

        lons = dataset["lon"]
        lats = dataset["lat"]

        dataset = dataset.loc[
            dict(lon = (lons > bbox[0]) & (lons < bbox[2]),
                 lat = (lats > bbox[1]) & (lats < bbox[3]))
        ]

        # dataset = dataset.squeeze("time", drop=True)
        return dataset

class CLMS(Bio):

    def __init__(self, path, date, bio_var,):

        bio_var = bio_var.upper()
        if (date == "2024-10-22" or date == '2024-10-25'):
            _date = "20241020"
        elif date == '2024-10-31':
            _date ='20241031'
        else:
            print(f"Warning! CLMS date not found for input date: {date}")

        pattern = f"CLMS_{bio_var.upper()}_{_date}.nc"

        super().__init__( path, date, bio_var,)
        self.bio_file = os.path.join(path, bio_var.upper(),  pattern)
