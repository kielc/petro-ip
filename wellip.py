from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import interpolate


@dataclass
class WellIP:
    """WellIP class is used to hold initial production information for a well."""

    wa: str
    uwi: str
    first_prod_month: int
    last_prod_month: int
    cum_prod_gas_e6m3: float
    cum_prod_oil_e3m3: float
    cum_prod_cond_e3m3: float
    cum_prod_water_e3m3: float
    cum_prod_days: float
    gas_ip_30_e3m3d: float = float("nan")
    oil_ip_30_m3d: float = float("nan")
    cond_ip_30_m3d: float = float("nan")
    water_ip_30_m3d: float = float("nan")
    gas_ip_90_e3m3d: float = float("nan")
    oil_ip_90_m3d: float = float("nan")
    cond_ip_90_m3d: float = float("nan")
    water_ip_90_m3d: float = float("nan")
    gas_ip_180_e3m3d: float = float("nan")
    oil_ip_180_m3d: float = float("nan")
    cond_ip_180_m3d: float = float("nan")
    water_ip_180_m3d: float = float("nan")
    gas_ip_365_e3m3d: float = float("nan")
    oil_ip_365_m3d: float = float("nan")
    cond_ip_365_m3d: float = float("nan")
    water_ip_365_m3d: float = float("nan")

    def __setattr__(self, name, value):
        # convert to built-in types, cannot json serialize numpy types
        if isinstance(value, np.floating):
            super().__setattr__(name, float(value))
        elif isinstance(value, np.integer):
            super().__setattr__(name, int(value))
        else:
            super().__setattr__(name, value)


def calculate_well_ip(df_one_well: pd.DataFrame) -> WellIP:
    """Calculate intial production information for a single well.

    df_one_well: monthly well production information in the csv download format
    provided by the BCOGC and imported as a pandas dataframe for a single WA.
    """
    df_one_well["Prod_days_cum"] = df_one_well["Prod_days "].cumsum()

    df_one_well["Total_prod_vol (m3)"] = (
        (df_one_well["Gas_prod_vol (e3m3)"] * 1000)
        + df_one_well["Oil_prod_vol (m3)"]
        + df_one_well["Water_prod_vol (m3)"]
        + df_one_well["Cond_prod_vol (m3)"]
    )

    well_ip = WellIP(
        wa=df_one_well["Wa_num"].iloc[0],
        uwi=df_one_well["UWI"].iloc[0],
        first_prod_month=df_one_well["Prod_period"].iloc[0],
        last_prod_month=df_one_well["Prod_period"].iloc[-1],
        cum_prod_gas_e6m3=df_one_well["Gas_prod_cum (e3m3)"].iloc[-1] / 1000,
        cum_prod_oil_e3m3=df_one_well["Oil_prod_cum (m3)"].iloc[-1] / 1000,
        cum_prod_cond_e3m3=df_one_well["Cond_prod_cum (m3)"].iloc[-1] / 1000,
        cum_prod_water_e3m3=df_one_well["Water_prod_cum (m3)"].iloc[-1] / 1000,
        cum_prod_days=df_one_well["Prod_days_cum"].iloc[-1],
    )

    # Must have >= 2 months production data for linear interpolation of well IP.
    #
    # If any months prior to cumulative 365 days production have volume reported without
    # any production days reported the IP values will not be calculated.
    if (
        len(df_one_well) >= 2
        and df_one_well[
            (df_one_well["Prod_days_cum"] <= 365)
            & (df_one_well["Prod_days "] == 0)
            & (df_one_well["Total_prod_vol (m3)"] > 0)
        ].empty
    ):
        # bounds_error=False, out of bounds values are assigned default fill_value of NaN
        interp_func_gas = interpolate.interp1d(
            df_one_well["Prod_days_cum"],
            df_one_well["Gas_prod_cum (e3m3)"],
            bounds_error=False,
        )
        interp_func_oil = interpolate.interp1d(
            df_one_well["Prod_days_cum"],
            df_one_well["Oil_prod_cum (m3)"],
            bounds_error=False,
        )
        interp_func_cond = interpolate.interp1d(
            df_one_well["Prod_days_cum"],
            df_one_well["Cond_prod_cum (m3)"],
            bounds_error=False,
        )
        interp_func_water = interpolate.interp1d(
            df_one_well["Prod_days_cum"],
            df_one_well["Water_prod_cum (m3)"],
            bounds_error=False,
        )

        days_arr = (30, 90, 180, 365)

        gas_ip = interp_func_gas(days_arr) / days_arr
        oil_ip = interp_func_oil(days_arr) / days_arr
        cond_ip = interp_func_cond(days_arr) / days_arr
        water_ip = interp_func_water(days_arr) / days_arr

        well_ip.gas_ip_30_e3m3d = gas_ip[0]
        well_ip.oil_ip_30_m3d = oil_ip[0]
        well_ip.cond_ip_30_m3d = cond_ip[0]
        well_ip.water_ip_30_m3d = water_ip[0]

        well_ip.gas_ip_90_e3m3d = gas_ip[1]
        well_ip.oil_ip_90_m3d = oil_ip[1]
        well_ip.cond_ip_90_m3d = cond_ip[1]
        well_ip.water_ip_90_m3d = water_ip[1]

        well_ip.gas_ip_180_e3m3d = gas_ip[2]
        well_ip.oil_ip_180_m3d = oil_ip[2]
        well_ip.cond_ip_180_m3d = cond_ip[2]
        well_ip.water_ip_180_m3d = water_ip[2]

        well_ip.gas_ip_365_e3m3d = gas_ip[3]
        well_ip.oil_ip_365_m3d = oil_ip[3]
        well_ip.cond_ip_365_m3d = cond_ip[3]
        well_ip.water_ip_365_m3d = water_ip[3]

    return well_ip


