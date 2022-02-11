import pytest
import requests


api = "https://petro-ip.herokuapp.com/api/"


@pytest.fixture()
def data() -> list[dict]:
    return [
        {
            "WA": "39167",
            "UWI": "203A044J094B1600",
            "First prod month": 202006,
            "Gas IP 30 (E3m3/d)": 113.1,
            "Oil IP 30 (m3/d)": 0.0,
            "Cond IP 30 (m3/d)": 4.8,
            "Water IP 30 (m3/d)": 114.4,
            "Gas IP 90 (E3m3/d)": 79.8,
            "Oil IP 90 (m3/d)": 0.0,
            "Cond IP 90 (m3/d)": 3.8,
            "Water IP 90 (m3/d)": 48.7,
            "Gas IP 180 (E3m3/d)": 62.2,
            "Oil IP 180 (m3/d)": 0.0,
            "Cond IP 180 (m3/d)": 2.8,
            "Water IP 180 (m3/d)": 28.3,
            "Gas IP 365 (E3m3/d)": 49.8,
            "Oil IP 365 (m3/d)": 0.0,
            "Cond IP 365 (m3/d)": 1.7,
            "Water IP 365 (m3/d)": 17.3,
        },
    ]


def test_data(data: list[dict]) -> None:
    """Test that api response is the same as data"""
    for d in data:
        r = requests.get(api + d["WA"]).json()
        for key, value in d.items():
            assert r.get(key) == value
