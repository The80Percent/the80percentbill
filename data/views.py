"""Read-only, anonymized views for pledge data visualization."""

import json
import re
from pathlib import Path

from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from pledge.models import Pledge

FIPS_TO_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
    "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
    "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
    "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
    "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
    "56": "WY", "60": "AS", "66": "GU", "69": "MP", "72": "PR",
    "78": "VI",
}

ABBR_TO_FIPS = {v: k for k, v in FIPS_TO_ABBR.items()}

# DC and territories use "98" for their at-large delegate/resident commissioner
_AT_LARGE_98 = {"DC", "AS", "GU", "MP", "PR", "VI"}

DISTRICT_RE = re.compile(r"^([A-Z]{2})-(\d{1,2})$")


def _load_valid_geoids():
    """Load the set of real GEOIDs from the TopoJSON file (runs once)."""
    topo_path = Path(settings.STATICFILES_DIRS[0]) / "data" / "districts-topo.json"
    try:
        with open(topo_path) as f:
            topo = json.load(f)
        obj = next(iter(topo["objects"].values()))
        return {g["properties"]["GEOID"] for g in obj["geometries"]}
    except Exception:
        return set()


_VALID_GEOIDS = _load_valid_geoids()


def _abbr_district_to_geoid(district_code):
    """Convert 'NY-14' to FIPS GEOID '3614'. Returns None if invalid or nonexistent."""
    m = DISTRICT_RE.match(district_code)
    if not m:
        return None
    abbr, num = m.group(1), m.group(2)
    fips = ABBR_TO_FIPS.get(abbr)
    if not fips:
        return None

    dist_int = int(num)
    if dist_int == 0:
        suffix = "98" if abbr in _AT_LARGE_98 else "00"
    else:
        suffix = num.zfill(2)

    geoid = f"{fips}{suffix}"
    return geoid if geoid in _VALID_GEOIDS else None


def index(request):
    """Serve the district map page. GET only, read-only."""
    return render(request, "data/index.html")


def district_counts(request):
    """Return anonymized pledge counts grouped by district. GET only, read-only.

    Only reads `district` column and aggregate count -- never touches
    name, email, or any PII.
    """
    rows = (
        Pledge.objects
        .values("district")
        .annotate(count=Count("id"))
    )

    districts = {}
    unmapped_count = 0

    for row in rows:
        raw = (row["district"] or "").strip().upper()
        geoid = _abbr_district_to_geoid(raw)
        if geoid:
            districts[geoid] = districts.get(geoid, 0) + row["count"]
        else:
            unmapped_count += row["count"]

    return JsonResponse({
        "districts": districts,
        "unmapped_count": unmapped_count,
    })
