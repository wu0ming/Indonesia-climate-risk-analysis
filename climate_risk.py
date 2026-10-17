#!/usr/bin/env python3
"""Indonesia climate screening: one entry point, optional scientific dependencies.

CSV commands use only Python's standard library. See README.md for data contracts.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import html
import importlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from types import SimpleNamespace
from datetime import datetime, timezone

VERSION = "0.4.0"
REPORT_CSS = """
:root{--ink:#182f38;--muted:#667b84;--accent:#087b78;--line:#dfE8e8;--paper:#fff;--low:#19805b;--medium:#ad760f;--high:#c7484e}
*{box-sizing:border-box}html{scroll-padding-top:22px}body{margin:0;background:#f2f6f5;color:var(--ink);font:15px/1.75 'Segoe UI','Microsoft YaHei',system-ui,sans-serif}button,input,select{font:inherit}button,a,summary{touch-action:manipulation}a{color:var(--accent);text-underline-offset:3px}button{cursor:pointer}button:focus-visible,a:focus-visible,summary:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #59bcb6;outline-offset:4px}
main{max-width:1240px;padding:36px 24px 64px;margin:auto}.report-header{position:relative;overflow:hidden;background:linear-gradient(115deg,#143c40,#115d5a);color:#fff;border-radius:20px;padding:34px 36px;margin-bottom:28px;box-shadow:0 14px 36px #133c4012}.report-header:after{content:'';position:absolute;right:-55px;top:-100px;width:330px;height:330px;border:1px solid #ffffff1a;border-radius:50%;pointer-events:none}.report-brand{font-size:11px;font-weight:700;letter-spacing:2.6px;color:#b5dcd5}.header-top,.header-bottom{display:flex;align-items:center;justify-content:space-between;gap:20px;position:relative;z-index:1}.report-header h1{font-size:30px;line-height:1.4;letter-spacing:.4px;margin:15px 0 8px;font-weight:650}.report-title{margin:0;color:#cfE6e1;font-size:16px}.report-meta{font-size:12px;color:#b8d9d2;margin:18px 0 0}.header-badge{border:1px solid #ffffff38;border-radius:30px;padding:5px 12px;color:#dcefeb;font-size:12px;white-space:nowrap}.header-actions{display:flex;gap:10px;flex-shrink:0}
.button{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid var(--line);border-radius:9px;padding:9px 16px;background:#fff;color:var(--ink);font-weight:600;text-decoration:none;line-height:1.5}.button.primary{background:var(--accent);border-color:var(--accent);color:#fff}.button.ghost{background:#ffffff0f;border-color:#ffffff30;color:#f1fbf8}.button:hover{filter:brightness(.97)}.button.ghost:hover{background:#ffffff20}.button.small{font-size:13px;padding:7px 13px}
h2{font-size:21px;line-height:1.45;margin:0 0 14px;font-weight:650}h3{font-size:17px;margin:24px 0 10px}p{margin:10px 0}.card,.risk-hero{background:var(--paper);border:1px solid var(--line);border-radius:15px;padding:26px;margin:20px 0;box-shadow:0 3px 12px #153f3c03}.section-heading{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px}.section-heading h2{margin:0}.eyebrow{font-size:11px;letter-spacing:1.8px;font-weight:700;color:var(--accent);text-transform:uppercase}.subtle{color:var(--muted);font-size:13px}.statistics{padding-bottom:20px}.stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.stat{background:#f5f8f8;border:1px solid #e7eeee;border-radius:12px;padding:19px 20px;min-width:0}.stat.primary-stat{background:#eef7f3;border-color:#d9eae2}.stat-label{font-size:13px;color:var(--muted);display:block;margin-bottom:11px}.stat-value{font-size:31px;font-weight:680;line-height:1.2;letter-spacing:-.7px;color:var(--risk-color,var(--ink));display:block;overflow-wrap:anywhere}.stat-value.grade-value{font-size:25px;letter-spacing:0}.stat-unit{font-size:12px;color:var(--muted);display:block;margin-top:9px}.stat.pending-stat{background:#fffaf0;border-color:#f0e5c8}.method-entry{display:flex;align-items:center;justify-content:space-between;gap:20px;border-top:1px solid var(--line);margin-top:20px;padding-top:18px}.method-entry strong{font-size:14px}.method-entry p{font-size:12px;color:var(--muted);margin:3px 0 0}
.risk-low{--risk-color:var(--low)}.risk-medium{--risk-color:var(--medium)}.risk-high{--risk-color:var(--high)}.risk-undetermined{--risk-color:#68798c}.risk-hero{border-left:5px solid var(--risk-color);padding:26px 30px}.risk-top{display:flex;justify-content:space-between;gap:16px;align-items:center;color:var(--muted);font-size:13px}.risk-main{display:flex;align-items:center;justify-content:space-between;gap:24px}.risk-headline{font-size:35px;line-height:1.3;margin:8px 0;color:var(--risk-color)}.risk-score{text-align:right}.risk-score strong{font-size:38px;line-height:1.25;display:block}.risk-score span{font-size:12px;color:var(--muted)}.risk-summary{font-size:16px;max-width:940px}.risk-status{background:#edf6f3;color:#28675a;padding:4px 11px;border-radius:20px;white-space:nowrap;font-size:12px}.risk-status.pending{background:#fff2d4;color:#916407}.risk-quality{background:#fff9ec;border:1px solid #f0e2bd;border-radius:9px;padding:12px 16px;margin:16px 0 0;color:#7e6228;font-size:13px}.risk-meter{height:10px;border-radius:8px;position:relative;margin:25px 0 10px}.risk-pointer{position:absolute;top:-7px;height:24px;width:5px;background:#183449;border:2px solid #fff;border-radius:3px;transform:translateX(-50%)}.risk-ticks{position:relative;height:22px;font-size:11px;color:var(--muted)}.risk-ticks span{position:absolute;transform:translateX(-50%)}.risk-note{font-size:12px;color:var(--muted)}.risk-guide{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.risk-guide div{padding:18px;border-radius:10px;background:#f7f9f9;border-top:3px solid var(--risk-color)}.risk-guide strong{display:block;color:var(--risk-color);font-size:18px}.risk-guide small{color:var(--muted);font-size:12px}.risk-guide p{font-size:13px;line-height:1.75;margin:8px 0 0}.risk-focus{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.risk-focus article{border:1px solid var(--line);border-radius:10px;padding:18px;background:#fbfcfc}.risk-focus strong{display:block;font-size:14px}.risk-focus p{font-size:13px;color:var(--muted);margin:8px 0 0}.report-nav{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}.report-nav a,.report-nav button{padding:8px 14px;background:#e8f1ef;color:#28625e;border:0;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600}
details.card{padding:0;overflow:hidden}details.card>summary{padding:20px 25px;cursor:pointer;font-size:15px;font-weight:600;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:14px}details.card>summary::-webkit-details-marker{display:none}details.card>summary:after{content:'+';color:var(--accent);font-size:22px;font-weight:400;line-height:1}details.card[open]>summary{border-bottom:1px solid var(--line);background:#fbfdfc}details.card[open]>summary:after{content:'−'}details.card>summary:hover{background:#f8fbfa}details.card>:not(summary){margin:20px 25px}details.card>.card{border:0;box-shadow:none;padding:0;margin:24px 25px}details.card>section.card+section.card{border-top:1px solid var(--line);padding-top:24px}.table{overflow:auto;border:1px solid var(--line);border-radius:10px;background:#fff;margin:18px 0}table{border-collapse:collapse;white-space:nowrap;width:100%;font-size:13px}th,td{text-align:left;padding:11px 14px;border-bottom:1px solid #e8eeee}th{background:#f0f6f5;font-size:12px;font-weight:650;color:#365a5a;position:sticky;top:0}tbody tr:nth-child(even){background:#fbfdfc}tbody tr:hover{background:#f2f8f5}tr:last-child td{border-bottom:0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f8f8;border-radius:10px;padding:18px;font-size:12px;line-height:1.7}figure{margin:24px 0 34px}figure img{border:1px solid #e8eeee;border-radius:10px;display:block;max-width:100%}figcaption{font-size:12px;color:var(--muted);margin-top:12px}figcaption a{white-space:nowrap}
.map-toolbar{display:grid;grid-template-columns:minmax(220px,1fr) minmax(180px,.65fr) 120px;gap:20px;padding:18px;background:#f4f8f7;border-radius:11px;margin:20px 0}.map-toolbar label{display:flex;align-items:center;gap:10px;font-size:13px;color:#4b686b;min-width:0}.map-toolbar select{max-width:100%;min-width:0;background:#fff;border:1px solid #cfdddd;border-radius:7px;padding:8px;flex:1}.map-toolbar input[type=range]{min-width:65px;width:100%;accent-color:var(--accent)}.map-frame{overflow:auto;max-height:680px;background:#1a3337;border:1px solid var(--line);border-radius:12px}.map-legend{display:flex;align-items:center;flex-wrap:wrap;gap:12px;color:var(--muted);font-size:12px}.map-legend span{display:inline-block;width:190px;height:10px;border-radius:6px;background:linear-gradient(to right,#15b94b,#a7da22 33%,#ffe01b 66%,#fb8d26 82%,#e5262a)}#mapSource{font-size:11px;color:var(--muted);overflow-wrap:anywhere}.map-footer{font-size:12px;color:var(--muted)}
.model-dialog{border:1px solid #d1e3df;border-radius:18px;padding:0;width:min(960px,calc(100% - 32px));max-height:88vh;color:var(--ink);box-shadow:0 25px 90px #092c3d44}.model-dialog::backdrop{background:#122d3dc2;backdrop-filter:blur(3px)}.dialog-heading{position:sticky;top:0;z-index:2;display:flex;justify-content:space-between;align-items:center;gap:20px;padding:20px 26px;background:#fff;border-bottom:1px solid var(--line)}.dialog-heading h2{font-size:19px;margin:0}.dialog-heading form{margin:0}.dialog-content{padding:10px 26px 28px}.dialog-content>.model-content{padding:12px 0}.dialog-content table{white-space:normal}.dialog-content li{margin:12px 0}.dialog-content img{max-width:100%;border-radius:10px;border:1px solid var(--line)}.report-footer{display:flex;justify-content:space-between;gap:20px;border-top:1px solid var(--line);margin-top:32px;padding-top:18px;color:var(--muted);font-size:11px}.synthetic-notice{padding:14px 18px;border:1px solid #f0dfa9;background:#fff8e5;border-radius:10px;font-size:13px;margin:20px 0}
@media(max-width:900px){.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.map-toolbar{grid-template-columns:1fr 1fr}.map-toolbar label:first-child{grid-column:1/-1}.header-bottom{align-items:flex-start;flex-direction:column}.report-header h1{font-size:26px}}
@media(max-width:600px){main{padding:18px 14px 40px}.report-header{padding:24px 22px;border-radius:14px}.report-header h1{font-size:23px}.header-top{align-items:flex-start}.header-badge{font-size:10px;padding:4px 9px}.report-brand{font-size:9px;letter-spacing:1.6px}.header-actions{width:100%}.header-actions .button{flex:1}.card,.risk-hero{padding:20px;border-radius:12px}.stat{padding:16px 14px}.stat-value{font-size:29px}.stat-value.grade-value{font-size:21px}.risk-headline{font-size:29px}.risk-top{align-items:flex-start;flex-direction:column;gap:9px}.risk-main{gap:12px}.risk-score strong{font-size:30px}.risk-guide{grid-template-columns:1fr}.method-entry{align-items:flex-start;flex-direction:column;gap:12px}.method-entry .button{width:100%}.map-toolbar{grid-template-columns:1fr;gap:12px;padding:14px}.map-toolbar label:first-child{grid-column:auto}.risk-focus{grid-template-columns:1fr}details.card>summary{padding:18px 20px}details.card>:not(summary),details.card>.card{margin:18px 20px}.dialog-heading{padding:18px}.dialog-content{padding:8px 18px 22px}.report-footer{flex-direction:column;gap:5px}}
@media print{body{background:#fff}main{max-width:none;padding:0}.report-header{background:#fff;color:var(--ink);box-shadow:none;border:1px solid var(--line);padding:20px}.report-header h1,.report-title,.report-meta,.report-brand{color:var(--ink)}.header-actions,.report-nav,.method-entry,.header-badge{display:none}.card,.risk-hero{box-shadow:none;break-inside:avoid}.table{overflow:visible}table{white-space:normal;font-size:9px}th,td{padding:5px 7px}figure{break-inside:avoid}.map-frame{max-height:none;overflow:visible}.model-dialog{display:block;position:static;max-height:none;width:100%;box-shadow:none;margin:20px 0;overflow:visible}.dialog-heading form{display:none}.risk-guide{grid-template-columns:repeat(3,1fr)}}
"""
REPORT_JS = """
const modelDialog = document.getElementById('model-method');
document.querySelectorAll('[data-open-model]').forEach(button => {
  button.addEventListener('click', () => {
    if (!modelDialog) return;
    if (typeof modelDialog.showModal === 'function') modelDialog.showModal();
    else modelDialog.setAttribute('open', '');
  });
});
if (modelDialog) {
  modelDialog.addEventListener('click', event => {
    const bounds = modelDialog.getBoundingClientRect();
    if (event.target === modelDialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) modelDialog.close();
  });
}
const printButton = document.getElementById('print-report');
if (printButton) printButton.addEventListener('click', () => window.print());
let printDetails = [];
window.addEventListener('beforeprint', () => {
  printDetails = Array.from(document.querySelectorAll('details')).map(element => [element, element.open]);
  printDetails.forEach(([element]) => { element.open = true; });
});
window.addEventListener('afterprint', () => {
  printDetails.forEach(([element, open]) => { element.open = open; });
  printDetails = [];
});
"""
BNPB_ROOT = "https://gis.bnpb.go.id/server/rest/services"
DEFAULT_SERVICES = ["INDEKS_BAHAYA_BANJIR", "INDEKS_BAHAYA_KEKERINGAN"]
INDEX_TOLERANCE = 1e-6  # Allow float32 roundoff at the documented 0/1 endpoints.
IMAGERY_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"
COMPARISON_SERVICES = {"IDX_H_EQ_GLOBAL", "layer_risiko_gempabumi_jkt"}
NETWORK = {"interval": 1.5, "next": {}, "failures": {}, "paused": set(), "log": None}


def configure_network(interval=1.5, log=None):
    NETWORK.update(interval=interval, next={}, failures={}, paused=set(), log=log)


def request_stage(url):
    path = urllib.parse.urlsplit(url).path.lower().rstrip("/")
    if path.endswith("/exportimage"):return "export_request"
    if "/arcgisoutput/" in path:return "tile_download"
    if path.endswith("/identify"):return "nodata_confirmation"
    if path.endswith("/inarisk"):return "catalog"
    if path.endswith("/imageserver"):return "service_metadata"
    return "satellite_or_other_metadata"


def log_request(url, attempt, started, status, headers=None, error=None, body=None):
    if NETWORK["log"] is None:return
    selected = {k.lower():str(v) for k,v in dict(headers or {}).items()
                if k.lower() in {"server", "cf-ray", "retry-after", "content-type", "via"}}
    record = {"utc": datetime.now(timezone.utc).isoformat(), "url": url, "stage": request_stage(url),
        "attempt": attempt + 1, "http_status": status, "seconds": round(time.monotonic()-started, 3),
        "headers": selected, "error": str(error) if error else None, "error_body_prefix": body}
    with Path(NETWORK["log"]).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def physical_services(catalog):
    """All physical H/V/R indices, one national source per indicator, plus comparisons."""
    return sorted(s["name"].split("/")[-1] for s in catalog.get("services", [])
        if s.get("type") == "ImageServer" and "COVID" not in s["name"].upper()
        and s["name"].split("/")[-1] != "INDEKS_RISIKO_TANAH_LONGSOR"
        and (re.search(r"/(INDEKS_(BAHAYA|KERENTANAN)_|INDEKS_MULTI_BAHAYA$|layer_risiko_)", s["name"])
             or s["name"].split("/")[-1] in COMPARISON_SERVICES))


def component(service):
    upper = service.upper()
    return ("vulnerability" if "KERENTANAN" in upper else "risk" if "RISIKO" in upper
            else "hazard" if "BAHAYA" in upper or service == "IDX_H_EQ_GLOBAL" else "other")


def layer_label(service):
    upper = service.upper().replace("_", "")
    hazard = next((zh for token, zh in (("BANJIRBANDANG", "山洪"), ("BANJIR", "洪水"),
        ("KEKERINGAN", "干旱"), ("CUACAEKSTRIM", "极端天气"), ("GEMPABUMI", "地震"),
        ("TANAHLONGSOR", "滑坡"), ("TSUNAMI", "海啸"), ("LIKUEFAKSI", "液化"),
        ("KARHUTLA", "森林及土地火灾"), ("KEBAKARANHUTAN", "森林及土地火灾"),
        ("GUNUNGAPI", "火山"), ("GELOMBANG", "极端海浪及侵蚀"), ("GEA", "极端海浪及侵蚀"),
        ("MULTI", "多灾种"), ("EQGLOBAL", "全球地震对照")) if token in upper), service)
    return hazard + {"hazard": "危险性", "vulnerability": "脆弱性", "risk": "风险", "other": "指数"}[component(service)] + ("（雅加达5米对照）" if service.endswith("_jkt") else "")


def score_grade(value, thresholds):
    return "undetermined" if value is None else "low" if value < thresholds[0] else "medium" if value < thresholds[1] else "high"
WRI_DICTIONARY = "https://github.com/wri/Aqueduct40/blob/master/data_dictionary_water-risk-atlas.md"
INDICATORS = {
    "bws": "Baseline water stress", "bwd": "Baseline water depletion",
    "iav": "Interannual variability", "sev": "Seasonal variability",
    "gtd": "Groundwater table decline", "rfr": "Riverine flood risk",
    "cfr": "Coastal flood risk", "drr": "Drought risk",
    "ucw": "Untreated connected wastewater", "cep": "Coastal eutrophication potential",
    "udw": "Unimproved/no drinking water", "usa": "Unimproved/no sanitation",
    "rri": "Peak RepRisk country ESG risk index",
    "ba": "Available blue water", "ww": "Gross water demand",
    "ws": "Water stress", "wd": "Water depletion",
    "iv": "Interannual variability", "sv": "Seasonal variability",
}


def require(name):
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise ValueError(f"缺少依赖 {name}；请运行 python -m pip install -r requirements.txt") from exc


def number(value, *, default=None):
    if value is None or str(value).strip().lower() in {"", "nan", "null", "none", "na", "n/a"}:
        return default
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"数值必须有限: {value!r}")
    return result


def read_csv(path):
    path = Path(path)
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"不支持的 CSV 编码: {path.name}")
    reader = csv.DictReader(io.StringIO(text))
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or not fields:
        raise ValueError("CSV 缺少表头或存在重复列名")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError("CSV 存在比表头更多的数据列")
    if not rows:
        raise ValueError("CSV 没有数据行")
    return rows


def csv_value(value):
    # Prevent spreadsheet formula execution in names supplied by input files.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"结果为空: {Path(path).name}")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: csv_value(v) for k, v in row.items()} for row in rows)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"name": Path(path).name, "bytes": Path(path).stat().st_size, "sha256": digest.hexdigest()}


def new_output(root, name):
    path = Path(root) / (name + "_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    path.mkdir(parents=True, exist_ok=False)
    return path


def risk_weight(value, thresholds, weights):
    low, middle = thresholds
    wlow, wmiddle, whigh = weights
    if value <= low:
        return wlow
    if value <= middle:
        return wlow + (wmiddle - wlow) * (value - low) / (middle - low)
    return wmiddle + (whigh - wmiddle) * (value - middle) / (1 - middle)


def validate_risk(args):
    if not (0 < args.thresholds[0] < args.thresholds[1] < 1):
        raise ValueError("风险阈值需满足 0 < 低阈值 < 中阈值 < 1")
    if not (0 <= args.weights[0] < args.weights[1] < args.weights[2]):
        raise ValueError("强度权重需非负且递增")
    if not (args.weights[0] < args.score_thresholds[0] < args.score_thresholds[1] < args.weights[2]):
        raise ValueError("评分阈值需递增且位于最低和最高权重之间")
    if not 0 <= args.min_coverage <= 1:
        raise ValueError("最低覆盖率需位于 0 到 1")
    values = [*args.thresholds, *args.weights, *args.score_thresholds, args.min_coverage]
    if not all(math.isfinite(x) for x in values):
        raise ValueError("风险参数必须为有限数")


def normalize(value, method):
    maximum = 1 if method == "index01" else 255
    if method == "index01" and math.isfinite(value) and -INDEX_TOLERANCE <= value <= 1 + INDEX_TOLERANCE:
        return min(1.0, max(0.0, value))
    if not math.isfinite(value) or not 0 <= value <= maximum:
        raise ValueError(f"像元值 {value} 超出 {method} 的范围；请核对数据和标准化方式")
    return 1 - value / 255 if method == "inverse-gray255" else value / maximum


def summarize_counts(counts, total, args):
    valid = sum(counts.values())
    if not math.isfinite(total) or total <= 0:
        raise ValueError("区域总像元数必须为正数")
    coverage = valid / total
    levels = [0.0, 0.0, 0.0]
    weighted = mean = 0.0
    for raw, count in counts.items():
        norm = normalize(raw, args.normalization)
        level = 0 if norm <= args.thresholds[0] else (1 if norm <= args.thresholds[1] else 2)
        levels[level] += count
        weighted += count * risk_weight(norm, args.thresholds, args.weights)
        mean += count * norm
    intensity = weighted / valid if valid else None
    # A legacy coverage-weighted score is retained only as a descriptive value.
    score = intensity * coverage if valid else None
    if not valid:
        quality = "no_valid_data"
    elif coverage > 1.01:
        quality = "coverage_exceeds_area"
    elif coverage < args.min_coverage:
        quality = "insufficient_coverage"
    else:
        quality = "ok"
    grade = "undetermined"
    if quality == "ok":
        grade = "low" if intensity < args.score_thresholds[0] else (
            "medium" if intensity < args.score_thresholds[1] else "high")
    return {
        "valid_pixels": valid, "total_pixels": total, "coverage": coverage,
        "mean_index": mean / valid if valid else None, "intensity": intensity,
        "coverage_weighted_score": score, "screening_level": grade, "data_quality": quality,
        "low_pixels": levels[0], "medium_pixels": levels[1], "high_pixels": levels[2],
        "low_fraction_valid": levels[0] / valid if valid else None,
        "medium_fraction_valid": levels[1] / valid if valid else None,
        "high_fraction_valid": levels[2] / valid if valid else None,
        "unknown_fraction": max(0, 1 - coverage) if coverage <= 1.01 else None,
    }


def histogram(args, out):
    validate_risk(args)
    rows = read_csv(args.input)
    histogram_columns = [(k, float(m.group(1))) for k in rows[0]
                         if (m := re.fullmatch(r"histo_?(-?\d+(?:\.\d+)?)", k, re.I))]
    if not histogram_columns:
        raise ValueError("找不到 histo0 / histo_0 等直方图列")
    result, seen, skipped = [], set(), 0
    for i, row in enumerate(rows, 2):
        layer = row.get("source_file") or row.get("Layer") or "index"
        if args.layer_pattern and not re.search(args.layer_pattern, layer, re.I):
            skipped += 1
            continue
        band = row.get("Band") or row.get("band")
        if band and int(number(band)) != args.band:
            skipped += 1
            continue
        zone = row.get("fid", row.get("Zone_ID", row.get("Id", str(i - 2))))
        identity = (layer, zone)
        if identity in seen:
            raise ValueError(f"重复的图层/区域 {identity}；请分离重叠数据或指定波段，不能重复计数")
        seen.add(identity)
        counts = {}
        for key, raw in histogram_columns:
            count = number(row.get(key), default=0)
            if count < 0 or not float(count).is_integer():
                raise ValueError(f"第 {i} 行 {key} 像元数必须为非负整数")
            if count and raw != args.nodata:
                normalize(raw, args.normalization)
                counts[raw] = counts.get(raw, 0) + count
        area = number(row.get("Area", row.get("area_ha")))
        px, py = number(row.get("pixel_size_x")), number(row.get("pixel_size_y"))
        unit = args.pixel_unit or row.get("pixel_size_unit", "").strip().lower()
        if unit not in {"meters", "metres", "meter", "metre", "m"}:
            raise ValueError(f"第 {i} 行像元单位 {unit!r} 不可换算面积；核实为米后可显式设置 --pixel-unit meters")
        if area is None or area <= 0 or px is None or py is None or px == 0 or py == 0:
            raise ValueError(f"第 {i} 行缺少有效 Area (ha)、pixel_size_x/y (m)")
        total = area * 10000 / abs(px * py)
        result.append({"layer": layer, "zone": zone, "area_ha": area, "band": args.band,
                       **summarize_counts(counts, total, args)})
    if not result:
        raise ValueError("没有匹配的指数图层；请检查 --layer-pattern 和 --band")
    return {"risk_summary": result}, [
        "筛查采用项目自定义模型，不是 BNPB 官方风险评级。标准化方向必须根据原始数据字典核实。",
        "NoData 表示未知；数据不足或覆盖率超过理论面积时不输出低风险结论。",
        "screening_level 按有效区域强度分级；coverage_weighted_score 仅保留作旧模型对照。",
        f"筛选跳过 {skipped} 行；未合并不同灾害、RGB 波段或空间重叠区域。",
    ]


def aqueduct(args, out):
    rows = read_csv(args.input)
    result = []
    for row_id, row in enumerate(rows):
        site = row.get("location_name") or row.get("points_id") or row.get("pfaf_id") or str(row_id)
        groups = {}
        for key, value in row.items():
            future = re.fullmatch(r"(bau|opt|pes)(30|50|80)_(ba|ww|ws|wd|iv|sv)_x_([rslc])", key)
            baseline = re.fullmatch(r"(" + "|".join(INDICATORS) + r")_(raw|score|label|cat)", key)
            if future:
                scenario, year, code, typ = future.groups()
                identity = (scenario, 2000 + int(year), code)
                field = {"r": "raw", "s": "score", "l": "label", "c": "category"}[typ]
            elif baseline:
                code, field = baseline.groups()
                identity = ("baseline", "baseline", code)
                field = "category" if field == "cat" else field
            else:
                continue
            record = groups.setdefault(identity, {"site": site, "row_id": row_id,
                "scenario": identity[0], "year": identity[1], "indicator": identity[2],
                "indicator_name": INDICATORS[code], "raw": None, "score": None,
                "label": "", "category": None,
                "raw_unit": "cm/year" if code in {"ba", "ww"} else "indicator_specific"})
            if field == "label":
                record[field] = value or ""
            else:
                parsed = number(value)
                missing = parsed in {-9999, -999} or (field in {"score", "category"} and parsed is not None and parsed < 0)
                record[field] = None if missing else parsed
        for record in groups.values():
            if record["score"] is not None and not 0 <= record["score"] <= 5:
                raise ValueError("Aqueduct score 超出官方 0–5 范围")
            record["data_quality"] = "ok" if any(record[x] is not None for x in ("raw", "score", "category")) else "label_only_or_missing"
            result.append(record)
    if not result:
        raise ValueError("未发现官方 Aqueduct 字段；请选择原始宽表 CSV，而非旧程序生成的中文结果表")
    return {"water_risk": result}, [
        "字段定义来源: " + WRI_DICTIONARY,
        "未来 ws=水压力，wd=水耗竭，ba=可用蓝水，ww=总用水需求；直接读取 ws，不计算 wd/ws。",
        "保留官方 raw、score、label、category；不把所有原始值解释为 0–1。-9999/-999 以及负评分/分类哨兵转换为空值，标签仍保留。",
        "不同指标不自行平均为一个总体风险分；筛查不等同于企业损失或洪水深度。",
    ]


def cdd(args, out):
    rows = read_csv(args.input)
    selected, seen = [], set()
    value_col = args.value_column
    country_names = {args.country.casefold()}
    if country_names & {"indonesia", "idn", "id"}:
        country_names = {"indonesia", "idn", "id"}
    for row in rows:
        if (row.get("Country") or "").strip().casefold() not in country_names:
            continue
        if args.territory and row.get("Territory", "") != args.territory:
            continue
        if value_col not in row:
            raise ValueError(f"找不到 CDD 数值列 {value_col}")
        date_text = row["Date"].strip()
        for fmt, text in (("%Y-%m-%d", date_text[:10]), ("%m-%Y", date_text), ("%Y-%m", date_text)):
            try:
                date = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"无法识别 CDD 日期 {date_text!r}；支持 YYYY-MM-DD / M-YYYY / YYYY-MM")
        identity = (date.year, date.month)
        if identity in seen:
            raise ValueError("同一月份存在多条记录；请用 --territory 选择一个序列")
        seen.add(identity)
        selected.append({"date": date.strftime("%Y-%m"), "year": date.year, "month": date.month,
                         "value": number(row[value_col]), "unit": row.get("Unit", ""),
                         "series": value_col, "country": row.get("Country"), "territory": row.get("Territory", "")})
    if not selected:
        raise ValueError("没有找到指定国家/地区的 CDD 数据")
    if len({r["unit"] for r in selected}) != 1 or len({r["territory"] for r in selected}) != 1:
        raise ValueError("CDD 包含多个单位或地区；请先选择一个序列")
    selected.sort(key=lambda r: r["date"])
    annual = []
    for year in sorted({r["year"] for r in selected}):
        values = [r["value"] for r in selected if r["year"] == year and r["value"] is not None]
        annual.append({"year": year, "valid_months": len(values),
                       "mean_monthly_value": statistics.mean(values) if values else None,
                       "data_quality": "complete" if len(values) == 12 else "incomplete_year",
                       "series": value_col, "unit": selected[0]["unit"]})
    return {"cdd_monthly": selected, "cdd_annual": annual}, [
        "CDD = Cooling Degree Days（制冷度日）；本工具汇总输入序列，不从温度重新推算。",
        "异常值序列仍作为异常值处理；年度输出是有效月份均值，不是全年制冷度日总数。",
        "不完整年份单独标记，不进行插值、外推或统计置信区间推断。",
    ]


def parse_period(text):
    if not re.fullmatch(r"\d{4}:\d{4}", text):
        raise ValueError("时期格式应为 2015:2025")
    start, end = map(int, text.split(":"))
    if not 1 <= start <= end <= 9999:
        raise ValueError("时期起止年份无效")
    return start, end


def prepare_precipitation(dataset, variable, bounds, units_override=None):
    np, xr = require("numpy"), require("xarray")
    if variable not in dataset:
        raise ValueError(f"NetCDF 不包含变量 {variable}")
    da = dataset[variable]
    names = {}
    for target, candidates in {"lat": ("lat", "latitude"), "lon": ("lon", "longitude"), "time": ("time",)}.items():
        match = next((name for name in candidates if name in da.coords), None)
        if match is None or da[match].ndim != 1 or da[match].dims != (match,):
            raise ValueError("仅支持 time/lat/lon 规则一维经纬度网格；请先重网格化曲线坐标")
        names[match] = target
    da = da.rename({key: val for key, val in names.items() if key != val})
    if set(da.dims) != {"time", "lat", "lon"}:
        raise ValueError("降水变量必须仅含 time、lat、lon 三个维度；请先选择模式/高度/成员")
    west, south, east, north = bounds
    if not all(math.isfinite(x) for x in bounds) or not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("范围应为西经度、南纬度、东经度、北纬度（不跨日期变更线）")
    da = da.assign_coords(lon=((da.lon + 180) % 360) - 180).sortby("lon").sortby("lat").sortby("time")
    for coord in ("lat", "lon", "time"):
        if len(set(da[coord].values.tolist())) != da.sizes[coord]:
            raise ValueError(f"坐标 {coord} 有重复值")
    da = da.sel(lon=slice(west, east), lat=slice(south, north))
    if not da.sizes["lat"] or not da.sizes["lon"] or not da.sizes["time"]:
        raise ValueError("指定范围没有网格中心或时间记录")
    units = (units_override or da.attrs.get("units", "")).lower().replace(" ", "").replace("**", "^")
    if units in {"kgm-2s-1", "kgm^-2s^-1", "kg/m2/s", "kg/m^2/s", "mms-1", "mm/s"}:
        da = da * 86400
    elif units in {"mm/day", "mmd-1", "mmday-1", "mmd^-1", "mmday^-1"}:
        pass
    elif units in {"mm/month", "mmmonth-1"}:
        da = da / da.time.dt.days_in_month
    else:
        raise ValueError(f"未知或不支持的降水单位 {units!r}；请核实元数据，不可默认乘 86400")
    da.attrs["units"] = "mm/day"
    da.attrs["monthly_accumulation"] = int(units in {"mm/month", "mmmonth-1"})
    return da.transpose("time", "lat", "lon")


def annual_precipitation(da, period):
    np, xr = require("numpy"), require("xarray")
    start, end = period
    sub = da.sel(time=slice(str(start), str(end)))
    if not sub.sizes["time"]:
        raise ValueError(f"缺少时期 {start}:{end} 的记录")
    years = sub.time.dt.year.values
    months = sub.time.dt.month.values
    days = sub.time.dt.day.values
    totals = []
    for year in range(start, end + 1):
        indices = np.flatnonzero(years == year)
        if not len(indices):
            raise ValueError(f"缺少 {year} 年；不能用不完整时期计算均值")
        part = sub.isel(time=indices)
        ym = list(zip(months[indices].tolist(), days[indices].tolist()))
        monthly = len(indices) == 12 and len(set(months[indices])) == 12
        if monthly:
            duration = part.time.dt.days_in_month
        else:
            if da.attrs.get("monthly_accumulation"):
                raise ValueError("mm/month 单位仅支持完整逐月累计数据")
            cal = part.time.dt.calendar
            expected = 360 if cal == "360_day" else (365 if cal in {"noleap", "365_day"} else (
                366 if cal in {"all_leap", "366_day"} else (366 if (year % 4 == 0 if cal == "julian" else calendar.isleap(year)) else 365)))
            if len(indices) != expected or len(set(ym)) != expected:
                raise ValueError(f"{year} 年不完整或不是月/日频率；要求完整 12 个月或完整逐日数据")
            duration = xr.ones_like(part.time, dtype=float)
        values = part.values
        if np.any(np.isinf(values)) or np.any(values[np.isfinite(values)] < 0):
            raise ValueError("降水包含无穷大或负值，请核对缺测值编码")
        # Any missing timestep makes that grid's annual total unknown.
        total = (part * duration).sum("time", skipna=False).expand_dims(year=[year])
        totals.append(total)
    return xr.concat(totals, dim="year")


def point_rows(path):
    result = []
    if Path(path).suffix.lower() == ".xlsx":
        book = require("openpyxl").load_workbook(path, read_only=True, data_only=True)
        try:
            rows = book.active.iter_rows(values_only=True)
            header = [str(v).strip() for v in next(rows)]
            if len(header) != len(set(header)):
                raise ValueError("Excel 资产表有重复列名")
            rows = [dict(zip(header, row)) for row in rows if any(v is not None for v in row)]
        finally:
            book.close()
    else:
        rows = read_csv(path)
    for row in rows:
        row = {str(k).strip().lower(): v for k, v in row.items()}
        def field(*names):
            return next((row[key] for key in names if key in row), None)
        name = field("name", "asset_name", "名称", "资产名称", "地点名称")
        lon, lat = number(field("lon", "longitude", "经度")), number(field("lat", "latitude", "纬度"))
        if not name or lon is None or lat is None or not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError("点位 CSV 必须包含 name,lon,lat，使用 WGS84 经纬度")
        result.append((name, lon, lat))
    if len({r[0] for r in result}) != len(result):
        raise ValueError("点位名称必须唯一")
    if not result:
        raise ValueError("资产点位为空")
    return result


def zone_features(path, layer=None):
    """Normalize polygon assets to WGS84 without uploading asset files."""
    shape, warp = require("shapely.geometry"), require("rasterio.warp")
    if Path(path).suffix.lower() in {".json", ".geojson"}:
        document = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if document.get("type") != "FeatureCollection" or "crs" in document:
            raise ValueError("GeoJSON 必须为不含旧版 crs 字段的 WGS84 FeatureCollection")
        source, crs = document.get("features", []), "EPSG:4326"
    else:
        fiona = require("fiona")
        layers = fiona.listlayers(path)
        if layer is None and len(layers) != 1:
            raise ValueError("区域文件包含多个图层；请使用 --zone-layer 指定资产图层：" + ", ".join(layers))
        with fiona.open(path, layer=layer or layers[0]) as collection:
            crs = collection.crs_wkt or collection.crs
            if not crs:
                raise ValueError("区域文件缺少坐标系，不能猜测 CRS")
            source = [{"geometry": dict(f["geometry"]), "properties": dict(f["properties"])} for f in collection]
    result, names = [], set()
    for index, feature in enumerate(source):
        geometry = shape.shape(feature.get("geometry"))
        if geometry.is_empty or not geometry.is_valid or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("区域边界必须为有效 Polygon/MultiPolygon")
        transformed = warp.transform_geom(crs, "EPSG:4326", shape.mapping(geometry))
        bounds = shape.shape(transformed).bounds
        if not (-180 <= bounds[0] <= bounds[2] <= 180 and -90 <= bounds[1] <= bounds[3] <= 90):
            raise ValueError("区域转换后超出 WGS84 范围")
        props = feature.get("properties") or {}
        name = str(next((props[k] for k in ("name", "asset_name", "名称", "资产名称", "Name", "id", "fid") if props.get(k) is not None), index))
        if name in names:
            raise ValueError("区域资产名称重复；请为每个区域设置唯一 name")
        names.add(name)
        result.append({"type": "Feature", "properties": {"name": name}, "geometry": transformed})
    if not result:
        raise ValueError("区域文件没有有效资产")
    return result


def precipitation(args, out):
    np, xr = require("numpy"), require("xarray")
    baseline, future = parse_period(args.baseline), parse_period(args.future)
    if baseline[1] >= future[0]:
        raise ValueError("对比时期必须在参考时期之后且不得重叠")
    with Path(args.input).open("rb") as stream:
        signature = stream.read(8)
    engine = "h5netcdf" if signature == b"\x89HDF\r\n\x1a\n" else "scipy"
    require(engine)
    with xr.open_dataset(args.input, engine=engine) as ds:
        da = prepare_precipitation(ds, args.variable, args.bounds, args.units)
        first = annual_precipitation(da, baseline)
        second = annual_precipitation(da, future)
        mean1, mean2 = first.mean("year", skipna=False), second.mean("year", skipna=False)
        difference = mean2 - mean1
        change = xr.where(mean1 > 0, difference / mean1 * 100, np.nan)
        midpoint_years = (sum(future) - sum(baseline)) / 2
        result_ds = xr.Dataset({"reference_mean_mm_year": mean1, "comparison_mean_mm_year": mean2,
            "difference_mm_year": difference, "change_pct": change,
            "linear_change_pct_per_year": change / midpoint_years})
        for var in result_ds:
            result_ds[var].attrs["units"] = "mm/year" if "mm_year" in var else ("%/year" if "per_year" in var else "%")
        result_ds.attrs.update(reference_period=args.baseline, comparison_period=args.future,
            spatial_scope="bounding box includes sea and neighbouring countries; not an Indonesia land mask",
            change_method="percent difference; annualized by period midpoints, not CAGR or fitted trend")
        for key in ("source_id", "experiment_id", "variant_label", "grid_label", "institution_id"):
            if key in ds.attrs:
                result_ds.attrs[key] = str(ds.attrs[key])
        require("h5netcdf")
        result_ds.to_netcdf(out / "precipitation_comparison.nc", engine="h5netcdf")
        tables = {"precipitation_summary": []}
        # Area approximation for a regular lon/lat grid. Renormalize only if every cell is valid.
        lat_spacing = np.diff(da.lat.values)
        lon_spacing = np.diff(da.lon.values)
        if (len(lat_spacing) and not np.allclose(lat_spacing, lat_spacing[0])) or (
            len(lon_spacing) and not np.allclose(lon_spacing, lon_spacing[0])):
            raise ValueError("区域面积加权仅支持等间距经纬度网格")
        weights = np.cos(np.deg2rad(da.lat))
        all_years = xr.concat([first, second], "year")
        series = []
        for year in all_years.year.values:
            field = all_years.sel(year=year)
            mean = float(field.weighted(weights).mean(("lat", "lon"), skipna=False))
            series.append({"site": "bounding_box", "year": int(year), "annual_precipitation_mm": mean if math.isfinite(mean) else None})
        bvalue = float(mean1.weighted(weights).mean(("lat", "lon"), skipna=False))
        fvalue = float(mean2.weighted(weights).mean(("lat", "lon"), skipna=False))
        locations = [("bounding_box", bvalue, fvalue)]
        for name, lon, lat in point_rows(args.points) if args.points else []:
            if not (float(da.lon.min()) <= lon <= float(da.lon.max()) and float(da.lat.min()) <= lat <= float(da.lat.max())):
                raise ValueError(f"点位 {name} 位于裁剪后网格中心范围之外")
            selected = all_years.sel(lon=lon, lat=lat, method="nearest")
            for year, value in zip(selected.year.values, selected.values):
                series.append({"site": name, "year": int(year),
                    "annual_precipitation_mm": float(value) if math.isfinite(value) else None,
                    "grid_lon": float(selected.lon), "grid_lat": float(selected.lat)})
            locations.append((name, float(mean1.sel(lon=lon, lat=lat, method="nearest")),
                              float(mean2.sel(lon=lon, lat=lat, method="nearest"))))
        for name, before, after in locations:
            valid = math.isfinite(before) and math.isfinite(after)
            pct = (after - before) / before * 100 if valid and before > 0 else None
            tables["precipitation_summary"].append({"site": name, "reference_period": args.baseline,
                "comparison_period": args.future, "reference_mm_year": before if math.isfinite(before) else None,
                "comparison_mm_year": after if math.isfinite(after) else None,
                "change_pct": pct, "linear_change_pct_per_year": pct / midpoint_years if pct is not None else None,
                "data_quality": "ok" if valid else "missing_grid_data"})
        tables["precipitation_annual"] = series
        if args.plots:
            mpl = require("matplotlib")
            mpl.use("Agg")
            plt = require("matplotlib.pyplot")
            fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
            vmax = float(max(mean1.max(), mean2.max()))
            finite_change = np.abs(change.values[np.isfinite(change.values)])
            change_limit = float(finite_change.max()) if finite_change.size and finite_change.max() > 0 else 1
            for ax, field, title in zip(axes, (mean1, mean2, change), (args.baseline, args.future, "Change (%)")):
                if np.isfinite(field.values).any():
                    im = ax.pcolormesh(da.lon, da.lat, field, shading="auto", cmap="RdBu_r" if field is change else "Blues",
                                      **({"vmin": -change_limit, "vmax": change_limit} if field is change else {"vmin": 0, "vmax": vmax}))
                    fig.colorbar(im, ax=ax, label="%" if field is change else "mm/year")
                ax.set(title=title, xlabel="Longitude", ylabel="Latitude")
            fig.savefig(out / "precipitation_comparison.png", dpi=160)
            plt.close(fig)
    return tables, [
        "按实际月份天数或完整逐日记录累加成年降水，再对完整年份等权平均；支持 CF 日历。",
        "边界框包括海洋和邻国，不代表印尼陆地平均；区域平均采用 cos(lat) 面积近似权重。",
        "线性年化百分比使用两个时期中点间隔，不是复合增长率或统计趋势。参考时期可为未来模式片段，不自动称为历史基线。",
        "点位采用最近网格中心，输出实际中心坐标；粗网格不能代表厂区极端降水或洪水损失。",
        "月均降水无法计算逐日极端指数；本工具不输出虚构的洪水重现期。",
    ]


def raster(args, out):
    validate_risk(args)
    np, rio = require("numpy"), require("rasterio")
    warp = require("rasterio.warp")
    result = []
    with rio.open(args.input) as src:
        if src.crs is None or args.band > src.count:
            raise ValueError("栅格缺少 CRS 或指定波段不存在")
        if src.count >= 3 and src.colorinterp[0].name == "red":
            raise ValueError("这是 RGB 渲染图，颜色不能直接作为数值风险；请提供原始单波段指数栅格")
        if args.points:
            points = point_rows(args.points)
            xs, ys = warp.transform("EPSG:4326", src.crs, [r[1] for r in points], [r[2] for r in points])
            for (name, lon, lat), x, y in zip(points, xs, ys):
                r, c = src.index(x, y)
                value = None
                if 0 <= r < src.height and 0 <= c < src.width:
                    sample = src.read(args.band, window=rio.windows.Window(c, r, 1, 1), masked=True)
                    if not np.ma.is_masked(sample[0, 0]):
                        raw = float(sample[0, 0])
                        if math.isfinite(raw) and raw != args.nodata:
                            value = normalize(raw, args.normalization)
                result.append({"site": name, "lon": lon, "lat": lat, "normalized_index": value,
                    "data_quality": "ok" if value is not None else "outside_or_nodata"})
        if args.zones:
            shape = require("shapely.geometry")
            mask = require("rasterio.mask")
            for index, feature in enumerate(zone_features(args.zones, getattr(args, "zone_layer", None))):
                geometry = feature.get("geometry")
                original = shape.shape(geometry)
                if original.geom_type not in {"Polygon", "MultiPolygon"} or original.is_empty or not original.is_valid:
                    raise ValueError("区域边界必须为有效 Polygon/MultiPolygon")
                if not (-180 <= original.bounds[0] <= original.bounds[2] <= 180 and -90 <= original.bounds[1] <= original.bounds[3] <= 90):
                    raise ValueError("GeoJSON 超出 WGS84 范围")
                geometry = warp.transform_geom("EPSG:4326", src.crs, geometry)
                name = feature.get("properties", {}).get("name", str(index))
                try:
                    image, transform = mask.mask(src, [geometry], indexes=args.band, crop=True, filled=False,
                                                 all_touched=args.all_touched)
                except ValueError as exc:
                    if "do not overlap" not in str(exc):
                        raise
                    result.append({"zone": name, "data_quality": "outside_raster", "screening_level": "undetermined"})
                    continue
                inside = require("rasterio.features").geometry_mask([geometry], image.shape, transform,
                    invert=True, all_touched=args.all_touched)
                total = int(inside.sum())
                if not total:
                    result.append({"zone": name, "data_quality": "no_pixel_centres", "screening_level": "undetermined"})
                    continue
                valid = inside & ~np.ma.getmaskarray(image) & np.isfinite(image.data)
                if args.nodata is not None:
                    valid &= image.data != args.nodata
                values, counts = np.unique(image.data[valid], return_counts=True)
                rasterized_total = total
                if getattr(args, "methodology", "index") == "reference":
                    if not src.crs.is_projected:
                        raise ValueError("面积覆盖评分要求投影坐标系，不能用经纬度平方作为面积")
                    total = shape.shape(geometry).area / abs(src.transform.a * src.transform.e - src.transform.b * src.transform.d)
                summary = summarize_counts(dict(zip(map(float, values), map(int, counts))), total, args)
                summary["rasterized_pixels"] = rasterized_total
                if getattr(args, "methodology", "index") == "reference":
                    summary["screening_level"] = score_grade(summary["coverage_weighted_score"], args.score_thresholds) if summary["data_quality"] == "ok" else "undetermined"
                    summary["reference_legacy_level"] = "low_insufficient_coverage" if summary["data_quality"] == "insufficient_coverage" else summary["screening_level"]
                    summary["coverage_basis"] = "polygon_area_in_source_crs / native_pixel_area"
                footprint = shape.Polygon([src.transform * p for p in ((0, 0), (src.width, 0), (src.width, src.height), (0, src.height))])
                if not footprint.covers(shape.shape(geometry)):
                    summary.update(data_quality="partial_raster_extent", screening_level="undetermined")
                result.append({"zone": name, "band": args.band, **summary})
    return {"raster_risk": result}, [
        "仅处理原始数值指数；不从地图颜色反推物理灾害量。不把 RGB 三波段平均为风险。",
        "点位输入为 WGS84，经坐标转换后取所在像元；区域按像元中心计数，可显式启用 all-touched。",
        "默认覆盖按栅格内区域像元计数；reference 模式按同一源投影的区域面积/原生像元面积计算理论总数。边界超出栅格时标记 partial_raster_extent。",
        "筛查阈值和强度权重属于项目自定义模型，不是 BNPB 官方定级，也不是损失概率。",
    ]


def http_bytes(url, timeout=30, limit=64 * 1024 * 1024, allowed_host="gis.bnpb.go.id"):
    """Bounded, rate-limited requests to the public BNPB host; never disable TLS."""
    parsed = urllib.parse.urlsplit(url)
    if allowed_host not in {"gis.bnpb.go.id", "server.arcgisonline.com"} or parsed.scheme != "https" or parsed.hostname != allowed_host or parsed.username or parsed.password:
        raise ValueError("下载 URL 必须为指定 BNPB/Esri 官方 HTTPS 服务")
    host = parsed.hostname
    if host in NETWORK["paused"]:
        raise ValueError(f"主机 {host} 本轮已暂停请求：连续失败或服务器要求较长等待；请查看 network_requests.jsonl，缓存仍可使用")
    for attempt in range(3):
        wait = NETWORK["next"].get(host, 0) - time.monotonic()
        if wait > 0:time.sleep(wait)
        started = time.monotonic()
        NETWORK["next"][host] = started + NETWORK["interval"]
        try:
            request = urllib.request.Request(url, headers={"User-Agent": f"IndonesiaClimateRisk/{VERSION}"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                final = urllib.parse.urlsplit(response.geturl())
                if final.hostname != parsed.hostname or final.scheme != "https":
                    raise ValueError("BNPB 下载跳转到非官方地址")
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise ValueError("响应超过大小上限，请缩小下载区域或分块")
                log_request(url, attempt, started, response.status, response.headers)
            NETWORK["failures"][host] = 0
            return data
        except (urllib.error.URLError, TimeoutError) as exc:
            code = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            headers = exc.headers if isinstance(exc, urllib.error.HTTPError) else {}
            body = None
            if isinstance(exc, urllib.error.HTTPError) and exc.fp is not None:
                try:body = exc.read(600).decode("utf-8", errors="replace")
                except OSError:pass
            log_request(url, attempt, started, code, headers, exc, body)
            if code == 403 and body and re.search(r"(?:error code:\s*1010|Error\s+1010)", body, re.I):
                NETWORK["paused"].add(host)
                raise ValueError("站点安全策略拒绝当前客户端（Cloudflare 1010，HTTP 403），本轮暂停该主机请求；需要站点允许的接入方式，延长请求间隔不保证解除拦截") from exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {429, 500, 502, 503, 504, 520, 522, 524}:
                raise
            retry_after = headers.get("Retry-After") if headers else None
            delay = 2 ** (attempt + 1)
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    try:
                        from email.utils import parsedate_to_datetime
                        delay = max(delay, parsedate_to_datetime(retry_after).timestamp() - time.time())
                    except (ValueError, TypeError, OverflowError):
                        pass
            elif code == 429:
                delay = max(delay, 10)
            if delay > 60:
                NETWORK["paused"].add(host)
                raise ValueError(f"服务器要求等待 {delay:.0f} 秒，本轮暂停该主机；这不是图层缺失，请稍后续跑") from exc
            if attempt == 2:
                NETWORK["failures"][host] = NETWORK["failures"].get(host, 0) + 1
                if NETWORK["failures"][host] >= 3:NETWORK["paused"].add(host)
                raise
            time.sleep(delay)


def http_json(url, params=None, timeout=30):
    query = urllib.parse.urlencode({"f": "json", **(params or {})})
    result = json.loads(http_bytes(url + "?" + query, timeout, 8 * 1024 * 1024).decode("utf-8-sig"))
    if not isinstance(result, dict) or "error" in result:
        raise ValueError("BNPB 服务错误: " + str(result.get("error", result) if isinstance(result, dict) else result))
    return result


def cached_metadata(path, url, args):
    if path.exists() and not args.refresh:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("url") != url:
            raise ValueError("缓存来源与请求服务不一致")
        return saved
    if args.offline:
        raise ValueError("离线缓存缺少服务目录/元数据，请先在线运行一次")
    path.parent.mkdir(parents=True, exist_ok=True)
    saved = {"url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
             "payload": http_json(url, timeout=args.timeout)}
    write_json(path, saved)
    return saved


def catalog(args, out):
    if args.offline and args.refresh:
        raise ValueError("--offline 与 --refresh 不能同时使用")
    data = cached_metadata(Path(args.cache) / "catalog.json", BNPB_ROOT + "/inarisk", args)
    rows = []
    for service in data["payload"].get("services", []):
        name, typ = service.get("name", ""), service.get("type", "")
        if not re.fullmatch(r"inarisk/[A-Za-z0-9_]+", name) or typ not in {"ImageServer", "MapServer"}:
            continue
        if not re.search(args.pattern, name, re.I):
            continue
        rows.append({"service": name.split("/")[-1], "type": typ,
            "component": "hazard" if "BAHAYA" in name.upper() else (
                "vulnerability" if "KERENTANAN" in name.upper() else "risk" if "RISIKO" in name.upper() else "other"),
            "url": f"{BNPB_ROOT}/{name}/{typ}", "candidate_for_raw_index": typ == "ImageServer" and "INDEKS_" in name.upper() and any(k in name.upper() for k in ("BAHAYA", "KERENTANAN", "RISIKO"))})
    write_json(out / "catalog_source.json", data)
    if not rows:
        raise ValueError("目录没有匹配的服务")
    return {"bnpb_catalog": rows}, [
        "来源: " + BNPB_ROOT + "/inarisk；仅抓取公开 REST 目录，不依赖网页排版。",
        "候选图层仍须核对单波段、原始值范围和原生像元尺寸；MapServer 展示图不进入数值计算。",
        "获取时间记录在 catalog_source.json；缓存不自动代表最新数据，可用 --refresh 强制更新。",
    ]


def asset_window(bounds, crs, metadata):
    """Return a window aligned exactly to the source grid, padded by one pixel."""
    warp = require("rasterio.warp")
    extent = metadata["extent"]
    target_crs = f"EPSG:{extent['spatialReference'].get('latestWkid') or extent['spatialReference'].get('wkid')}"
    west, south, east, north = warp.transform_bounds(crs, target_crs, *bounds, densify_pts=21)
    px, py = abs(float(metadata["pixelSizeX"])), abs(float(metadata["pixelSizeY"]))
    if px <= 0 or py <= 0 or not all(math.isfinite(v) for v in (west, south, east, north, px, py)):
        raise ValueError("服务像元尺寸或资产范围无效")
    width = round((extent["xmax"] - extent["xmin"]) / px)
    height = round((extent["ymax"] - extent["ymin"]) / py)
    c0 = max(0, math.floor((west - extent["xmin"]) / px) - 1)
    c1 = min(width, math.floor((east - extent["xmin"]) / px) + 2)
    r0 = max(0, math.floor((extent["ymax"] - north) / py) - 1)
    r1 = min(height, math.floor((extent["ymax"] - south) / py) + 2)
    if c1 <= c0 or r1 <= r0:
        raise ValueError("资产位于该服务覆盖范围之外")
    return (c0, r0, c1, r1), target_crs


def validate_tile(path, bbox, width, height, crs, resolution, confirmed_nodata=()):
    np, rio = require("numpy"), require("rasterio")
    with rio.open(path) as tile:
        if tile.count != 1 or tile.dtypes[0] not in {"float32", "float64"}:
            raise ValueError("服务返回的并非单波段浮点原始指数，拒绝计算渲染图")
        if tile.width != width or tile.height != height or tile.crs != rio.crs.CRS.from_string(crs):
            raise ValueError("下载栅格尺寸/CRS 与请求不符")
        if not np.allclose(tile.bounds, bbox, atol=1e-4, rtol=0) or not np.allclose(tile.res, resolution, atol=1e-6, rtol=0):
            raise ValueError("下载栅格改变了范围或原生分辨率")
        values = tile.read(1, masked=True).compressed()
        for value in confirmed_nodata:
            values = values[values != value]
        if np.any(~np.isfinite(values)) or np.any(values < -INDEX_TOLERANCE) or np.any(values > 1 + INDEX_TOLERANCE):
            raise ValueError("原始指数超出元数据声明的 0–1 范围；需要核对 NoData 和数据标定")


def confirm_unlabelled_nodata(path, service_url, timeout):
    """Do not guess missing-value codes: confirm each extreme float code upstream."""
    np, rio = require("numpy"), require("rasterio")
    confirmations = []
    with rio.open(path) as tile:
        values = tile.read(1, masked=True)
        candidates = np.unique(values.compressed()[values.compressed() < -3e38])
        if len(candidates) > 3:
            raise ValueError("出现多个异常极端负数，无法安全确认 NoData 编码")
        for value in candidates:
            row, col = np.argwhere(values.data == value)[0]
            x, y = tile.xy(int(row), int(col))
            geometry = {"x": x, "y": y, "spatialReference": tile.crs.to_dict()}
            epsg = tile.crs.to_epsg()
            if epsg:
                geometry["spatialReference"] = {"wkid": epsg}
            response = http_json(service_url + "/identify", {"geometry": json.dumps(geometry),
                "geometryType": "esriGeometryPoint", "returnGeometry": "false", "returnCatalogItems": "false",
                "renderingRule": json.dumps({"rasterFunction": "None"})}, timeout)
            if str(response.get("value", "")).strip().lower() != "nodata":
                raise ValueError("极端负数未被官方接口确认为 NoData，拒绝推断")
            confirmations.append({"raw_value": float(value), "source": service_url + "/identify",
                                  "geometry": geometry, "response": response})
    return confirmations


def download_window(service, metadata, window, crs, args, destination, requests):
    rio, merge = require("rasterio"), require("rasterio.merge")
    extent = metadata["extent"]
    px, py = abs(float(metadata["pixelSizeX"])), abs(float(metadata["pixelSizeY"]))
    c0, r0, c1, r1 = window
    block = min(args.tile_size, int(metadata.get("maxImageWidth", 1024)), int(metadata.get("maxImageHeight", 1024)))
    if block < 1:
        raise ValueError("服务未提供有效分块尺寸")
    service_url = f"{BNPB_ROOT}/inarisk/{service}/ImageServer"
    cache = Path(args.cache) / service / "tiles"
    cache.mkdir(parents=True, exist_ok=True)
    paths, missing_values = [], set()
    for row in range(r0, r1, block):
        for col in range(c0, c1, block):
            width, height = min(block, c1 - col), min(block, r1 - row)
            bbox = [extent["xmin"] + col * px, extent["ymax"] - (row + height) * py,
                    extent["xmin"] + (col + width) * px, extent["ymax"] - row * py]
            params = {"bbox": ",".join(map(str, bbox)), "bboxSR": crs.split(":")[-1],
                "imageSR": crs.split(":")[-1], "size": f"{width},{height}", "format": "tiff",
                "pixelType": "F32", "interpolation": "RSP_NearestNeighbor", "adjustAspectRatio": "false",
                "renderingRule": json.dumps({"rasterFunction": "None"})}
            key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
            tile, receipt = cache / (key + ".tif"), cache / (key + ".json")
            reused = False
            confirmations = []
            if tile.exists() and receipt.exists() and not args.refresh:
                previous = json.loads(receipt.read_text(encoding="utf-8"))
                reused = previous.get("sha256") == file_digest(tile)["sha256"]
                confirmations = previous.get("nodata_confirmations", [])
            if not reused:
                if args.offline:
                    raise ValueError("离线缓存缺失或校验失败，请在线重新获取对应资产范围")
                exported = http_json(service_url + "/exportImage", params, args.timeout)
                href = exported.get("href", "")
                if not urllib.parse.urlsplit(href).path.startswith("/server/rest/directories/arcgisoutput/"):
                    raise ValueError("BNPB 未返回可下载的官方导出文件")
                data = http_bytes(href, args.timeout)
                temporary = tile.with_suffix(".part")
                temporary.write_bytes(data)
                confirmations = confirm_unlabelled_nodata(temporary, service_url, args.timeout)
                validate_tile(temporary, bbox, width, height, crs, (px, py), [c["raw_value"] for c in confirmations])
                temporary.replace(tile)
                write_json(receipt, {"request": params, "service": service_url,
                    "retrieved_utc": datetime.now(timezone.utc).isoformat(), "sha256": file_digest(tile)["sha256"],
                    "nodata_confirmations": confirmations})
            validate_tile(tile, bbox, width, height, crs, (px, py), [c["raw_value"] for c in confirmations])
            missing_values.update(c["raw_value"] for c in confirmations)
            paths.append(tile)
            requests.append({"service": service, "tile_key": key, "cache_hit": reused,
                             "width": width, "height": height, "sha256": file_digest(tile)["sha256"],
                             "nodata_confirmations": confirmations})
    # ponytail: in-memory mosaic capped by --max-pixels; use streaming mosaics for larger portfolios.
    from contextlib import ExitStack
    with ExitStack() as stack:
        sources = [stack.enter_context(rio.open(path)) for path in paths]
        array, transform = merge.merge(sources, nodata=-9999)
        for value in missing_values:
            array[array == value] = -9999
        profile = sources[0].profile.copy()
        profile.update(width=array.shape[2], height=array.shape[1], transform=transform,
                       nodata=-9999, driver="GTiff", compress="deflate")
        with rio.open(destination, "w", **profile) as target:
            target.write(array)


def reference_aggregate(rows, args):
    """Reproduce the supplied report's valid-pixel weighting, with quality retained."""
    aggregate = []
    for asset in dict.fromkeys(r["asset"] for r in rows if r["asset_type"] == "zone"):
        selected = [r for r in rows if r["asset"] == asset and r["asset_type"] == "zone" and r["service"] not in COMPARISON_SERVICES]
        for group in ("all", "hazard", "vulnerability", "risk"):
            expected = [r for r in selected if group == "all" or component(r["service"]) == group]
            if not expected:
                continue
            usable = [r for r in expected if r.get("coverage_weighted_score") is not None and r.get("valid_pixels", 0) > 0
                      and r.get("data_quality") in {"ok", "insufficient_coverage"}]
            total = sum(r["valid_pixels"] for r in usable)
            score = sum(r["coverage_weighted_score"] * r["valid_pixels"] for r in usable) / total if total else None
            quality = "ok" if len(usable) == len(expected) and all(r["data_quality"] == "ok" for r in usable) else "incomplete_or_low_coverage"
            aggregate.append({"asset": asset, "group": group, "score": score,
                "reference_computed_level": score_grade(score, args.score_thresholds),
                "screening_level": score_grade(score, args.score_thresholds) if quality == "ok" else "undetermined",
                "data_quality": quality, "included_layers": len(usable), "expected_layers": len(expected),
                "valid_pixels_sum": total, "weighting": "valid_pixels_i / sum_valid_pixels",
                "excluded_services": ", ".join(r["service"] for r in expected if r not in usable)})
            if group == "all":
                for row in usable:
                    row["inter_layer_weight"] = row["valid_pixels"] / total
                    row["composite_contribution"] = row["coverage_weighted_score"] * row["inter_layer_weight"]
    return aggregate


def satellite_maps(rows, assets, args, out):
    """A georeferenced, cached real imagery background and transparent numeric overlays."""
    np, rio, warp = require("numpy"), require("rasterio"), require("rasterio.warp")
    Image = require("PIL.Image")
    maps = out / "maps"
    maps.mkdir()
    records = []
    for index, asset in enumerate(assets):
        if asset["kind"] != "zone":
            continue
        try:
            bbox = warp.transform_bounds("EPSG:4326", "EPSG:3857", *asset["bounds"], densify_pts=21)
            params = {"bbox": ",".join(map(str, bbox)), "bboxSR": 3857, "imageSR": 3857,
                "size": f"{args.map_size},{args.map_size}", "format": "jpg", "f": "json"}
            request_url = IMAGERY_URL + "/export?" + urllib.parse.urlencode(params)
            key = hashlib.sha256(request_url.encode()).hexdigest()
            cache = Path(args.cache) / "world-imagery" / key
            receipt_path, image_path = cache / "receipt.json", cache / "image.jpg"
            if receipt_path.exists() and image_path.exists() and not args.refresh:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                if receipt["request_url"] != request_url or receipt["image_sha256"] != file_digest(image_path)["sha256"]:
                    raise ValueError("卫星影像缓存来源或校验不符")
            else:
                if args.offline:
                    raise ValueError("离线缺少卫星底图缓存；请先在线生成一次")
                cache.mkdir(parents=True, exist_ok=True)
                fetch = lambda url: http_bytes(url, timeout=args.timeout, allowed_host="server.arcgisonline.com")
                service = json.loads(fetch(IMAGERY_URL + "?f=json"))
                export = json.loads(fetch(request_url))
                if "error" in export or not export.get("href"):
                    raise ValueError("Esri 影像导出失败: " + str(export))
                data = fetch(export["href"])
                with Image.open(io.BytesIO(data)) as check:
                    check.verify()
                image_path.write_bytes(data)
                receipt = {"request_url": request_url, "source": IMAGERY_URL,
                    "retrieved_utc": datetime.now(timezone.utc).isoformat(), "export": export,
                    "attribution": service.get("copyrightText", "Esri World Imagery"),
                    "acquisition_date": "not verified; mosaic dates vary", "image_sha256": file_digest(image_path)["sha256"]}
                write_json(receipt_path, receipt)
            background = maps / f"satellite_{index:05d}.jpg"
            background.write_bytes(image_path.read_bytes())
            with Image.open(background) as image:
                width, height = image.size
            export = receipt["export"]
            if (width, height) != (export["width"], export["height"]):
                raise ValueError("卫星图尺寸与地理参考不一致")
            extent = export["extent"]
            if (extent["spatialReference"].get("latestWkid") or extent["spatialReference"].get("wkid")) not in {3857, 102100}:
                raise ValueError("卫星图不是请求的 Web Mercator 投影")
            bounds = (extent["xmin"], extent["ymin"], extent["xmax"], extent["ymax"])
            transform = rio.transform.from_bounds(*bounds, width, height)
            feature = zone_features(asset["file"])[0]
            geometry = warp.transform_geom("EPSG:4326", "EPSG:3857", feature["geometry"])
            mask = require("rasterio.features").geometry_mask([geometry], (height, width), transform, invert=True)
            svg_paths = []
            polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            for polygon in polygons:
                for ring in polygon:
                    pts = [~transform * tuple(p[:2]) for p in ring]
                    svg_paths.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z")
            outline = maps / f"boundary_{index:05d}.svg"
            outline.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"><path d="{" ".join(svg_paths)}" fill="none" stroke="#ffffff" stroke-width="6"/><path d="{" ".join(svg_paths)}" fill="none" stroke="#19334b" stroke-width="2"/><path d="M{width/2-16},{height/2}h32 M{width/2},{height/2-16}v32" stroke="#fff" stroke-width="6"/><path d="M{width/2-16},{height/2}h32 M{width/2},{height/2-16}v32" stroke="#df253d" stroke-width="3"/></svg>', encoding="utf-8")
            write_json(maps / f"satellite_{index:05d}.json", receipt)
            # One image per layer, same exact grid as the background. NoData stays transparent.
            cmap = require("matplotlib.colors").LinearSegmentedColormap.from_list("risk", [(0, "#15b94b"), (.33, "#a7da22"), (.66, "#ffe01b"), (.82, "#fb8d26"), (1, "#e5262a")])
            for row in rows:
                if row["asset"] != asset["name"] or row["asset_type"] != "zone" or not row.get("raw_raster"):
                    continue
                with rio.open(out / row["raw_raster"]) as src:
                    projected = np.full((height, width), np.nan, dtype="float32")
                    warp.reproject(source=rio.band(src, 1), destination=projected, src_transform=src.transform,
                        src_crs=src.crs, src_nodata=src.nodata, dst_transform=transform, dst_crs="EPSG:3857",
                        dst_nodata=np.nan, resampling=warp.Resampling.nearest)
                valid = mask & np.isfinite(projected)
                rgba = (cmap(np.nan_to_num(np.clip(projected, 0, 1))) * 255).astype("uint8")
                rgba[:, :, 3] = np.where(valid, 255, 0)
                overlay = maps / f"{index:05d}_{row['service']}.png"
                Image.fromarray(rgba).save(overlay)
                records.append({"asset": asset["name"], "service": row["service"], "label": layer_label(row["service"]),
                    "component": component(row["service"]), "background": background.relative_to(out).as_posix(),
                    "overlay": overlay.relative_to(out).as_posix(), "boundary": outline.relative_to(out).as_posix(),
                    "attribution": receipt["attribution"], "crs": "EPSG:3857", "width": width, "height": height,
                    "bounds": list(bounds), "native_pixel_size": list(src.res), "source_crs": str(src.crs),
                    "score": row.get("coverage_weighted_score"), "coverage": row.get("coverage"),
                    "screening_level": row.get("screening_level"), "status": "ok"})
        except (ValueError, OSError, KeyError) as exc:
            records.append({"asset": asset["name"], "status": "unavailable", "error": str(exc)})
    return records or [{"status": "not_applicable", "error": "卫星叠图需要区域边界"}]


def inarisk(args, out):
    validate_risk(args)
    if args.offline and args.refresh:
        raise ValueError("--offline 与 --refresh 不能同时使用")
    if not (1 <= args.tile_size <= 4096 and 1 <= args.max_pixels <= 100000000 and 1 <= args.timeout <= 120):
        raise ValueError("分块、像元上限或超时设置超出允许范围")
    if not args.points and not args.zones:
        raise ValueError("全流程至少需要资产点位 --points 或资产边界 --zones")
    args.services = args.services or DEFAULT_SERVICES.copy()
    if len(set(args.services)) != len(args.services) or not all(re.fullmatch(r"[A-Za-z0-9_]+", s) for s in args.services):
        raise ValueError("服务名称须唯一，且仅含字母、数字、下划线")
    shape = require("shapely.geometry")
    assets = []
    folder = out / "assets"
    folder.mkdir()
    for name, lon, lat in point_rows(args.points) if args.points else []:
        path = folder / f"point_{len(assets):05d}.csv"
        write_csv(path, [{"name": name, "lon": lon, "lat": lat}])
        assets.append({"name": name, "kind": "point", "bounds": (lon, lat, lon, lat), "file": path})
    for feature in zone_features(args.zones, args.zone_layer) if args.zones else []:
        path = folder / f"zone_{len(assets):05d}.geojson"
        write_json(path, {"type": "FeatureCollection", "features": [feature]})
        area = shape.shape(require("rasterio.warp").transform_geom("EPSG:4326", "EPSG:6933", feature["geometry"])).area / 1e6
        assets.append({"name": feature["properties"]["name"], "kind": "zone", "area_km2": area,
                       "bounds": shape.shape(feature["geometry"]).bounds, "file": path})
    write_json(out / "asset_inventory.json", [{"name": a["name"], "kind": a["kind"], "bounds_wgs84": a["bounds"],
        "area_km2": a.get("area_km2"), "area_basis": "EPSG:6933 equal-area; source CRS area used separately for scoring"} for a in assets])
    try:
        catalog_data = cached_metadata(Path(args.cache) / "catalog.json", BNPB_ROOT + "/inarisk", args)
    except (ValueError, OSError) as exc:
        catalog_data = {"url": BNPB_ROOT + "/inarisk", "payload": {}, "error": str(exc)}
    available = {(s.get("name"), s.get("type")) for s in catalog_data["payload"].get("services", [])}
    if args.profile == "physical-all":
        args.services = physical_services(catalog_data["payload"])
        if not args.services:
            raise ValueError("官方目录无可用物理灾害图层，无法扩展评估范围")
    write_json(out / "selected_services.json", [{"service": s, "label": layer_label(s), "component": component(s),
        "comparison_only": s in COMPARISON_SERVICES} for s in args.services])
    plans, results, source_data, requests = [], [], [], []
    pixels = 0
    for service in args.services:
        try:
            if "error" in catalog_data:
                raise ValueError("官方服务目录读取失败: " + catalog_data["error"])
            if not any(kind in service.upper() for kind in ("BAHAYA", "KERENTANAN", "RISIKO")) and service not in COMPARISON_SERVICES:
                raise ValueError("未确认此指数的危险性/脆弱性/风险方向；不自动将能力、人口或其他指数分为高低风险")
            if ("inarisk/" + service, "ImageServer") not in available:
                raise ValueError("官方目录中无该 ImageServer；不能用 MapServer 渲染图替代")
            source = cached_metadata(Path(args.cache) / service / "metadata.json",
                f"{BNPB_ROOT}/inarisk/{service}/ImageServer", args)
            meta = source["payload"]
            if (meta.get("bandCount") != 1 or meta.get("pixelType") not in {"F32", "F64"}
                    or not meta.get("minValues") or not meta.get("maxValues")
                    or min(meta["minValues"]) < -INDEX_TOLERANCE or max(meta["maxValues"]) > 1 + INDEX_TOLERANCE):
                raise ValueError("此服务不是元数据明确的单波段 0–1 浮点指数")
            source_data.append(source)
            for index, asset in enumerate(assets):
                try:
                    window, crs = asset_window(asset["bounds"], "EPSG:4326", meta)
                    pixels += (window[2] - window[0]) * (window[3] - window[1])
                    plans.append((service, meta, asset, index, window, crs))
                except ValueError as exc:
                    results.append({"service": service, "asset": asset["name"], "asset_type": asset["kind"],
                        "data_quality": "unavailable", "screening_level": "undetermined", "error": str(exc)})
        except (ValueError, OSError) as exc:
            for asset in assets:
                results.append({"service": service, "asset": asset["name"], "asset_type": asset["kind"],
                    "data_quality": "unavailable", "screening_level": "undetermined", "error": str(exc)})
    if pixels > args.max_pixels:
        raise ValueError(f"按原生分辨率需下载 {pixels:,} 像元，超过 --max-pixels {args.max_pixels:,}；请拆分资产批次或明确提高上限，不自动降采样")
    for service, meta, asset, index, window, crs in plans:
        print(f"BNPB: {service} · asset {index + 1}/{len(assets)}", flush=True)
        download_dir = out / "downloads" / service
        download_dir.mkdir(parents=True, exist_ok=True)
        destination = download_dir / f"asset_{index:05d}.tif"
        try:
            download_window(service, meta, window, crs, args, destination, requests)
            task = SimpleNamespace(**{**vars(args), "input": str(destination), "normalization": "index01",
                "band": 1, "nodata": None, "zone_layer": None,
                "points": str(asset["file"]) if asset["kind"] == "point" else None,
                "zones": str(asset["file"]) if asset["kind"] == "zone" else None})
            table = raster(task, out)[0]["raster_risk"]
            for row in table:
                value = row.get("normalized_index") if asset["kind"] == "point" else row.get("mean_index")
                if asset["kind"] == "zone":
                    row["custom_intensity_level"] = score_grade(row.get("intensity"), args.score_thresholds) if row["data_quality"] == "ok" else "undetermined"
                    row["mean_index_level"] = "undetermined" if value is None or row["data_quality"] != "ok" else "low" if value <= args.thresholds[0] else "medium" if value <= args.thresholds[1] else "high"
                if asset["kind"] == "point" or args.methodology == "index":
                    row["screening_level"] = "undetermined" if value is None or row["data_quality"] != "ok" else (
                        "low" if value <= args.thresholds[0] else "medium" if value <= args.thresholds[1] else "high")
                row.update(service=service, asset=asset["name"], asset_type=asset["kind"],
                    component=component(service), label=layer_label(service), comparison_only=service in COMPARISON_SERVICES,
                    raw_raster=str(destination.relative_to(out)).replace("\\", "/"))
                results.append(row)
        except (ValueError, OSError) as exc:
            results.append({"service": service, "asset": asset["name"], "asset_type": asset["kind"],
                "data_quality": "unavailable", "screening_level": "undetermined", "error": str(exc)})
    write_json(out / "source_metadata.json", {"catalog": catalog_data, "services": source_data})
    write_json(out / "download_manifest.json", requests)
    bad = sum(row.get("data_quality") != "ok" for row in results)
    status = "complete" if not bad else "partial" if bad < len(results) else "unavailable"
    tables = {"asset_risk": results, "pipeline_status": [{"status": status, "assets": len(assets),
        "services": len(args.services), "result_rows": len(results), "rows_needing_review": bad,
        "planned_native_pixels": pixels, "tiles": len(requests), "cache_hits": sum(r["cache_hit"] for r in requests)}]}
    if args.methodology == "reference":
        aggregate = reference_aggregate(results, args)
        if aggregate:
            tables["reference_aggregate"] = aggregate
    if args.satellite:
        tables["satellite_maps"] = satellite_maps(results, assets, args, out)
    return tables, [
        f"全流程状态: {status}；需核查的资产/图层结果 {bad}/{len(results)}。缺失与失败不会归为低风险。",
        "获取 BNPB 公开目录与服务元数据 → 导入资产 → 按资产范围分块获取原始 TIFF → 本地分析 → 出具报告。",
        "请求使用原生坐标系/像元尺寸、None 渲染规则、F32 TIFF 和最近邻重采样；逐块校验范围、分辨率、值域和 SHA-256。",
        "在线获取 BNPB 原始指数；启用卫星图时另向 Esri World Imagery 发送范围参数，不发送资产文件或名称。缓存支持 --offline。",
        "BAHAYA 是危险性，KERENTANAN 是脆弱性，RISIKO 是风险；分开呈现，不混算企业损失。",
        "reference 模式按用户方法计算 I=有效像元分段权重均值，α=N有效/(源投影区域面积/原生像元面积)，S=I×α；S<3低、3≤S<7.5中、S≥7.5高。默认 index 模式按原始指数/区域均值筛查。",
        "reference 跨层权重=N有效_i/ΣN有效，综合分=Σ(S_i×权重_i)。同时列危险性、脆弱性、风险分组；全球地震及雅加达5米图层仅对照，避免与国家层重复加权。综合分属于自定义筛查，不是损失概率。",
        "用户参考报告参数摘要采用覆盖阈值15%（附录示例为10%）；请用 --min-coverage 0.15 复现。覆盖不足保留旧法低分标签对照，但正式结果标待核查。NoData透明显示，不算零值。",
        "原始文件保持不变；计算允许 1e-6 内的浮点端点舍入误差并夹到 0–1，超出容差拒绝。reference 的面积与原生像元面积采用同一源投影。",
        "完整请求与原始文件可从 source_metadata.json、download_manifest.json、downloads/ 和缓存校验追溯。",
        "缓存保留原始 TIFF 字节；未标记的极端负数仅在官方 identify 确认为 NoData 后，才在合并分析文件中转为 -9999；确认记录随下载清单保留。",
    ]


COMMANDS = {"histogram": histogram, "aqueduct": aqueduct, "cdd": cdd,
            "precipitation": precipitation, "raster": raster, "catalog": catalog, "inarisk": inarisk}


def assessment_charts(out, tables, metadata):
    """Export offline report figures using the same numeric results as the tables."""
    if "asset_risk" not in tables or metadata["parameters"].get("methodology") != "reference":
        return []
    try:
        mpl = require("matplotlib")
    except ValueError:
        return []
    mpl.use("Agg")
    plt, np = require("matplotlib.pyplot"), require("numpy")
    fonts = require("matplotlib.font_manager")
    family = next((name for name in ("Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Zen Hei", "Arial Unicode MS")
                   if any(f.name == name for f in fonts.fontManager.ttflist)), "DejaVu Sans")
    chinese = family != "DejaVu Sans"
    text = lambda zh, en: zh if chinese else en
    folder = out / "charts"
    folder.mkdir(exist_ok=True)
    figures = []
    def save(fig, filename, title, caption):
        fig.savefig(folder / (filename + ".png"), dpi=145, bbox_inches="tight")
        fig.savefig(folder / (filename + ".svg"), bbox_inches="tight")
        plt.close(fig)
        figures.append({"title": title, "caption": caption, "png": "charts/" + filename + ".png", "svg": "charts/" + filename + ".svg"})
    params = metadata["parameters"]
    colors = {"low": "#30a779", "medium": "#efb83e", "high": "#dd5754", "undetermined": "#9da8b6"}
    with mpl.rc_context({"font.family": family, "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False}):
        rows = tables["asset_risk"]
        for asset_index, asset in enumerate(dict.fromkeys(r["asset"] for r in rows if r["asset_type"] == "zone")):
            all_rows = [r for r in rows if r["asset"] == asset and r["asset_type"] == "zone"]
            ranked = sorted((r for r in all_rows if r.get("coverage_weighted_score") is not None), key=lambda r: r["coverage_weighted_score"], reverse=True)[:40]
            prefix = f"asset_{asset_index:05d}"
            categories = ("hazard", "vulnerability", "risk", "comparison")
            available, missing = [], []
            for group in categories:
                subset = [r for r in all_rows if (r["service"] in COMPARISON_SERVICES if group == "comparison" else r["service"] not in COMPARISON_SERVICES and component(r["service"]) == group)]
                available.append(sum(r.get("coverage_weighted_score") is not None for r in subset))
                missing.append(len(subset) - available[-1])
            fig, ax = plt.subplots(figsize=(9, 3.6), layout="constrained")
            xs = np.arange(4)
            ax.bar(xs, available, color="#278f91", label=text("已完成数值分析", "Numeric results"))
            ax.bar(xs, missing, bottom=available, color="#d6dde6", label=text("缺失/未取得", "Missing / unavailable"))
            for x, yes, no in zip(xs, available, missing):
                ax.text(x, yes + no + .15, f"{yes}/{yes+no}", ha="center")
            ax.set_xticks(xs, [text("危险性", "Hazard"), text("脆弱性", "Vulnerability"), text("风险", "Risk"), text("对照", "Comparison")])
            ax.set_ylabel(text("图层数量", "Layer count")); ax.set_ylim(0, max([a+b for a,b in zip(available,missing)] or [1]) * 1.25 + 1)
            ax.legend(loc="upper right", frameon=False)
            save(fig, prefix + "_availability", "图层数据获取摘要", "柱顶为已取得/已选择图层数。缺失图层不计为低风险，两个对照源不参加综合加权。")
            if not ranked:
                continue
            labels = [layer_label(r["service"]) if chinese else r["service"].replace("INDEKS_", "").replace("layer_", "") for r in ranked]
            ys = np.arange(len(ranked)); height = max(3.4, len(ranked) * .38 + 1.2)
            fig, ax = plt.subplots(figsize=(11, height), layout="constrained")
            ax.barh(ys - .17, [r["intensity"] for r in ranked], height=.30, color="#c4d3df", label=text("有效区域强度 I", "Valid-area intensity I"))
            ax.barh(ys + .17, [r["coverage_weighted_score"] for r in ranked], height=.30, color=[colors[r["screening_level"]] for r in ranked], label=text("覆盖加权得分 S", "Coverage-weighted score S"))
            for y, row in zip(ys, ranked):
                ax.text(row["coverage_weighted_score"] + .06, y + .17, f'{row["coverage_weighted_score"]:.2f}', va="center", fontsize=9)
            for cutoff in params["score_thresholds"]:
                ax.axvline(cutoff, color="#5b6a7a", linestyle="--", linewidth=.8)
            ax.set_yticks(ys, labels); ax.invert_yaxis(); ax.set_xlim(0, max(params["weights"]) * 1.08)
            ax.set_xlabel(text("得分（虚线为分级阈值）", "Score (dashed lines: grade thresholds)"));ax.legend(loc="lower right", frameon=False)
            save(fig, prefix + "_scores", "各指标评分对比", "浅色条为 I，彩色条为 S=I×α。覆盖缺失会压低 S；这不是缺失区域安全的证据。按 S 降序展示，最多40层。")
            fig, axes = plt.subplots(1, 2, figsize=(15, height), sharey=True, layout="constrained")
            for ax, denominator, title in zip(axes, ("valid_pixels", "total_pixels"), (text("有效区域内部构成", "Within valid area"), text("整个目标区域构成", "Across target area"))):
                left = np.zeros(len(ranked))
                for key, color, legend in (("low_pixels", "#30a779", text("低值", "Low")), ("medium_pixels", "#efc54a", text("中值", "Medium")), ("high_pixels", "#dd5754", text("高值", "High"))):
                    values = np.array([r[key] / r[denominator] * 100 if r[denominator] else 0 for r in ranked])
                    ax.barh(ys, values, left=left, color=color, label=legend);left += values
                if denominator == "total_pixels":
                    ax.barh(ys, np.maximum(0, 100-left), left=left, color="#d6dde6", label=text("未知/缺测", "Unknown / NoData"))
                ax.set_title(title, pad=34);ax.set_xlim(0, max(100, float(left.max())));ax.set_xlabel(text("像元占比（%）", "Pixel share (%)"));ax.legend(loc="lower center", bbox_to_anchor=(.5,1.02), ncol=4, frameon=False, fontsize=8)
            axes[0].set_yticks(ys, labels);axes[0].invert_yaxis()
            save(fig, prefix + "_composition", "风险指数构成：内部占比与总体占比", "左图分母为有效像元数；右图分母为目标区域理论总像元数，灰色为未知。零值属于有效低值，NoData 不属于零值。图层相互重叠，不把多层占比累加为土地面积。")
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), layout="constrained")
        xs = np.linspace(0, 1, 301)
        weights = [risk_weight(float(v), params["thresholds"], params["weights"]) for v in xs]
        axes[0].plot(xs, weights, color="#168c91", linewidth=2.5)
        for cutoff in params["thresholds"]:axes[0].axvline(cutoff, color="#9da8b6", linestyle="--")
        axes[0].set_xlabel(text("原始指数 v", "Raw index v"));axes[0].set_ylabel(text("像元权重 W(v)", "Pixel weight W(v)"));axes[0].set_title(text("分段连续权重函数", "Piecewise continuous weight"))
        coverage = np.linspace(0, 1, 101)
        for intensity in params["weights"]:axes[1].plot(coverage, intensity * coverage, label=f"I={intensity:g}")
        for cutoff in params["score_thresholds"]:axes[1].axhline(cutoff, color="#9da8b6", linestyle="--", linewidth=.8)
        axes[1].set_xlabel(text("有效覆盖率 α", "Valid coverage alpha"));axes[1].set_ylabel(text("得分 S=I×α", "Score S=I x alpha"));axes[1].set_title(text("覆盖率如何影响得分", "Effect of coverage on score"));axes[1].legend(frameon=False)
        save(fig, "algorithm", "算法示意", "权重、指数阈值、评分阈值均来自本次参数。右图说明：即使强度不变，缺测增加也会降低得分。")
    write_json(folder / "manifest.json", figures)
    return figures


def assessment_dashboard(tables, out, metadata):
    if "asset_risk" not in tables:
        return ""
    esc = lambda value: html.escape(str(value))
    rows = tables["asset_risk"]
    services = set(r["service"] for r in rows)
    available = {r["service"] for r in rows if r.get("coverage_weighted_score") is not None or r.get("normalized_index") is not None}
    areas = {}
    inventory = out / "asset_inventory.json"
    if inventory.exists():
        areas = {r["name"]:r.get("area_km2") for r in json.loads(inventory.read_text(encoding="utf-8"))}
    summaries = [r for r in tables.get("reference_aggregate", []) if r["group"] == "all"]
    parameters = metadata["parameters"]
    limits = parameters.get("score_thresholds", [3, 7.5])
    maximum = parameters.get("weights", [1,5,10])[-1]
    names = {"low": "低风险", "medium": "中风险", "high": "高风险", "undetermined": "暂无法评价"}
    descriptions = {
        "low": "综合评分处于模型的低风险区间，仍需单独关注局部高值和个别较高的风险指标。",
        "medium": "综合评分处于模型的中风险区间，应优先核实主要风险来源，并检查现有防护措施。",
        "high": "综合评分处于模型的高风险区间，应优先开展专项评估，并检查应急安排及关键资产防护。",
        "undetermined": "现有有效数据不足，当前无法计算区域综合风险等级。"}
    sections = []
    for summary_index, summary in enumerate(summaries):
        score = summary["score"]
        level = score_grade(score, limits)
        provisional = summary["data_quality"] != "ok" and score is not None
        title = names[level] + ("（暂评）" if provisional else "")
        status = "数据待补齐 · 正式评价待确认" if provisional else "当前无有效综合结果" if score is None else "已选主指标评价完整"
        area = areas.get(summary["asset"])
        area_text = f"分析面积 {area:.2f} km²" if area is not None else "区域综合评价"
        score_text = f"{score:.2f}" if score is not None else "—"
        area_value = f"{area:.2f}" if area is not None else "—"
        sections.append(f'''<section class="card statistics" aria-label="关键统计数据"><div class="section-heading"><h2>关键统计数据</h2><span class="subtle">{esc(summary['asset'])}</span></div><div class="stat-grid">
<article class="stat primary-stat" data-metric="composite-score"><span class="stat-label">综合风险评分</span><strong class="stat-value">{score_text}</strong><span class="stat-unit">满分 {maximum:g} · 按主指标加权汇总</span></article>
<article class="stat risk-{level}" data-metric="composite-grade"><span class="stat-label">综合风险等级</span><strong class="stat-value grade-value">{title}</strong><span class="stat-unit">依据综合风险评价模型</span></article>
<article class="stat"><span class="stat-label">分析面积</span><strong class="stat-value">{area_value}</strong><span class="stat-unit">平方千米 · 区域边界统计</span></article>
<article class="stat{' pending-stat' if summary['data_quality'] != 'ok' else ''}"><span class="stat-label">主指标纳入情况</span><strong class="stat-value">{summary['included_layers']}<span style="font-size:18px;color:var(--muted)"> / {summary['expected_layers']}</span></strong><span class="stat-unit">{'完整评价' if summary['data_quality'] == 'ok' else '数据待补齐 · 暂评' if score is not None else '尚无有效评价结果'}</span></article></div>
<div class="method-entry"><div><strong>综合风险评价方法</strong><p>了解风险强度、有效覆盖率与多指标加权如何形成最终等级。</p></div><button class="button primary" type="button" data-open-model>查看评价方法 <span aria-hidden="true">↗</span></button></div></section>''')
        sections.append(f'<section id="risk-summary-{summary_index}" class="risk-hero risk-{level}" data-assessment-status="{"provisional" if provisional else "unavailable" if score is None else "complete"}"><div class="risk-top"><span>{esc(summary["asset"])} · {area_text}</span><span class="risk-status{" pending" if summary["data_quality"] != "ok" else ""}">{status}</span></div><div class="risk-main"><div><p class="risk-note">综合风险等级 · 综合风险评价模型</p><h2 class="risk-headline">{title}</h2></div><div class="risk-score"><strong>{score:.2f}</strong><span>综合风险评分 / {maximum:g}</span></div></div>' if score is not None else f'<section class="risk-hero risk-undetermined" data-assessment-status="unavailable"><p>{esc(summary["asset"])}</p><h2 class="risk-headline">暂无法评价</h2>')
        sections.append(f'<p class="risk-summary">{descriptions[level]}</p>')
        if score is not None:
            start, end = (v / maximum * 100 for v in limits)
            position = min(100, max(0, score / maximum * 100))
            sections.append(f'<div class="risk-meter" role="img" aria-label="综合评分{score:.2f}，{title}" style="background:linear-gradient(to right,#20976d 0%,#20976d {start}%,#efbd43 {start}%,#efbd43 {end}%,#d95b59 {end}%,#d95b59 100%)"><i class="risk-pointer" style="left:{position}%"></i></div><div class="risk-ticks"><span style="left:0%">0</span><span style="left:{start}%">{limits[0]:g}</span><span style="left:{end}%">{limits[1]:g}</span><span style="left:100%">{maximum:g}</span></div>')
            sections.append(f'<p class="risk-note">先计算各指标的单项综合评分，再按有效像元数加权，得到这里的综合风险评分。已纳入 {summary["included_layers"]}/{summary["expected_layers"]} 个主评价指标。</p>')
        if provisional:
            missing = summary["expected_layers"]-summary["included_layers"]
            reason = f"尚有 {missing} 个主评价指标未纳入" if missing else "部分已纳入指标的有效覆盖不足"
            sections.append(f'<div class="risk-quality">当前为基于已有数据的暂评结果。{reason}，补齐后评分与等级可能变化。缺失数据没有计为零风险。</div>')
        sections.append('</section>')
        asset_rows = [r for r in rows if r["asset"] == summary["asset"] and r["asset_type"] == "zone" and r["service"] not in COMPARISON_SERVICES]
        high = sorted((r for r in asset_rows if r.get("screening_level") == "high"), key=lambda r:r.get("coverage_weighted_score",0), reverse=True)[:3]
        coverage_review = sorted((r for r in asset_rows if r.get("coverage") is not None and r["coverage"] < .95), key=lambda r:r["coverage"])[:1]
        focus = []
        for row in high:
            focus.append(f'<article><strong>{esc(layer_label(row["service"]))} · 高</strong><p>单项综合评分 {row["coverage_weighted_score"]:.2f}。建议优先核对相关防护与应急安排。</p></article>')
        for row in coverage_review:
            high_share = row.get("high_fraction_valid")
            extra = f'；有效区域中高值占 {high_share:.1%}' if high_share is not None else ''
            focus.append(f'<article><strong>{esc(layer_label(row["service"]))} · 需核查覆盖</strong><p>有效覆盖 {row["coverage"]:.1%}{extra}。未覆盖部分仍为未知。</p></article>')
        if focus:sections.append('<section class="card"><h2>重点关注</h2><p>综合等级来自多指标加权，个别指标仍可能较高。</p><div class="risk-focus">' + ''.join(focus) + '</div></section>')
    if summaries:
        sections.append(f'<section class="card"><h2>低、中、高风险如何理解？</h2><div class="risk-guide"><div class="risk-low"><strong>低风险</strong><small>综合评分 &lt; {limits[0]:g}</small><p>{descriptions["low"]}</p></div><div class="risk-medium"><strong>中风险</strong><small>{limits[0]:g} ≤ 综合评分 &lt; {limits[1]:g}</small><p>{descriptions["medium"]}</p></div><div class="risk-high"><strong>高风险</strong><small>综合评分 ≥ {limits[1]:g}</small><p>{descriptions["high"]}</p></div></div><p class="risk-note">等级来自你的自定义综合评价模型，用于风险筛查与比较；不等于灾害发生概率或财务损失比例。</p></section>')
    else:
        sections.append('<section class="card"><h2>综合风险评价</h2><p>当前任务未形成区域综合评分，请查看单项结果；区域综合评价需要边界及综合模型计算结果。</p></section>')
    links = []
    if any(r.get("status") == "ok" for r in tables.get("satellite_maps", [])):
        links.append('<a href="#risk-map">查看空间分布</a>')
    if summaries:
        links.append('<a href="#indicator-details" onclick="document.getElementById(\'indicator-details\').open=true">单项评价详情</a>')
    if parameters.get("methodology") == "reference":
        links.append('<button type="button" data-open-model>模型计算说明</button>')
    sections.append('<nav class="report-nav" aria-label="报告内容">' + ''.join(links) + '</nav>')
    sections.append(f'<details class="card"><summary>数据完整性与分析范围</summary><p>已选择 {len(services)} 个图层，其中 {len(available)} 个有数值结果，{len(services-available)} 个未取得结果。对照图层单独展示，不参加主评价加权。</p><p>分析面积采用等积投影估算；计算覆盖率时使用源栅格投影的区域面积与原生像元面积。</p></details>')
    return ''.join(sections)


def algorithm_section(parameters):
    if parameters.get("methodology") != "reference":return ""
    low, middle = parameters["thresholds"];w1,w2,w3 = parameters["weights"];s1,s2 = parameters["score_thresholds"]
    return f'''<section class="model-content"><h2>综合评分如何得到？</h2><p>单项综合评分 S=风险强度 I×有效覆盖率 α；多项评分按有效像元数加权后，得到首页的综合风险评分。单项风险等级描述一个指标，综合风险等级描述模型汇总后的区域结果。</p><p>原始 TIFF 指数已为0—1，直接使用；不从截图颜色反推，不重复除以255。</p>
<table><tr><th>参数</th><th>本次取值</th></tr><tr><td>指数阈值</td><td>{low:g} / {middle:g}</td></tr><tr><td>权重节点</td><td>{w1:g} / {w2:g} / {w3:g}</td></tr><tr><td>S 分级阈值</td><td>{s1:g} / {s2:g}</td></tr><tr><td>最低有效覆盖率</td><td>{parameters['min_coverage']:.0%}</td></tr></table>
<ol><li><strong>像元权重：</strong>v≤{low:g} 时 W={w1:g}；{low:g}&lt;v≤{middle:g} 时 W={w1:g}+({w2:g}−{w1:g})(v−{low:g})/({middle:g}−{low:g})；其余 W={w2:g}+({w3:g}−{w2:g})(v−{middle:g})/(1−{middle:g})。</li>
<li><strong>区域统计：</strong>N总=区域在源投影中的面积÷原生像元面积；N有效排除NoData、保留零值。低/中/高值像元分别计数，并同时计算占有效区域和整个区域的比例。</li>
<li><strong>强度与得分：</strong>I=ΣW(v)/N有效；α=N有效/N总；S=I×α。S&lt;{s1:g} 为低，{s1:g}≤S&lt;{s2:g} 为中，S≥{s2:g} 为高。</li>
<li><strong>跨层加权：</strong>wᵢ=N有效ᵢ/ΣN有效ᵢ；S综合=Σ(wᵢSᵢ)。两个地震对照源不重复加权；危险性、脆弱性、风险另列分组结果。</li>
<li><strong>质量判断：</strong>覆盖率低于{parameters['min_coverage']:.0%}、面积明显不符、或主评价缺层时，已有数据的综合等级标“暂评”，正式评价保留待确认；完全无有效数据时不输出低、中、高等级。参考报告参数摘要使用15%覆盖阈值，附录示例为10%，本次以表中参数为准。</li></ol></section>'''


def network_summary_section(out):
    esc = lambda value: html.escape(str(value))
    sections = []
    log = out / "network_requests.jsonl"
    if log.exists():
        records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
        counts = {}
        for row in records:
            key = (row["stage"], row["http_status"])
            counts[key] = counts.get(key, 0) + 1
        body = "".join(f'<tr><td>{esc(stage)}</td><td>{esc(code if code is not None else "连接/读取失败")}</td><td>{count}</td></tr>' for (stage,code),count in counts.items())
        sections.append('<p>逐次请求及重试的实际记录；缓存读取不算网络请求。403/1010为访问拦截，429为明确的频率限制信号，5xx本身不证明限流。</p><table><tr><th>阶段</th><th>HTTP状态</th><th>请求次数</th></tr>' + body + '</table><p><a href="network_requests.jsonl">完整请求记录</a></p>')
    diagnosis = out / "connectivity_diagnosis.json"
    if diagnosis.exists():
        data = json.loads(diagnosis.read_text(encoding="utf-8"))
        sections.append('<p><strong>' + esc(data["summary"]) + '</strong></p><ul>' + ''.join('<li>' + esc(value) + '</li>' for value in data["observations"]) + '</ul><p><a href="connectivity_diagnosis.json">本次排查证据摘要</a> · <a href="network_diagnosis.html">完整排查说明</a> · <a href="https://inarisk.bnpb.go.id/v4/config/arcgis-layers.json">官网图层配置</a> · <a href="https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/">Cloudflare 1010说明</a></p>')
    return '<section class="card"><h2>数据获取与接口排查</h2>' + ''.join(sections) + '</section>' if sections else ""


def assessment_section(tables, metadata):
    esc = lambda value: html.escape(str(value))
    levels = {"low": "低", "medium": "中", "high": "高", "undetermined": "待核查"}
    groups = {"all": "全部指标综合", "hazard": "危险性", "vulnerability": "脆弱性", "risk": "风险"}
    sections = []
    if "reference_aggregate" in tables:
        parameters = metadata["parameters"]
        sections.append(f'<section class="card"><h2>按参考方法评价</h2><p>I 为有效像元的分段权重均值（权重 {esc(parameters["weights"])}），α 为有效像元数除以源投影区域面积对应的理论像元数，S=I×α。S 的分级阈值为 {esc(parameters["score_thresholds"])}，覆盖阈值为 {parameters["min_coverage"]:.0%}。跨层权重为各层有效像元数占比。</p><p>下列综合分复现用户自定义加权方法。危险性、脆弱性和风险含义不同，多灾种层与单灾种层存在重叠，全部指标综合仅用于该方法下的比较。全球地震和雅加达5米层列作对照，未重复计权。</p>')
        for aggregate in tables["reference_aggregate"]:
            score = aggregate["score"]
            label = levels[aggregate["reference_computed_level"]] + ("（暂评，正式评价待确认）" if aggregate["data_quality"] != "ok" else "")
            sections.append(f'<p><strong>{esc(aggregate["asset"])} · {groups[aggregate["group"]]}：{score:.3f} · {label}</strong>（纳入 {aggregate["included_layers"]}/{aggregate["expected_layers"]} 层）</p>' if score is not None else f'<p>{groups[aggregate["group"]]}：无可用数据</p>')
        sections.append('<h3>重点评价</h3><ul>')
        rows = tables["asset_risk"]
        for group in ("hazard", "vulnerability", "risk"):
            ranked = sorted((r for r in rows if r.get("asset_type") == "zone" and component(r["service"]) == group and not r.get("comparison_only") and r.get("coverage_weighted_score") is not None), key=lambda r: r["coverage_weighted_score"], reverse=True)
            for row in ranked[:3]:
                sections.append(f'<li>{esc(row["asset"])} · {esc(layer_label(row["service"]))}：S={row["coverage_weighted_score"]:.3f}（{levels[row["screening_level"]]}），I={row["intensity"]:.3f}，覆盖 {row["coverage"]:.1%}，有效区域高值像元占 {row["high_fraction_valid"]:.1%}。{("建议优先核对资产防护、现场条件与应急安排。" if row["screening_level"] == "high" else "需结合局部高值分布判断，区域均值不能替代资产位置评价。")}</li>')
        missing = [r for r in rows if r.get("asset_type") == "zone" and (r.get("coverage", 1) < .95 or r.get("data_quality") != "ok")]
        for row in missing:
            coverage = row.get("coverage")
            sections.append(f'<li>数据核查：{esc(layer_label(row["service"]))} · {esc(row["asset"])}，覆盖 {coverage:.1%}。空缺保持透明；覆盖加权会降低 S，低分不能解释为缺失区域安全。</li>' if coverage is not None else f'<li>未完成：{esc(layer_label(row["service"]))} · {esc(row.get("error", row["data_quality"]))}。</li>')
        sections.append('</ul><p>零值只表示该官方图层在该像元给出的指数为零，不证明现实灾害不存在。本次为公开静态指数筛查，没有企业资产脆弱性调查、未来情景或损失模型，不能直接推出财务损失。</p></section>')
        detail = []
        fmt = lambda value: "—" if value is None else f"{value:.3f}"
        pct = lambda value: "—" if value is None else f"{value:.1%}"
        for row in sorted((r for r in rows if r["asset_type"] == "zone"), key=lambda r: (component(r["service"]), r["service"])):
            detail.append('<tr><td>' + esc(layer_label(row["service"])) + ('（对照）' if row["service"] in COMPARISON_SERVICES else '') + '</td><td>' +
                '</td><td>'.join(esc(x) for x in (fmt(row.get("mean_index")), fmt(row.get("intensity")), pct(row.get("coverage")),
                fmt(row.get("coverage_weighted_score")), levels[row["screening_level"]], pct(row.get("high_fraction_valid")),
                "可用" if row.get("data_quality") == "ok" else "需核查")) + '</td></tr>')
        sections.append('<section class="card"><h2>各指标评价明细</h2><p>单项综合评分是每个指标的评分；首页综合评分是这些评分再加权后的结果。高值占比以有效区域为分母，地图颜色显示原始局部指数。</p><div class="table"><table><tr><th>指标</th><th>平均指数</th><th>风险强度</th><th>有效覆盖率</th><th>单项综合评分</th><th>单项风险等级</th><th>高值占比</th><th>数据状态</th></tr>' + ''.join(detail) + '</table></div></section>')
    assessment_html = '<details class="card" id="indicator-details"><summary>查看单项评价详情与分组结果</summary>' + "".join(sections) + '</details>' if sections else ""
    sections = []
    maps = [r for r in tables.get("satellite_maps", []) if r.get("status") == "ok"]
    if maps:
        maps.sort(key=lambda r: (r["service"] != "layer_risiko_banjir", r["service"] != "INDEKS_BAHAYA_BANJIR", r["label"]))
        payload = json.dumps(maps, ensure_ascii=False).replace("<", "\\u003c")
        options = "".join(f'<option value="{i}">{esc(r["asset"])} · {esc(r["label"])}</option>' for i, r in enumerate(maps))
        sections.append('''<section class="card" id="risk-map"><h2>风险空间分布</h2><p>这里的颜色显示所选指标的局部指数；首页综合风险等级由可用主指标加权计算。切换指标可查看局部高值，调低图层不透明度可对照建筑和道路。底图为真实卫星/航空拼接影像，拍摄日期未核实；空缺透明显示。</p>
<div class="map-toolbar"><label>风险指标 <select id="mapSelect">''' + options + '''</select></label> <label>不透明度 <input id="opacity" type="range" min="0" max="100" value="55"><span id="opacityLabel">55%</span></label> <label>放大 <select id="zoom"><option value="100">1×</option><option value="200">2×</option><option value="400">4×</option></select></label></div>
<p class="map-legend"><span></span> 原始指数 0 → 1 · 低值 ≤0.33，中值 ≤0.66，高值 &gt;0.66</p>
<div class="map-frame"><div id="mapStage" style="position:relative;width:100%;line-height:0"><img id="mapBase" alt="真实 World Imagery 影像" style="width:100%"><img id="mapOverlay" alt="原始指数，NoData透明" style="position:absolute;inset:0;width:100%;opacity:.55"><img id="mapBoundary" alt="区域边界" style="position:absolute;inset:0;width:100%;pointer-events:none"><span style="position:absolute;right:15px;top:20px;color:white;font-size:20px;text-shadow:0 0 4px black;line-height:1.4">↑ N</span></div></div>
<p id="mapSource"></p><p class="map-footer">边界为输入区域；十字标记为显示范围中心。放大不增加原始风险数据精度。<a id="rawMap" href="">下载当前透明图层</a></p></section>
<script>const maps=''' + payload + ''';const select=document.getElementById('mapSelect');function showMap(){const m=maps[+select.value];document.getElementById('mapBase').src=m.background;document.getElementById('mapOverlay').src=m.overlay;document.getElementById('mapBoundary').src=m.boundary;document.getElementById('mapSource').textContent=m.attribution+' · EPSG:3857 · '+m.width+'×'+m.height+' 显示采样像素（非原生影像分辨率） · 指数原生像元 '+(m.native_pixel_size||[]).join('×')+' 源投影单位';document.getElementById('rawMap').href=m.overlay}select.onchange=showMap;document.getElementById('opacity').oninput=function(){document.getElementById('mapOverlay').style.opacity=this.value/100;document.getElementById('opacityLabel').textContent=this.value+'%'};document.getElementById('zoom').onchange=function(){document.getElementById('mapStage').style.width=this.value+'%'};showMap();</script>''')
    for row in tables.get("satellite_maps", []):
        if row.get("status") == "unavailable":
            sections.append('<section class="card"><h2>卫星图未生成</h2><p>' + esc(row["error"]) + '</p></section>')
    return "".join(sections) + assessment_html


def render_report(out, title, tables, notes, metadata):
    esc = lambda value: html.escape("" if value is None else str(value))
    figures = assessment_charts(out, tables, metadata)
    charts_html = '<section class="card"><h2>可视化图表</h2>' + ''.join(f'<figure><h3>{esc(f["title"])}</h3><a href="{f["svg"]}"><img src="{f["png"]}" alt="{esc(f["title"])}" style="width:100%"></a><figcaption>{esc(f["caption"])} · <a href="{f["svg"]}">矢量图</a></figcaption></figure>' for f in figures) + '</section>' if figures else ""
    network_html = network_summary_section(out)
    model_body = algorithm_section(metadata["parameters"])
    if model_body and (out / "charts/algorithm.png").exists():
        model_body += '<figure><img src="charts/algorithm.png" alt="像元权重及覆盖率如何影响综合评分"><figcaption>按本次参数绘制：缺测会降低覆盖加权分数，需同时查看评价完整性。</figcaption></figure>'
    model_dialog = '<dialog class="model-dialog" id="model-method" aria-labelledby="model-title"><header class="dialog-heading"><div><span class="eyebrow">METHODOLOGY</span><h2 id="model-title">综合风险评价方法</h2></div><form method="dialog"><button class="button small" type="submit" aria-label="关闭评价方法">关闭 ×</button></form></header><div class="dialog-content">' + model_body + '</div></dialog>' if model_body else ""
    sections = [assessment_dashboard(tables, out, metadata), assessment_section(tables, metadata),
        '<details class="card"><summary>查看分析图表</summary>' + charts_html + '</details>' if charts_html else "",
        '<details class="card"><summary>数据获取与接口排查记录</summary>' + network_html + '</details>' if network_html else ""]
    if "asset_risk" in tables:
        rows = tables["asset_risk"]
        state = tables["pipeline_status"][0]
        services = list(dict.fromkeys(row["service"] for row in rows))
        assets = list(dict.fromkeys((row["asset"], row["asset_type"]) for row in rows))
        levels = {"low": "低", "medium": "中", "high": "高", "undetermined": "待核查"}
        state_text = {"complete": "全流程完成", "partial": "部分结果缺失，需核查", "unavailable": "未取得有效结果"}[state["status"]]
        header = "".join(f'<th title="{esc(s)}">{esc(layer_label(s))}</th>' for s in services)
        body = []
        for name, kind in assets:
            cells = []
            for service in services:
                row = next(r for r in rows if r["asset"] == name and r["asset_type"] == kind and r["service"] == service)
                level = row.get("screening_level", "undetermined")
                value = row.get("coverage_weighted_score") if metadata["parameters"].get("methodology") == "reference" and kind == "zone" else row.get("normalized_index", row.get("mean_index"))
                cells.append('<td>' + levels.get(level, level) + (f" · {value:.3f}" if value is not None else "") +
                    ("<br><small>数据需核查</small>" if row.get("data_quality") != "ok" else "") + '</td>')
            body.append(f'<tr><td>{esc(name)}</td><td>{"点位" if kind == "point" else "区域"}</td>' + "".join(cells) + '</tr>')
        sections.append(f'<details class="card"><summary>查看资产与指标对照矩阵</summary><p><strong>{state_text}</strong> · {state["assets"]} 项资产 · {state["services"]} 个图层 · {state["rows_needing_review"]} 条结果需核查</p><p>区域采用模型计算时，表内为单项综合评分及等级；其他情况为原始指数或区域均值。首页另列多指标加权后的综合风险等级。</p><div class="table"><table><tr><th>资产</th><th>类型</th>{header}</tr>{"".join(body)}</table></div></details>')
    exports = []
    for name, rows in tables.items():
        fields = list(dict.fromkeys(k for row in rows for k in row))
        head = "".join("<th>" + esc(k) + "</th>" for k in fields)
        body = "".join("<tr>" + "".join("<td>" + esc(row.get(k)) + "</td>" for k in fields) + "</tr>" for row in rows[:1000])
        exports.append(f'<h3>{esc(name)} · {len(rows)} 条数据</h3><p><a href="{name}.csv">下载 CSV</a></p><div class="table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
    sections.append('<details class="card"><summary>完整数据与导出</summary>' + ''.join(exports) + '</details>')
    notes_html = "".join("<li>" + esc(note) + "</li>" for note in notes)
    plot_html = '<section class="card"><img src="precipitation_comparison.png" alt="Precipitation period comparison" style="max-width:100%"></section>' if (out / "precipitation_comparison.png").exists() else ""
    state = tables.get("pipeline_status", [{}])[0].get("status")
    badge = {"complete": "当前评价范围已完成", "partial": "部分数据待补齐", "unavailable": "等待有效数据"}.get(state, "本地数据分析报告")
    synthetic = metadata["parameters"].get("data_kind") == "synthetic"
    if synthetic:badge = "合成数据 · 验证演示"
    stamp = str(metadata.get("report_regenerated_utc", metadata["generated_utc"])).replace("T", " ")[:16] + " UTC"
    source = {"inarisk":"BNPB InaRISK", "catalog":"BNPB InaRISK", "aqueduct":"WRI Aqueduct", "precipitation":"CMIP6", "cdd":"CDD"}.get(metadata.get("command"), "本地空间与指标分析")
    notice = '<p class="synthetic-notice">本报告使用合成数据验证计算与报告流程，不代表真实资产或实际灾害评价；分数仅用于功能演示。</p>' if synthetic else ""
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{esc(title)} · 综合风险分析</title><style>{REPORT_CSS}</style></head><body>
<main><header class="report-header"><div class="header-top"><span class="report-brand">INDONESIA / CLIMATE RISK</span><span class="header-badge">{badge}</span></div><div class="header-bottom"><div><h1>印尼气候与灾害风险评估</h1><p class="report-title">{esc(title)}</p></div><div class="header-actions"><a class="button ghost small" href="results.json">导出数据</a><button class="button ghost small" id="print-report" type="button">打印报告</button></div></div><p class="report-meta">{esc(source)} · 报告生成 {esc(stamp)} · v{VERSION}</p></header>{notice}{plot_html}{''.join(sections)}<details class="card"><summary>方法与数据质量补充说明</summary><ul>{notes_html}</ul></details><details class="card"><summary>运行记录</summary><p><a href="metadata.json">参数与输入文件校验值</a> · <a href="results.json">完整 JSON</a></p><pre>{esc(json.dumps(metadata, ensure_ascii=False, indent=2))}</pre></details><footer class="report-footer"><span>Indonesia Climate Risk · 可复现的资产风险分析</span><span>结果解释请同时参考评价完整性与计算方法。</span></footer></main>{model_dialog}<script>{REPORT_JS}</script></body></html>'''
    (out / "report.html").write_text(document, encoding="utf-8")


def execute(args):
    if args.command == "raster" and not (args.points or args.zones):
        raise ValueError("栅格分析至少需要 --points 或 --zones")
    if getattr(args, "band", 1) < 1:
        raise ValueError("波段从 1 开始")
    interval = getattr(args, "request_interval", 1.5)
    if not math.isfinite(interval) or not .25 <= interval <= 60:
        raise ValueError("请求间隔须为0.25至60秒的有限数")
    out = new_output(args.out, args.command)
    configure_network(interval, out / "network_requests.jsonl")
    try:
        tables, notes = COMMANDS[args.command](args, out)
        inputs = [getattr(args, k, None) for k in ("input", "points", "zones")]
        for path in list(inputs):
            if path and Path(path).suffix.lower() == ".shp":
                inputs.extend(str(p) for p in Path(path).parent.glob(Path(path).stem + ".*")
                              if p.suffix.lower() in {".shx", ".dbf", ".prj", ".cpg"})
        params = {k: v for k, v in vars(args).items() if k not in {"input", "points", "zones", "out"}}
        metadata = {"version": VERSION, "generated_utc": datetime.now(timezone.utc).isoformat(),
            "command": args.command, "parameters": params,
            "inputs": [file_digest(p) for p in inputs if p], "notes": notes,
            "python": sys.version.split()[0], "dependencies": {}}
        if "pipeline_status" in tables:
            metadata["run_status"] = tables["pipeline_status"][0]["status"]
        for package in ("numpy", "xarray", "h5netcdf", "h5py", "scipy", "cftime", "matplotlib", "rasterio", "shapely", "fiona", "openpyxl"):
            try:
                metadata["dependencies"][package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                pass
        for name, rows in tables.items():
            write_csv(out / (name + ".csv"), rows)
        write_json(out / "results.json", tables)
        write_json(out / "metadata.json", metadata)
        render_report(out, args.command, tables, notes, metadata)
    except Exception as exc:
        write_json(out / "FAILED.json", {"error": str(exc), "command": args.command})
        raise
    print(f"报告已生成: {out.resolve()}" + (f" · {metadata['run_status']}" if "run_status" in metadata else ""))
    return out


def batch(config, output, parser):
    path = Path(config).resolve()
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if set(data) != {"jobs"} or not isinstance(data["jobs"], list) or not data["jobs"]:
        raise ValueError("配置应为非空 jobs 列表")
    validated = []
    for job in data["jobs"]:
        if not isinstance(job, dict) or job.get("command") not in COMMANDS:
            raise ValueError("每个任务必须含受支持的 command")
        argv = [job["command"]]
        for key, value in job.items():
            if key == "command":
                continue
            if key in {"out", "help"}:
                raise ValueError("任务内不允许设置 out/help；输出由批处理统一管理")
            option = "--" + key.replace("_", "-")
            if isinstance(value, bool):
                if value:
                    argv.append(option)
            else:
                if key in {"input", "points", "zones", "cache"}:
                    value = str((path.parent / value).resolve())
                argv.append(option)
                argv.extend(map(str, value if isinstance(value, list) else [value]))
        validated.append(parser.parse_args(argv))
    root = new_output(output, "batch")
    links, records = [], []
    for args in validated:
        args.out = str(root)
        folder = execute(args)
        status = json.loads((folder / "metadata.json").read_text(encoding="utf-8")).get("run_status", "complete")
        records.append({"command": args.command, "report": folder.name + "/report.html", "status": status})
        links.append(f'<li><a href="{folder.name}/report.html">{html.escape(args.command)}</a> · {status}</li>')
    overall = "complete" if all(r["status"] == "complete" for r in records) else "partial"
    write_json(root / "metadata.json", {"version": VERSION, "run_status": overall, "jobs": records})
    (root / "report.html").write_text('<!doctype html><meta charset="utf-8"><title>Batch results</title><h1>批量分析报告</h1><p>状态: ' + overall + '</p><ul>' + "".join(links) + "</ul>", encoding="utf-8")
    print(f"批处理报告: {(root / 'report.html').resolve()}")
    return root


def demo(output, parser):
    root = new_output(output, "demo")
    data = root / "synthetic"
    data.mkdir()
    write_csv(data / "histogram.csv", [
        {"fid": "A", "Area": 1, "pixel_size_x": 10, "pixel_size_y": 10,
         "pixel_size_unit": "meters", "source_file": "synthetic_drought_index", "histo0": 10, "histo128": 20, "histo255": 70},
        {"fid": "B", "Area": 1, "pixel_size_x": 10, "pixel_size_y": 10,
         "pixel_size_unit": "meters", "source_file": "synthetic_drought_index", "histo0": 2, "histo128": 0, "histo255": 3}])
    write_csv(data / "aqueduct.csv", [{"location_name": "Synthetic Site A", "bws_raw": 0.15,
        "bws_score": 1.5, "bws_label": "Low-Medium", "bau30_ws_x_r": 0.45,
        "bau30_ws_x_l": "High", "bau30_wd_x_r": 0.12, "bau30_ba_x_r": 50, "bau30_ww_x_r": 20}])
    write_csv(data / "cdd.csv", [{"Country": "Indonesia", "Territory": "Synthetic", "Unit": "degree days",
        "Date": f"2020-{month:02d}-01", "CDDhum18dailybypopValue Anomalies": month - 6}
        for month in range(1, 13)])
    config = {"jobs": [
        {"command": "histogram", "input": "histogram.csv", "normalization": "inverse-gray255"},
        {"command": "aqueduct", "input": "aqueduct.csv"},
        {"command": "cdd", "input": "cdd.csv"}]}
    write_json(data / "config.json", config)
    return batch(data / "config.json", root, parser)


def gui(parser):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    import queue
    import threading
    import webbrowser
    root = tk.Tk()
    root.title("印尼气候风险分析")
    root.geometry("820x700")
    pane = ttk.Frame(root, padding=22)
    pane.pack(fill="both", expand=True)
    pane.columnconfigure(1, weight=1)
    ttk.Label(pane, text="印尼气候风险分析", font=("Microsoft YaHei", 18)).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
    modes = {"BNPB 数据获取到报告（全流程）": "inarisk", "获取 BNPB 图层目录": "catalog", "InaRISK 区域直方图": "histogram", "Aqueduct 水风险": "aqueduct",
             "CMIP6 降水对比": "precipitation", "原始栅格点位/区域": "raster", "CDD 制冷度日": "cdd", "配置文件批量运行": "batch", "合成数据演示": "demo"}
    mode = tk.StringVar(value=next(iter(modes)))
    ttk.Label(pane, text="分析任务").grid(row=1, column=0, sticky="w")
    ttk.Combobox(pane, textvariable=mode, values=list(modes), state="readonly").grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
    fields = {}
    def add_file(label, key, row, directory=False):
        value = tk.StringVar(value="outputs" if key == "out" else "")
        fields[key] = value
        ttk.Label(pane, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(pane, textvariable=value).grid(row=row, column=1, sticky="ew", padx=8)
        def browse():
            selected = filedialog.askdirectory(parent=root) if directory else filedialog.askopenfilename(parent=root)
            if selected:
                value.set(selected)
        ttk.Button(pane, text="选择…", command=browse).grid(row=row, column=2)
    for row, (label, key) in enumerate((("本地数据 / 批量配置", "input"), ("输出目录", "out"),
            ("资产点位 CSV / Excel", "points"), ("资产区域 GeoJSON / GPKG / SHP", "zones")), 2):
        add_file(label, key, row, key == "out")
    norm = tk.StringVar(value="inverse-gray255")
    ttk.Label(pane, text="指数标准化").grid(row=6, column=0, sticky="w", pady=6)
    ttk.Combobox(pane, textvariable=norm, values=["inverse-gray255", "gray255", "index01"], state="readonly").grid(row=6, column=1, sticky="ew", padx=8)
    metre = tk.BooleanVar()
    ttk.Checkbutton(pane, text="已核实直方图像元尺寸单位为米", variable=metre).grid(row=7, column=1, sticky="w")
    period1, period2 = tk.StringVar(value="2015:2025"), tk.StringVar(value="2040:2050")
    for row, label, value in ((8, "降水参考时期", period1), (9, "降水对比时期", period2)):
        ttk.Label(pane, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(pane, textvariable=value).grid(row=row, column=1, sticky="ew", padx=8)
    services = tk.StringVar(value="")
    ttk.Label(pane, text="BNPB 自选图层（空白=全部物理灾害）").grid(row=10, column=0, sticky="w", pady=4)
    ttk.Entry(pane, textvariable=services).grid(row=10, column=1, columnspan=2, sticky="ew", padx=8)
    ttk.Label(pane, text="全流程：默认全部物理灾害危险性、脆弱性及风险图层，区域采用 I×覆盖率评分。\n覆盖阈值15%，出具卫星叠图；原生像元超过500万时请用配置文件调整。", foreground="#52616b").grid(row=11, column=0, columnspan=3, sticky="w", pady=12)
    messages = queue.Queue()
    status = tk.StringVar(value="就绪；每次运行生成独立结果目录。")
    ttk.Label(pane, textvariable=status, wraplength=740).grid(row=13, column=0, columnspan=3, sticky="w", pady=15)
    last_report = []
    def start():
        command = modes[mode.get()]
        argv = [command, "--out", fields["out"].get() or "outputs"]
        if command not in {"demo", "catalog", "inarisk"}:
            if not fields["input"].get():
                messagebox.showerror("缺少输入", "请选择数据文件或批量配置文件。", parent=root)
                return
            argv += ["--config" if command == "batch" else "--input", fields["input"].get()]
        if command in {"histogram", "raster"}:
            argv += ["--normalization", norm.get()]
        if command == "histogram" and metre.get():
            argv += ["--pixel-unit", "meters"]
        if command == "precipitation":
            argv += ["--baseline", period1.get(), "--future", period2.get(), "--plots"]
        for key in ("points", "zones"):
            if fields[key].get() and (command in {"raster", "inarisk"} or command == "precipitation" and key == "points"):
                argv += ["--" + key, fields[key].get()]
        if command == "inarisk":
            selected = [s.strip() for s in services.get().replace("，", ",").split(",") if s.strip()]
            argv += ["--services", *selected] if selected else ["--profile", "physical-all"]
            argv += ["--methodology", "reference", "--min-coverage", "0.15"]
            if fields["zones"].get():
                argv += ["--satellite"]
        try:
            args = parser.parse_args(argv)
        except SystemExit:
            messagebox.showerror("参数错误", "请检查输入及时间格式。", parent=root)
            return
        run_button.config(state="disabled")
        status.set("正在计算，请稍候…")
        def worker():
            try:
                result = batch(args.config, args.out, parser) if command == "batch" else (
                    demo(args.out, parser) if command == "demo" else execute(args))
                messages.put((True, result))
            except (Exception, SystemExit) as exc:
                messages.put((False, str(exc)))
        threading.Thread(target=worker, daemon=True).start()
    def poll():
        try:
            success, value = messages.get_nowait()
            run_button.config(state="normal")
            if success:
                last_report[:] = [(value / "report.html").resolve()]
                status.set(f"报告已生成，请查看数据质量与缺失说明：{value.resolve()}")
            else:
                status.set("运行失败；请根据错误修正输入。")
                messagebox.showerror("运行失败", str(value), parent=root)
        except queue.Empty:
            pass
        root.after(200, poll)
    run_button = ttk.Button(pane, text="开始分析", command=start)
    run_button.grid(row=12, column=1, sticky="ew", padx=8)
    ttk.Button(pane, text="打开结果报告", command=lambda: webbrowser.open(last_report[0].as_uri()) if last_report else None).grid(row=12, column=2)
    poll()
    root.mainloop()


def make_parser():
    parser = argparse.ArgumentParser(description="Indonesia climate screening / 印尼气候风险分析")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command")
    for name in COMMANDS:
        p = sub.add_parser(name)
        if name not in {"catalog", "inarisk"}:
            p.add_argument("--input", required=True)
        p.add_argument("--out", default="outputs")
        if name in {"histogram", "raster", "inarisk"}:
            if name == "inarisk":
                p.set_defaults(normalization="index01", band=1, nodata=None)
            else:
                p.add_argument("--normalization", choices=["inverse-gray255", "gray255", "index01"], required=True)
                p.add_argument("--nodata", type=float)
                p.add_argument("--band", type=int, default=1)
            p.add_argument("--thresholds", nargs=2, type=float, default=[0.33, 0.66])
            p.add_argument("--weights", nargs=3, type=float, default=[1, 5, 10])
            p.add_argument("--score-thresholds", nargs=2, type=float, default=[3, 7.5])
            p.add_argument("--min-coverage", type=float, default=0.1)
            if name in {"raster", "inarisk"}:
                p.add_argument("--methodology", choices=["index", "reference"], default="index")
        if name == "histogram":
            p.add_argument("--pixel-unit", choices=["meters"])
            p.add_argument("--layer-pattern", default="指数|index")
        if name in {"precipitation", "raster", "inarisk"}:
            p.add_argument("--points")
        if name in {"raster", "inarisk"}:
            p.add_argument("--zones")
            p.add_argument("--zone-layer")
            p.add_argument("--all-touched", action="store_true")
        if name in {"catalog", "inarisk"}:
            p.add_argument("--cache", default="data/inarisk-cache")
            p.add_argument("--offline", action="store_true")
            p.add_argument("--refresh", action="store_true")
            p.add_argument("--timeout", type=int, default=30)
            p.add_argument("--request-interval", type=float, default=1.5)
        if name == "catalog":
            p.add_argument("--pattern", default="INDEKS|layer_risiko")
        if name == "inarisk":
            p.add_argument("--services", nargs="+")
            p.add_argument("--profile", choices=["core", "physical-all"], default="core")
            p.add_argument("--satellite", action="store_true")
            p.add_argument("--map-size", type=int, choices=[1024, 2048, 4096], default=2048)
            p.add_argument("--tile-size", type=int, default=1024)
            p.add_argument("--max-pixels", type=int, default=5000000)
        if name == "precipitation":
            p.add_argument("--variable", default="pr")
            p.add_argument("--units", help="Explicit verified override of NetCDF units")
            p.add_argument("--bounds", nargs=4, type=float, default=[95, -11, 141, 6], metavar=("WEST", "SOUTH", "EAST", "NORTH"))
            p.add_argument("--baseline", default="2015:2025")
            p.add_argument("--future", default="2040:2050")
            p.add_argument("--plots", action="store_true")
        if name == "cdd":
            p.add_argument("--country", default="Indonesia")
            p.add_argument("--territory")
            p.add_argument("--value-column", default="CDDhum18dailybypopValue Anomalies")
    p = sub.add_parser("batch")
    p.add_argument("--config", required=True)
    p.add_argument("--out", default="outputs")
    p = sub.add_parser("demo")
    p.add_argument("--out", default="outputs")
    sub.add_parser("gui")
    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        if args.command in {None, "gui"}:
            gui(parser)
        elif args.command == "batch":
            folder = batch(args.config, args.out, parser)
            if json.loads((folder / "metadata.json").read_text(encoding="utf-8"))["run_status"] != "complete":
                return 3
        elif args.command == "demo":
            demo(args.out, parser)
        else:
            folder = execute(args)
            if args.command == "inarisk":
                results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
                if results["pipeline_status"][0]["status"] != "complete":
                    return 3
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
