import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const runRoot = String.raw`D:\MT5测试\MetaTrader 5\SingleEAReports\six_best_2015_2019_20260617`;
const csvPath = path.join(runRoot, "EA_Test_Log.csv");
const normalizedCsv = path.join(runRoot, "Six_Best_2015_2019_Normalized.csv");
const outputXlsx = path.join(runRoot, "Six_Best_2015_2019_Report.xlsx");
const previewPng = path.join(runRoot, "Six_Best_2015_2019_Report_preview.png");

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  const headers = rows.shift() ?? [];
  return rows.filter((r) => r.some((c) => c !== "")).map((r) => {
    const obj = {};
    headers.forEach((h, idx) => { obj[h] = r[idx] ?? ""; });
    return obj;
  });
}

function csvEscape(value) {
  const s = String(value ?? "");
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function toNumber(value) {
  const s = String(value ?? "").replace(/\s/g, "").replace(/,/g, "").replace("%", "");
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function ddPct(text) {
  const s = String(text ?? "");
  let m = s.match(/\(([0-9.,\s]+)%\)/);
  if (m) return toNumber(m[1]);
  m = s.match(/([0-9.,\s]+)%/);
  return m ? toNumber(m[1]) : null;
}

function riskTag(row) {
  const net = row.NetProfit;
  const pf = row.ProfitFactor;
  const dd = row.EquityDDPct;
  const trades = row.Trades;
  if (net > 0 && pf >= 1.5 && dd <= 30 && trades >= 30) return "Preferred";
  if (net > 0 && pf >= 1.15 && dd <= 40 && trades >= 15) return "Watch";
  return "Reject";
}

function score(row) {
  if (row.NetProfit <= 0 || row.ProfitFactor <= 0 || row.EquityDDPct == null || row.Trades <= 0) return -999999;
  return Number((row.ProfitFactor * Math.log(Math.max(row.Trades, 2)) + row.NetProfit / 10000 - row.EquityDDPct / 25).toFixed(6));
}

const rawRows = parseCsv(await fs.readFile(csvPath, "utf8"));
const rows = rawRows.map((r) => {
  const normalized = {
    EA: r.EA,
    SetFile: r["参数文件"],
    Symbol: r["品种"],
    Period: r["周期"],
    FromDate: r["开始日期"],
    ToDate: r["结束日期"],
    Status: r["状态"],
    NetProfit: toNumber(r["净利润"]),
    GrossProfit: toNumber(r["毛利"]),
    GrossLoss: toNumber(r["毛损"]),
    ProfitFactor: toNumber(r["盈利因子"]),
    ExpectedPayoff: toNumber(r["预期收益"]),
    MaxEquityDrawdown: r["最大净值回撤"],
    RelativeEquityDrawdown: r["相对净值回撤"],
    EquityDDPct: ddPct(r["相对净值回撤"]),
    Trades: toNumber(String(r["交易总计"]).split(" ")[0]),
    WinningTrades: r["盈利交易"],
    LosingTrades: r["亏损交易"],
    ReportPath: r["报告路径"],
    Note: r["备注"],
  };
  normalized.RiskTag = riskTag(normalized);
  normalized.RobustScore = score(normalized);
  return normalized;
});

const headers = ["EA", "SetFile", "Symbol", "Period", "FromDate", "ToDate", "Status", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "RiskTag", "RobustScore", "MaxEquityDrawdown", "RelativeEquityDrawdown", "WinningTrades", "LosingTrades", "ReportPath", "Note"];
await fs.writeFile(
  normalizedCsv,
  [headers.join(","), ...rows.map((r) => headers.map((h) => csvEscape(r[h])).join(","))].join("\n"),
  "utf8",
);

const byScore = [...rows].sort((a, b) => b.RobustScore - a.RobustScore);
const bestByEa = [];
for (const ea of [...new Set(rows.map((r) => r.EA))]) {
  bestByEa.push([...rows].filter((r) => r.EA === ea).sort((a, b) => b.RobustScore - a.RobustScore)[0]);
}
bestByEa.sort((a, b) => b.RobustScore - a.RobustScore);

const recommendations = [
  {
    Decision: "Can test live small",
    EA: "SniperTrendEA_v8.7_RiskFix",
    Period: "H4",
    Reason: "Positive in 2015-2019 with low drawdown and enough trades.",
  },
  {
    Decision: "Can test live small, lower risk",
    EA: "BBRSI-v1.6",
    Period: "H1",
    Reason: "Positive across 2015-2019 and 2020-2025, but early-period drawdown is above 30%.",
  },
  {
    Decision: "Do not prioritize",
    EA: "3MAF-v1.5",
    Period: "H4",
    Reason: "Strong in 2020-2025, but failed badly in 2015-2019.",
  },
  {
    Decision: "Reject for now",
    EA: "DHLAOS-v1.5",
    Period: "H4",
    Reason: "Positive in 2020-2025, but early-period test failed with very high drawdown.",
  },
  {
    Decision: "Reject for now",
    EA: "OmniAggressiveHedgeEngine",
    Period: "H1/H4",
    Reason: "Both periods are negative in 2015-2019.",
  },
  {
    Decision: "Reject for now",
    EA: "Vegas_Trend_Master_H4_Multi_V4.1_Optimized_FIXED",
    Period: "H1/H4",
    Reason: "Both periods are negative in 2015-2019; previous sample was too small.",
  },
];

function writeTable(sheet, startRow, startCol, tableHeaders, tableRows) {
  const matrix = [tableHeaders, ...tableRows.map((r) => tableHeaders.map((h) => r[h] ?? ""))];
  const range = sheet.getRangeByIndexes(startRow, startCol, matrix.length, tableHeaders.length);
  range.values = matrix;
  sheet.getRangeByIndexes(startRow, startCol, 1, tableHeaders.length).format = {
    fill: "#1F4E78",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
  };
  sheet.getRangeByIndexes(startRow + 1, startCol, Math.max(matrix.length - 1, 1), tableHeaders.length).format = {
    borders: { preset: "all", style: "thin", color: "#D9E2EC" },
    wrapText: true,
  };
  range.format.autofitColumns();
}

function setColumnWidths(sheet, widths) {
  widths.forEach((widthPx, colIdx) => {
    sheet.getRangeByIndexes(0, colIdx, 80, 1).format.columnWidthPx = widthPx;
  });
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
summary.getRange("A1").values = [["Six EA Historical Validation: 2015-2019"]];
summary.getRange("A1").format = { font: { bold: true, size: 16, color: "#111827" } };
summary.getRange("A3:B8").values = [
  ["Symbol", "XAUUSD"],
  ["Period tested", "2015.01.01 - 2019.12.31"],
  ["Timeframes", "H1 and H4"],
  ["Model", "0"],
  ["Tests", rows.length],
  ["Best usable rows", rows.filter((r) => r.RiskTag !== "Reject").length],
];
summary.getRange("A3:A8").format = { font: { bold: true }, fill: "#EAF2F8" };
summary.getRange("A3:B8").format = { borders: { preset: "all", style: "thin", color: "#D9E2EC" } };

summary.getRange("A10").values = [["Recommendation"]];
summary.getRange("A10").format = { font: { bold: true, size: 13 } };
writeTable(summary, 11, 0, ["Decision", "EA", "Period", "Reason"], recommendations);
setColumnWidths(summary, [300, 310, 80, 520, 120, 120, 120, 300]);
summary.getRange("A12:D18").format.rowHeightPx = 52;

summary.getRange("A21").values = [["Best row per EA in 2015-2019"]];
summary.getRange("A21").format = { font: { bold: true, size: 13 } };
writeTable(summary, 22, 0, ["EA", "Period", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "RiskTag", "SetFile"], bestByEa);
setColumnWidths(summary, [300, 310, 90, 520, 100, 75, 90, 420]);
summary.freezePanes.freezeRows(11);

const detail = workbook.worksheets.add("All_12_Tests");
detail.getRange("A1").values = [["All 2015-2019 H1/H4 tests"]];
detail.getRange("A1").format = { font: { bold: true, size: 15 } };
writeTable(detail, 2, 0, headers, byScore);
setColumnWidths(detail, [300, 430, 90, 70, 95, 95, 90, 95, 95, 95, 70, 95, 95, 140, 150, 120, 120, 460, 170]);
detail.freezePanes.freezeRows(3);

const rejected = workbook.worksheets.add("Rejected_Notes");
rejected.getRange("A1").values = [["Rejected or downgraded cases"]];
rejected.getRange("A1").format = { font: { bold: true, size: 15 } };
writeTable(rejected, 2, 0, ["EA", "Period", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "RiskTag", "SetFile"], rows.filter((r) => r.RiskTag === "Reject"));
setColumnWidths(rejected, [300, 80, 95, 95, 95, 75, 90, 430]);
rejected.freezePanes.freezeRows(3);

const preview = await workbook.render({ sheetName: "Summary", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(previewPng, new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputXlsx);

console.log(JSON.stringify({ outputXlsx, previewPng, normalizedCsv, rows: rows.length }, null, 2));
