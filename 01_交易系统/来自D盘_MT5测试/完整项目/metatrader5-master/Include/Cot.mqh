//+------------------------------------------------------------------+
//|                                                          Cot.mqh |
//|                                     Copyright 2024-2025, Geraked |
//|                                       https://github.com/geraked |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024-2025, Geraked"
#property link      "https://github.com/geraked"
#property version   "1.1"

#include <WinINet.mqh>
#include <SysTime.mqh>
#include <Shell.mqh>
#include <Storage.mqh>

#define COT_APP_TOKEN          ""
#define COT_DB_PATH            "Geraked\\cot.db"
#define COT_DB_CO_PATH         "Geraked\\cot-co.db"
#define COT_DIR_PATH           "Geraked\\cot\\"
#define COT_INIT_TIMEOUT_MINS  1

// Use major currencies only
#define COT_USE_CO      true
#define COT_CURRENCIES  "'232741','099741','096742','112741','090741','092741','097741','098662'"

enum ENUM_COT_REPORT {
    COT_REPORT_L = 1, // Legacy Futures Only Report
    COT_REPORT_LC, // Legacy Combined Report
    COT_REPORT_T, // TFF Futures Only Report
    COT_REPORT_TC, // TFF Combined Report
    COT_REPORT_D, // Disaggregated Futures Only Report
    COT_REPORT_DC, // Disaggregated Combined Report
    COT_REPORT_S // Supplemental Report
};

enum ENUM_COT_CLASS {
    COT_CLASS_COM = 1, // Commercial
    COT_CLASS_NCOM, // Non-Commercial
    COT_CLASS_NR, // Non-Reportables
    COT_CLASS_DEALER, // Dealer/Intermediary
    COT_CLASS_ASSET, // Asset Manager/Institutional
    COT_CLASS_LEV, // Leveraged Funds
    COT_CLASS_ORT, // Other Reportables (TFF)
    COT_CLASS_PM, // Producer/Merchant/Processor/User
    COT_CLASS_SD, // Swap Dealers
    COT_CLASS_MM, // Managed Money
    COT_CLASS_ORD, // Other Reportables (Disaggregated)
    COT_CLASS_IT // Index Traders
};

enum ENUM_COT_REPORT_CO {
    COT_REPORT_CO_L = 1, // Legacy Futures Only Report
    COT_REPORT_CO_LC, // Legacy Combined Report
    COT_REPORT_CO_T, // TFF Futures Only Report
    COT_REPORT_CO_TC // TFF Combined Report
};

enum ENUM_COT_CLASS_CO {
    COT_CLASS_CO_COM = 1, // Commercial
    COT_CLASS_CO_NCOM, // Non-Commercial
    COT_CLASS_CO_NR, // Non-Reportables
    COT_CLASS_CO_DEALER, // Dealer/Intermediary
    COT_CLASS_CO_ASSET, // Asset Manager/Institutional
    COT_CLASS_CO_LEV, // Leveraged Funds
    COT_CLASS_CO_ORT // Other Reportables
};

enum ENUM_COT_MODE {
    COT_MODE_COP, // Futures & Options Combined
    COT_MODE_FO // Futures Only
};

//+------------------------------------------------------------------+
//| Necessary to call in 'OnInit' function before using COT lib.     |
//+------------------------------------------------------------------+
bool CotInit(ENUM_COT_REPORT report_type, datetime start_date = 0, bool print_logs = true) {
    if (!IsWindows()) {
        Print("Error: The COT library can only be used on the Windows operating system.");
        return false;
    }

    if (MQLInfoInteger(MQL_OPTIMIZATION)) {
        Print("Error: The COT library cannot be used in optimization mode.");
        return false;
    }

    string rt = (string)((int) report_type);
    string k_running = "cot_init_running_" + rt;
    string k_year = "cot_init_year_" + rt;
    string k_status = "cot_init_status_" + rt;

    bool running, timeout;
    do {
        if (IsStopped()) return false;
        Sleep(500);
        running = ((bool) StorageGet(k_running, 0)) || ((bool) GlobalVariableGet(k_running));
        timeout = (TimeSystem() - StorageLastUpdate(k_running)) > 60 * COT_INIT_TIMEOUT_MINS;
    } while(running && !timeout);

    GlobalVariableSet(k_running, 1);
    StorageSet(k_running, 1);

    MqlDateTime oldbar_dts, stime_dts;
    datetime oldbar_dt;
    if (start_date == 0) {
        int bars = iBars(NULL, 0);
        if (bars < 1) {
            oldbar_dt = D'2011.01.01';
        } else {
            oldbar_dt = iTime(NULL, 0, bars - 1);
            if (oldbar_dt <= 0)
                oldbar_dt = D'2011.01.01';
        }
    } else {
        oldbar_dt = start_date;
    }
    TimeToStruct(oldbar_dt, oldbar_dts);
    datetime stime = TimeSystem(stime_dts);
    int start_year = MathMax(2011, oldbar_dts.year);
    int end_year = stime_dts.year;

    int year = StorageGet(k_year, end_year + 1);
    int status = StorageGet(k_status, 0);
    timeout = (TimeSystem() - StorageLastUpdate(k_status)) > 60 * COT_INIT_TIMEOUT_MINS;

    if (start_year >= year && !timeout && status > 0) {
        StorageSet(k_running, 0);
        GlobalVariableDel(k_running);
        if (status == 1)
            return true;
        else
            return false;
    }

    StorageSet(k_year, start_year);
    if (print_logs)
        PrintFormat("CotInit (%s) started...", rt);

    MqlDateTime t_dts;
    datetime date_from, date_to;
    datetime time = StringToTime(StringFormat("%d.01.01", start_year));
    CotGetDateRange(time, date_from, date_to);

    for (datetime t = date_from; t <= stime; t += 7 * PeriodSeconds(PERIOD_D1)) {
        if (IsStopped()) {
            StorageSet(k_status, 0);
            StorageSet(k_running, 0);
            GlobalVariableDel(k_running);
            return false;
        }

        if (!CotIsAvailable(report_type, t, true)) {
            if (stime - t <= 7 * PeriodSeconds(PERIOD_D1))
                continue;
            TimeToStruct(t, t_dts);
            if (t_dts.mon == 12 && t_dts.day > 19)
                continue;
            if (IsStopped()) {
                StorageSet(k_status, 0);
                StorageSet(k_running, 0);
                GlobalVariableDel(k_running);
                return false;
            }
            PrintFormat("CotInit (%s) failed: %s", rt, TimeToString(t, TIME_DATE));
            PrintFormat("Try again %d minutes later.", COT_INIT_TIMEOUT_MINS);
            StorageSet(k_status, 2);
            StorageSet(k_running, 0);
            GlobalVariableDel(k_running);
            return false;
        }
    }

    if (print_logs)
        PrintFormat("CotInit (%s) successfully ended.", rt);
    StorageSet(k_status, 1);
    StorageSet(k_running, 0);
    GlobalVariableDel(k_running);
    return true;
}

