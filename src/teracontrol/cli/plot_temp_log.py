import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot a temperature log file"
    )

    parser.add_argument("file_path", type=Path)

    return parser.parse_args()


def main():
    args = parse_args()

    df = pd.read_csv(args.file_path, index_col=0, parse_dates=True)
    time = df["elapsed_s"] / 60 / 60  # convert to hours
    
    plt.style.use("dark_background")

    fig, ax = plt.subplots(1, 1, figsize=[6, 6], layout="constrained")
    ax2 = ax.twinx()

    ax2.set_zorder(0)
    ax.set_zorder(1)
    ax.patch.set_visible(False)
    ax2.patch.set_visible(True)

    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Temperature (K)")
    ax2.set_ylabel("Pressure (mBar)")
        
    ax.plot(time, df["PT2_DB7"], label="PT2", c="C0")
    ax.plot(time, df["Magnet_MB1"], label="Magnet", c="C1")
    ax.plot(time, df["VTI_MB1"], label="VTI", c="C2")
    ax.plot(time, df["Probe_DB8"], label="Probe", c="C3")

    ax.legend(
        title="Temperatures", 
        title_fontsize="small",
        fontsize="small",
    )
    
    ax2.fill_between(
        time,
        0,
        df["Pressure_DB5"],
        label="Pressure",
        color="gray",
        alpha=0.5,
    )

    nvalve = df["N.V_DB4"]

    counts = nvalve.value_counts()
    dt15 = pd.Timedelta(minutes=15)

    var = nvalve[nvalve.diff().abs().fillna(1).gt(0.1)]
    var = var[var.map(counts).gt(10)]
    var = var[var.index.diff().fillna(dt15) >= dt15]
 
    if len(var) > 1:
        var = var.iloc[1:] if var.iloc[0] == var.iloc[1] else var

    for tstamp, val in var.items():
        t = df.loc[tstamp, "elapsed_s"] / 3600

        ax2.axvline(t, ls="--", color="C4")

        ax2.text(
            t,
            1.0,
            f"{val:.1f}",
            transform=ax2.get_xaxis_transform(),
            ha="center",
            va="bottom",
            color="C4",
        )

    ax2.text(
        0.0,
        1.0,
        "N.V. (%)",
        transform=ax2.transAxes,
        ha="right",
        va="bottom",
        color="C4",
    )

    plt.show()

    
if __name__ == "__main__":
    main()