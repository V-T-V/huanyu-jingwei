/* ═══════════ 寰宇经纬 · 展示配置（道设色 / 底图） ═══════════
   解析数据在 data/site_data.js（build_data.py 生成）；本文件为人工整编展示层。 */

/* 十三道设色（+四夷） */
const DAOCOLORS = {
  henan: "#a0772f", guanxi: "#8a6a9e", hedong: "#9c4a3c", hebei: "#7d5530",
  jiannanxi: "#2f5d70", jiannandong: "#3d7a72", jiangnandong: "#4a7a9b",
  jiangnanxi: "#5a8368", huainan: "#b23a2e", shannanxi: "#6b7f3f",
  shannandong: "#33658a", longyou: "#845b8f", lingnan: "#4f7d5c", siyi: "#8b8069",
};

const DAO_NOTE = {
  yutu: "十三道 · 州治点织 · zoom≥6 县微点（附郭+方位里程三角化推算）",
  fen: "道 → 州名录 → 原卷全文 · 懒加载分片",
  duizhao: "宋府州 ×《读史方舆纪要》明府属州 · 三重证据匹配 · ↗方舆深链",
  about: "数据源流 · 存佚如实 · 校勘约定",
};

/* 底图 */
const BASEMAPS = {
  physical: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
    maxNative: 8, maxZoom: 10, attr: "Esri",
  },
};

const CONF = {
  bounds: [[16, 88], [46, 132]],
  center: [34.0, 112.5],
  zoom: 5,
};
