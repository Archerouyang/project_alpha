#!/usr/bin/env python3
"""
缓存管理器 - 用于管理智能缓存系统
支持清理、初始化、大小检查等功能
"""
import os
import sys
import shutil
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def get_cache_size(cache_dir="cache_data"):
    """计算缓存目录总大小"""
    total_size = 0
    if os.path.exists(cache_dir):
        for dirpath, dirnames, filenames in os.walk(cache_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
    return total_size

def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def count_cache_files(cache_dir="cache_data"):
    """计算缓存文件数量"""
    if not os.path.exists(cache_dir):
        return {"data": 0, "chart": 0, "analysis": 0, "total": 0}
    
    counts = {"data": 0, "chart": 0, "analysis": 0, "total": 0}
    
    for category in ["data", "chart", "analysis"]:
        category_dir = os.path.join(cache_dir, category)
        if os.path.exists(category_dir):
            counts[category] = len([f for f in os.listdir(category_dir) if f.endswith('.cache')])
    
    counts["total"] = sum(counts[k] for k in ["data", "chart", "analysis"])
    return counts

def clear_cache(cache_dir="cache_data", category=None):
    """清理缓存
    
    Args:
        cache_dir: 缓存目录路径
        category: 要清理的类别 ('data', 'chart', 'analysis'), None表示全部
    """
    if not os.path.exists(cache_dir):
        print(f"❌ 缓存目录不存在: {cache_dir}")
        return 0
    
    cleared_count = 0
    
    if category:
        # 清理特定类别
        category_dir = os.path.join(cache_dir, category)
        if os.path.exists(category_dir):
            files = [f for f in os.listdir(category_dir) if f.endswith('.cache')]
            for file in files:
                os.remove(os.path.join(category_dir, file))
                cleared_count += 1
            print(f"✅ 清理了 {category} 缓存: {cleared_count} 个文件")
        else:
            print(f"❌ 类别目录不存在: {category_dir}")
    else:
        # 清理所有缓存
        for category in ["data", "chart", "analysis"]:
            category_dir = os.path.join(cache_dir, category)
            if os.path.exists(category_dir):
                files = [f for f in os.listdir(category_dir) if f.endswith('.cache')]
                for file in files:
                    os.remove(os.path.join(category_dir, file))
                    cleared_count += 1
        print(f"✅ 清理了所有缓存: {cleared_count} 个文件")
    
    return cleared_count

def init_cache_dirs(cache_dir="cache_data"):
    """初始化缓存目录结构"""
    categories = ["data", "chart", "analysis"]
    created_dirs = []
    
    for category in categories:
        category_dir = os.path.join(cache_dir, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir, exist_ok=True)
            created_dirs.append(category)
    
    if created_dirs:
        print(f"✅ 创建了缓存目录: {', '.join(created_dirs)}")
    else:
        print("✅ 缓存目录结构已存在")

def show_cache_status(cache_dir="cache_data"):
    """显示缓存状态"""
    print("📊 === 缓存状态 ===")
    
    if not os.path.exists(cache_dir):
        print("❌ 缓存目录不存在")
        return
    
    # 计算大小和文件数
    total_size = get_cache_size(cache_dir)
    file_counts = count_cache_files(cache_dir)
    
    print(f"📁 缓存目录: {cache_dir}")
    print(f"💾 总大小: {format_size(total_size)}")
    print(f"📄 文件数量:")
    print(f"   数据缓存: {file_counts['data']} 个")
    print(f"   图表缓存: {file_counts['chart']} 个")
    print(f"   分析缓存: {file_counts['analysis']} 个")
    print(f"   总计: {file_counts['total']} 个")

def clear_expired_cache():
    """使用智能缓存系统清理过期缓存"""
    try:
        from backend.core.smart_cache import get_cache
        cache = get_cache()
        cleared_count = cache.clear_expired_cache()
        print(f"✅ 智能缓存系统清理了 {cleared_count} 个过期条目")
        return cleared_count
    except Exception as e:
        print(f"❌ 智能缓存清理失败: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="缓存管理器")
    parser.add_argument("action", choices=["status", "clear", "init", "clear-expired"], 
                       help="要执行的操作")
    parser.add_argument("--category", choices=["data", "chart", "analysis"], 
                       help="缓存类别（仅用于clear操作）")
    parser.add_argument("--cache-dir", default="cache_data", 
                       help="缓存目录路径（默认: cache_data）")
    
    args = parser.parse_args()
    
    print("🚀 缓存管理器启动")
    print("=" * 40)
    
    if args.action == "status":
        show_cache_status(args.cache_dir)
        
    elif args.action == "init":
        init_cache_dirs(args.cache_dir)
        
    elif args.action == "clear":
        cleared = clear_cache(args.cache_dir, args.category)
        if cleared > 0:
            print(f"💾 释放了缓存空间")
            
    elif args.action == "clear-expired":
        cleared = clear_expired_cache()
        
    print("\n🏁 操作完成")

if __name__ == "__main__":
    main() 