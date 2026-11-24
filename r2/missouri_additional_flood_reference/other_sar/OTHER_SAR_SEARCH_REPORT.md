# Missouri 事件：其他 SAR 与洪水产品检索记录

检索日期：2026-11-15。研究区 WGS84 bbox：[-94.1241, 36.4828, -92.5184, 37.8490]；优先时段：2025-05-23 至 2025-05-30 UTC（含首尾）。光学比较日期为 2025-05-30。目的为寻找与研究区实际重叠、日期接近且可获取像元的独立 SAR 洪水参考。当前没有取得满足条件的其他 SAR 像元，也没有产生新的 Missouri 精度统计。

## 开放商业 SAR 目录：逐场景几何核验

- [Umbra 开放数据 2025-05 静态 STAC 月目录](https://s3.us-west-2.amazonaws.com/umbra-open-data-catalog/stac/2025/2025-05/catalog.json)：8 个日期目录，逐项读取 63 条 Item，63 条成功；GeoJSON 场景多边形与上述 bbox 求交，0 条相交。数据集提供开放许可和下载，详见 [Umbra 官方说明](https://umbra.space/open-data/)。
- [Capella 开放数据 2025-05 静态 STAC 月目录](https://capella-open-data.s3.us-west-2.amazonaws.com/stac/capella-open-data-by-datetime/capella-open-data-2025/capella-open-data-2025-05/catalog.json)：区间内有 6 个日期目录列出影像，逐项读取 30 条 Item，30 条成功，0 条与 bbox 相交。产品 Item 可能是同一采集的不同产品，30 不是独立过境次数。[AWS 官方目录](https://registry.opendata.aws/capella_opendata/)标注 CC BY 4.0，公开 S3 读取无需 AWS 账号。
- 完整执行结果和代码：`open_stac_search_results.json`、`search_open_stac.py`；请求均成功、无漏读报错。JSON 原始快照为 `external/data/Geocarto_R2_20261115/raw/missouri_other_sar_stac_20261115/`，文件名为 URL 的 SHA-256，便于脚本按 URL 找回。目录内容会随提供者更新，结论仅适用于检索日期时可见的开放样本，不覆盖商业、受限或尚未开放的档案，也不排除其他时间有影像。

## NASA CMR 指定集合

使用 [NASA CMR Granule Search API](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)，bounding_box 参数为上述 bbox，temporal 为 2025-05-01T00:00:00Z 至 2025-06-30T23:59:59Z。UAVSAR PolSAR（`C4261555796-ASF`）、UAVSAR RPI（`C4261689115-ASF`）、ALOS-2 PALSAR-2 ScanSAR（`C3315903479-ASF`）各返回 0 条。移除时空条件时集合有大量索引 granule，故并非空集合。只说明上述特定集合与给定时空约束的结果为 0，不代表所有 ALOS-2、所有 UAVSAR 产品或其他平台均无影像。各次原始 JSON 保存在 `external/data/Geocarto_R2_20261115/raw/missouri_other_sar_cmr_20261115/`，控制查询及 URL 保存在 `iceye_and_cmr_manifest.json` 和相应 F 盘原始快照。

RADARSAT-2 NRCan、RADARSAT-2 ESA、ICEYE ESA 在 CMR 的三个集合未经时空筛选也均为 0 条 granule；它们的空间查询无法作为是否有数据的证据。不能据此宣称这些平台没有覆盖。

## ICEYE 历史事件线索

[ICEYE 公开历史事件点图层](https://services5.arcgis.com/LsNj2OtQESAjac8r/arcgis/rest/services/ICEYE_historic_flood_events_points_hourly/FeatureServer/0)包含 `FSD-2497`，事件名 South Central USA，记录起始 2025-05-23，区域点大致位于 (-94.0329, 35.6511)，在研究 bbox 以南。该点是区域事件点，**不是** SAR 场景边界、有效像元或洪水范围，不能据此声称覆盖研究区；点图层并未提供可用于交叉验证的水体栅格。[ICEYE 历史事件产品说明](https://www.arcgis.com/home/item.html?id=4d6d5febe4734aeba138645437e03cc4)表示洪水范围/深度数据可购买。可由用户或团队向提供方核对事件编号 FSD-2497，询问具体观测时间、footprint 是否覆盖研究区、洪水栅格及许可；目前既未获取产品，也未发送询问。

## 核验与复现

- 结果目录：`external/analysis/Geocarto_R2_20261115/missouri_flood_reference_20261115/other_sar/`。
- 原始快照目录及每份文件的 SHA-256 和字节数见 `raw_snapshot_hashes.json`。复现脚本读取在线静态 STAC 并依照真实场景 geometry 用 Shapely 与研究 bbox 求交；重复运行时如线上原始 JSON 与既有快照不一致，脚本拒绝覆盖并报告错误，应另建版本快照比较。
- 未编造结果；没有获取与事件时空匹配的可使用像元，无法根据这些目录结论增加新的洪水验证结果，也不能把以上区域事件点当作验证证据。
