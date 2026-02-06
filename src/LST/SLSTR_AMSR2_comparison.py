from LST.Datacube import SLSTR_AMSR2_DC
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")






if __name__=="__main__":

    bbox = [
        -1.8436850670557021,
        14.57195894818102,
        -1.1848809443806658,
        15.101533687736719
    ]

    data = SLSTR_AMSR2_DC(
        region="sahel",
        bbox = bbox
    )

    dflist = []

    for m in range(1,13):
        date = f"2024-{m}-20"
        dflist.append(data.process_date(date = date))

