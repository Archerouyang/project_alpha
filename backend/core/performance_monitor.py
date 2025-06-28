# backend/core/performance_monitor.py
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import json
import os

class PerformanceMonitor:
    """
    性能监控系统
    - 记录各个步骤的耗时
    - 统计缓存命中率
    - 生成性能报告
    - 线程安全设计
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._monitor_lock = threading.RLock()
        
        # 操作记录存储
        self._operations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 缓存统计
        self._cache_stats = {
            'data': {'hits': 0, 'misses': 0},
            'chart': {'hits': 0, 'misses': 0},
            'analysis': {'hits': 0, 'misses': 0}
        }
        
        # 会话统计
        self._session_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'session_start': time.time()
        }
        
        print("PerformanceMonitor initialized")
    
    def track_operation(self, operation: str, duration: float, cache_hit: bool = False, 
                       metadata: Optional[Dict[str, Any]] = None):
        """记录操作性能数据"""
        with self._monitor_lock:
            timestamp = time.time()
            record = {
                'timestamp': timestamp,
                'duration': duration,
                'cache_hit': cache_hit,
                'metadata': metadata or {}
            }
            
            self._operations[operation].append(record)
            
            # 更新缓存统计
            if operation in ['data_fetch', 'chart_generation', 'llm_analysis']:
                cache_type = operation.replace('_fetch', '').replace('_generation', '').replace('llm_', '')
                if cache_type == 'data_fetch':
                    cache_type = 'data'
                elif cache_type == 'chart_generation':
                    cache_type = 'chart'
                elif cache_type == 'llm_analysis':
                    cache_type = 'analysis'
                
                if cache_type in self._cache_stats:
                    if cache_hit:
                        self._cache_stats[cache_type]['hits'] += 1
                    else:
                        self._cache_stats[cache_type]['misses'] += 1
        
        print(f"Performance: {operation} took {duration:.2f}s {'(cache hit)' if cache_hit else ''}")
    
    def track_request(self, success: bool, total_duration: float):
        """记录完整请求的统计信息"""
        with self._monitor_lock:
            self._session_stats['total_requests'] += 1
            
            if success:
                self._session_stats['successful_requests'] += 1
            else:
                self._session_stats['failed_requests'] += 1
            
            # 更新平均响应时间（加权平均）
            current_avg = self._session_stats['average_response_time']
            total_requests = self._session_stats['total_requests']
            
            self._session_stats['average_response_time'] = (
                (current_avg * (total_requests - 1) + total_duration) / total_requests
            )
    
    def get_operation_stats(self, operation: str, minutes: int = 60) -> Dict[str, Any]:
        """获取指定操作的统计信息"""
        with self._monitor_lock:
            if operation not in self._operations:
                return {'error': f'No data for operation: {operation}'}
            
            # 过滤指定时间范围内的记录
            cutoff_time = time.time() - (minutes * 60)
            recent_records = [
                record for record in self._operations[operation]
                if record['timestamp'] >= cutoff_time
            ]
            
            if not recent_records:
                return {'operation': operation, 'period_minutes': minutes, 'count': 0}
            
            durations = [r['duration'] for r in recent_records]
            cache_hits = sum(1 for r in recent_records if r['cache_hit'])
            
            return {
                'operation': operation,
                'period_minutes': minutes,
                'count': len(recent_records),
                'average_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'cache_hit_rate': (cache_hits / len(recent_records)) * 100 if recent_records else 0,
                'cache_hits': cache_hits,
                'cache_misses': len(recent_records) - cache_hits
            }
    
    def get_cache_hit_rates(self) -> Dict[str, float]:
        """获取各类缓存的命中率"""
        with self._monitor_lock:
            hit_rates = {}
            for cache_type, stats in self._cache_stats.items():
                total = stats['hits'] + stats['misses']
                if total > 0:
                    hit_rates[cache_type] = (stats['hits'] / total) * 100
                else:
                    hit_rates[cache_type] = 0.0
            
            return hit_rates
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取完整的性能统计信息"""
        with self._monitor_lock:
            # 基础会话统计
            session_duration = time.time() - self._session_stats['session_start']
            
            stats = {
                'session': {
                    **self._session_stats,
                    'session_duration_minutes': session_duration / 60,
                    'requests_per_minute': self._session_stats['total_requests'] / (session_duration / 60) if session_duration > 0 else 0
                },
                'cache_hit_rates': self.get_cache_hit_rates(),
                'cache_stats': dict(self._cache_stats),
                'operations': {}
            }
            
            # 各操作的统计
            key_operations = ['data_fetch', 'chart_generation', 'llm_analysis', 'report_generation']
            for operation in key_operations:
                stats['operations'][operation] = self.get_operation_stats(operation, 60)
            
            return stats
    
    def generate_report(self) -> str:
        """生成可读的性能报告"""
        stats = self.get_performance_stats()
        
        report_lines = [
            "=== AI金融分析服务性能报告 ===",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 会话统计:",
            f"  总请求数: {stats['session']['total_requests']}",
            f"  成功请求: {stats['session']['successful_requests']}",
            f"  失败请求: {stats['session']['failed_requests']}",
            f"  成功率: {(stats['session']['successful_requests'] / max(stats['session']['total_requests'], 1)) * 100:.1f}%",
            f"  平均响应时间: {stats['session']['average_response_time']:.2f}秒",
            f"  请求频率: {stats['session']['requests_per_minute']:.1f}次/分钟",
            "",
            "🎯 缓存命中率:",
        ]
        
        for cache_type, hit_rate in stats['cache_hit_rates'].items():
            cache_display = {
                'data': '数据获取',
                'chart': '图表生成', 
                'analysis': 'AI分析'
            }.get(cache_type, cache_type)
            
            report_lines.append(f"  {cache_display}: {hit_rate:.1f}%")
        
        report_lines.extend([
            "",
            "⏱️ 各步骤性能 (最近1小时):"
        ])
        
        operation_display = {
            'data_fetch': '数据获取',
            'chart_generation': '图表生成',
            'llm_analysis': 'AI分析',
            'report_generation': '报告生成'
        }
        
        for operation, display_name in operation_display.items():
            op_stats = stats['operations'].get(operation, {})
            if op_stats.get('count', 0) > 0:
                report_lines.extend([
                    f"  {display_name}:",
                    f"    请求次数: {op_stats['count']}",
                    f"    平均耗时: {op_stats['average_duration']:.2f}秒",
                    f"    最快: {op_stats['min_duration']:.2f}秒",
                    f"    最慢: {op_stats['max_duration']:.2f}秒",
                    f"    缓存命中率: {op_stats['cache_hit_rate']:.1f}%"
                ])
        
        # 性能建议
        report_lines.extend([
            "",
            "💡 性能分析:"
        ])
        
        # 基于统计数据给出建议
        overall_hit_rate = sum(stats['cache_hit_rates'].values()) / len(stats['cache_hit_rates']) if stats['cache_hit_rates'] else 0
        
        if overall_hit_rate < 50:
            report_lines.append("  ⚠️ 缓存命中率较低，建议增加缓存TTL或检查缓存策略")
        elif overall_hit_rate > 80:
            report_lines.append("  ✅ 缓存效果良好，性能优化显著")
        else:
            report_lines.append("  📈 缓存效果中等，还有优化空间")
        
        if stats['session']['average_response_time'] > 20:
            report_lines.append("  ⚠️ 平均响应时间较长，建议检查瓶颈步骤")
        elif stats['session']['average_response_time'] < 5:
            report_lines.append("  ✅ 响应时间优秀，缓存效果显著")
        
        return "\n".join(report_lines)
    
    def save_report_to_file(self, filepath: Optional[str] = None) -> str:
        """保存性能报告到文件"""
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"performance_report_{timestamp}.txt"
        
        report = self.generate_report()
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Performance report saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error saving performance report: {e}")
            return ""
    
    def export_stats_json(self) -> str:
        """导出统计数据为JSON格式"""
        stats = self.get_performance_stats()
        
        # 添加时间戳
        stats['export_timestamp'] = datetime.now().isoformat()
        
        try:
            return json.dumps(stats, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error exporting stats to JSON: {e}")
            return "{}"
    
    def reset_stats(self):
        """重置所有统计数据"""
        with self._monitor_lock:
            self._operations.clear()
            
            for cache_type in self._cache_stats:
                self._cache_stats[cache_type] = {'hits': 0, 'misses': 0}
            
            self._session_stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0.0,
                'session_start': time.time()
            }
        
        print("Performance statistics reset")

# 全局性能监控实例
_monitor_instance = None

def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控实例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance 