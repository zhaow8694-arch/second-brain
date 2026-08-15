import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const runRoot = String.raw`D:\MT5测试\MetaTrader 5\SingleEAReports\top3_pf_settings_seq_20260617`;
const outputXlsx = path.join(runRoot, "Top3_EA_Best_Settings_Report.xlsx");
const previewPng = path.join(runRoot, "Top3_EA_Best_Settings_Report_preview.png");

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
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

async function readCsv(file) {
  return parseCsv(await fs.readFile(file, "utf8"));
}

function n(value) {
  const x = Number(String(value ?? "").replace(/,/g, ""));
  return Number.isFinite(x) ? x : null;
}

function rowFrom(obj, headers) {
  return headers.map((h) => {
    const v = obj[h] ?? "";
    const numeric = n(v);
    return numeric !== null && /^-?\d+(\.\d+)?$/.test(String(v)) ? numeric : v;
  });
}

function writeSheet(sheet, headers, rows, opts = {}) {
  const title = opts.title ?? sheet.name;
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1").format = {
    font: { bold: true, size: 15, color: "#111827" },
  };
  const table = [headers, ...rows.map((r) => rowFrom(r, headers))];
  const range = sheet.getRangeByIndexes(2, 0, table.length, headers.length);
  range.values = table;
  sheet.getRangeByIndexes(2, 0, 1, headers.length).format = {
    fill: "#1F4E78",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
  };
  sheet.getRangeByIndexes(3, 0, Math.max(table.length - 1, 1), headers.length).format = {
    borders: { preset: "all", style: "thin", color: "#D9E2EC" },
    wrapText: true,
  };
  sheet.getRangeByIndexes(2, 0, table.length, headers.length).format.autofitColumns();
  sheet.freezePanes.freezeRows(3);
}

const validation = await readCsv(path.join(runRoot, "Top3_SequentialSweep_ValidatedSettings.csv"));
const sweep = await readCsv(path.join(runRoot, "Top3_SequentialSweep_2025.csv"));
const selected = await readCsv(path.join(runRoot, "Top3_SequentialSweep_SelectedForValidation.csv"));

const usable = validation.filter((r) => ["Preferred", "Watch", "HighRisk"].includes(r.RiskTag));
const bestByEa = [
  validation.find((r) => r.EA === "BBRSI-v1.6" && r.Period === "H1" && r.CandidateId === "01"),
  validation.find((r) => r.EA === "3MAF-v1.5" && r.Period === "H4" && r.CandidateId === "02"),
  validation.find((r) => r.EA === "DHLAOS-v1.5" && r.Period === "H4" && r.CandidateId === "01"),
].filter(Boolean);

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
summary.getRange("A1").values = [["Top 3 EA Best Settings"]];
summary.getRange("A1").format = { font: { bold: true, size: 16, color: "#111827" } };
summary.getRange("A3:B8").values = [
  ["Symbol", "XAUUSD"],
  ["Sweep period", "2025.01.01 - 2025.12.31"],
  ["Validation period", "2020.01.01 - 2025.12.31"],
  ["Model", "0"],
  ["Sweep rows", sweep.length],
  ["Validated rows", validation.length],
];
summary.getRange("A3:A8").format = { font: { bold: true }, fill: "#EAF2F8" };
summary.getRange("A3:B8").format = { borders: { preset: "all", style: "thin", color: "#D9E2EC" } };

const recHeaders = ["Rank", "EA", "UsePeriod", "CandidateId", "RiskTag", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "Parameters", "SetArchivePath"];
const recRows = bestByEa.map((r, idx) => ({
  Rank: idx + 1,
  EA: r.EA,
  UsePeriod: r.Period,
  CandidateId: r.CandidateId,
  RiskTag: r.RiskTag,
  NetProfit: r.NetProfit,
  ProfitFactor: r.ProfitFactor,
  EquityDDPct: r.EquityDDPct,
  Trades: r.Trades,
  Parameters: r.Parameters || "default",
  SetArchivePath: r.SetArchivePath,
}));
summary.getRange("A11").values = [["Recommended settings after 2020-2025 validation"]];
summary.getRange("A11").format = { font: { bold: true, size: 13, color: "#111827" } };
summary.getRangeByIndexes(12, 0, recRows.length + 1, recHeaders.length).values = [
  recHeaders,
  ...recRows.map((r) => rowFrom(r, recHeaders)),
];
summary.getRangeByIndexes(12, 0, 1, recHeaders.length).format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
};
summary.getRangeByIndexes(13, 0, recRows.length, recHeaders.length).format = {
  borders: { preset: "all", style: "thin", color: "#D9E2EC" },
  wrapText: true,
};
summary.getRange("A21").values = [["Interpretation"]];
summary.getRange("A21").format = { font: { bold: true, size: 13 } };
summary.getRange("A22:B26").values = [
  ["Preferred", "Profit, PF, drawdown and trade count passed the validation filter."],
  ["Watch", "Profitable but drawdown is above preferred range; observe only or reduce risk."],
  ["HighRisk", "Profitable but low sample or weaker filter result; not a primary setting."],
  ["Reject", "Failed long-period validation or risk filters."],
  ["Note", "Do not choose by 2025 profit factor alone; long-period validation is the anti-overfit check."],
];
summary.getRange("A22:A26").format = { font: { bold: true }, fill: "#F2F6FA" };
summary.getRange("A22:B26").format = { borders: { preset: "all", style: "thin", color: "#D9E2EC" }, wrapText: true };
summary.getRange("A1:K26").format.autofitColumns();
summary.freezePanes.freezeRows(12);

const best = workbook.worksheets.add("Best_By_EA");
writeSheet(best, recHeaders, recRows, { title: "Best setting selected for each EA" });

const valSheet = workbook.worksheets.add("Validation_2020_2025");
const valHeaders = ["EA", "Period", "CandidateId", "RiskTag", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "RobustScore", "Parameters", "SetFile", "SetArchivePath", "ReportPath"];
writeSheet(valSheet, valHeaders, validation.sort((a, b) => (n(b.RobustScore) ?? -999999) - (n(a.RobustScore) ?? -999999)), { title: "2020-2025 validation results" });

const sweepSheet = workbook.worksheets.add("Sweep_2025");
const sweepHeaders = ["EA", "Period", "CandidateId", "NetProfit", "ProfitFactor", "EquityDDPct", "Trades", "RobustScore", "Parameters", "SetFile", "ReportPath"];
writeSheet(sweepSheet, sweepHeaders, sweep, { title: "2025 sequential parameter sweep" });

const selectedSheet = workbook.worksheets.add("Selected_For_Validation");
writeSheet(selectedSheet, sweepHeaders, selected, { title: "Candidates selected for 2020-2025 validation" });

const preview = await workbook.render({ sheetName: "Summary", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(previewPng, new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputXlsx);

console.log(JSON.stringify({ outputXlsx, previewPng, validationRows: validation.length, sweepRows: sweep.length }, null, 2));
