#!/usr/bin/env python3
"""
清理过期报告和索引。默认保留最近7天的报告。
用法: python scripts/cleanup_reports.py [days_to_keep]
"""
import os
import sys
from pathlib import Path

# 将项目根目录添加到 sys.path，确保可以直接执行该脚本
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from datetime import datetime, timedelta
from backend.db.reports import DB_PATH
import sqlite3


def cleanup(days_to_keep: int = 7):
    # 计算日期阈值
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    cutoff_ts = cutoff.timestamp()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 获取所有报告记录
    c.execute("SELECT id, filepath FROM reports")
    rows = c.fetchall()

    deleted = 0
    for report_id, filepath in rows:
        try:
            # 检查文件修改时间
            if os.path.exists(filepath):
                mtime = os.path.getmtime(filepath)
                if mtime < cutoff_ts:
                    os.remove(filepath)
                    # 尝试删除父目录，如果空则删除
                    parent_dir = os.path.dirname(filepath)
                    if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                    # 从数据库中删除记录
                    c.execute("DELETE FROM reports WHERE id = ?", (report_id,))
                    deleted += 1
                    print(f"Deleted expired report: {filepath}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    conn.commit()
    conn.close()
    print(f"Cleanup complete. Deleted {deleted} reports older than {days_to_keep} days.")


if __name__ == '__main__':
    try:
        days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    except ValueError:
        print("Invalid days_to_keep, using default 7 days.")
        days = 7
    cleanup(days) 