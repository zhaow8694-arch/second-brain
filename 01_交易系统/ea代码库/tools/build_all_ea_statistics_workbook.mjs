import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const reportsRoot = String.raw`D:\MT5测试\MetaTrader 5\SingleEAReports`;
const outputDir = path.join(reportsRoot, "_AllEAStatistics_20260617");
const outputXlsx = path.join(outputDir, "All_EA_Test_Statistics_20260617.xlsx");
const previewPng = path.join(outputDir, "All_EA_Test_Statistics_20260617_preview.png");
const normalizedCsv = path.join(outputDir, "All_EA_Test_Statistics_20260617_Normalized.csv");

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
  return rows.filter((r) => r.some((c) => c !== ""));
}

function csvEscape(value) {
  const s = String(value ?? "");
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function toNumber(value) {
  const s = String(value ?? "").replace(/\s/g, "").replace(/,/g, "").replace("%", "");
  if (!s || s === "∞" || s.toLowerCase() === "inf") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function pctFromText(text) {
  const s = String(text ?? "");
  const m = s.match(/([0-9.,\s]+)%/);
  return m ? toNumber(m[1]) : null;
}

function tradeCount(text) {
  const s = String(text ?? "").trim();
  const m = s.match(/^([0-9\s,]+)/);
  return m ? toNumber(m[1]) : null;
}

function winRate(text) {
  return pctFromText(text);
}

function isCompleted(status) {
  return String(status ?? "").includes("完成");
}

function riskTag(row) {
  if (!isCompleted(row.Status)) return "NoReport";
  if (row.NetProfit == null || row.NetProfit <= 0) return "Reject";
  if ((row.Trades ?? 0) < 20 && (row.ProfitFactor ?? 0) >= 1.15) return "LowSample";
  if ((row.ProfitFactor ?? 0) >= 2.0 && (row.EquityDDPct ?? 999) <= 15 && (row.Trades ?? 0) >= 20) return "Strong";
  if ((row.ProfitFactor ?? 0) >= 1.5 && (row.EquityDDPct ?? 999) <= 30 && (row.Trades ?? 0) >= 25) return "Good";
  if ((row.ProfitFactor ?? 0) >= 1.15 && (row.EquityDDPct ?? 999) <= 40 && (row.Trades ?? 0) >= 20) return "Watch";
  return "Reject";
}

function robustScore(row) {
  if (!isCompleted(row.Status) || row.NetProfit == null || row.ProfitFactor == null || row.EquityDDPct == null || row.Trades == null) return -999999;
  if (row.NetProfit <= 0 || row.ProfitFactor <= 0 || row.Trades <= 0) return -999999;
  const cappedPf = Math.min(row.ProfitFactor, 5);
  const tradeWeight = Math.log(Math.max(row.Trades, 2));
  const lowSamplePenalty = row.Trades < 20 ? 5 + (20 - row.Trades) * 0.25 : 0;
  const highDdPenalty = row.EquityDDPct > 40 ? 5 : 0;
  const score = cappedPf * tradeWeight + row.NetProfit / 10000 - row.EquityDDPct / 15 - lowSamplePenalty - highDdPenalty;
  return Number(score.toFixed(6));
}

async function walk(dir) {
  const out = [];
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "_AllEAStatistics_20260617") continue;
      out.push(...await walk(full));
    } else if (entry.isFile() && entry.name === "EA_Test_Log.csv") {
      out.push(full);
    }
  }
  return out;
}

function runNameFromLog(logPath) {
  return path.basename(path.dirname(logPath));
}

