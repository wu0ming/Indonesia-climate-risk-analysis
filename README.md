# Indonesia Climate Risk

一个 Python 主脚本，完成 **BNPB/InaRISK 官方数据获取 → 资产坐标/区域导入 → 风险分析 → 报告出具**。同时保留区域直方图、CMIP6 降水、Aqueduct 水风险和 CDD 制冷度日分析。支持文件选择界面、单任务命令行和配置文件批量运行，生成 HTML 报告、CSV、JSON、原始下载数据与校验记录。

**One Python entry point for reproducible Indonesia climate screening.** The source code is MIT licensed. Included examples are synthetic. Original corporate data, site coordinates, boundaries and third-party datasets are not distributed.

这是通用的分析工具，风险指数、降水变化和制冷度日分别展示。它们不是同一种物理量，也不合成为未经验证的“企业损失概率”。

## 快速使用

建议 Python 3.12；最低 Python 3.10。CSV 分析和演示仅使用标准库。图形界面需要 tkinter（Windows 官方 Python 通常自带；部分 Linux 发行版需要另行安装 python3-tk）。

```sh
python climate_risk.py demo
python climate_risk.py
```

第一条生成完全由合成数据组成的演示报告；第二条打开文件选择界面。Windows 也可双击 `start_gui.bat`。报告位置会显示在界面或终端中。

需要处理 NetCDF、GeoTIFF 或生成降水图时：

```sh
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python climate_risk.py gui
# macOS / Linux
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python climate_risk.py gui
```

无需 QGIS、PyQt、Pandoc 或 LaTeX。BNPB 在线模式向官方服务发送资产范围以获取数据，卫星叠图另从 Esri World Imagery 获取真实影像；不上传资产文件或名称。本地分析及完整缓存离线模式不联网。依赖只需首次手动安装。每次运行创建独立目录，默认在 `outputs/` 下，保留已有结果。失败的运行目录包含 `FAILED.json`，不应当作成功结果。

## 从 BNPB 数据获取到资产报告

首次安装依赖后，可以直接运行整个流程，不需要打开 QGIS：

```sh
python climate_risk.py inarisk --points examples/inarisk-points.csv --zones examples/inarisk-zones.geojson
```

示例是人工构造的雅加达测试点和小矩形，不代表真实企业资产。将 `--points` 和 `--zones` 替换为你的资料；两者至少提供一个。命令行未指定范围时仅获取洪水和干旱危险性原始指数。图形界面默认全部物理灾害指标、参考方法评分和区域卫星叠图；也可以填写服务名称自选图层。

### 全部物理灾害、参考方法评分与卫星叠图

```sh
python climate_risk.py inarisk --zones data/assets.geojson --profile physical-all --methodology reference --min-coverage 0.15 --satellite
```

`physical-all` 从官方目录选择洪水、山洪、极端天气、海浪及侵蚀、地震、火山、森林及土地火灾、干旱、液化、滑坡、海啸的危险性/脆弱性/风险，以及多灾种指标。排除 COVID19、人口、能力等方向不同的指标；同一滑坡风险选国家 `layer_risiko_tanah_longsor`，避免和 `INDEKS_RISIKO_TANAH_LONGSOR` 重复。全球地震、雅加达5米地震风险作为对照，不参与跨层加权。图层总数由当次官方目录决定，2026-10-17 目录为38个（36主层+2对照），不是38种不同灾害。

`reference` 复现用户提供的区域评分方法，直接使用原始0–1指数：

- 像元权重：v≤0.33 时 W=1；0.33<v≤0.66 时 W=1+4(v−0.33)/0.33；其余 W=5+5(v−0.66)/0.34。
- I=有效像元 W 的均值；理论总像元数=区域在源投影中的面积/原生像元面积；α=有效像元数/理论总像元数；S=I×α。像元中心法边界计数会有小量离散误差，原始α保留，不强制截为100%。
- S<3 为低，3≤S<7.5 为中，S≥7.5 为高。用户参考报告参数摘要的覆盖阈值为15%，附录示例为10%；命令显式传入0.15以复现摘要。
- 跨层权重=N有效_i/ΣN有效，综合分=ΣS_i×权重_i；同时列出危险性、脆弱性、风险各组。多灾种与单灾种存在重叠，全部指标综合只是该自定义方法的比较值。
- 缺失数据不算零。覆盖不足时保留旧法“低（覆盖不足）”对照标签，正式评价标为待核查；缺层时计算已有数据的描述分并明确列出缺层，不宣称完成综合定级。

