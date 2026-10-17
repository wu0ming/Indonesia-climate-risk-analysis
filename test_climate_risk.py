"""Regression checks; synthetic inputs only. Run: python -m unittest -v."""
import csv
import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import climate_risk as cr

SCIENCE = all(importlib.util.find_spec(m) for m in ("numpy", "xarray", "h5netcdf", "cftime"))
GIS = all(importlib.util.find_spec(m) for m in ("numpy", "rasterio", "shapely"))


class BaseChecks(unittest.TestCase):
    def setUp(self):
        cr.configure_network(interval=0)
        self.work = Path(__file__).resolve().parent / "outputs" / "tests"
        self.work.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.work)
        self.root = Path(self.temp.name)
        self.parser = cr.make_parser()

    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.work.resolve()):
            raise RuntimeError("Refusing to clean a directory outside the test workspace")
        self.temp.cleanup()

    def args(self, command, path, *options):
        return self.parser.parse_args([command, "--input", str(path), "--out", str(self.root / "out"), *options])

    def hist(self, rows, *options):
        path = self.root / "hist.csv"
        cr.write_csv(path, rows)
        return cr.histogram(self.args("histogram", path, "--normalization", "inverse-gray255", *options), self.root)[0]["risk_summary"]

    def row(self, **overrides):
        return {"fid": 1, "Area": 1, "pixel_size_x": 10, "pixel_size_y": -10,
                "pixel_size_unit": "meters", "source_file": "test_index", **overrides}


