# -*- coding: utf-8 -*-
"""
新闻数据ORM模型
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3
import json

from utils.core.logger_manager import get_logger

class NewsORM:
    """新闻数据ORM"""
    
    def __init__(self, db_path: str = "quant_trading.db"):
        self.db_path = db_path
        self.logger = get_logger("news_orm")
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建新闻表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crypto_news (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT,
                        url TEXT UNIQUE NOT NULL,
                        source TEXT NOT NULL,
                        published_at DATETIME NOT NULL,
                        sentiment TEXT,
                        impact_score REAL,
                        keywords TEXT,
                        category TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_valid BOOLEAN DEFAULT 1
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_published_at ON crypto_news(published_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_source ON crypto_news(source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_category ON crypto_news(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_sentiment ON crypto_news(sentiment)")
                
                conn.commit()
                self.logger.info("新闻数据表初始化完成")
                
        except Exception as e:
            self.logger.error("初始化新闻数据表失败: {}".format(e))
            raise
    
    def save_news_item(self, news_data: Dict[str, Any]) -> bool:
        """保存新闻项"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在
                cursor.execute("SELECT id FROM crypto_news WHERE url = ?", (news_data['url'],))
                if cursor.fetchone():
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE crypto_news SET
                            title = ?, content = ?, source = ?, published_at = ?,
                            sentiment = ?, impact_score = ?, keywords = ?, category = ?,
                            updated_at = CURRENT_TIMESTAMP, is_valid = ?
                        WHERE url = ?
                    """, (
                        news_data['title'], news_data['content'], news_data['source'],
                        news_data['published_at'], news_data.get('sentiment'),
                        news_data.get('impact_score'), news_data.get('keywords'),
                        news_data.get('category'), news_data.get('is_valid', True),
                        news_data['url']
                    ))
                else:
                    # 插入新记录
                    cursor.execute("""
                        INSERT INTO crypto_news (
                            title, content, url, source, published_at,
                            sentiment, impact_score, keywords, category, is_valid
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        news_data['title'], news_data['content'], news_data['url'],
                        news_data['source'], news_data['published_at'],
                        news_data.get('sentiment'), news_data.get('impact_score'),
                        news_data.get('keywords'), news_data.get('category'),
                        news_data.get('is_valid', True)
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error("保存新闻项失败: {}".format(e))
            return False
    
    def get_news_by_time_range(self, start_time: datetime, end_time: datetime, limit: int = 50) -> List[Dict[str, Any]]:
        """根据时间范围获取新闻"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM crypto_news
                    WHERE published_at BETWEEN ? AND ? AND is_valid = 1
                    ORDER BY published_at DESC
                    LIMIT ?
                """, (start_time, end_time, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error("根据时间范围获取新闻失败: {}".format(e))
            return []
    
    def get_news_by_keywords(self, keywords: List[str], start_time: datetime, end_time: datetime, limit: int = 50) -> List[Dict[str, Any]]:
        """根据关键词获取新闻"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建关键词查询条件
                keyword_conditions = []
                params = []
                
                for keyword in keywords:
                    keyword_conditions.append("(title LIKE ? OR content LIKE ? OR keywords LIKE ?)")
                    keyword_pattern = "%{}%".format(keyword)
                    params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
                
                params.extend([start_time, end_time, limit])
                
                query = """
                    SELECT * FROM crypto_news
                    WHERE ({})
                    AND published_at BETWEEN ? AND ? AND is_valid = 1
                    ORDER BY published_at DESC
                    LIMIT ?
                """.format(' OR '.join(keyword_conditions))
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error("根据关键词获取新闻失败: {}".format(e))
            return []
    
    def get_news_by_sentiment(self, sentiment: str, hours_back: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """根据情感分析获取新闻"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                start_time = datetime.now() - timedelta(hours=hours_back)
                
                cursor.execute("""
                    SELECT * FROM crypto_news
                    WHERE sentiment = ? AND published_at >= ? AND is_valid = 1
                    ORDER BY published_at DESC
                    LIMIT ?
                """, (sentiment, start_time, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error("根据情感获取新闻失败: {}".format(e))
            return []
    
    def update_news_analysis(self, news_id: int, sentiment: str, impact_score: float, keywords: List[str]) -> bool:
        """更新新闻分析结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE crypto_news SET
                        sentiment = ?, impact_score = ?, keywords = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (sentiment, impact_score, ','.join(keywords), news_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error("更新新闻分析结果失败: {}".format(e))
            return False
    
    def get_news_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """获取新闻统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_time = datetime.now() - timedelta(hours=hours_back)
                
                # 总新闻数
                cursor.execute("SELECT COUNT(*) FROM crypto_news WHERE published_at >= ? AND is_valid = 1", (start_time,))
                total_count = cursor.fetchone()[0]
                
                # 按来源统计
                cursor.execute("""
                    SELECT source, COUNT(*) as count FROM crypto_news
                    WHERE published_at >= ? AND is_valid = 1
                    GROUP BY source
                """, (start_time,))
                source_stats = dict(cursor.fetchall())
                
                # 按情感统计
                cursor.execute("""
                    SELECT sentiment, COUNT(*) as count FROM crypto_news
                    WHERE published_at >= ? AND is_valid = 1 AND sentiment IS NOT NULL
                    GROUP BY sentiment
                """, (start_time,))
                sentiment_stats = dict(cursor.fetchall())
                
                return {
                    'total_count': total_count,
                    'source_stats': source_stats,
                    'sentiment_stats': sentiment_stats,
                    'time_range_hours': hours_back
                }
                
        except Exception as e:
            self.logger.error("获取新闻统计信息失败: {}".format(e))
            return {}
    
    def cleanup_old_news(self, days_to_keep: int = 30) -> int:
        """清理旧新闻数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_time = datetime.now() - timedelta(days=days_to_keep)
                
                cursor.execute("DELETE FROM crypto_news WHERE published_at < ?", (cutoff_time,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                self.logger.info("清理了 {} 条旧新闻数据".format(deleted_count))
                return deleted_count
                
        except Exception as e:
            self.logger.error("清理旧新闻数据失败: {}".format(e))
            return 0