默认 `index` 模式继续按原始指数/区域均值筛查；点位没有面积覆盖率，始终按原始指数筛查。`raster` 也支持 `--methodology reference`，要求投影栅格；跨层汇总由 `inarisk` 完成。不同资产区域分别评价，不将相互重叠区域累加。

`--satellite` 下载真实 Esri World Imagery 卫星/航空拼接影像，保留来源、请求范围、获取时间、地理范围和SHA-256。原始指数以最近邻配准叠加，NoData完全透明。HTML提供图层切换、透明度及放大控件，保存后可离线打开。影像拍摄日期、当地原生影像分辨率未核实；`--map-size 1024/2048/4096` 仅控制显示采样像素，不提高风险数据分辨率。第三方影像不随开源仓库发布。底图失败会单独标记，不影响已有数值结果；查看 `satellite_maps` 状态确认地图是否完成。

reference 报告自动提供关键统计卡片、数据与评价摘要、分组数据获取柱图、I/S评分对比、有效区域与整个区域的风险指数构成图，以及权重函数和覆盖率作用示意。图表保存为PNG和SVG，无需在线图表库；使用同一份计算结果，不将未知区域画成低风险。Windows使用已安装的中文字体；其他系统未装中文字体时图中采用英文标注，报告正文仍为中文。底层核查表与运行记录可展开查看。

首页优先显示综合风险评价模型汇总的**综合风险等级与评分**，以低/中/高文字、分级色带及行动说明解释结果。单项评分 S=I×α；首页综合评分为各单项评分按有效像元数再加权后的结果，不是最高单项等级。缺主指标或有效覆盖不足时仍可显示基于已有数据的“低/中/高风险（暂评）”，同时醒目标明正式评价待确认；机器结果中的 `screening_level` 继续保持 `undetermined`，计算得到的区间保存在 `reference_computed_level`。完全没有有效数据时显示“暂无法评价”，不会输出零分或低风险。单项详情、分析图表、计算参数、获取记录及原始导出默认折叠保留。

关键统计数据同时列出综合评分、综合风险等级、区域面积和已纳入主指标数。“查看评价方法”按钮打开完整计算说明，包含权重函数、覆盖率、跨层加权及质量判定；支持键盘关闭。报告采用响应式卡片、统一图表和地图控件；打印时自动展开详细数据和方法说明，打印后恢复原来的展开状态。

### 请求失败与限流排查

网络请求按主机串行，默认请求起点间隔1.5秒，可用 `--request-interval` 调整（0.25—60秒）。这是客户端设置，不是已确认的BNPB官方配额。429、503、520等暂时错误最多尝试3次；采用退避并遵守 `Retry-After`。服务器要求等待超过60秒时本轮停止该主机，保留缓存供稍后续跑；连续3个请求最终失败也暂停该主机，避免对每个图层继续重复访问。

`network_requests.jsonl` 记录目录、元数据、导出请求、TIFF下载等阶段，保留时间、URL、HTTP状态、有限响应头和错误正文前缀。HTTP 403 + Cloudflare 1010 表示客户端访问被安全策略拒绝，立即暂停，不尝试绕过；520本身不是限流证明。只有429、明确的频率限制消息或站点规定，才支持判断请求配额。一次连接失败也不能证明地址不存在；应先对照官方目录和配置。