class CSVChecks(BaseChecks):
    def test_model_summary_prioritizes_grade_and_marks_provisional_results(self):
        args = self.parser.parse_args(["inarisk", "--zones", "unused", "--methodology", "reference"])
        rows = [{"asset": "Test area", "asset_type": "zone", "service": "INDEKS_BAHAYA_BANJIR",
            "valid_pixels": 10, "coverage_weighted_score": 2.5, "data_quality": "ok", "screening_level": "low"}]
        def summary():
            tables = {"asset_risk": rows, "reference_aggregate": cr.reference_aggregate(rows, args)}
            return cr.assessment_dashboard(tables, self.root, {"parameters": vars(args)})
        for score, grade in ((2.5,"低风险"),(3,"中风险"),(7.5,"高风险")):
            rows[0]["coverage_weighted_score"] = score
            rendered = summary()
            self.assertIn(f'<h2 class="risk-headline">{grade}</h2>', rendered)
            self.assertIn('data-assessment-status="complete"', rendered)
        rows[0]["coverage_weighted_score"] = 2.5
        rows.append({"asset":"Test area", "asset_type":"zone", "service":"INDEKS_BAHAYA_KEKERINGAN", "data_quality":"unavailable"})
        rendered = summary()
        self.assertIn('<h2 class="risk-headline">低风险（暂评）</h2>', rendered)
        self.assertIn('data-assessment-status="provisional"', rendered)
        self.assertIn('尚有 1 个主评价指标未纳入', rendered)
        self.assertIn('正式评价待确认', rendered)
        self.assertLess(rendered.index('risk-headline'), rendered.index('数据完整性与分析范围'))
        rows[0]["coverage_weighted_score"] = None
        rows[0]["data_quality"] = "no_valid_data"
        rendered = summary()
        self.assertIn('<h2 class="risk-headline">暂无法评价</h2>', rendered)
        self.assertNotIn('<h2 class="risk-headline">低风险', rendered)
        self.assertNotIn('risk-pointer', rendered.split('</style>')[-1])

    def test_cloudflare_signature_denial_is_logged_without_repeated_requests(self):
        import io
        import urllib.error
        url = "https://gis.bnpb.go.id/server/rest/services/inarisk/layer_risiko_banjir/ImageServer?f=json"
        cr.configure_network(interval=0, log=self.root / "network.jsonl")
        error = urllib.error.HTTPError(url, 403, "Forbidden", {"Server": "cloudflare", "CF-RAY": "synthetic-ray"}, io.BytesIO(b"error code: 1010\n"))
        with patch.object(cr.urllib.request, "urlopen", side_effect=error) as request:
            with self.assertRaisesRegex(ValueError, "1010"):cr.http_bytes(url)
            with self.assertRaisesRegex(ValueError, "暂停"):cr.http_bytes(url)
            self.assertEqual(request.call_count, 1)
        record = json.loads((self.root / "network.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(record["stage"], "service_metadata")
        self.assertEqual(record["http_status"], 403)
        self.assertIn("1010", record["error_body_prefix"])

    def test_retry_after_is_honoured_and_host_outage_stops_extra_calls(self):
        import urllib.error
        url = "https://gis.bnpb.go.id/server/rest/services/inarisk/X/ImageServer/exportImage?f=json"
        cr.configure_network(interval=0, log=self.root / "network.jsonl")
        error = urllib.error.HTTPError(url, 429, "rate limited", {"Retry-After": "120"}, None)
        with patch.object(cr.urllib.request, "urlopen", side_effect=error) as request:
            with self.assertRaisesRegex(ValueError, "120"):
                cr.http_bytes(url)
            with self.assertRaisesRegex(ValueError, "暂停"):
                cr.http_bytes(url)
            self.assertEqual(request.call_count, 1)
        record = json.loads((self.root / "network.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(record["http_status"], 429)
        self.assertEqual(record["stage"], "export_request")
        self.assertEqual(record["headers"]["retry-after"], "120")
        cr.configure_network(interval=0)
        with patch.object(cr.urllib.request, "urlopen", side_effect=TimeoutError("unreachable")) as request, patch.object(cr.time, "sleep"):
            for unused in range(3):
                with self.assertRaises(TimeoutError):cr.http_bytes(url)
            with self.assertRaisesRegex(ValueError, "暂停"):cr.http_bytes(url)
            self.assertEqual(request.call_count, 9)

    def test_official_download_boundary_and_transient_520_retry(self):
        import urllib.error
        from unittest.mock import MagicMock
        url = "https://gis.bnpb.go.id/server/rest/services/inarisk?f=json"
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = url
        response.read.return_value = b'{"services":[]}'
        with patch.object(cr.urllib.request, "urlopen", side_effect=[urllib.error.HTTPError(url, 520, "upstream", {}, None), response]) as request, patch.object(cr.time, "sleep"):
            self.assertEqual(cr.http_bytes(url), b'{"services":[]}')
            self.assertEqual(request.call_count, 2)
        with self.assertRaises(ValueError):
            cr.http_bytes("https://example.com/image.jpg", allowed_host="server.arcgisonline.com")

    def test_full_physical_profile_and_reference_aggregation(self):
        names = ["INDEKS_BAHAYA_BANJIR", "INDEKS_KERENTANAN_TSUNAMI", "layer_risiko_banjir",
            "INDEKS_MULTI_BAHAYA", "IDX_H_EQ_GLOBAL", "layer_risiko_gempabumi_jkt",
            "INDEKS_BAHAYA_COVID19", "INDEKS_KAPASITAS_BANJIR", "INDEKS_RISIKO_TANAH_LONGSOR"]
        catalog = {"services": [{"name": "inarisk/" + n, "type": "ImageServer"} for n in names]}
        self.assertEqual(set(cr.physical_services(catalog)), set(names[:6]))
        args = self.parser.parse_args(["inarisk", "--zones", "unused", "--methodology", "reference"])
        rows = [{"asset": "A", "asset_type": "zone", "service": service, "valid_pixels": valid,
            "coverage_weighted_score": score, "data_quality": "ok"} for service, valid, score in [
                ("INDEKS_BAHAYA_BANJIR", 10, 2), ("layer_risiko_banjir", 30, 6), ("IDX_H_EQ_GLOBAL", 10000, 10)]]
        result = cr.reference_aggregate(rows, args)
        self.assertEqual(result[0]["score"], 5)
        self.assertEqual(result[0]["included_layers"], 2)
        self.assertEqual(rows[0]["inter_layer_weight"], .25)
        rows[1]["data_quality"] = "insufficient_coverage"
        self.assertEqual(cr.reference_aggregate(rows, args)[0]["screening_level"], "undetermined")

    def test_zero_bin_and_sparse_columns(self):
        rows = self.hist([self.row(histo0=25, histo255=75), self.row(fid=2, histo128=1)])
        self.assertEqual(rows[0]["high_pixels"], 25)
        self.assertEqual(rows[0]["low_pixels"], 75)
        self.assertAlmostEqual(rows[0]["intensity"], 3.25)
        self.assertEqual(rows[1]["valid_pixels"], 1)
        self.assertEqual(rows[1]["screening_level"], "undetermined")

    def test_nodata_and_unknown_are_never_low_risk(self):
        row = self.hist([self.row(histo_0=3, histo_255=0)])[0]
        self.assertEqual(row["data_quality"], "insufficient_coverage")
        self.assertEqual(row["screening_level"], "undetermined")
        row = self.hist([self.row(histo0=0, histo255=100)], "--nodata", "255")[0]
        self.assertEqual(row["data_quality"], "no_valid_data")
        self.assertIsNone(row["intensity"])
        row = self.hist([self.row(histo0=200)])[0]
        self.assertEqual(row["data_quality"], "coverage_exceeds_area")

    def test_units_counts_and_duplicates(self):
        with self.assertRaisesRegex(ValueError, "单位"):
            self.hist([self.row(histo0=1, pixel_size_unit="unknown")])
        with self.assertRaisesRegex(ValueError, "非负整数"):
            self.hist([self.row(histo0=1.2)])
        with self.assertRaisesRegex(ValueError, "重复"):
            self.hist([self.row(histo0=10), self.row(histo0=20)])
        with self.assertRaisesRegex(ValueError, "超出"):
            self.hist([self.row(histo256=1)])

    def test_filter_and_band(self):
        result = self.hist([self.row(Band=1, histo0=10), self.row(Band=2, histo0=70),
                            self.row(source_file="rgb_picture", histo0=40)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["valid_pixels"], 10)

    def test_normalization_and_weight_boundaries(self):
        self.assertEqual(cr.normalize(0, "inverse-gray255"), 1)
        self.assertEqual(cr.normalize(255, "gray255"), 1)
        self.assertEqual(cr.normalize(0.5, "index01"), 0.5)
        self.assertEqual(cr.normalize(1.000000119, "index01"), 1)
        for value, expected in ((0, 1), (0.33, 1), (0.66, 5), (1, 10)):
            self.assertAlmostEqual(cr.risk_weight(value, [0.33, 0.66], [1, 5, 10]), expected)
        with self.assertRaises(ValueError):
            cr.normalize(1.01, "index01")

    def test_aqueduct_uses_official_stress_without_recalculation(self):
        path = self.root / "water.csv"
        cr.write_csv(path, [{"location_name": "Synthetic", "bau30_ws_x_r": 0.4,
            "bau30_wd_x_r": 0.2, "bau30_ba_x_r": 200, "bau30_ws_x_l": "High",
            "bws_score": -9999, "gtd_raw": -0.5}])
        records = cr.aqueduct(self.args("aqueduct", path), self.root)[0]["water_risk"]
        found = {r["indicator"]: r for r in records}
        self.assertEqual(found["ws"]["raw"], 0.4)
        self.assertEqual(found["ba"]["raw_unit"], "cm/year")
        self.assertIsNone(found["bws"]["score"])
        self.assertEqual(found["gtd"]["raw"], -0.5)
        self.assertNotIn("calc_ws", found)

    def test_cdd_incomplete_year_and_duplicate_month(self):
        path = self.root / "cdd.csv"
        rows = [{"Country": "Indonesia", "Territory": "Synthetic", "Unit": "degree days",
                 "Date": f"2021-{m:02d}-01", "value": m} for m in range(1, 12)]
        cr.write_csv(path, rows)
        args = self.args("cdd", path, "--value-column", "value")
        annual = cr.cdd(args, self.root)[0]["cdd_annual"][0]
        self.assertEqual(annual["data_quality"], "incomplete_year")
        self.assertEqual(annual["mean_monthly_value"], 6)
        cr.write_csv(path, rows + [rows[0]])
        with self.assertRaisesRegex(ValueError, "多条"):
            cr.cdd(args, self.root)

    def test_cdd_idn_country_and_month_year_export(self):
        path = self.root / "cdd.csv"
        cr.write_csv(path, [{"Country": "IDN", "Territory": "", "Unit": "degree days", "Date": "1-2000", "value": -2}])
        result = cr.cdd(self.args("cdd", path, "--value-column", "value"), self.root)[0]
        self.assertEqual(result["cdd_monthly"][0]["date"], "2000-01")
        self.assertEqual(result["cdd_annual"][0]["mean_monthly_value"], -2)

    def test_reports_escape_input_and_do_not_overwrite(self):
        path = self.root / "water.csv"
        cr.write_csv(path, [{"location_name": "<script>alert(1)</script>", "bws_raw": 0.2}])
        args = self.args("aqueduct", path)
        first, second = cr.execute(args), cr.execute(args)
        self.assertNotEqual(first, second)
        report = (first / "report.html").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"<script>(.*?)</script>", report, re.S), [cr.REPORT_JS])
        self.assertNotIn("<script>alert(1)</script>", report)
        self.assertIn("&lt;script&gt;", report)
        self.assertEqual(len(json.loads((first / "metadata.json").read_text(encoding="utf-8"))["inputs"][0]["sha256"]), 64)
        self.assertTrue(cr.csv_value("=HYPERLINK(1)").startswith("'="))

    def test_demo_and_batch_relative_inputs(self):
        folder = cr.demo(self.root / "demo", self.parser)
        self.assertEqual(len(list(folder.glob("*/metadata.json"))), 3)
        self.assertTrue((folder / "report.html").exists())

    def test_reject_duplicate_csv_headers(self):
        path = self.root / "bad.csv"
        path.write_text("a,a\n1,2\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            cr.read_csv(path)


@unittest.skipUnless(SCIENCE, "scientific dependencies not installed")
class PrecipitationChecks(BaseChecks):
    def dataset(self, calendar="standard"):
        import numpy as np
        import xarray as xr
        times = xr.date_range("2020-01-01", periods=24, freq="MS", calendar=calendar, use_cftime=True)
        data = np.ones((24, 2, 2)) / 86400
        data[12:] *= 2
        return xr.Dataset({"pr": (("time", "latitude", "longitude"), data, {"units": "kg m-2 s-1"})},
            coords={"time": times, "latitude": [-5, -6], "longitude": [106, 107]})

    def test_month_lengths_leap_year_and_descending_lat(self):
        da = cr.prepare_precipitation(self.dataset(), "pr", [95, -11, 141, 6])
        before = cr.annual_precipitation(da, (2020, 2020))
        after = cr.annual_precipitation(da, (2021, 2021))
        self.assertAlmostEqual(float(before.mean()), 366)
        self.assertAlmostEqual(float(after.mean()), 730)
        self.assertEqual(da.lat.values.tolist(), [-6, -5])

    def test_360_day_calendar(self):
        da = cr.prepare_precipitation(self.dataset("360_day"), "pr", [95, -11, 141, 6])
        self.assertAlmostEqual(float(cr.annual_precipitation(da, (2020, 2020)).mean()), 360)

    def test_missing_month_and_unsupported_units(self):
        ds = self.dataset()
        da = cr.prepare_precipitation(ds, "pr", [95, -11, 141, 6])
        with self.assertRaisesRegex(ValueError, "不完整"):
            cr.annual_precipitation(da.isel(time=slice(1, None)), (2020, 2020))
        with self.assertRaisesRegex(ValueError, "不支持"):
            cr.prepare_precipitation(ds, "pr", [95, -11, 141, 6], "kelvin")

    def test_missing_timestep_propagates_to_annual(self):
        import numpy as np
        ds = self.dataset()
        ds.pr.values[0, 0, 0] = np.nan
        da = cr.prepare_precipitation(ds, "pr", [95, -11, 141, 6])
        annual = cr.annual_precipitation(da, (2020, 2020))
        self.assertTrue(np.isnan(annual.sel(lat=-5, lon=106).item()))

    def test_netcdf_end_to_end_and_plots(self):
        path = self.root / "synthetic.nc"
        self.dataset().to_netcdf(path, engine="h5netcdf")
        args = self.args("precipitation", path, "--baseline", "2020:2020", "--future", "2021:2021", "--plots")
        folder = cr.execute(args)
        summary = json.loads((folder / "results.json").read_text(encoding="utf-8"))["precipitation_summary"][0]
        self.assertAlmostEqual(summary["reference_mm_year"], 366)
        self.assertAlmostEqual(summary["comparison_mm_year"], 730)
        self.assertTrue((folder / "precipitation_comparison.png").stat().st_size > 1000)


@unittest.skipUnless(GIS, "GIS dependencies not installed")
class RasterChecks(BaseChecks):
    def reference_fixture(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        from rasterio.warp import transform_geom
        path, zones = self.root / "reference.tif", self.root / "reference.geojson"
        with rasterio.open(path, "w", driver="GTiff", height=2, width=2, count=1, dtype="float32",
                crs="EPSG:3857", transform=from_origin(0, 2, 1, 1), nodata=-9999) as dst:
            dst.write(np.array([[1, 1], [0, -9999]], dtype="float32"), 1)
        geom = transform_geom("EPSG:3857", "EPSG:4326", {"type": "Polygon", "coordinates": [[[0,0],[2,0],[2,2],[0,2],[0,0]]]})
        cr.write_json(zones, {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "A"}, "geometry": geom}]})
        return path, zones

    def test_reference_score_uses_area_coverage_and_s_grade(self):
        path, zones = self.reference_fixture()
        args = self.args("raster", path, "--normalization", "index01", "--zones", str(zones), "--methodology", "reference", "--min-coverage", ".15")
        row = cr.raster(args, self.root)[0]["raster_risk"][0]
        self.assertAlmostEqual(row["total_pixels"], 4, places=5)
        self.assertAlmostEqual(row["coverage"], .75, places=5)
        self.assertEqual(row["intensity"], 7)
        self.assertAlmostEqual(row["coverage_weighted_score"], 5.25, places=5)
        self.assertEqual(row["screening_level"], "medium")

    @unittest.skipUnless(importlib.util.find_spec("PIL") and importlib.util.find_spec("matplotlib"), "map dependencies not installed")
    def test_satellite_registration_nodata_transparency_and_offline_cache(self):
        import io
        from PIL import Image
        path, zones = self.reference_fixture()
        memory = io.BytesIO()
        Image.new("RGB", (2,2), (110,120,130)).save(memory, format="JPEG")
        def fetch(url, **kwargs):
            if "/export?" in url:
                return json.dumps({"href": "https://server.arcgisonline.com/test.jpg", "width": 2, "height": 2,
                    "extent": {"xmin": 0, "ymin": 0, "xmax": 2, "ymax": 2, "spatialReference": {"wkid": 3857}}}).encode()
            return memory.getvalue() if url.endswith(".jpg") else b'{"copyrightText":"Synthetic attribution"}'
        args = self.parser.parse_args(["inarisk", "--zones", str(zones), "--satellite", "--cache", str(self.root / "cache")])
        import shapely.geometry
        asset = {"name": "A", "kind": "zone", "file": zones, "bounds": shapely.geometry.shape(cr.zone_features(zones)[0]["geometry"]).bounds}
        rows = [{"asset": "A", "asset_type": "zone", "service": "INDEKS_BAHAYA_BANJIR", "raw_raster": path.name}]
        with patch.object(cr, "http_bytes", side_effect=fetch):
            records = cr.satellite_maps(rows, [asset], args, self.root)
        self.assertEqual(records[0]["status"], "ok")
        with Image.open(self.root / records[0]["overlay"]) as overlay:
            self.assertEqual(overlay.getpixel((1,1))[3], 0)
            self.assertEqual(overlay.getpixel((0,1))[3], 255)
        args.offline = True
        offline = self.root / "offline"
        offline.mkdir()
        rows[0]["raw_raster"] = "../" + path.name
        with patch.object(cr, "http_bytes", side_effect=AssertionError("network forbidden")):
            repeated = cr.satellite_maps(rows, [asset], args, offline)
        self.assertEqual(repeated[0]["status"], "ok")

    def test_points_zones_nodata_and_partial_extent(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        path = self.root / "synthetic.tif"
        with rasterio.open(path, "w", driver="GTiff", height=2, width=2, count=1,
                dtype="float32", crs="EPSG:4326", transform=from_origin(106, -5, 1, 1), nodata=-9999) as dst:
            dst.write(np.array([[0, 255], [128, -9999]], dtype="float32"), 1)
        points = self.root / "points.csv"
        cr.write_csv(points, [{"name": "A", "lon": 106.5, "lat": -5.5}, {"name": "B", "lon": 120, "lat": 0}])
        zones = self.root / "zones.geojson"
        def zone(name, west):
            return {"type": "Feature", "properties": {"name": name}, "geometry": {"type": "Polygon",
                "coordinates": [[[west, -5], [108, -5], [108, -7], [west, -7], [west, -5]]]}}
        cr.write_json(zones, {"type": "FeatureCollection", "features": [zone("full", 106), zone("partial", 105)]})
        args = self.args("raster", path, "--normalization", "inverse-gray255", "--points", str(points), "--zones", str(zones))
        result = cr.raster(args, self.root)[0]["raster_risk"]
        self.assertEqual(result[0]["normalized_index"], 1)
        self.assertIsNone(result[1]["normalized_index"])
        self.assertEqual(result[2]["valid_pixels"], 3)
        self.assertAlmostEqual(result[2]["coverage"], 0.75)
        self.assertEqual(result[3]["data_quality"], "partial_raster_extent")
        self.assertEqual(result[3]["screening_level"], "undetermined")


@unittest.skipUnless(GIS, "GIS dependencies not installed")
class PipelineChecks(BaseChecks):
    @unittest.skipUnless(importlib.util.find_spec("matplotlib"), "chart dependencies not installed")
    def test_example_assets_generate_complete_model_report(self):
        import urllib.parse
        import numpy as np
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.warp import transform_geom
        from shapely.geometry import shape
        examples = Path(__file__).resolve().parent / "examples"
        zones, points = examples / "inarisk-zones.geojson", examples / "inarisk-points.csv"
        feature = cr.zone_features(zones)[0]
        point = cr.point_rows(points)[0]
        self.assertTrue(shape(feature["geometry"]).contains(shape({"type":"Point", "coordinates":point[1:]})))
        west,south,east,north = shape(transform_geom("EPSG:4326","EPSG:3395",feature["geometry"])).bounds
        px,py = (east-west)/20,(north-south)/20
        values = {"INDEKS_BAHAYA_BANJIR":.2, "INDEKS_KERENTANAN_BANJIR":.5, "layer_risiko_banjir":.9}
        def response(url, params=None, timeout=30):
            if url.endswith("/inarisk"):
                return {"services":[{"name":"inarisk/"+name,"type":"ImageServer"} for name in values]}
            if url.endswith("/exportImage"):
                service = url.split("/")[-3]
                query=urllib.parse.urlencode({"bbox":params["bbox"],"size":params["size"],"value":values[service]})
                return {"href":"https://gis.bnpb.go.id/server/rest/directories/arcgisoutput/synthetic.tif?"+query}
            return {"bandCount":1,"pixelType":"F32","minValues":[0],"maxValues":[1],
                "pixelSizeX":px,"pixelSizeY":py,"maxImageWidth":1024,"maxImageHeight":1024,
                "extent":{"xmin":west-5*px,"xmax":east+5*px,"ymin":south-5*py,"ymax":north+5*py,"spatialReference":{"wkid":3395}}}
        def download(url, *unused, **kwargs):
            query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            bounds=list(map(float,query["bbox"][0].split(",")));width,height=map(int,query["size"][0].split(","))
            with MemoryFile() as memory:
                with memory.open(driver="GTiff",width=width,height=height,count=1,dtype="float32",crs="EPSG:3395",
                        transform=rasterio.transform.from_bounds(*bounds,width,height),nodata=-9999) as image:
                    image.write(np.full((height,width),float(query["value"][0]),dtype="float32"),1)
                return memory.read()
        args=self.parser.parse_args(["inarisk","--points",str(points),"--zones",str(zones),"--services",*values,
            "--methodology","reference","--min-coverage",".15","--cache",str(self.root/"cache"),"--out",str(self.root/"out")])
        args.data_kind="synthetic"
        with patch.object(cr,"http_json",side_effect=response),patch.object(cr,"http_bytes",side_effect=download):
            folder=cr.execute(args)
        data=json.loads((folder/"results.json").read_text(encoding="utf-8"))
        self.assertEqual(data["pipeline_status"][0]["status"],"complete")
        self.assertEqual(len(data["asset_risk"]),6)
        aggregate=data["reference_aggregate"][0]
        self.assertEqual(aggregate["included_layers"],3)
        self.assertEqual(aggregate["screening_level"],"medium")
        self.assertAlmostEqual(aggregate["score"],(1+(1+4*.17/.33)+(5+5*.24/.34))/3,places=4)
        report=(folder/"report.html").read_text(encoding="utf-8")
        for token in ('data-metric="composite-score"','data-metric="composite-grade"','data-open-model',
                '<dialog class="model-dialog" id="model-method"','form method="dialog"','合成数据','中风险</h2>'):
            self.assertIn(token,report)
        self.assertEqual(len(list((folder/"charts").glob("*.png"))),4)
        self.assertTrue((folder/"asset_risk.csv").exists())
        args.offline=True
        with patch.object(cr,"http_bytes",side_effect=AssertionError("offline request")):
            repeated=cr.execute(args)
        again=json.loads((repeated/"results.json").read_text(encoding="utf-8"))
        self.assertEqual(again["reference_aggregate"][0]["score"],aggregate["score"])
        self.complete_report_output=folder

    def metadata(self):
        return {"bandCount": 1, "pixelType": "F32", "minValues": [0], "maxValues": [1],
                "pixelSizeX": 1, "pixelSizeY": 1, "maxImageWidth": 2, "maxImageHeight": 2,
                "extent": {"xmin": 0, "ymin": 0, "xmax": 2, "ymax": 2,
                           "spatialReference": {"wkid": 4326}}}

    def pipeline_args(self):
        points = self.root / "points.csv"
        cr.write_csv(points, [{"name": "Synthetic A", "lon": 0.5, "lat": 1.5}])
        zones = self.root / "zones.geojson"
        cr.write_json(zones, {"type": "FeatureCollection", "features": [{"type": "Feature",
            "properties": {"name": "Synthetic Zone"}, "geometry": {"type": "Polygon",
            "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]}}]})
        return self.parser.parse_args(["inarisk", "--points", str(points), "--zones", str(zones),
            "--services", "INDEKS_BAHAYA_TEST", "--cache", str(self.root / "cache"), "--out", str(self.root / "out")])

    def fake_json(self, url, params=None, timeout=30):
        if url.endswith("/inarisk"):
            return {"services": [{"name": "inarisk/INDEKS_BAHAYA_TEST", "type": "ImageServer"}]}
        if url.endswith("/exportImage"):
            self.assertEqual(params["format"], "tiff")
            self.assertEqual(params["pixelType"], "F32")
            self.assertEqual(json.loads(params["renderingRule"]), {"rasterFunction": "None"})
            self.assertEqual(params["interpolation"], "RSP_NearestNeighbor")
            return {"href": "https://gis.bnpb.go.id/server/rest/directories/arcgisoutput/test.tif"}
        return self.metadata()

    def tile_bytes(self, *args, **kwargs):
        import numpy as np
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        with MemoryFile() as memory:
            with memory.open(driver="GTiff", width=2, height=2, count=1, dtype="float32",
                             crs="EPSG:4326", transform=from_origin(0, 2, 1, 1), nodata=-9999) as tile:
                tile.write(np.array([[0.2, 0.8], [0.5, -9999]], dtype="float32"), 1)
            return memory.read()

    def test_full_pipeline_cache_offline_and_corruption(self):
        args = self.pipeline_args()
        with patch.object(cr, "http_json", side_effect=self.fake_json), patch.object(cr, "http_bytes", side_effect=self.tile_bytes):
            folder = cr.execute(args)
        results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(results["pipeline_status"][0]["status"], "complete")
        self.assertEqual(results["pipeline_status"][0]["cache_hits"], 1)
        self.assertEqual(results["asset_risk"][1]["valid_pixels"], 3)
        self.assertAlmostEqual(results["asset_risk"][0]["normalized_index"], 0.2, places=6)
        self.assertTrue((folder / "source_metadata.json").exists())
        self.assertTrue((folder / "report.html").exists())
        args.offline = True
        with patch.object(cr, "http_json", side_effect=AssertionError("offline network request")), patch.object(cr, "http_bytes", side_effect=AssertionError("offline download")):
            offline = cr.execute(args)
        offline_data = json.loads((offline / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(offline_data["pipeline_status"][0]["cache_hits"], 2)
        next((self.root / "cache").rglob("*.tif")).write_bytes(b"corrupt")
        with patch.object(cr, "http_json", side_effect=AssertionError("offline network request")):
            corrupt = cr.execute(args)
        corrupt_data = json.loads((corrupt / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(corrupt_data["pipeline_status"][0]["status"], "unavailable")
        self.assertTrue(all(row["screening_level"] == "undetermined" for row in corrupt_data["asset_risk"]))

    def test_download_budget_and_invalid_service(self):
        args = self.pipeline_args()
        args.max_pixels = 1
        with patch.object(cr, "http_json", side_effect=self.fake_json):
            with self.assertRaisesRegex(ValueError, "像元"):
                cr.execute(args)
        args.max_pixels = 100
        args.services = ["../unsafe"]
        with self.assertRaisesRegex(ValueError, "服务名称"):
            cr.execute(args)

    def test_unlabelled_nodata_requires_upstream_confirmation(self):
        import numpy as np
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        args = self.pipeline_args()
        def unlabelled_tile(*unused, **kwargs):
            with MemoryFile() as memory:
                with memory.open(driver="GTiff", width=2, height=2, count=1, dtype="float32",
                        crs="EPSG:4326", transform=from_origin(0, 2, 1, 1)) as tile:
                    tile.write(np.array([[0.2, 0.8], [0.5, -3.402823e38]], dtype="float32"), 1)
                return memory.read()
        def response(url, params=None, timeout=30):
            if url.endswith("/identify"):
                return {"value": "NoData"}
            return self.fake_json(url, params, timeout)
        with patch.object(cr, "http_json", side_effect=response), patch.object(cr, "http_bytes", side_effect=unlabelled_tile):
            folder = cr.execute(args)
        data = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(data["pipeline_status"][0]["status"], "complete")
        self.assertEqual(data["asset_risk"][1]["valid_pixels"], 3)
        manifest = json.loads((folder / "download_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest[0]["nodata_confirmations"][0]["response"]["value"], "NoData")
        args.offline = True
        with patch.object(cr, "http_json", side_effect=AssertionError("offline request")):
            offline = cr.execute(args)
        self.assertTrue((offline / "report.html").exists())
        args.offline, args.refresh = False, True
        def not_missing(url, params=None, timeout=30):
            return {"value": "0.5"} if url.endswith("/identify") else self.fake_json(url, params, timeout)
        with patch.object(cr, "http_json", side_effect=not_missing), patch.object(cr, "http_bytes", side_effect=unlabelled_tile):
            rejected = cr.execute(args)
        rejected_data = json.loads((rejected / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(rejected_data["pipeline_status"][0]["status"], "unavailable")

    def test_rendered_source_is_reported_as_unavailable(self):
        args = self.pipeline_args()
        meta = self.metadata()
        meta["bandCount"] = 3
        def response(url, params=None, timeout=30):
            return self.fake_json(url, params, timeout) if url.endswith("/inarisk") else meta
        with patch.object(cr, "http_json", side_effect=response), patch.object(cr, "http_bytes", side_effect=AssertionError("must not download RGB")):
            folder = cr.execute(args)
        data = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(data["pipeline_status"][0]["status"], "unavailable")

    def test_catalog_network_failure_still_produces_asset_report(self):
        args = self.pipeline_args()
        with patch.object(cr, "http_json", side_effect=OSError("Network unavailable")):
            folder = cr.execute(args)
        data = json.loads((folder / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(data["pipeline_status"][0]["status"], "unavailable")
        self.assertTrue((folder / "report.html").exists())
        self.assertTrue(all("Network unavailable" in row["error"] for row in data["asset_risk"]))

    def test_batch_preserves_partial_status(self):
        args = self.pipeline_args()
        config = self.root / "batch.json"
        cr.write_json(config, {"jobs": [{"command": "inarisk", "points": args.points,
            "services": ["INDEKS_BAHAYA_MISSING"], "cache": args.cache}]})
        with patch.object(cr, "http_json", side_effect=self.fake_json):
            folder = cr.batch(config, self.root / "batch-output", self.parser)
        metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["run_status"], "partial")
        self.assertEqual(metadata["jobs"][0]["status"], "unavailable")

    @unittest.skipUnless(importlib.util.find_spec("fiona") and importlib.util.find_spec("openpyxl"), "asset dependencies not installed")
    def test_projected_geopackage_and_excel_import(self):
        import fiona
        import openpyxl
        gpkg = self.root / "assets.gpkg"
        with fiona.open(gpkg, "w", driver="GPKG", layer="assets", crs="EPSG:3857",
                schema={"geometry": "Polygon", "properties": {"name": "str"}}) as dst:
            dst.write({"geometry": {"type": "Polygon", "coordinates": [[[0,0],[1000,0],[1000,1000],[0,1000],[0,0]]]},
                       "properties": {"name": "Projected Asset"}})
        normalized = cr.zone_features(gpkg, "assets")
        maximum = max(p[0] for p in normalized[0]["geometry"]["coordinates"][0])
        self.assertTrue(0 < maximum < 0.01)
        book = openpyxl.Workbook()
        book.active.append(["资产名称", "经度", "纬度"])
        book.active.append(["Synthetic Excel Asset", 106.82, -6.17])
        path = self.root / "points.xlsx"
        book.save(path)
        book.close()
        self.assertEqual(cr.point_rows(path), [("Synthetic Excel Asset", 106.82, -6.17)])


if __name__ == "__main__":
    unittest.main()
