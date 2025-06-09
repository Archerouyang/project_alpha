import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

# Path to the SQLite database file
DB_PATH = Path(__file__).resolve().parent / "reports.db"


def init_db() -> None:
    """
    初始化 SQLite 数据库，创建 reports 表。
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        symbol TEXT NOT NULL,
        interval TEXT NOT NULL,
        filepath TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        latest_close REAL,
        bollinger_upper REAL,
        bollinger_middle REAL,
        bollinger_lower REAL,
        stoch_rsi_k REAL,
        stoch_rsi_d REAL
    )
    """
    )
    conn.commit()
    conn.close()


def insert_report(
    user_id: Optional[str],
    symbol: str,
    interval: str,
    filepath: str,
    generated_at: str,
    latest_close: Optional[float],
    bollinger_upper: Optional[float],
    bollinger_middle: Optional[float],
    bollinger_lower: Optional[float],
    stoch_rsi_k: Optional[float],
    stoch_rsi_d: Optional[float]
) -> None:
    """
    向 reports 表插入一条新的报告记录。
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO reports (
            user_id, symbol, interval, filepath, generated_at,
            latest_close, bollinger_upper, bollinger_middle,
            bollinger_lower, stoch_rsi_k, stoch_rsi_d
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id, symbol, interval, filepath, generated_at,
            latest_close, bollinger_upper, bollinger_middle,
            bollinger_lower, stoch_rsi_k, stoch_rsi_d
        )
    )
    conn.commit()
    conn.close()


def get_reports(
    user_id: Optional[str] = None,
    date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查询报告记录，可选根据 user_id 和生成日期过滤。
    日期格式应为 YYYY-MM-DD。
    返回列表，每项为 dict。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    query = "SELECT * FROM reports WHERE 1=1"
    params: List[Any] = []
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    if date:
        # 匹配开始为 date 的 generated_at
        query += " AND generated_at LIKE ?"
        params.append(f"{date}%")
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    # 转换为普通 dict 返回
    return [dict(row) for row in rows] 