def wellip_to_dict(well_ip: WellIP, units: str = "metric") -> dict:
    """Convert an instance of WellIP class to a dictionary.

    units: "metric" or "field"
    """
    BBL_M3 = 6.29
    MCF_E3M3 = 35.315

    if units == "field":
        d = {
            "WA": well_ip.wa,
            "UWI": well_ip.uwi,
            "First prod month": well_ip.first_prod_month,
            "Last prod month": well_ip.last_prod_month,
            "Cum prod gas (Bcf)": well_ip.cum_prod_gas_e6m3 * MCF_E3M3 * 0.001,
            "Cum prod oil (Mbbl)": well_ip.cum_prod_oil_e3m3 * BBL_M3,
            "Cum prod cond (Mbbl)": well_ip.cum_prod_cond_e3m3 * BBL_M3,
            "Cum prod water (Mbbl)": well_ip.cum_prod_water_e3m3 * BBL_M3,
            "Cum prod days": well_ip.cum_prod_days,
            "Gas IP 30 (Mcf/d)": well_ip.gas_ip_30_e3m3d * MCF_E3M3,
            "Oil IP 30 (bbl/d)": well_ip.oil_ip_30_m3d * BBL_M3,
            "Cond IP 30 (bbl/d)": well_ip.cond_ip_30_m3d * BBL_M3,
            "Water IP 30 (bbl/d)": well_ip.water_ip_30_m3d * BBL_M3,
            "Gas IP 90 (Mcf/d)": well_ip.gas_ip_90_e3m3d * MCF_E3M3,
            "Oil IP 90 (bbl/d)": well_ip.oil_ip_90_m3d * BBL_M3,
            "Cond IP 90 (bbl/d)": well_ip.cond_ip_90_m3d * BBL_M3,
            "Water IP 90 (bbl/d)": well_ip.water_ip_90_m3d * BBL_M3,
            "Gas IP 180 (Mcf/d)": well_ip.gas_ip_180_e3m3d * MCF_E3M3,
            "Oil IP 180 (bbl/d)": well_ip.oil_ip_180_m3d * BBL_M3,
            "Cond IP 180 (bbl/d)": well_ip.cond_ip_180_m3d * BBL_M3,
            "Water IP 180 (bbl/d)": well_ip.water_ip_180_m3d * BBL_M3,
            "Gas IP 365 (Mcf/d)": well_ip.gas_ip_365_e3m3d * MCF_E3M3,
            "Oil IP 365 (bbl/d)": well_ip.oil_ip_365_m3d * BBL_M3,
            "Cond IP 365 (bbl/d)": well_ip.cond_ip_365_m3d * BBL_M3,
            "Water IP 365 (bbl/d)": well_ip.water_ip_365_m3d * BBL_M3,
        }
    else:
        d = {
            "WA": well_ip.wa,
            "UWI": well_ip.uwi,
            "First prod month": well_ip.first_prod_month,
            "Last prod month": well_ip.last_prod_month,
            "Cum prod gas (E6m3)": well_ip.cum_prod_gas_e6m3,
            "Cum prod oil (E3m3)": well_ip.cum_prod_oil_e3m3,
            "Cum prod cond (E3m3)": well_ip.cum_prod_cond_e3m3,
            "Cum prod water (E3m3)": well_ip.cum_prod_water_e3m3,
            "Cum prod days": well_ip.cum_prod_days,
            "Gas IP 30 (E3m3/d)": well_ip.gas_ip_30_e3m3d,
            "Oil IP 30 (m3/d)": well_ip.oil_ip_30_m3d,
            "Cond IP 30 (m3/d)": well_ip.cond_ip_30_m3d,
            "Water IP 30 (m3/d)": well_ip.water_ip_30_m3d,
            "Gas IP 90 (E3m3/d)": well_ip.gas_ip_90_e3m3d,
            "Oil IP 90 (m3/d)": well_ip.oil_ip_90_m3d,
            "Cond IP 90 (m3/d)": well_ip.cond_ip_90_m3d,
            "Water IP 90 (m3/d)": well_ip.water_ip_90_m3d,
            "Gas IP 180 (E3m3/d)": well_ip.gas_ip_180_e3m3d,
            "Oil IP 180 (m3/d)": well_ip.oil_ip_180_m3d,
            "Cond IP 180 (m3/d)": well_ip.cond_ip_180_m3d,
            "Water IP 180 (m3/d)": well_ip.water_ip_180_m3d,
            "Gas IP 365 (E3m3/d)": well_ip.gas_ip_365_e3m3d,
            "Oil IP 365 (m3/d)": well_ip.oil_ip_365_m3d,
            "Cond IP 365 (m3/d)": well_ip.cond_ip_365_m3d,
            "Water IP 365 (m3/d)": well_ip.water_ip_365_m3d,
        }

    for key, value in d.items():
        if isinstance(value, float):
            d[key] = round(value, 1)

    return d
