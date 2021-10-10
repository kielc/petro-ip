import io
import os
import pickle
import zipfile

import boto3
import pandas as pd
import requests

from wellip import calculate_well_ip


S3_BUCKET = os.environ["S3_BUCKET"]

dtype = {
    "Wa_num": str,
    "Prod_period": int,
    "UWI": str,
    "Gas_prod_vol (e3m3)": float,
    "Oil_prod_vol (m3)": float,
    "Water_prod_vol (m3)": float,
    "Cond_prod_vol (m3)": float,
    "Prod_days ": float,
    "Gas_prod_cum (e3m3)": float,
    "Oil_prod_cum (m3)": float,
    "Water_prod_cum (m3)": float,
    "Cond_prod_cum (m3)": float,
}

response = requests.get("https://iris.bcogc.ca/download/prod_csv.zip")

with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
    with zf.open("zone_prd.csv") as f:
        df_all_wells = pd.read_csv(f, header=1, usecols=dtype.keys(), dtype=dtype)

most_recent_prod_period = df_all_wells["Prod_period"].max()

all_wells_ip = {
    well_ip.wa: well_ip
    for well_ip in (
        calculate_well_ip(df_all_wells[df_all_wells["Wa_num"] == wa].copy())
        for wa in df_all_wells["Wa_num"].unique()
    )
}

s3 = boto3.resource("s3")
s3.Object(S3_BUCKET, "most_recent_prod_period.pkl").put(
    Body=pickle.dumps(most_recent_prod_period)
)
s3.Object(S3_BUCKET, "all_wells_ip.pkl").put(Body=pickle.dumps(all_wells_ip))