官网当前公开的图层配置见 [arcgis-layers.json](https://inarisk.bnpb.go.id/v4/config/arcgis-layers.json)。它也包含用于地图显示的渲染层；脚本从官方REST目录选择原始数值指数，不能直接拿渲染图层替换数值层。错误含义见 [Cloudflare 1010](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)、[429](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/4xx-client-error/error-429/) 和 [520](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-520/)。

流程会执行：

1. 从 BNPB 官方公开 REST 目录发现服务，读取并保存元数据。
2. 导入资产点位或区域，检查坐标和边界并转换坐标系。
3. 按每项资产的范围，以原生分辨率分块导出单波段 F32 TIFF；使用 None 渲染规则和最近邻重采样。不会把 PNG/RGB 展示图当数值数据。
4. 检查下载栅格的 CRS、范围、分辨率和值域，保存校验值，逐资产分析。
5. 生成资产风险矩阵、逐图层明细、数据缺失说明和可追溯报告，保留原始 TIFF。

支持的资产输入：

- 点位：CSV 或 `.xlsx` 的首个工作表。表头可用 `name,lon,lat`、`asset_name,longitude,latitude` 或“资产名称、经度、纬度”。坐标为 WGS84，经纬度顺序明确。
- 区域：WGS84 GeoJSON，或带 CRS 的 GeoPackage / Shapefile。GeoPackage 多图层时使用 `--zone-layer 图层名`；Shapefile 的 `.shp/.shx/.dbf/.prj` 等配套文件应放在同一目录。脚本只读资产资料，不修改原文件。

先获取目录、选择其他图层，或运行配置文件：

```sh
python climate_risk.py catalog
python climate_risk.py inarisk --points data/assets.xlsx --zones data/assets.gpkg --zone-layer assets --services INDEKS_BAHAYA_BANJIR INDEKS_BAHAYA_KEKERINGAN
python climate_risk.py batch --config examples/inarisk-batch.json
```

仅自动处理元数据表明为单波段、0–1 浮点原始指数的 ImageServer。不同服务开放的数据类型不同；不能获取的数据会在报告中标为不可用，不用展示图替代，也不推定为低风险。原始值保持不变；计算允许 1e-6 内的端点浮点舍入误差，超出该范围拒绝。

部分 BNPB TIFF 使用极端浮点负数编码 NoData，却不写入 TIFF 缺测标记。工具会先向同一官方服务的 `identify` 接口确认该值确为 NoData，再在分析合并文件中改为标准缺测编码；原始下载字节保留，确认响应写入清单。无法确认的异常值仍拒绝计算。0 值不自动当作缺测。

**断网与续跑**：请求和原始分块缓存在 `data/inarisk-cache/`。重新执行同一命令会复用 SHA-256 校验通过的分块，不必重下。已缓存同一资产范围后，可完全离线重跑：

```sh
python climate_risk.py inarisk --points examples/inarisk-points.csv --zones examples/inarisk-zones.geojson --offline
```

离线模式不会发起网络请求；若更换资产范围、图层或缓存损坏，报告会明确说明缺失。`--refresh` 可重新获取元数据与数据，不能与 `--offline` 同用。缓存时间写入记录，不将缓存数据自动称为最新。

默认总下载上限为 500 万原生像元，可用 `--max-pixels` 明确调整；默认分块 1024 像元，可用 `--tile-size` 调整。资产分布分散时逐资产下载，避免下载整个国家。超出预算直接提示，不自动降低分辨率。网络失败有有限重试，成功分块会保留以便续跑。

报告状态为 `complete`、`partial` 或 `unavailable`。单任务 `inarisk` 在部分/全部数据不可用时仍出具报告，并返回退出码 3；其他参数/文件错误返回 2。缺失项不参与低风险结论。图形界面和批量任务应查看报告里的状态。

## 输入与命令

| 任务 | 输入 | 主要结果 |
|---|---|---|
| `catalog` | BNPB 官方在线目录或缓存 | 可用图层清单及来源记录 |
| `inarisk` | 资产点位/区域、图层选择 | 自动获取原始指数，分析并出具资产报告 |
| `histogram` | QGIS 导出的区域直方图 CSV | 像元分级、有效数据覆盖率、自定义强度和筛查级别 |
| `raster` | 原始数值 GeoTIFF + 点位 CSV / 区域 GeoJSON | 坐标转换后的点位指数、逐区域统计 |
| `precipitation` | CMIP6 降水 NetCDF，可选点位 CSV | 年降水、时期变化、对比 NetCDF、可选 PNG |
| `aqueduct` | Aqueduct 原始宽表 CSV | 基线/未来指标长表，保留官方原始值和标签 |
| `cdd` | IEA/CMCC 格式 CSV | 指定国家的月序列与年均月值，标记不完整年 |
| `batch` | JSON 配置 | 多任务输出目录和汇总入口 |

### InaRISK 区域直方图

```sh
python climate_risk.py histogram --input examples/histogram.csv --normalization inverse-gray255
```

支持 `histo0`、`histo_0` 至 `histo255`、`histo_255`，也支持浮点数值列（配合 `index01`）；空计数按零处理。`histoNODATA` / `histo_nodata` 不计入有效数据。需要区域编号 `fid`（或 `Zone_ID` / `Id`）、`Area`（公顷）、`pixel_size_x/y` 和 `pixel_size_unit`（米）。`area_ha` 也可代替 `Area`。

同一图层同一区域出现多行会拒绝，防止重复计数。多波段导出时可用 `--band 1`；默认仅处理名称包含“指数”或 `index` 的图层。可用 `--layer-pattern "drought|flood"` 修改筛选，或 `--layer-pattern ""` 明确选择所有行。

旧导出若写入 `pixel_size_unit=unknown`，必须先核实原栅格投影和像元单位，再显式使用 `--pixel-unit meters`。经纬度像元不能直接当米。图层名称中的“指数”也不能证明像元方向或标定正确。

标准化方式必须显式选择：

- `inverse-gray255`：`1 - 原值/255`，对应部分旧流程的灰度约定。
- `gray255`：`原值/255`。
- `index01`：已经是 0–1 的原始指数，保持原值。

三者都需要数据字典支持。地图截图和渲染 RGB 不具备可以自动反演的风险量纲。零值是有效数值；只有元数据指定 NoData，或显式 `--nodata 0` 时才排除零。

默认分级阈值 0.33、0.66，强度权重 1、5、10，采用旧项目的分段线性权重函数；这是一套**自定义筛查规则**，不是 BNPB 官方风险定级。可通过 `--thresholds`、`--weights`、`--score-thresholds`、`--min-coverage` 修改。权重与评分阈值分别配置，修改权重后也应核对评分阈值。

### 原始栅格点位及区域

```sh
python climate_risk.py raster --input data/drought_index.tif --points examples/points.csv --zones examples/zones.geojson --normalization index01
```

点位列为 `name,lon,lat`，采用 WGS84 经纬度；也支持上述 Excel 和中文表头。脚本转换到栅格 CRS 后取所在像元。区域支持 GeoJSON、GeoPackage 和 Shapefile，几何需为有效 Polygon/MultiPolygon；多图层文件用 `--zone-layer` 指定。默认为像元中心纳入，可用 `--all-touched` 改为接触即纳入。

区域统计按像元个数加权，不是精确面积加权；经纬度网格跨大范围时尤其需要注意。边界超出栅格范围会标记数据不完整。已标识为 RGB 的栅格会拒绝，其他输入仍需自行核对是否为原始指数。

### CMIP6 降水

```sh
python climate_risk.py precipitation --input data/pr.nc --baseline 2015:2025 --future 2040:2050 --points examples/points.csv --plots
```

变量默认 `pr`；支持 `lat/lon` 或 `latitude/longitude` 命名，自动处理纬度降序及 0–360 经度。仅支持规则一维坐标、等间距经纬度网格，变量须仅含时间、纬度、经度三个维度。模式集合、曲线网格、额外高度维度需先选择或重网格化。

支持降水通量 `kg m-2 s-1`、`mm/s`，日均速率 `mm/day`，逐月累计 `mm/month`；不认识的单位会报错。`--units` 仅用于已核实的元数据修正。使用 HDF5 和 NetCDF3 后端，兼容 Windows 中文文件路径。

计算顺序：通量转为 mm/day → 按实际月份天数/完整逐日数据累计成年降水 mm/year → 对完整年份等权平均 → 比较两个时期。支持 Gregorian、noleap、360_day 等 CF 日历；缺年、缺月或缺日会报错，网格内部缺测会传递为未知，不把缺测求和为零。

默认范围是 `95,-11,141,6` 的矩形，包含海洋和邻国；**不代表印尼陆地平均**。可用 `--bounds 西 南 东 北` 指定其他范围。区域均值采用 cos(纬度) 近似面积权重。点位为最近网格中心，输出实际匹配中心坐标。

输出 `change_pct=(对比均值-参考均值)/参考均值×100`；参考为零时百分比为空。`linear_change_pct_per_year` 再除以两个时期的中点间隔；这是描述性线性年化量，不是回归趋势或复合增长率。2015–2025 可作为模式内参考片段，不自动解释成历史观测基线。

### Aqueduct 水风险

```sh
python climate_risk.py aqueduct --input examples/aqueduct.csv
```

读取官方 `bws_raw/score/label/cat` 等基线列和 `bau30_ws_x_r/l/s/c` 等未来列。`ws` 是水压力，`wd` 是水耗竭；`ba` 是可用蓝水、`ww` 是总用水需求（两者原始量单位为 cm/year）。**直接使用官方 ws，不计算 wd/ws**。保留标签、类别、评分和原始量，不自行重建官方分类，也不将不同指标平均成总体评分。已有错误旧版生成的中文结果表不能代替原始宽表。

原始量单位依指标而异；除 ba/ww 外，在表中标为 `indicator_specific`，应查技术说明。-9999/-999 和负评分/分类哨兵转为空值，标签保留，其他负原始量保留供核对。方法来源见 [WRI 官方数据字典](https://github.com/wri/Aqueduct40/blob/master/data_dictionary_water-risk-atlas.md)。

### CDD 制冷度日

```sh
python climate_risk.py cdd --input examples/cdd.csv --country Indonesia
```

CDD（Cooling Degree Days，制冷度日）默认数值列为 `CDDhum18dailybypopValue Anomalies`；需有 `Country,Territory,Unit,Date` 列，日期支持 `YYYY-MM-DD`、`M-YYYY`、`YYYY-MM`。Indonesia、IDN、ID 作为印尼别名匹配。其他数值列可用 `--value-column` 指定，多个地区序列用 `--territory` 选择。同月重复、多个单位或地区混合会报错。全年不足 12 个有效月份会标记不完整。年度结果是**有效月值均值**，不把异常值当绝对 CDD，也不外推未来趋势。

### 一次运行多个任务

```sh
python climate_risk.py batch --config examples/batch.json
python climate_risk.py --help
python climate_risk.py histogram --help
```

配置中的文件路径相对于配置文件本身。字段名对应命令参数，以 `_` 替代 `-`；数值列表直接写 JSON 数组。每个任务生成一个独立结果目录，遇到失败立即停止，已完成任务保留。配置示例只使用合成数据。真实文件应放在被忽略的 `data/` 目录，私人配置可使用 `local-config.json`。

## 输出和可复现性

- `report.html`：离线报告，无外部脚本、字体或统计追踪，可用浏览器打印为 PDF；表格预览最多 1000 行。
- `*.csv` / `results.json`：完整数据，CSV 使用 UTF-8 BOM，方便表格软件打开。
- `metadata.json`：版本、参数、输入文件名/大小/SHA-256、依赖版本、方法提示和 UTC 时间。
- 降水分析另外生成 `precipitation_comparison.nc` 和可选 `precipitation_comparison.png`。
- BNPB 全流程另外生成 `source_metadata.json`、`download_manifest.json`、`asset_inventory.json` 和 `downloads/` 中的原始数值栅格。资产风险矩阵直接展示各资产/图层的项目筛查等级及指数。

风险、气候变量、数据覆盖率始终分别提供。默认直方图/栅格筛查级别基于有效区域强度，`coverage_weighted_score=强度×覆盖率` 作对照；显式启用 `reference` 时区域改按该 S 评分定级。覆盖不足、无有效值或明显超过理论面积时为 `undetermined`。未知面积不叫“无风险区”。不同资产区域不合并；跨灾害汇总仅在 `inarisk --methodology reference` 启用。

BNPB 默认 index 模式的 `screening_level` 按点位指数/区域平均指数划分，默认阈值 0.33、0.66；reference 模式区域按 S 的3和7.5阈值分级。直接运行 `histogram` 默认按强度分级，`raster` 可切换 reference。所有这些级别都不是官方 BNPB 评级，不代表损失概率。危险性（BAHAYA）、脆弱性（KERENTANAN）和风险（RISIKO）在目录与报告中区分。

```sh
python -m unittest -v
```

未安装科学依赖时对应检查会明确跳过。完整安装可验证闰年、360 天日历、缺测传播、标准化边界、单位校验、字段映射、栅格坐标取样、报告转义及批量路径解析。GitHub Actions 同时检查纯标准库和完整科学依赖环境。

资产全流程检查直接使用仓库内的示例点位和区域，模拟官方目录、元数据与原始 TIFF 的接口格式，验证危险性/脆弱性/风险三层的综合结果、完整 HTML 和四组 PNG/SVG 图表，并确认缓存离线重跑分数一致。该检查使用合成数据，不证明 BNPB 在线接口当时可用；实际数据缺层时报告仍明确标为部分完成。

`requirements-lock.txt` 记录本次 Windows / Python 3.12 完整验证的精确依赖版本，可用 `python -m pip install -r requirements-lock.txt` 复现；其他环境先使用常规 `requirements.txt`。

## 整理范围和许可

旧流程到新命令的映射与不兼容修正见 [MIGRATION.md](MIGRATION.md)。第三方数据的出处和许可边界见 [DATA_SOURCES.md](DATA_SOURCES.md)。代码与合成示例采用 MIT；原始第三方数据不随本仓库分发。输出可能含你输入的地点信息和敏感边界，因此 `outputs/`、`data/`、数据库、工作簿和 GIS 大文件默认被忽略。

InaRISK 在线原始指数获取已包含在本版全流程中。ESGF 下载器、QGIS 桌面插件安装、NGFS 转型情景表格和 IEA 关键矿产行业分析保留为原项目资料，不混入物理风险分数。原始资料保持原位；本仓库只发布主脚本、文档、合成示例和检查，真实资产、缓存及下载结果不随代码发布。