//+------------------------------------------------------------------+
//| Check if COT report is available in DB.                          |
//+------------------------------------------------------------------+
bool CotIsAvailable(ENUM_COT_REPORT report_type, datetime time = 0, bool force_retrieve = false) {
    if (time == 0) time = TimeCurrent();
    datetime date_from, date_to;
    MqlDateTime dts_from, dts_to;
    CotGetDateRange(time, date_from, date_to);
    TimeToStruct(date_from, dts_from);
    TimeToStruct(date_to, dts_to);

    int db, dp, t;
    string sql;
    string table = CotGetTableName(report_type);
    db = CotInitDb();
    if (db == INVALID_HANDLE) return false;

    sql = StringFormat("SELECT EXISTS (SELECT 1 FROM %s WHERE date >= %d AND date < %d AND rid=%d", table, date_from, date_to, report_type);
    if (COT_USE_CO) sql += StringFormat(" AND cid IN (%s)", COT_CURRENCIES);
    sql += " LIMIT 1)";
    dp = DatabasePrepare(db, sql);
    DatabaseRead(dp);
    DatabaseColumnInteger(dp, 0, t);
    DatabaseFinalize(dp);
    DatabaseClose(db);
    if (t) return true;

    if (!force_retrieve && MQLInfoInteger(MQL_TESTER))
        return false;

    if (!force_retrieve && !MQLInfoInteger(MQL_TESTER) && MathAbs(TimeSystem() - time) > 30 * PeriodSeconds(PERIOD_D1))
        return false;

    if (IsStopped()) return false;

    WininetRequest req;
    WininetResponse res;
    string date_from_str = TimeToString(date_from, TIME_DATE);
    string date_to_str = TimeToString(date_to, TIME_DATE);
    StringReplace(date_from_str, ".", "-");
    StringReplace(date_to_str, ".", "-");
    string query = StringFormat("SELECT 1 WHERE `report_date_as_yyyy_mm_dd` >= '%s' "
                                "AND `report_date_as_yyyy_mm_dd` < '%s'",
                                date_from_str, date_to_str);
    if (COT_USE_CO) query += StringFormat(" AND cftc_contract_market_code IN (%s)", COT_CURRENCIES);
    query += " LIMIT 1";
    req.host = "publicreporting.cftc.gov";
    req.path = "/resource/" + cotGetRequestId(report_type) + ".csv" + "?$query=" + query;
    if (COT_APP_TOKEN != "")
        req.headers = StringFormat("X-App-Token: %s\r\n", COT_APP_TOKEN);
    WebReq(req, res);
    if (res.status != 200) {
        PrintFormat("CotIsAvailable request failed! (status=%d, rt=%d, df=%s, dt=%s)", res.status, report_type, date_from_str, date_to_str);
        return false;
    }

    string ds[];
    string data = res.GetDataStr();
    StringTrimLeft(data);
    int n = StringSplit(data, '\n', ds);
    if (n < 2) return false;
    StringReplace(ds[1], "\"", "");
    StringReplace(ds[1], "'", "");
    StringTrimLeft(ds[1]);
    StringTrimRight(ds[1]);
    if (ds[1] != "1") return false;

    string fp1 = cotGetCsvFilePath(report_type, dts_from.year);
    string fp2 = cotGetCsvFilePath(report_type, dts_to.year);
    if (FileIsExist(fp1, FILE_COMMON)) {
        if (!FileDelete(fp1, FILE_COMMON)) {
            PrintFormat("Error (%s, FileDelete): #%d", __FUNCTION__, GetLastError());
            return false;
        }
    }
    if (!cotReadReport(report_type, dts_from.year))
        return false;
    if (fp1 != fp2) {
        if (FileIsExist(fp2, FILE_COMMON)) {
            if (!FileDelete(fp2, FILE_COMMON)) {
                PrintFormat("Error (%s, FileDelete): #%d", __FUNCTION__, GetLastError());
                return false;
            }
        }
        if (!cotReadReport(report_type, dts_to.year))
            return false;
    }

    if (IsStopped()) return false;

    db = CotInitDb();
    if (db == INVALID_HANDLE) return false;

    dp = DatabasePrepare(db, sql);
    DatabaseRead(dp);
    DatabaseColumnInteger(dp, 0, t);
    DatabaseFinalize(dp);
    DatabaseClose(db);
    if (!t) {
        PrintFormat("Warning: COT is not available! (rt=%d, df=%s, dt=%s)", report_type, date_from_str, date_to_str);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Find the correct date range for COT.                             |
//+------------------------------------------------------------------+
void CotGetDateRange(datetime time, datetime &date_from, datetime &date_to) {
    MqlDateTime dts;
    datetime date = StringToTime(TimeToString(time, TIME_DATE));
    TimeToStruct(date, dts);
    int dow = dts.day_of_week;
    if (dow == 6) {
        dow = 0;
        date += PeriodSeconds(PERIOD_D1);
    }
    date_to = date - dow * PeriodSeconds(PERIOD_D1); // Last Sunday
    date_to -= 3 * PeriodSeconds(PERIOD_D1); // Last Thursday
    date_from = date_to - 3 * PeriodSeconds(PERIOD_D1); // 2nd Last Monday
}

//+------------------------------------------------------------------+
//| Fetch the COT report from the csv file and insert into the DB.   |
//+------------------------------------------------------------------+
bool cotReadReport(ENUM_COT_REPORT report_type, int year) {
    string file_path = cotGetCsvFilePath(report_type, year);
    if (!FileIsExist(file_path, FILE_COMMON))
        if (!cotDownloadReport(report_type, year))
            return false;

    string ccols[], ccols_str;
    string cols[], cols_str;
    string table = CotGetTableName(report_type);
    ccols_str = cotGetTableColumns("contract", ccols);
    cols_str = cotGetTableColumns(table, cols);
    if (ccols_str == NULL || cols_str == NULL)
        return false;

    int fh = FileOpen(file_path, FILE_READ | FILE_SHARE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON, CP_UTF8);
    if (fh == INVALID_HANDLE) {
        PrintFormat("Error (%s, FileOpen): #%d", __FUNCTION__, GetLastError());
        return false;
    }

    int cmap[], map[];
    string fcols[];
    string head =  FileReadString(fh);
    StringReplace(head, "__", "_");
    cotSplitCsvRecord(head, fcols);
    cotMapFcolsToDbcols(fcols, ccols, cmap);
    cotMapFcolsToDbcols(fcols, cols, map);

    int db, dp, t;
    string sql;
    db = CotInitDb(DATABASE_OPEN_READWRITE);
    if (db == INVALID_HANDLE) return false;

    if (!DatabaseTransactionBegin(db)) {
        PrintFormat("Error (%s, DatabaseTransactionBegin): #%d", __FUNCTION__, GetLastError());
        DatabaseClose(db);
        FileClose(fh);
        return false;
    }

    string r[];
    int n, m;
    string values;
    datetime date;
    int fo = CotIsFuturesOnly(report_type);
    while (!FileIsEnding(fh)) {
        if (IsStopped()) {
            PrintFormat("%s (loop: file) stopped!", __FUNCTION__);
            DatabaseTransactionRollback(db);
            DatabaseClose(db);
            FileClose(fh);
            return false;
        }

        m = cotSplitCsvRecord(FileReadString(fh), r);
        if (m <= 0) continue;

        sql = StringFormat("SELECT EXISTS (SELECT 1 FROM contract WHERE id='%s' LIMIT 1)", r[cmap[0]]);
        dp = DatabasePrepare(db, sql);
        DatabaseRead(dp);
        DatabaseColumnInteger(dp, 0, t);
        DatabaseFinalize(dp);

        if (!t) {
            values = "";
            n = ArraySize(cmap);
            for (int i = 0; i < n; i++) {
                if (StringLen(values) > 0)
                    StringAdd(values, ",");
                if (cmap[i] == -1)
                    StringAdd(values, "NULL");
                else
                    StringAdd(values, StringFormat("'%s'", r[cmap[i]]));
            }
            sql = StringFormat("INSERT INTO contract(%s) VALUES(%s)", ccols_str, values);
        } else {
            values = "";
            n = ArraySize(cmap);
            for (int i = 0; i < n; i++) {
                if (cmap[i] == -1)
                    continue;
                if (StringLen(values) > 0)
                    StringAdd(values, ",");
                StringAdd(values, StringFormat("%s='%s'", ccols[i], r[cmap[i]]));
            }
            sql = StringFormat("UPDATE contract SET %s WHERE id='%s' AND contract_market_name IS NULL", values, r[cmap[0]]);
        }

        if (!DatabaseExecute(db, sql)) {
            PrintFormat("Error (%s, Insert, contract): #%d", __FUNCTION__, GetLastError());
            DatabaseTransactionRollback(db);
            DatabaseClose(db);
            FileClose(fh);
            return false;
        }

        date = StringToTime(r[map[0]]);
        sql = StringFormat("SELECT EXISTS (SELECT 1 FROM %s WHERE date=%d AND rid=%d AND cid='%s' LIMIT 1)", table, date, report_type, r[map[2]]);
        dp = DatabasePrepare(db, sql);
        DatabaseRead(dp);
        DatabaseColumnInteger(dp, 0, t);
        DatabaseFinalize(dp);

        if (!t) {
            values = "";
            n = ArraySize(map);
            for (int i = 0; i < n; i++) {
                if (StringLen(values) > 0)
                    StringAdd(values, ",");
                if (cols[i] == "date")
                    StringAdd(values, StringFormat("%d", date));
                else if (cols[i] == "rid")
                    StringAdd(values, StringFormat("%d", report_type));
                else if (cols[i] == "cid")
                    StringAdd(values, StringFormat("'%s'", r[map[i]]));
                else if (cols[i] == "fo")
                    StringAdd(values, StringFormat("%d", fo));
                else if (map[i] == -1)
                    StringAdd(values, "NULL");
                else
                    StringAdd(values, StringFormat("%s", r[map[i]]));
            }
            sql = StringFormat("INSERT INTO %s(%s) VALUES(%s)", table, cols_str, values);
            if (!DatabaseExecute(db, sql)) {
                PrintFormat("Error (%s, Insert, %s): #%d", __FUNCTION__, table, GetLastError());
                DatabaseTransactionRollback(db);
                DatabaseClose(db);
                FileClose(fh);
                return false;
            }
        }
    }

    if (!DatabaseTransactionCommit(db)) {
        PrintFormat("Error (%s, DatabaseTransactionCommit): #%d", __FUNCTION__, GetLastError());
        DatabaseTransactionRollback(db);
        DatabaseClose(db);
        FileClose(fh);
        return false;
    }

    DatabaseClose(db);
    FileClose(fh);
    if (FileIsExist(file_path, FILE_COMMON))
        FileDelete(file_path, FILE_COMMON);

    return true;
}

//+------------------------------------------------------------------+
//| Download the COT report and save it as a csv file.               |
//+------------------------------------------------------------------+
bool cotDownloadReport(ENUM_COT_REPORT report_type, int year) {
    if (year < 2010) {
        Print("Downloading COT report older than year 2010 is not allowed!");
        return false;
    }

    MqlDateTime dts;
    TimeSystem(dts);
    if (year > dts.year) {
        Print("Downloading COT report for future years is not possible!");
        return false;
    }

    string file_name = cotGetCsvFileName(report_type, year);
    string file_path = cotGetCsvFilePath(report_type, year);

    if (FileIsExist(file_path, FILE_COMMON))
        return true;

    WininetRequest req;
    WininetResponse res;

    string query = StringFormat("SELECT * WHERE `report_date_as_yyyy_mm_dd` >= '%d-01-01' "
                                "AND `report_date_as_yyyy_mm_dd` < '%d-01-01'",
                                year, year + 1
                               );
    if (COT_USE_CO)
        query += StringFormat(" AND `cftc_contract_market_code` IN (%s)", COT_CURRENCIES);
    query += " ORDER BY `report_date_as_yyyy_mm_dd` DESC LIMIT 100000";

    req.host = "publicreporting.cftc.gov";
    req.path = "/resource/" + cotGetRequestId(report_type) + ".csv" + "?$query=" + query;
    if (COT_APP_TOKEN != "")
        req.headers = StringFormat("X-App-Token: %s\r\n", COT_APP_TOKEN);

    PrintFormat("Downloading '%s' file...", file_name);
    WebReq(req, res);
    if (res.status != 200) {
        PrintFormat("Downloading '%s' failed! (status=%d)", file_name, res.status);
        return false;
    }
    if (FileIsExist(file_path, FILE_COMMON))
        return true;
    PrintFormat("The file '%s' has been successfully downloaded. (%d bytes)", file_name, ArraySize(res.data));

    int file_handle = FileOpen(file_path, FILE_WRITE | FILE_BIN | FILE_COMMON);
    if (file_handle == INVALID_HANDLE) {
        PrintFormat("Error (%s, FileOpen): #%d", __FUNCTION__, GetLastError());
        return false;
    }
    if (!FileWriteArray(file_handle, res.data)) {
        PrintFormat("Error (%s, FileWriteArray): #%d", __FUNCTION__, ERR_FILE_WRITEERROR);
        FileClose(file_handle);
        FileDelete(file_path, FILE_COMMON);
        return false;
    }
    FileClose(file_handle);

    return true;
}

//+------------------------------------------------------------------+
//| Get column names of the table.                                   |
//+------------------------------------------------------------------+
string cotGetTableColumns(string table, string &arr[]) {
    string columns, col;
    int db, dp;
    string sql;
    int n;

    db = CotInitDb();
    if (db == INVALID_HANDLE) return NULL;

    sql = StringFormat("SELECT name FROM PRAGMA_TABLE_INFO('%s')", table);
    dp = DatabasePrepare(db, sql);
    if (dp == INVALID_HANDLE) {
        PrintFormat("Error (%s, DatabasePrepare): #%d", __FUNCTION__, GetLastError());
        DatabaseClose(db);
        return NULL;
    }

    columns = "";
    while (DatabaseRead(dp) && !IsStopped()) {
        if (!DatabaseColumnText(dp, 0, col)) {
            PrintFormat("Error (%s, DatabaseColumnText): #%d", __FUNCTION__, GetLastError());
            DatabaseFinalize(dp);
            DatabaseClose(db);
            return NULL;
        }
        n = ArraySize(arr);
        ArrayResize(arr, n + 1);
        arr[n] = col;
        if (StringLen(columns) > 0)
            StringAdd(columns, ",");
        StringAdd(columns, col);
    }

    DatabaseFinalize(dp);
    DatabaseClose(db);
    return columns;
}

//+------------------------------------------------------------------+
//| Map the csv file columns to the DB table columns.                |
//+------------------------------------------------------------------+
void cotMapFcolsToDbcols(const string &fcols[], const string &dbcols[], int &map[]) {
    int n = ArraySize(dbcols);
    ArrayResize(map, n);
    for (int i = 0; i < n; i++) {
        if (dbcols[i] == "id" || dbcols[i] == "cid")
            map[i] = ArraySearch(fcols, "cftc_contract_market_code", false);
        else if (dbcols[i] == "date")
            map[i] = ArraySearch(fcols, "report_date_as_yyyy_mm_dd", false);
        else
            map[i] = ArraySearch(fcols, dbcols[i], false);
    }
}

//+------------------------------------------------------------------+
//| Fetch values from the csv record.                                |
//+------------------------------------------------------------------+
int cotSplitCsvRecord(const string record, string &arr[]) {
    string rec = record;
    StringReplace(rec, "\",", "¡");
    while(StringReplace(rec, "¡,", "¡ ¡") > 0);
    int n = StringSplit(rec, '¡', arr);
    if (n == -1) {
        PrintFormat("Error (%s, StringSplit): #%d", __FUNCTION__, GetLastError());
        return -1;
    }
    for (int i = 0; i < n; i++) {
        StringReplace(arr[i], "\"", "");
        StringReplace(arr[i], "'", "''");
        StringTrimLeft(arr[i]);
        StringTrimRight(arr[i]);
        if (arr[i] == "")
            arr[i] = "NULL";
    }
    return n;
}

//+------------------------------------------------------------------+
//| Get the csv file name containing the COT report.                 |
//+------------------------------------------------------------------+
string cotGetCsvFileName(ENUM_COT_REPORT report_type, int year) {
    string file_name = IntegerToString(report_type) + "-" + IntegerToString(year);
    if (COT_USE_CO)
        file_name += "-co";
    file_name += ".csv";
    return file_name;
}

//+------------------------------------------------------------------+
//| Get the csv file path containing the COT report.                 |
//+------------------------------------------------------------------+
string cotGetCsvFilePath(ENUM_COT_REPORT report_type, int year) {
    string file_name = cotGetCsvFileName(report_type, year);
    string file_path = COT_DIR_PATH + file_name;
    return file_path;
}

//+------------------------------------------------------------------+
//| Initialize the COT DB and return the handle.                     |
//+------------------------------------------------------------------+
int CotInitDb(uint flags = DATABASE_OPEN_READONLY) {
    int db;
    string sql;
    string db_path = COT_USE_CO ? COT_DB_CO_PATH : COT_DB_PATH;

    if (!FileIsExist(db_path, FILE_COMMON))
        flags = DATABASE_OPEN_READWRITE | DATABASE_OPEN_CREATE;

    flags |= DATABASE_OPEN_COMMON;
    db = DatabaseOpen(db_path, flags);
    if (db == INVALID_HANDLE) {
        PrintFormat("Error (%s, DatabaseOpen): #%d", __FUNCTION__, GetLastError());
        return INVALID_HANDLE;
    }

    if (!DatabaseTableExists(db, "contract")) {
        sql = "CREATE TABLE contract ("
              "id TEXT,"
              "name TEXT,"
              "market_and_exchange_names TEXT,"
              "contract_market_name TEXT,"
              "cftc_market_code TEXT,"
              "cftc_region_code TEXT,"
              "cftc_commodity_code TEXT,"
              "commodity_name TEXT,"
              "contract_units TEXT,"
              "commodity TEXT,"
              "commodity_subgroup_name TEXT,"
              "commodity_group_name TEXT,"
              "cftc_subgroup_code TEXT,"
              "PRIMARY KEY(id)"
              ");";

        sql += "INSERT INTO contract(id, name) "
               "VALUES "
               "('232741', 'AUD'),"
               "('099741', 'EUR'),"
               "('096742', 'GBP'),"
               "('112741', 'NZD'),"
               "('090741', 'CAD'),"
               "('092741', 'CHF'),"
               "('097741', 'JPY'),"
               "('098662', 'USD')";

        sql += ","
               "('122741', 'ZAR'),"
               "('095741', 'MXN'),"
               "('089741', 'RUB'),"
               "('102741', 'RBL'),"
               "('088691', 'XAU'),"
               "('084691', 'XAG'),"
               "('133741', 'BTC'),"
               "('146021', 'ETH')";

        sql += ";";

        if (!DatabaseExecute(db, sql)) {
            PrintFormat("Error (%s, CreateTable, contract): #%d", __FUNCTION__, GetLastError());
            DatabaseClose(db);
            return INVALID_HANDLE;
        }
    }

    if (!DatabaseTableExists(db, "L")) {
        sql = "CREATE TABLE L ("
              "date INT, rid INT, cid TEXT, fo INT,"

              "open_interest_all INT, noncomm_positions_long_all INT, noncomm_positions_short_all INT, noncomm_postions_spread_all INT,"
              "comm_positions_long_all INT, comm_positions_short_all INT, tot_rept_positions_long_all INT, tot_rept_positions_short INT,"
              "nonrept_positions_long_all INT, nonrept_positions_short_all INT, open_interest_old INT, noncomm_positions_long_old INT,"
              "noncomm_positions_short_old INT, noncomm_positions_spread INT, comm_positions_long_old INT, comm_positions_short_old INT,"
              "tot_rept_positions_long_old INT, tot_rept_positions_short_1 INT, nonrept_positions_long_old INT, nonrept_positions_short_old INT,"
              "open_interest_other INT, noncomm_positions_long_other INT, noncomm_positions_short_other INT, noncomm_positions_spread_1 INT,"
              "comm_positions_long_other INT, comm_positions_short_other INT, tot_rept_positions_long_other INT, tot_rept_positions_short_2 INT,"
              "nonrept_positions_long_other INT, nonrept_positions_short_other INT, change_in_open_interest_all INT, change_in_noncomm_long_all INT,"
              "change_in_noncomm_short_all INT, change_in_noncomm_spead_all INT, change_in_comm_long_all INT, change_in_comm_short_all INT,"
              "change_in_tot_rept_long_all INT, change_in_tot_rept_short INT, change_in_nonrept_long_all INT, change_in_nonrept_short_all INT,"
              "pct_of_open_interest_all REAL, pct_of_oi_noncomm_long_all REAL, pct_of_oi_noncomm_short_all REAL, pct_of_oi_noncomm_spread REAL,"
              "pct_of_oi_comm_long_all REAL, pct_of_oi_comm_short_all REAL, pct_of_oi_tot_rept_long_all REAL, pct_of_oi_tot_rept_short REAL,"
              "pct_of_oi_nonrept_long_all REAL, pct_of_oi_nonrept_short_all REAL, pct_of_open_interest_old REAL, pct_of_oi_noncomm_long_old REAL,"
              "pct_of_oi_noncomm_short_old REAL, pct_of_oi_noncomm_spread_1 REAL, pct_of_oi_comm_long_old REAL, pct_of_oi_comm_short_old REAL,"
              "pct_of_oi_tot_rept_long_old REAL, pct_of_oi_tot_rept_short_1 REAL, pct_of_oi_nonrept_long_old REAL, pct_of_oi_nonrept_short_old REAL,"
              "pct_of_open_interest_other REAL, pct_of_oi_noncomm_long_other REAL, pct_of_oi_noncomm_short_other REAL, pct_of_oi_noncomm_spread_2 REAL,"
              "pct_of_oi_comm_long_other REAL, pct_of_oi_comm_short_other REAL, pct_of_oi_tot_rept_long_other REAL, pct_of_oi_tot_rept_short_2 REAL,"
              "pct_of_oi_nonrept_long_other REAL, pct_of_oi_nonrept_short_other REAL, traders_tot_all INT, traders_noncomm_long_all INT,"
              "traders_noncomm_short_all INT, traders_noncomm_spread_all INT, traders_comm_long_all INT, traders_comm_short_all INT,"
              "traders_tot_rept_long_all INT, traders_tot_rept_short_all INT, traders_tot_old INT, traders_noncomm_long_old INT,"
              "traders_noncomm_short_old INT, traders_noncomm_spead_old INT, traders_comm_long_old INT, traders_comm_short_old INT, traders_tot_rept_long_old INT,"
              "traders_tot_rept_short_old INT, traders_tot_other INT, traders_noncomm_long_other INT, traders_noncomm_short_other INT, traders_noncomm_spread_other INT,"
              "traders_comm_long_other INT, traders_comm_short_other INT, traders_tot_rept_long_other INT, traders_tot_rept_short_other INT,"
              "conc_gross_le_4_tdr_long REAL, conc_gross_le_4_tdr_short REAL, conc_gross_le_8_tdr_long REAL, conc_gross_le_8_tdr_short REAL, conc_net_le_4_tdr_long_all REAL,"
              "conc_net_le_4_tdr_short_all REAL, conc_net_le_8_tdr_long_all REAL, conc_net_le_8_tdr_short_all REAL, conc_gross_le_4_tdr_long_1 REAL,"
              "conc_gross_le_4_tdr_short_1 REAL, conc_gross_le_8_tdr_long_1 REAL, conc_gross_le_8_tdr_short_1 REAL, conc_net_le_4_tdr_long_old REAL,"
              "conc_net_le_4_tdr_short_old REAL, conc_net_le_8_tdr_long_old REAL, conc_net_le_8_tdr_short_old REAL, conc_gross_le_4_tdr_long_2 REAL,"
              "conc_gross_le_4_tdr_short_2 REAL, conc_gross_le_8_tdr_long_2 REAL, conc_gross_le_8_tdr_short_2 REAL, conc_net_le_4_tdr_long_other REAL,"
              "conc_net_le_4_tdr_short_other REAL, conc_net_le_8_tdr_long_other REAL, conc_net_le_8_tdr_short_other REAL,"

              "FOREIGN KEY(cid) REFERENCES contract(id),"
              "PRIMARY KEY(date, rid, cid)"
              ");"

              "CREATE INDEX idx_L_1 ON L(date);"
              ;

        if (!DatabaseExecute(db, sql)) {
            PrintFormat("Error (%s, CreateTable, L): #%d", __FUNCTION__, GetLastError());
            DatabaseClose(db);
            return INVALID_HANDLE;
        }
    }

    if (!DatabaseTableExists(db, "T")) {
        sql = "CREATE TABLE T ("
              "date INT, rid INT, cid TEXT, fo INT,"

              "open_interest_all INT, dealer_positions_long_all INT, dealer_positions_short_all INT, dealer_positions_spread_all INT,"
              "asset_mgr_positions_long INT, asset_mgr_positions_short INT, asset_mgr_positions_spread INT,"
              "lev_money_positions_long INT, lev_money_positions_short INT, lev_money_positions_spread INT,"
              "other_rept_positions_long INT, other_rept_positions_short INT, other_rept_positions_spread INT,"
              "tot_rept_positions_long_all INT, tot_rept_positions_short INT, nonrept_positions_long_all INT, nonrept_positions_short_all INT,"
              "change_in_open_interest_all INT, change_in_dealer_long_all INT, change_in_dealer_short_all INT, change_in_dealer_spread_all INT,"
              "change_in_asset_mgr_long INT, change_in_asset_mgr_short INT, change_in_asset_mgr_spread INT,"
              "change_in_lev_money_long INT, change_in_lev_money_short INT, change_in_lev_money_spread INT,"
              "change_in_other_rept_long INT, change_in_other_rept_short INT, change_in_other_rept_spread INT,"
              "change_in_tot_rept_long_all INT, change_in_tot_rept_short INT, change_in_nonrept_long_all INT, change_in_nonrept_short_all INT,"
              "pct_of_open_interest_all REAL, pct_of_oi_dealer_long_all REAL, pct_of_oi_dealer_short_all REAL, pct_of_oi_dealer_spread_all REAL,"
              "pct_of_oi_asset_mgr_long REAL, pct_of_oi_asset_mgr_short REAL, pct_of_oi_asset_mgr_spread REAL,"
              "pct_of_oi_lev_money_long REAL, pct_of_oi_lev_money_short REAL, pct_of_oi_lev_money_spread REAL,"
              "pct_of_oi_other_rept_long REAL, pct_of_oi_other_rept_short REAL, pct_of_oi_other_rept_spread REAL,"
              "pct_of_oi_tot_rept_long_all REAL, pct_of_oi_tot_rept_short REAL, pct_of_oi_nonrept_long_all REAL, pct_of_oi_nonrept_short_all REAL,"
              "traders_tot_all INT, traders_dealer_long_all INT, traders_dealer_short_all INT, traders_dealer_spread_all INT,"
              "traders_asset_mgr_long_all INT, traders_asset_mgr_short_all INT, traders_asset_mgr_spread INT,"
              "traders_lev_money_long_all INT, traders_lev_money_short_all INT, traders_lev_money_spread INT,"
              "traders_other_rept_long_all INT, traders_other_rept_short INT, traders_other_rept_spread INT,"
              "traders_tot_rept_long_all INT, traders_tot_rept_short_all INT,"
              "conc_gross_le_4_tdr_long REAL, conc_gross_le_4_tdr_short REAL, conc_gross_le_8_tdr_long REAL, conc_gross_le_8_tdr_short REAL,"
              "conc_net_le_4_tdr_long_all REAL, conc_net_le_4_tdr_short_all REAL, conc_net_le_8_tdr_long_all REAL, conc_net_le_8_tdr_short_all REAL,"

              "FOREIGN KEY(cid) REFERENCES contract(id),"
              "PRIMARY KEY(date, rid, cid)"
              ");"

              "CREATE INDEX idx_T_1 ON T(date);"
              ;

        if (!DatabaseExecute(db, sql)) {
            PrintFormat("Error (%s, CreateTable, T): #%d", __FUNCTION__, GetLastError());
            DatabaseClose(db);
            return INVALID_HANDLE;
        }
    }

    if (!DatabaseTableExists(db, "D")) {
        sql = "CREATE TABLE D ("
              "date INT, rid INT, cid TEXT, fo INT,"

              "open_interest_all INT, prod_merc_positions_long INT, prod_merc_positions_short INT,"
              "swap_positions_long_all INT, swap_positions_short_all INT, swap_positions_spread_all INT,"
              "m_money_positions_long_all INT, m_money_positions_short_all INT, m_money_positions_spread INT,"
              "other_rept_positions_long INT, other_rept_positions_short INT, other_rept_positions_spread INT,"
              "tot_rept_positions_long_all INT, tot_rept_positions_short INT, nonrept_positions_long_all INT, nonrept_positions_short_all INT,"
              "open_interest_old INT, prod_merc_positions_long_1 INT, prod_merc_positions_short_1 INT,"
              "swap_positions_long_old INT, swap_positions_short_old INT, swap_positions_spread_old INT,"
              "m_money_positions_long_old INT, m_money_positions_short_old INT, m_money_positions_spread_1 INT,"
              "other_rept_positions_long_1 INT, other_rept_positions_short_1 INT, other_rept_positions_spread_1 INT,"
              "tot_rept_positions_long_old INT, tot_rept_positions_short_1 INT, nonrept_positions_long_old INT, nonrept_positions_short_old INT,"
              "open_interest_other INT, prod_merc_positions_long_2 INT, prod_merc_positions_short_2 INT,"
              "swap_positions_long_other INT, swap_positions_short_other INT, swap_positions_spread_other INT,"
              "m_money_positions_long_other INT, m_money_positions_short_other INT, m_money_positions_spread_2 INT,"
              "other_rept_positions_long_2 INT, other_rept_positions_short_2 INT, other_rept_positions_spread_2 INT,"
              "tot_rept_positions_long_other INT, tot_rept_positions_short_2 INT, nonrept_positions_long_other INT, nonrept_positions_short_other INT,"
              "change_in_open_interest_all INT, change_in_prod_merc_long INT, change_in_prod_merc_short INT,"
              "change_in_swap_long_all INT, change_in_swap_short_all INT, change_in_swap_spread_all INT,"
              "change_in_m_money_long_all INT, change_in_m_money_short_all INT, change_in_m_money_spread INT,"
              "change_in_other_rept_long INT, change_in_other_rept_short INT, change_in_other_rept_spread INT,"
              "change_in_tot_rept_long_all INT, change_in_tot_rept_short INT, change_in_nonrept_long_all INT, change_in_nonrept_short_all INT,"
              "pct_of_open_interest_all REAL, pct_of_oi_prod_merc_long REAL, pct_of_oi_prod_merc_short REAL,"
              "pct_of_oi_swap_long_all REAL, pct_of_oi_swap_short_all REAL, pct_of_oi_swap_spread_all REAL,"
              "pct_of_oi_m_money_long_all REAL, pct_of_oi_m_money_short_all REAL, pct_of_oi_m_money_spread REAL,"
              "pct_of_oi_other_rept_long REAL, pct_of_oi_other_rept_short REAL, pct_of_oi_other_rept_spread REAL,"
              "pct_of_oi_tot_rept_long_all REAL, pct_of_oi_tot_rept_short REAL, pct_of_oi_nonrept_long_all REAL, pct_of_oi_nonrept_short_all REAL,"
              "pct_of_open_interest_old REAL, pct_of_oi_prod_merc_long_1 REAL, pct_of_oi_prod_merc_short_1 REAL,"
              "pct_of_oi_swap_long_old REAL, pct_of_oi_swap_short_old REAL, pct_of_oi_swap_spread_old REAL,"
              "pct_of_oi_m_money_long_old REAL, pct_of_oi_m_money_short_old REAL, pct_of_oi_m_money_spread_1 REAL,"
              "pct_of_oi_other_rept_long_1 REAL, pct_of_oi_other_rept_short_1 REAL, pct_of_oi_other_rept_spread_1 REAL,"
              "pct_of_oi_tot_rept_long_old REAL, pct_of_oi_tot_rept_short_1 REAL, pct_of_oi_nonrept_long_old REAL, pct_of_oi_nonrept_short_old REAL,"
              "pct_of_open_interest_other REAL, pct_of_oi_prod_merc_long_2 REAL, pct_of_oi_prod_merc_short_2 REAL,"
              "pct_of_oi_swap_long_other REAL, pct_of_oi_swap_short_other REAL, pct_of_oi_swap_spread_other REAL,"
              "pct_of_oi_m_money_long_other REAL, pct_of_oi_m_money_short_other REAL, pct_of_oi_m_money_spread_2 REAL,"
              "pct_of_oi_other_rept_long_2 REAL, pct_of_oi_other_rept_short_2 REAL, pct_of_oi_other_rept_spread_2 REAL,"
              "pct_of_oi_tot_rept_long_other REAL, pct_of_oi_tot_rept_short_2 REAL, pct_of_oi_nonrept_long_other REAL, pct_of_oi_nonrept_short_other REAL,"
              "traders_tot_all INT, traders_prod_merc_long_all INT, traders_prod_merc_short_all INT,"
              "traders_swap_long_all INT, traders_swap_short_all INT, traders_swap_spread_all INT,"
              "traders_m_money_long_all INT, traders_m_money_short_all INT, traders_m_money_spread_all INT,"
              "traders_other_rept_long_all INT, traders_other_rept_short INT, traders_other_rept_spread INT,"
              "traders_tot_rept_long_all INT, traders_tot_rept_short_all INT, traders_tot_old INT, traders_prod_merc_long_old INT, traders_prod_merc_short_old INT,"
              "traders_swap_long_old INT, traders_swap_short_old INT, traders_swap_spread_old INT,"
              "traders_m_money_long_old INT, traders_m_money_short_old INT, traders_m_money_spread_old INT,"
              "traders_other_rept_long_old INT, traders_other_rept_short_1 INT, traders_other_rept_spread_1 INT,"
              "traders_tot_rept_long_old INT, traders_tot_rept_short_old INT, traders_tot_other INT, traders_prod_merc_long_other INT, traders_prod_merc_short_other INT,"
              "traders_swap_long_other INT, traders_swap_short_other INT, traders_swap_spread_other INT,"
              "traders_m_money_long_other INT, traders_m_money_short_other INT, traders_m_money_spread_other INT,"
              "traders_other_rept_long_other INT, traders_other_rept_short_2 INT, traders_other_rept_spread_2 INT, traders_tot_rept_long_other INT, traders_tot_rept_short_other INT,"
              "conc_gross_le_4_tdr_long REAL, conc_gross_le_4_tdr_short REAL, conc_gross_le_8_tdr_long REAL, conc_gross_le_8_tdr_short REAL,"
              "conc_net_le_4_tdr_long_all REAL, conc_net_le_4_tdr_short_all REAL, conc_net_le_8_tdr_long_all REAL, conc_net_le_8_tdr_short_all REAL,"
              "conc_gross_le_4_tdr_long_1 REAL, conc_gross_le_4_tdr_short_1 REAL, conc_gross_le_8_tdr_long_1 REAL,"
              "conc_gross_le_8_tdr_short_1 REAL, conc_net_le_4_tdr_long_old REAL, conc_net_le_4_tdr_short_old REAL, conc_net_le_8_tdr_long_old REAL, conc_net_le_8_tdr_short_old REAL,"
              "conc_gross_le_4_tdr_long_2 REAL, conc_gross_le_4_tdr_short_2 REAL, conc_gross_le_8_tdr_long_2 REAL, conc_gross_le_8_tdr_short_2 REAL,"
              "conc_net_le_4_tdr_long_other REAL, conc_net_le_4_tdr_short_other REAL, conc_net_le_8_tdr_long_other REAL, conc_net_le_8_tdr_short_other REAL,"

              "FOREIGN KEY(cid) REFERENCES contract(id),"
              "PRIMARY KEY(date, rid, cid)"
              ");"

              "CREATE INDEX idx_D_1 ON D(date);"
              ;

        if (!DatabaseExecute(db, sql)) {
            PrintFormat("Error (%s, CreateTable, D): #%d", __FUNCTION__, GetLastError());
            DatabaseClose(db);
            return INVALID_HANDLE;
        }
    }

    if (!DatabaseTableExists(db, "S")) {
        sql = "CREATE TABLE S ("
              "date INT, rid INT, cid TEXT, fo INT,"

              "open_interest_all INT, ncomm_postions_long_all_nocit INT, ncomm_postions_short_all_nocit INT, ncomm_postions_spread_all_nocit INT,"
              "comm_positions_long_all_nocit INT, comm_positions_short_all_nocit INT,"
              "tot_rept_positions_long_all INT, tot_rept_positions_short INT, nonrept_positions_long_all INT, nonrept_positions_short_all INT,"
              "cit_positions_long_all INT, cit_positions_short_all INT,"
              "change_open_interest_all INT, change_noncomm_long_all_nocit INT, change_noncomm_short_all_nocit INT, change_noncomm_spead_all_nocit INT,"
              "change_comm_long_all_nocit INT, change_comm_short_all_nocit INT, change_tot_rept_long_all INT, change_tot_rept_short_all INT,"
              "change_nonrept_long_all INT, change_nonrept_short_all INT, change_cit_long_all INT, change_cit_short_all INT,"
              "pct_open_interest_all REAL, pct_oi_noncomm_long_all_nocit REAL, pct_oi_noncomm_short_all_nocit REAL, pct_oi_noncomm_spread_all_nocit REAL,"
              "pct_oi_comm_long_all_nocit REAL, pct_oi_comm_short_all_nocit REAL, pct_oi_tot_rept_long_all_nocit REAL, pct_oi_tot_rept_short_all_nocit REAL,"
              "pct_oi_nonrept_long_all_nocit REAL, pct_oi_nonrept_short_all_nocit REAL, pct_oi_cit_long_all REAL, pct_oi_cit_short_all REAL,"
              "traders_tot_all INT, traders_noncomm_long_all_nocit INT, traders_noncomm_short_all_nocit INT, traders_noncomm_spread_all_nocit INT,"
              "traders_comm_long_all_nocit INT, traders_comm_short_all_nocit INT, traders_tot_rept_long_all_nocit INT,"
              "traders_tot_rept_short_all_nocit INT, traders_cit_long_all INT, traders_cit_short_all INT,"

              "FOREIGN KEY(cid) REFERENCES contract(id),"
              "PRIMARY KEY(date, rid, cid)"
              ");"

              "CREATE INDEX idx_S_1 ON S(date);"
              ;

        if (!DatabaseExecute(db, sql)) {
            PrintFormat("Error (%s, CreateTable, S): #%d", __FUNCTION__, GetLastError());
            DatabaseClose(db);
            return INVALID_HANDLE;
        }
    }

    return db;
}

//+------------------------------------------------------------------+
//| Retrieve the URL id associated with the COT report.              |
//+------------------------------------------------------------------+
string cotGetRequestId(ENUM_COT_REPORT report_type) {
    string rid;
    switch(report_type) {
    case COT_REPORT_L:
        rid = "6dca-aqww";
        break;
    case COT_REPORT_LC:
        rid = "jun7-fc8e";
        break;
    case COT_REPORT_T:
        rid = "gpe5-46if";
        break;
    case COT_REPORT_TC:
        rid = "yw9f-hn96";
        break;
    case COT_REPORT_D:
        rid = "72hh-3qpy";
        break;
    case COT_REPORT_DC:
        rid = "kh3c-gbw2";
        break;
    case COT_REPORT_S:
        rid = "4zgm-a668";
        break;
    }
    return rid;
}

//+------------------------------------------------------------------+
//| Retrieve the name of the DB table associated with the COT report.|
//+------------------------------------------------------------------+
string CotGetTableName(ENUM_COT_REPORT report_type) {
    string table;
    switch(report_type) {
    case COT_REPORT_L:
        table = "L";
        break;
    case COT_REPORT_LC:
        table = "L";
        break;
    case COT_REPORT_T:
        table = "T";
        break;
    case COT_REPORT_TC:
        table = "T";
        break;
    case COT_REPORT_D:
        table = "D";
        break;
    case COT_REPORT_DC:
        table = "D";
        break;
    case COT_REPORT_S:
        table = "S";
        break;
    }
    return table;
}

//+------------------------------------------------------------------+
//| Determine the COT report is futures only or combined with options|
//+------------------------------------------------------------------+
int CotIsFuturesOnly(ENUM_COT_REPORT report_type) {
    int fo = 0;
    switch(report_type) {
    case COT_REPORT_L:
        fo = 1;
        break;
    case COT_REPORT_LC:
        fo = 0;
        break;
    case COT_REPORT_T:
        fo = 1;
        break;
    case COT_REPORT_TC:
        fo = 0;
        break;
    case COT_REPORT_D:
        fo = 1;
        break;
    case COT_REPORT_DC:
        fo = 0;
        break;
    case COT_REPORT_S:
        fo = 0;
        break;
    }
    return fo;
}

//+------------------------------------------------------------------+
//| Retrieve COT report type.                                        |
//+------------------------------------------------------------------+
ENUM_COT_REPORT CotGetReportType(ENUM_COT_CLASS clss, ENUM_COT_MODE mode) {
    ENUM_COT_REPORT t = 1;
    int i = (int) clss;
    if (i >= 1 && i < 4)
        t = (mode == COT_MODE_FO) ? COT_REPORT_L : COT_REPORT_LC;
    else if (i >= 4 && i < 8)
        t = (mode == COT_MODE_FO) ? COT_REPORT_T : COT_REPORT_TC;
    else if (i >= 8 && i < 12)
        t = (mode == COT_MODE_FO) ? COT_REPORT_D : COT_REPORT_DC;
    else if (i == 12)
        t = COT_REPORT_S;
    return t;
}

//+------------------------------------------------------------------+
//| Retrieve the COT field clause.                                   |
//+------------------------------------------------------------------+
string CotGetColClause(ENUM_COT_CLASS clss) {
    string c;
    switch(clss) {
    case COT_CLASS_COM:
        c = "comm";
        break;
    case COT_CLASS_NCOM:
        c = "noncomm";
        break;
    case COT_CLASS_NR:
        c = "nonrept";
        break;
    case COT_CLASS_DEALER:
        c = "dealer";
        break;
    case COT_CLASS_ASSET:
        c = "asset_mgr";
        break;
    case COT_CLASS_LEV:
        c = "lev_money";
        break;
    case COT_CLASS_ORT:
        c = "other_rept";
        break;
    case COT_CLASS_PM:
        c = "prod_merc";
        break;
    case COT_CLASS_SD:
        c = "swap";
        break;
    case COT_CLASS_MM:
        c = "m_money";
        break;
    case COT_CLASS_ORD:
        c = "other_rept";
        break;
    case COT_CLASS_IT:
        c = "cit";
        break;
    }
    return c;
}

//+------------------------------------------------------------------+
//| Retrieve the description about COT types.                        |
//+------------------------------------------------------------------+
string CotGetDescription(ENUM_COT_CLASS clss) {
    string c;
    switch(clss) {
    case COT_CLASS_COM:
        c = "Commercial";
        break;
    case COT_CLASS_NCOM:
        c = "Non-Commercial";
        break;
    case COT_CLASS_NR:
        c = "Non-Reportables";
        break;
    case COT_CLASS_DEALER:
        c = "Dealer/Intermediary";
        break;
    case COT_CLASS_ASSET:
        c = "Asset Manager/Institutional";
        break;
    case COT_CLASS_LEV:
        c = "Leveraged Funds";
        break;
    case COT_CLASS_ORT:
        c = "Other Reportables (TFF)";
        break;
    case COT_CLASS_PM:
        c = "Producer/Merchant/Processor/User";
        break;
    case COT_CLASS_SD:
        c = "Swap Dealers";
        break;
    case COT_CLASS_MM:
        c = "Managed Money";
        break;
    case COT_CLASS_ORD:
        c = "Other Reportables (Disaggregated)";
        break;
    case COT_CLASS_IT:
        c = "Index Traders";
        break;
    }
    return c;
}

//+------------------------------------------------------------------+
//| Overload                                                         |
//+------------------------------------------------------------------+
string CotGetDescription(ENUM_COT_MODE mode) {
    string s;
    switch(mode) {
    case COT_MODE_COP:
        s = "Futures & Options Combined";
        break;
    case COT_MODE_FO:
        s = "Futures Only";
        break;
    }
    return s;
}

//+------------------------------------------------------------------+
//| Overload                                                         |
//+------------------------------------------------------------------+
string CotGetDescription(ENUM_COT_CLASS_CO clss) {
    return CotGetDescription((ENUM_COT_CLASS) ((int) clss));
}

//+------------------------------------------------------------------+
//| Overload                                                         |
//+------------------------------------------------------------------+
string CotGetColClause(ENUM_COT_CLASS_CO clss) {
    return CotGetColClause((ENUM_COT_CLASS) ((int) clss));
}

//+------------------------------------------------------------------+
//| Overload                                                         |
//+------------------------------------------------------------------+
ENUM_COT_REPORT CotGetReportType(ENUM_COT_CLASS_CO clss, ENUM_COT_MODE mode) {
    return CotGetReportType((ENUM_COT_CLASS) ((int) clss), mode);
}

//+------------------------------------------------------------------+
//| Overload                                                         |
//+------------------------------------------------------------------+
string CotGetTableName(ENUM_COT_CLASS clss) {
    return CotGetTableName(CotGetReportType(clss, COT_MODE_FO));
}

//+------------------------------------------------------------------+
//| Overload                                                         |
//+------------------------------------------------------------------+
string CotGetTableName(ENUM_COT_REPORT_CO report_type) {
    return CotGetTableName((ENUM_COT_REPORT) ((int) report_type));
}

//+------------------------------------------------------------------+
//| Overload                                                         |
//+------------------------------------------------------------------+
string CotGetTableName(ENUM_COT_CLASS_CO clss) {
    return CotGetTableName((ENUM_COT_CLASS) ((int) clss));
}

//+------------------------------------------------------------------+
//| Find the index of the value in the array.                        |
//+------------------------------------------------------------------+
int ArraySearch(const string &arr[], string value, bool case_sensitive = true) {
    int n = ArraySize(arr);
    string s1, s2;
    for (int i = 0; i < n; i++) {
        if (case_sensitive) {
            if (arr[i] == value)
                return i;
        } else {
            s1 = arr[i];
            s2 = value;
            StringToLower(s1);
            StringToLower(s2);
            if (s1 == s2)
                return i;
        }
    }
    return -1;
}
//+------------------------------------------------------------------+