function rowFromCells(cells, logPath, indexInLog) {
  const row = {
    SourceLog: logPath,
    RunName: runNameFromLog(logPath),
    RowInLog: indexInLog,
    TestTime: cells[0] ?? "",
    EA: cells[1] ?? "",
    SetFile: cells[2] ?? "",
    Symbol: cells[3] ?? "",
    Period: cells[4] ?? "",
    FromDate: cells[5] ?? "",
    ToDate: cells[6] ?? "",
    Status: cells[7] ?? "",
    NetProfit: toNumber(cells[8]),
    GrossProfit: toNumber(cells[9]),
    GrossLoss: toNumber(cells[10]),
    ProfitFactor: toNumber(cells[11]),
    ExpectedPayoff: toNumber(cells[12]),
    MaxEquityDrawdown: cells[13] ?? "",
    RelativeEquityDrawdown: cells[14] ?? "",
    EquityDDPct: pctFromText(cells[14]),
    Trades: tradeCount(cells[15]),
    WinningTrades: cells[16] ?? "",
    WinRatePct: winRate(cells[16]),
    LosingTrades: cells[17] ?? "",
    MaxWinTrade: toNumber(cells[18]),
    MaxLossTrade: toNumber(cells[19]),
    AvgWinTrade: toNumber(cells[20]),
    AvgLossTrade: toNumber(cells[21]),
    ReportPath: cells[22] ?? "",
    Note: cells[23] ?? "",
  };
  row.DateRange = `${row.FromDate}-${row.ToDate}`;
  row.RiskTag = riskTag(row);
  row.RobustScore = robustScore(row);
  return row;
}

function bestBy(rows, keyFn, sortFn) {
  const map = new Map();
  for (const row of rows) {
    const key = keyFn(row);
    const prev = map.get(key);
    if (!prev || sortFn(row, prev) < 0) map.set(key, row);
  }
  return [...map.values()];
}

function avg(nums) {
  const clean = nums.filter((n) => typeof n === "number" && Number.isFinite(n));
  if (!clean.length) return null;
  return Number((clean.reduce((a, b) => a + b, 0) / clean.length).toFixed(4));
}

function joinUnique(values, max = 8) {
  const unique = [...new Set(values.filter(Boolean))];
  const shown = unique.slice(0, max).join("; ");
  return unique.length > max ? `${shown}; +${unique.length - max} more` : shown;
}

function recommendation(row) {
  if (!row) return "";
  if (row.RiskTag === "Strong") return "Priority";
  if (row.RiskTag === "Good") return "Candidate";
  if (row.RiskTag === "Watch" || row.RiskTag === "LowSample") return "Observe";
  return "Reject";
}

function writeTable(sheet, startRow, startCol, headers, rows) {
  const matrix = [headers, ...rows.map((row) => headers.map((h) => row[h] ?? ""))];
  const range = sheet.getRangeByIndexes(startRow, startCol, matrix.length, headers.length);
  range.values = matrix;
  sheet.getRangeByIndexes(startRow, startCol, 1, headers.length).format = {
    fill: "#1F4E78",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
  };
  if (matrix.length > 1) {
    sheet.getRangeByIndexes(startRow + 1, startCol, matrix.length - 1, headers.length).format = {
      borders: { preset: "all", style: "thin", color: "#D9E2EC" },
      wrapText: false,
    };
  }
  try {
    const endRow = startRow + matrix.length - 1;
    const endCol = String.fromCharCode("A".charCodeAt(0) + startCol + headers.length - 1);
    const startColLetter = String.fromCharCode("A".charCodeAt(0) + startCol);
    if (headers.length <= 26) sheet.tables.add(`${startColLetter}${startRow + 1}:${endCol}${endRow + 1}`, true);
  } catch {
    // Table creation is cosmetic; ranges remain fully populated.
  }
  return range;
}

function setColumnWidths(sheet, widths, rows = 800) {
  widths.forEach((widthPx, colIdx) => {
    sheet.getRangeByIndexes(0, colIdx, rows, 1).format.columnWidthPx = widthPx;
  });
}

const logs = (await walk(reportsRoot)).sort();
const allRows = [];
const runIndex = [];

for (const log of logs) {
  const text = await fs.readFile(log, "utf8");
  const parsed = parseCsv(text);
  const dataRows = parsed.slice(1);
  let added = 0;
  dataRows.forEach((cells, idx) => {
    if (!cells.some((c) => String(c ?? "").trim())) return;
    allRows.push(rowFromCells(cells, log, idx + 1));
    added += 1;
  });
  const stat = await fs.stat(log);
  runIndex.push({
    RunName: runNameFromLog(log),
    Rows: added,
    SourceLog: log,
    LastWriteTime: stat.mtime.toISOString().replace("T", " ").slice(0, 19),
  });
}

