# 数据来源与分发边界

本仓库仅分发代码与人工构造的合成示例。用户自行获取的数据及生成的真实报告不适用本仓库的 MIT 许可，不随代码公开。

| 数据体系 | 官方入口 | 本工具使用方式 |
|---|---|---|
| BNPB InaRISK | https://inarisk.bnpb.go.id/ | 全流程从官方 REST 服务发现并按资产范围下载原始指数，也支持用户本地栅格/区域直方图 |
| BNPB REST 目录 | https://gis.bnpb.go.id/server/rest/services/inarisk | 目录和元数据发现；保留服务名称、类型、获取时间与原始响应 |
| 当前官网图层配置 | https://inarisk.bnpb.go.id/v4/config/arcgis-layers.json | 用于核对官网使用的主机与展示服务；渲染服务不能直接替代原始数值指数 |
| 洪水原始危险性指数 | https://gis.bnpb.go.id/server/rest/services/inarisk/INDEKS_BAHAYA_BANJIR/ImageServer | 已在线验证单波段 F32、100 米、0–1 指数以及 None 渲染 TIFF 导出 |
| ArcGIS exportImage 官方文档 | https://developers.arcgis.com/rest/services-reference/enterprise/export-image/ | 原生坐标系与尺寸、F32 TIFF、None 渲染、最近邻插值的请求设置 |
| Esri World Imagery | https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer | 可选真实卫星/航空影像拼接底图；保留服务署名及导出地理范围，不从影像颜色反演风险，不将拍摄日期认定为获取日期 |
| WRI Aqueduct 4.0 | https://www.wri.org/data/aqueduct-global-maps-40-data | 读取用户下载的原始字段，保留指标含义和标签 |
| WRI 数据字典 | https://github.com/wri/Aqueduct40/blob/master/data_dictionary_water-risk-atlas.md | 核对基线/未来字段定义；该字典说明数据为 CC BY 4.0，实际分发时应按来源要求署名 |
| CMIP6 / ESGF | https://esgf.llnl.gov/ | 用户本地的 CF 格式降水 NetCDF；模式、实验、成员和许可随原始数据而定 |
| IEA Weather for Energy Tracker | https://www.iea.org/data-and-statistics/data-tools/weather-for-energy-tracker | 用户提供的国家级月度 CDD/异常值 CSV；原始序列定义与许可应从下载来源核实 |

WRI 建议引用：Kuzma, S., et al. 2023. *Aqueduct 4.0: Updated Decision-Relevant Global Water Risk Indicators*. World Resources Institute. https://doi.org/10.46830/writn.23.00061

官方接口核对日期：2026-10-17。`catalog` 和 `inarisk` 在线模式需要连接 BNPB；已有完整缓存时 `--offline` 可无网络运行。其他本地分析命令不联网。在线导出请求会传输资产范围，不上传资产文件或名称。InaRISK 渲染图服务显示的颜色与灰度不自动等于可分析的原始风险指数。原始数据许可仍由提供方决定；可访问不代表可随代码再分发。单一 CMIP6 模式/情景结果也不能代表多模式不确定性。
