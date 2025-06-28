# backend/core/smart_cache.py
import os
import json
import hashlib
import pickle
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import pandas as pd
from pathlib import Path
import yaml

class SmartCache:
    """
    多层智能缓存系统
    - 内存缓存 + 磁盘缓存双层架构
    - 支持TTL过期策略
    - 线程安全设计
    - LRU内存管理
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式确保全局唯一缓存实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._access_times: Dict[str, float] = {}
        
        # 加载配置
        self._load_config()
        
        # 确保磁盘缓存目录存在
        os.makedirs(self.storage_path, exist_ok=True)
        
        print(f"SmartCache initialized: Memory limit={self.max_memory_entries}, Disk path={self.storage_path}")
        
        # 启动后台清理任务
        self._start_cleanup_thread()
    
    def _load_config(self):
        """加载缓存配置"""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'cache_config.yaml')
        
        # 默认配置
        default_config = {
            'cache': {
                'enabled': True,
                'storage_path': './cache_data',
                'data_ttl': 300,      # 5分钟
                'chart_ttl': 600,     # 10分钟  
                'analysis_ttl': 1800, # 30分钟
                'max_memory_entries': 1000,
                'max_disk_size_mb': 500,
                'cleanup_interval': 3600  # 1小时
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                config = default_config
                print(f"Config file not found, using defaults: {config_path}")
        except Exception as e:
            print(f"Error loading config, using defaults: {e}")
            config = default_config
        
        cache_config = config.get('cache', {})
        self.enabled = cache_config.get('enabled', True)
        self.storage_path = os.path.abspath(cache_config.get('storage_path', './cache_data'))
        self.data_ttl = cache_config.get('data_ttl', 300)
        self.chart_ttl = cache_config.get('chart_ttl', 600)
        self.analysis_ttl = cache_config.get('analysis_ttl', 1800)
        self.max_memory_entries = cache_config.get('max_memory_entries', 1000)
        self.max_disk_size_mb = cache_config.get('max_disk_size_mb', 500)
        self.cleanup_interval = cache_config.get('cleanup_interval', 3600)
    
    def _generate_key(self, cache_type: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [cache_type]
        for k, v in sorted(kwargs.items()):
            if isinstance(v, pd.DataFrame):
                # 对DataFrame生成哈希
                v = self._get_dataframe_hash(v)
            key_parts.append(f"{k}:{v}")
        return hashlib.md5('_'.join(key_parts).encode()).hexdigest()
    
    def _get_dataframe_hash(self, df: pd.DataFrame) -> str:
        """生成DataFrame的哈希值"""
        if df is None or df.empty:
            return "empty_df"
        
        # 基于数据形状、时间范围、关键价格信息生成哈希
        hash_components = [
            f"shape:{df.shape[0]}x{df.shape[1]}",
            f"start:{df.index[0]}",
            f"end:{df.index[-1]}",
        ]
        
        # 添加最新价格作为哈希组件
        if 'close' in df.columns:
            hash_components.append(f"last_close:{df['close'].iloc[-1]:.4f}")
        
        return hashlib.md5('_'.join(hash_components).encode()).hexdigest()[:16]
    
    def _get_disk_path(self, key: str, cache_type: str) -> str:
        """获取磁盘缓存文件路径"""
        subdir = os.path.join(self.storage_path, cache_type)
        os.makedirs(subdir, exist_ok=True)
        return os.path.join(subdir, f"{key}.cache")
    
    def _is_expired(self, entry: Dict[str, Any], ttl: int) -> bool:
        """检查缓存项是否过期"""
        if 'timestamp' not in entry:
            return True
        return time.time() - entry['timestamp'] > ttl
    
    def _evict_lru(self):
        """LRU策略清理内存缓存"""
        if len(self._memory_cache) <= self.max_memory_entries:
            return
        
        # 按访问时间排序，删除最久未使用的项
        sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
        num_to_remove = len(self._memory_cache) - self.max_memory_entries + 100  # 多删除一些避免频繁清理
        
        for key, _ in sorted_keys[:num_to_remove]:
            self._memory_cache.pop(key, None)
            self._access_times.pop(key, None)
        
        print(f"SmartCache: Evicted {num_to_remove} entries from memory cache")
    
    def _cleanup_expired_entries(self):
        """清理过期的缓存项"""
        current_time = time.time()
        
        # 清理内存缓存
        with self._cache_lock:
            expired_keys = []
            for key, entry in self._memory_cache.items():
                cache_type = entry.get('type', 'unknown')
                ttl = self._get_ttl_by_type(cache_type)
                if self._is_expired(entry, ttl):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._memory_cache.pop(key, None)
                self._access_times.pop(key, None)
        
        # 清理磁盘缓存
        self._cleanup_disk_cache()
        
        if expired_keys:
            print(f"SmartCache: Cleaned up {len(expired_keys)} expired entries")
    
    def _cleanup_disk_cache(self):
        """清理磁盘缓存中的过期文件"""
        try:
            for cache_type in ['data', 'chart', 'analysis']:
                cache_dir = os.path.join(self.storage_path, cache_type)
                if not os.path.exists(cache_dir):
                    continue
                
                ttl = self._get_ttl_by_type(cache_type)
                current_time = time.time()
                
                for filename in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, filename)
                    if os.path.isfile(file_path):
                        # 检查文件修改时间
                        if current_time - os.path.getmtime(file_path) > ttl:
                            os.remove(file_path)
        except Exception as e:
            print(f"Error during disk cache cleanup: {e}")
    
    def _get_ttl_by_type(self, cache_type: str) -> int:
        """根据缓存类型获取TTL"""
        ttl_map = {
            'data': self.data_ttl,
            'chart': self.chart_ttl,
            'analysis': self.analysis_ttl
        }
        return ttl_map.get(cache_type, 300)
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired_entries()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        print(f"SmartCache: Background cleanup thread started (interval: {self.cleanup_interval}s)")
    
    def _get_from_memory(self, key: str, cache_type: str) -> Optional[Any]:
        """从内存缓存获取数据"""
        if not self.enabled:
            return None
        
        with self._cache_lock:
            if key not in self._memory_cache:
                return None
            
            entry = self._memory_cache[key]
            ttl = self._get_ttl_by_type(cache_type)
            
            if self._is_expired(entry, ttl):
                del self._memory_cache[key]
                self._access_times.pop(key, None)
                return None
            
            # 更新访问时间
            self._access_times[key] = time.time()
            return entry['data']
    
    def _set_to_memory(self, key: str, data: Any, cache_type: str):
        """设置数据到内存缓存"""
        if not self.enabled:
            return
        
        with self._cache_lock:
            self._memory_cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'type': cache_type
            }
            self._access_times[key] = time.time()
            
            # 检查是否需要清理
            if len(self._memory_cache) > self.max_memory_entries:
                self._evict_lru()
    
    def _get_from_disk(self, key: str, cache_type: str) -> Optional[Any]:
        """从磁盘缓存获取数据"""
        if not self.enabled:
            return None
        
        try:
            file_path = self._get_disk_path(key, cache_type)
            if not os.path.exists(file_path):
                return None
            
            ttl = self._get_ttl_by_type(cache_type)
            if time.time() - os.path.getmtime(file_path) > ttl:
                os.remove(file_path)
                return None
            
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # 将数据加载到内存缓存
            self._set_to_memory(key, data, cache_type)
            return data
        
        except Exception as e:
            print(f"Error reading from disk cache {key}: {e}")
            return None
    
    def _set_to_disk(self, key: str, data: Any, cache_type: str):
        """设置数据到磁盘缓存"""
        if not self.enabled:
            return
        
        try:
            file_path = self._get_disk_path(key, cache_type)
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error writing to disk cache {key}: {e}")
    
    # 公共API方法
    
    def get_data_cache(self, symbol: str, interval: str) -> Optional[pd.DataFrame]:
        """获取数据缓存"""
        key = self._generate_key('data', symbol=symbol, interval=interval)
        
        # 先尝试内存缓存
        data = self._get_from_memory(key, 'data')
        if data is not None:
            print(f"SmartCache: Data cache HIT (memory) for {symbol}_{interval}")
            return data
        
        # 尝试磁盘缓存
        data = self._get_from_disk(key, 'data')
        if data is not None:
            print(f"SmartCache: Data cache HIT (disk) for {symbol}_{interval}")
            return data
        
        print(f"SmartCache: Data cache MISS for {symbol}_{interval}")
        return None
    
    def set_data_cache(self, symbol: str, interval: str, data: pd.DataFrame):
        """设置数据缓存"""
        if data is None or data.empty:
            return
        
        key = self._generate_key('data', symbol=symbol, interval=interval)
        self._set_to_memory(key, data, 'data')
        self._set_to_disk(key, data, 'data')
        print(f"SmartCache: Data cached for {symbol}_{interval}")
    
    def get_chart_cache(self, symbol: str, interval: str, data_hash: str) -> Optional[bytes]:
        """获取图表缓存"""
        key = self._generate_key('chart', symbol=symbol, interval=interval, data_hash=data_hash)
        
        # 先尝试内存缓存
        data = self._get_from_memory(key, 'chart')
        if data is not None:
            print(f"SmartCache: Chart cache HIT (memory) for {symbol}_{interval}")
            return data
        
        # 尝试磁盘缓存
        data = self._get_from_disk(key, 'chart')
        if data is not None:
            print(f"SmartCache: Chart cache HIT (disk) for {symbol}_{interval}")
            return data
        
        print(f"SmartCache: Chart cache MISS for {symbol}_{interval}")
        return None
    
    def set_chart_cache(self, symbol: str, interval: str, data_hash: str, chart_bytes: bytes):
        """设置图表缓存"""
        if not chart_bytes:
            return
        
        key = self._generate_key('chart', symbol=symbol, interval=interval, data_hash=data_hash)
        self._set_to_memory(key, chart_bytes, 'chart')
        self._set_to_disk(key, chart_bytes, 'chart')
        print(f"SmartCache: Chart cached for {symbol}_{interval}")
    
    def get_analysis_cache(self, symbol: str, data_hash: str) -> Optional[str]:
        """获取AI分析缓存"""
        key = self._generate_key('analysis', symbol=symbol, data_hash=data_hash)
        
        # 先尝试内存缓存
        data = self._get_from_memory(key, 'analysis')
        if data is not None:
            print(f"SmartCache: Analysis cache HIT (memory) for {symbol}")
            return data
        
        # 尝试磁盘缓存
        data = self._get_from_disk(key, 'analysis')
        if data is not None:
            print(f"SmartCache: Analysis cache HIT (disk) for {symbol}")
            return data
        
        print(f"SmartCache: Analysis cache MISS for {symbol}")
        return None
    
    def set_analysis_cache(self, symbol: str, data_hash: str, analysis: str):
        """设置AI分析缓存"""
        if not analysis:
            return
        
        key = self._generate_key('analysis', symbol=symbol, data_hash=data_hash)
        self._set_to_memory(key, analysis, 'analysis')
        self._set_to_disk(key, analysis, 'analysis')
        print(f"SmartCache: Analysis cached for {symbol}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._cache_lock:
            memory_stats = {
                'total_entries': len(self._memory_cache),
                'max_entries': self.max_memory_entries,
                'usage_percent': (len(self._memory_cache) / self.max_memory_entries) * 100
            }
        
        # 磁盘使用统计
        disk_stats = {'total_size_mb': 0, 'file_count': 0}
        try:
            if os.path.exists(self.storage_path):
                total_size = 0
                file_count = 0
                for root, dirs, files in os.walk(self.storage_path):
                    for file in files:
                        if file.endswith('.cache'):
                            file_count += 1
                            total_size += os.path.getsize(os.path.join(root, file))
                
                disk_stats = {
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'file_count': file_count,
                    'max_size_mb': self.max_disk_size_mb
                }
        except Exception as e:
            print(f"Error calculating disk stats: {e}")
        
        return {
            'enabled': self.enabled,
            'memory': memory_stats,
            'disk': disk_stats,
            'ttl_settings': {
                'data_ttl': self.data_ttl,
                'chart_ttl': self.chart_ttl,
                'analysis_ttl': self.analysis_ttl
            }
        }
    
    def clear_expired_cache(self) -> int:
        """清理过期缓存，返回清理的项目数"""
        print("SmartCache: Starting manual cache cleanup...")
        initial_memory_count = len(self._memory_cache)
        
        # 获取磁盘文件数量
        initial_disk_count = 0
        try:
            if os.path.exists(self.storage_path):
                for root, dirs, files in os.walk(self.storage_path):
                    initial_disk_count += len([f for f in files if f.endswith('.cache')])
        except Exception:
            pass
        
        self._cleanup_expired_entries()
        
        final_memory_count = len(self._memory_cache)
        final_disk_count = 0
        try:
            if os.path.exists(self.storage_path):
                for root, dirs, files in os.walk(self.storage_path):
                    final_disk_count += len([f for f in files if f.endswith('.cache')])
        except Exception:
            pass
        
        cleared_count = (initial_memory_count - final_memory_count) + (initial_disk_count - final_disk_count)
        print(f"SmartCache: Cleared {cleared_count} expired entries")
        return cleared_count
    
    def clear_all_cache(self) -> int:
        """清空所有缓存"""
        print("SmartCache: Clearing ALL cache...")
        
        total_cleared = 0
        
        # 清空内存缓存
        with self._cache_lock:
            total_cleared += len(self._memory_cache)
            self._memory_cache.clear()
            self._access_times.clear()
        
        # 清空磁盘缓存
        try:
            if os.path.exists(self.storage_path):
                import shutil
                shutil.rmtree(self.storage_path)
                os.makedirs(self.storage_path, exist_ok=True)
        except Exception as e:
            print(f"Error clearing disk cache: {e}")
        
        print(f"SmartCache: Cleared {total_cleared} total entries")
        return total_cleared

# 全局缓存实例
_cache_instance = None

def get_cache() -> SmartCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SmartCache()
    return _cache_instance 