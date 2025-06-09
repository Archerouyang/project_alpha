#!/usr/bin/env python3
"""
初始化 reports 数据库，创建所需表结构。
"""
import sys
from pathlib import Path

# 获取项目根目录（上溯三层：文件->db->backend->project root）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from backend.db.reports import init_db

def main():
    db_path = Path(__file__).resolve().parent / 'reports.db'
    init_db()
    print(f"Initialized reports database at {db_path}")

if __name__ == '__main__':
    main() 