const detailHeaders = [
  "RunName", "EA", "SetFile", "Symbol", "Period", "FromDate", "ToDate", "DateRange", "Status",
  "NetProfit", "GrossProfit", "GrossLoss", "ProfitFactor", "ExpectedPayoff",
  "EquityDDPct", "Trades", "WinRatePct", "RiskTag", "RobustScore",
  "MaxEquityDrawdown", "RelativeEquityDrawdown", "WinningTrades", "LosingTrades",
  "MaxWinTrade", "MaxLossTrade", "AvgWinTrade", "AvgLossTrade", "ReportPath", "Note", "SourceLog",
];

const completedRows = allRows.filter((r) => isCompleted(r.Status));
const positiveRows = completedRows.filter((r) => (r.NetProfit ?? 0) > 0);
const uniqueEAs = [...new Set(allRows.map((r) => r.EA).filter(Boolean))].sort();
const uniqueRuns = [...new Set(allRows.map((r) => r.RunName).filter(Boolean))].sort();

const topRows = [...completedRows]
  .filter((r) => (r.NetProfit ?? 0) > 0)
  .filter((r) => ["Strong", "Good", "Watch"].includes(r.RiskTag))
  .sort((a, b) => b.RobustScore - a.RobustScore)
  .slice(0, 25);

const bestRowsByEA = bestBy(
  completedRows,
  (r) => r.EA,
  (a, b) => b.RobustScore - a.RobustScore,
).sort((a, b) => b.RobustScore - a.RobustScore);

const summaryByEA = uniqueEAs.map((ea) => {
  const rows = allRows.filter((r) => r.EA === ea);
  const done = rows.filter((r) => isCompleted(r.Status));
  const pos = done.filter((r) => (r.NetProfit ?? 0) > 0);
  const bestScore = bestRowsByEA.find((r) => r.EA === ea);
  const bestNet = [...done].sort((a, b) => (b.NetProfit ?? -999999) - (a.NetProfit ?? -999999))[0];
  return {
    EA: ea,
    Tests: rows.length,
    Completed: done.length,
    PositiveRows: pos.length,
    PositiveRate: done.length ? Number((pos.length / done.length).toFixed(4)) : null,
    BestScore: bestScore?.RobustScore ?? null,
    BestScoreTag: bestScore?.RiskTag ?? "",
    BestScorePeriod: bestScore?.Period ?? "",
    BestScoreRange: bestScore?.DateRange ?? "",
    BestScoreNetProfit: bestScore?.NetProfit ?? null,
    BestScorePF: bestScore?.ProfitFactor ?? null,
    BestScoreDDPct: bestScore?.EquityDDPct ?? null,
    BestScoreTrades: bestScore?.Trades ?? null,
    BestNetProfit: bestNet?.NetProfit ?? null,
    AvgProfitFactor: avg(done.map((r) => r.ProfitFactor)),
    WorstDDPct: Math.max(...done.map((r) => r.EquityDDPct ?? 0)),
    Periods: joinUnique(rows.map((r) => r.Period), 6),
    DateRanges: joinUnique(rows.map((r) => r.DateRange), 6),
    Recommendation: recommendation(bestScore),
  };
}).sort((a, b) => (b.BestScore ?? -999999) - (a.BestScore ?? -999999));

