import os
import pickle

import fastapi
import boto3
import uvicorn

from wellip import wellip_to_dict


S3_BUCKET = os.environ["S3_BUCKET"]

s3 = boto3.resource("s3")
most_recent_prod_period: int = pickle.loads(
    s3.Object(S3_BUCKET, "most_recent_prod_period.pkl").get()["Body"].read()
)
all_wells_ip: dict = pickle.loads(
    s3.Object(S3_BUCKET, "all_wells_ip.pkl").get()["Body"].read()
)

api = fastapi.FastAPI(title="Petro-IP")


@api.get("/")
def root():
    body = (
        "<html>"
        "<body style='padding: 10px;'>"
        "<h2>Petro-IP API</h2>"
        """<p>Inital production (IP30, 90, 180, 365) calculated for wells in British
        Columbia. IP values are interpolated between monthly reported production totals.
        Null values indicate insufficient cumulative producing days or missing data.
        Older wells may have volume reported without producing days reported for the same
        same period in which case IP values cannot be calculated.</p>"""
        "<a href='/api/39167?units=field'>GET /api/{wa}?units={units}</a>"
        "<p>Required: {wa} - British Columbia well authorization number</p>"
        "<p>Optional: units={units} - metric or field, default value is metric</p>"
        f"<p>BCOGC production data current to {most_recent_prod_period}</p>"
        "</body>"
        "</html>"
    )

    return fastapi.responses.HTMLResponse(content=body)


@api.get("/api/{wa}")
def ip(wa: str, units: str = "metric"):
    if len(wa) != 5 or not wa.isnumeric():
        raise fastapi.HTTPException(
            status_code=400, detail="WA must be 0 padded, 5 character numeric string"
        )
    if units not in ["metric", "field"]:
        raise fastapi.HTTPException(
            status_code=400, detail="Units must be 'metric' or 'field'"
        )

    try:
        d: dict = wellip_to_dict(all_wells_ip[wa], units)
        # nan is not valid json
        for key, value in d.items():
            if value != value:
                d[key] = None
        return d
    except KeyError:
        raise fastapi.HTTPException(status_code=404, detail="WA not found")


if __name__ == "__main__":
    uvicorn.run(api)
