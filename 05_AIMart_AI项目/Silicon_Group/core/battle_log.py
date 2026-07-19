"""
📁 作战日志系统 (Battle Log) — 状态持久化与断点恢复 (SQLite Version)

职责:
  1. 标准化日志记录（时间戳/会话ID/Agent角色/任务/结果/成本）
  2. 状态快照：每个任务完成后强制执行"状态落盘"
  3. 断点恢复：扫描未完成任务，从断点处唤醒
  4. 会话元数据管理

设计原则:
  - 日志和状态存储于 SQLite 数据库中，实现强一致性和高性能
  - 向后兼容部分基于文件的日志输出（为旧系统和审查使用）
"""
import os
import json
from datetime import datetime
from core.database import get_connection

LOG_DIR = "battle_logs"

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def write_log(session_id: str, stage: str, target: str, content: str):
    """写入一条标准化日志到 SQLite"""
    ensure_log_dir()
    
    # 写入文件（兼容旧模块读取）
    filename = f"{LOG_DIR}/{session_id}.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n---\n## [{timestamp}] 目标: {target} | 阶段: {stage}\n{content}\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(entry)
        
    # 写入 SQLite
    conn = get_connection()
    conn.execute(
        "INSERT INTO battle_logs (session_id, stage, target, content) VALUES (?, ?, ?, ?)",
        (session_id, stage, target, content)
    )
    conn.commit()
    conn.close()

def generate_session_id() -> str:
    """生成唯一会话 ID"""
    return datetime.now().strftime("OP_%Y%m%d_%H%M%S")

# ===== 状态快照系统 (State Snapshot) =====

def save_snapshot(session_id: str, stage: str, context: dict):
    """保存状态快照到 SQLite"""
    conn = get_connection()
    # Replace existing snapshot for this stage
    conn.execute(
        "INSERT OR REPLACE INTO snapshots (session_id, stage, context) VALUES (?, ?, ?)",
        (session_id, stage, json.dumps(context, ensure_ascii=False))
    )
    conn.commit()
    conn.close()

    write_log(session_id, "SNAPSHOT", stage, f"状态快照已保存: {stage}")

def load_snapshot(session_id: str, stage: str = None) -> dict:
    """从 SQLite 加载状态快照"""
    conn = get_connection()
    
    if stage:
        row = conn.execute(
            "SELECT context FROM snapshots WHERE session_id = ? AND stage = ?", 
            (session_id, stage)
        ).fetchone()
        conn.close()
        return json.loads(row['context']) if row else {}
    else:
        rows = conn.execute(
            "SELECT stage, context, timestamp FROM snapshots WHERE session_id = ? ORDER BY timestamp ASC", 
            (session_id,)
        ).fetchall()
        conn.close()
        
        snapshots = {}
        for row in rows:
            snapshots[row['stage']] = {
                "timestamp": row['timestamp'],
                "session_id": session_id,
                "stage": row['stage'],
                "context": json.loads(row['context']),
            }
        return snapshots

def get_unfinished_sessions() -> list:
    """扫描未完成的会话（有快照但无 FINAL_REPORT 日志的）"""
    conn = get_connection()
    
    # 找到有快照的 session_ids
    sessions = conn.execute("SELECT DISTINCT session_id FROM snapshots").fetchall()
    unfinished = []
    
    for session in sessions:
        session_id = session['session_id']
        
        # 检查是否有完成标志的日志
        has_final = conn.execute(
            "SELECT COUNT(*) as cnt FROM battle_logs WHERE session_id = ? AND (stage = 'FINAL_REPORT' OR content LIKE '%FINAL_REPORT%')",
            (session_id,)
        ).fetchone()['cnt'] > 0
        
        if not has_final:
            # 获取最后快照
            last_snapshot = conn.execute(
                "SELECT stage, timestamp FROM snapshots WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1",
                (session_id,)
            ).fetchone()
            
            stage_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM snapshots WHERE session_id = ?",
                (session_id,)
            ).fetchone()['cnt']
            
            if last_snapshot:
                unfinished.append({
                    "session_id": session_id,
                    "last_stage": last_snapshot['stage'],
                    "stage_count": stage_count,
                    "snapshot_time": last_snapshot['timestamp'],
                })
                
    conn.close()
    return unfinished

def clear_snapshot(session_id: str):
    """清除指定会话的快照（任务完成后调用）"""
    conn = get_connection()
    conn.execute("DELETE FROM snapshots WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_session_summary(session_id: str) -> dict:
    """获取会话摘要"""
    conn = get_connection()
    
    logs = conn.execute(
        "SELECT timestamp, target, stage, content FROM battle_logs WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    ).fetchall()
    
    stage_list = []
    has_final = False
    
    for row in logs:
        if row['stage'] == 'FINAL_REPORT' or 'FINAL_REPORT' in row['content']:
            has_final = True
            
        stage_list.append({
            "timestamp": row['timestamp'],
            "target": row['target'],
            "stage": row['stage'],
            "detail_preview": row['content'][:100],
        })
        
    conn.close()
    
    return {
        "session_id": session_id,
        "status": "completed" if has_final else "in_progress",
        "stages": stage_list,
        "stage_count": len(stage_list),
    }

def get_logs_summary() -> dict:
    """获取所有日志的摘要统计"""
    conn = get_connection()
    
    session_ids = conn.execute(
        "SELECT DISTINCT session_id FROM battle_logs ORDER BY timestamp DESC LIMIT 20"
    ).fetchall()
    
    conn.close()
    
    sessions = [get_session_summary(row['session_id']) for row in session_ids]
    unfinished = get_unfinished_sessions()

    # Fallback to files if DB is empty
    if not session_ids and os.path.exists(LOG_DIR):
        log_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".md")]
        return {
            "total_sessions": len(log_files),
            "recent_sessions": [],
            "unfinished_sessions": unfinished,
            "has_unfinished": len(unfinished) > 0,
        }

    # Count total unique sessions in DB
    conn = get_connection()
    total_count = conn.execute("SELECT COUNT(DISTINCT session_id) as cnt FROM battle_logs").fetchone()['cnt']
    conn.close()

    return {
        "total_sessions": total_count,
        "recent_sessions": sessions[:10],
        "unfinished_sessions": unfinished,
        "has_unfinished": len(unfinished) > 0,
    }