await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(
  normalizedCsv,
  [detailHeaders.join(","), ...allRows.map((row) => detailHeaders.map((h) => csvEscape(row[h])).join(","))].join("\n"),
  "utf8",
);

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
dashboard.showGridLines = false;
dashboard.getRange("A1").values = [["All EA Test Statistics"]];
dashboard.getRange("A1").format = { font: { bold: true, size: 18, color: "#111827" } };
dashboard.getRange("A3:B11").values = [
  ["Total rows", allRows.length],
  ["Completed rows", completedRows.length],
  ["Positive rows", positiveRows.length],
  ["Unique EAs", uniqueEAs.length],
  ["Run batches", uniqueRuns.length],
  ["Strong rows", allRows.filter((r) => r.RiskTag === "Strong").length],
  ["Good rows", allRows.filter((r) => r.RiskTag === "Good").length],
  ["Watch rows", allRows.filter((r) => r.RiskTag === "Watch").length],
  ["Generated", new Date().toISOString().replace("T", " ").slice(0, 19)],
];
dashboard.getRange("A3:A11").format = { fill: "#EAF2F8", font: { bold: true } };
dashboard.getRange("A3:B11").format = { borders: { preset: "all", style: "thin", color: "#D9E2EC" } };
dashboard.getRange("A13").values = [["Top rows by robust score"]];
dashboard.getRange("A13").format = { font: { bold: true, size: 13 } };
writeTable(dashboard, 14, 0, ["EA", "SetFile", "Symbol", "Period", "DateRange", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "RiskTag", "RobustScore", "RunName"], topRows);
setColumnWidths(dashboard, [300, 420, 90, 70, 190, 95, 95, 95, 70, 90, 95, 300], 80);
dashboard.freezePanes.freezeRows(14);

const allSheet = workbook.worksheets.add("All_Tests");
allSheet.getRange("A1").values = [["All normalized test rows"]];
allSheet.getRange("A1").format = { font: { bold: true, size: 15 } };
writeTable(allSheet, 2, 0, detailHeaders, allRows);
setColumnWidths(allSheet, [280, 300, 420, 90, 70, 95, 95, 190, 95, 95, 95, 95, 95, 95, 95, 70, 85, 90, 95, 145, 155, 120, 120, 95, 95, 95, 95, 520, 320, 520], allRows.length + 5);
allSheet.freezePanes.freezeRows(3);

const bestSheet = workbook.worksheets.add("Best_By_EA");
bestSheet.getRange("A1").values = [["Best single row per EA by robust score"]];
bestSheet.getRange("A1").format = { font: { bold: true, size: 15 } };
writeTable(bestSheet, 2, 0, ["EA", "SetFile", "Symbol", "Period", "DateRange", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "WinRatePct", "RiskTag", "RobustScore", "RunName", "ReportPath"], bestRowsByEA);
setColumnWidths(bestSheet, [310, 420, 90, 70, 190, 95, 95, 95, 70, 85, 90, 95, 300, 520], bestRowsByEA.length + 5);
bestSheet.freezePanes.freezeRows(3);

const eaSheet = workbook.worksheets.add("EA_Summary");
eaSheet.getRange("A1").values = [["EA-level summary"]];
eaSheet.getRange("A1").format = { font: { bold: true, size: 15 } };
writeTable(eaSheet, 2, 0, ["EA", "Tests", "Completed", "PositiveRows", "PositiveRate", "BestScore", "BestScoreTag", "BestScorePeriod", "BestScoreRange", "BestScoreNetProfit", "BestScorePF", "BestScoreDDPct", "BestScoreTrades", "BestNetProfit", "AvgProfitFactor", "WorstDDPct", "Periods", "DateRanges", "Recommendation"], summaryByEA);
setColumnWidths(eaSheet, [310, 70, 80, 90, 90, 90, 100, 90, 190, 115, 95, 105, 90, 110, 100, 100, 130, 360, 110], summaryByEA.length + 5);
eaSheet.freezePanes.freezeRows(3);

const runSheet = workbook.worksheets.add("Run_Index");
runSheet.getRange("A1").values = [["Source log index"]];
runSheet.getRange("A1").format = { font: { bold: true, size: 15 } };
writeTable(runSheet, 2, 0, ["RunName", "Rows", "LastWriteTime", "SourceLog"], runIndex);
setColumnWidths(runSheet, [360, 80, 160, 620], runIndex.length + 5);
runSheet.freezePanes.freezeRows(3);

const preview = await workbook.render({ sheetName: "Dashboard", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(previewPng, new Uint8Array(await preview.arrayBuffer()));

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputXlsx);

console.log(JSON.stringify({
  outputXlsx,
  previewPng,
  normalizedCsv,
  logs: logs.length,
  rows: allRows.length,
  completed: completedRows.length,
  uniqueEAs: uniqueEAs.length,
}, null, 2));
