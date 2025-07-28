"""
SQLite Database Module for Call Analyzer
Handles all database operations for audio analysis data storage and retrieval.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

class CallAnalyzerDB:
    def __init__(self, db_path: str = "call_analyzer.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    department TEXT,
                    role TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create analysis_results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    analysis_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    processed_at TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    industry TEXT NOT NULL CHECK (industry IN ('eCommerce', 'Telecom', 'Healthcare', 'Travel', 'Real Estate')),
                    duration REAL DEFAULT 0.0,
                    participants INTEGER DEFAULT 0,
                    sentiment TEXT DEFAULT 'neutral',
                    transcription_text TEXT,
                    transcription_confidence REAL DEFAULT 0.0,
                    transcription_language TEXT DEFAULT 'en-US',
                    conversation_data TEXT, -- JSON string
                    intents_data TEXT, -- JSON string
                    overall_sentiment_label TEXT DEFAULT 'neutral',
                    overall_sentiment_score REAL DEFAULT 0.0,
                    participant_sentiments TEXT, -- JSON string
                    topics_data TEXT, -- JSON string
                    summary TEXT,
                    quality_score REAL DEFAULT 0.0,
                    insights TEXT, -- JSON string
                    file_path TEXT, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create processing_status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_status (
                    analysis_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES analysis_results (analysis_id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed_at ON analysis_results(processed_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_industry ON analysis_results(industry)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON analysis_results(sentiment)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON analysis_results(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON processing_status(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_active ON users(is_active)')
            
            conn.commit()
            
            # Insert default users if table is empty
            self._insert_default_users()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def save_analysis_result(self, analysis_data: Dict[str, Any]) -> bool:
        """Save complete analysis result to database."""
        try:
            print(f"[DEBUG] save_analysis_result called with analysis_id: {analysis_data.get('analysis_id')}")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Extract data from analysis_data
                analysis_id = analysis_data.get('analysis_id')
                user_id = analysis_data.get('user_id', 'default_user')
                processed_at = analysis_data.get('processed_at')
                source_file = analysis_data.get('source_file')
                industry = analysis_data.get('industry')
                duration = analysis_data.get('duration', 0.0)
                participants = analysis_data.get('participants', 0)
                sentiment = analysis_data.get('sentiment', 'neutral')   
                
                # Validate required fields
                if not analysis_id:
                    print(f"[ERROR] Missing analysis_id")
                    return False
                if not processed_at:
                    print(f"[ERROR] Missing processed_at")
                    return False
                if not source_file:
                    print(f"[ERROR] Missing source_file")
                    return False
                if not industry:
                    print(f"[ERROR] Missing industry")
                    return False
                
                # Validate industry constraint
                valid_industries = ['eCommerce', 'Telecom', 'Healthcare', 'Travel', 'Real Estate']
                if industry not in valid_industries:
                    print(f"[ERROR] Invalid industry '{industry}'. Must be one of: {valid_industries}")
                    return False
                
                # Transcription data
                transcription = analysis_data.get('transcription', {})
                transcription_text = transcription.get('full_text', '')
                transcription_confidence = transcription.get('confidence', 0.0)
                transcription_language = transcription.get('language', 'en-US')
                
                # Conversation data
                conversation_data = json.dumps(analysis_data.get('conversation', []))
                
                # Analysis data
                analysis = analysis_data.get('analysis', {})
                intents_data = json.dumps(analysis.get('intents', []))                 
                overall_sentiment = analysis.get('overall_sentiment', {})
                overall_sentiment_label = overall_sentiment.get('label', 'neutral')
                overall_sentiment_score = overall_sentiment.get('score', 0.0)
                
                participant_sentiments = json.dumps(analysis.get('participant_sentiments', []))
                topics_data = json.dumps(analysis.get('topic_analysis', {}))
                qualityMetrics = analysis.get('quality_metrics', {})                 
                summary = analysis['conversation_summary']
                quality_score = qualityMetrics.get('overall_score', 0.0)
                insights = json.dumps(analysis.get('insights', []))
                
                
                if duration == 0.0 and len(transcription_text) == 0 and len(conversation_data) <= 2:
                    print(f"[WARNING] Saving analysis with empty/incomplete data:")
                
                # File paths (if available)
                file_path = analysis_data.get('file_path', '')
                
                print(f"[DEBUG] About to execute INSERT query...")
                
                cursor.execute('''
                    INSERT OR REPLACE INTO analysis_results (
                        analysis_id, user_id, processed_at, source_file, industry, duration, participants,
                        sentiment, transcription_text, transcription_confidence, transcription_language,
                        conversation_data, intents_data, overall_sentiment_label, overall_sentiment_score,
                        participant_sentiments, topics_data, summary, quality_score, insights, file_path
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                ''', (
                    analysis_id, user_id, processed_at, source_file, industry, duration, participants,
                    sentiment, transcription_text, transcription_confidence, transcription_language,
                    conversation_data, intents_data, overall_sentiment_label, overall_sentiment_score,
                    participant_sentiments, topics_data, summary, quality_score, insights, file_path
                ))
                
                print(f"[DEBUG] INSERT executed, about to commit...")
                conn.commit()
                
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Database integrity error: {e}")
            print(f"[ERROR] Analysis ID: {analysis_data.get('analysis_id', 'UNKNOWN')}")
            print(f"[ERROR] Industry: {analysis_data.get('industry', 'UNKNOWN')}")
            return False
        except sqlite3.Error as e:
            print(f"[ERROR] Database error: {e}")
            print(f"[ERROR] Analysis ID: {analysis_data.get('analysis_id', 'UNKNOWN')}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"[ERROR] Error saving analysis result: {e}")
            print(f"[ERROR] Analysis ID: {analysis_data.get('analysis_id', 'UNKNOWN')}")
            print(f"[ERROR] Industry: {analysis_data.get('industry', 'UNKNOWN')}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM analysis_results WHERE analysis_id = ?', (analysis_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_analysis_dict(row)
                return None
                
        except Exception as e:
            print(f"Error retrieving analysis result: {e}")
            return None
    
    def get_all_analysis_results(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve all analysis results with pagination."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM analysis_results 
                    ORDER BY processed_at DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                rows = cursor.fetchall()
                
                return [self._row_to_analysis_dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error retrieving analysis results: {e}")
            return []
    
    def get_analysis_history(self, limit: int = 50, date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """Get analysis history for history page with optional date filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query with optional date filters
                query = '''
                    SELECT analysis_id, processed_at, source_file, industry, duration, 
                           participants, sentiment, summary, quality_score
                    FROM analysis_results 
                '''
                params = []
                
                # Add date filters if provided
                where_conditions = []
                if date_from:
                    where_conditions.append("DATE(processed_at) >= ?")
                    params.append(date_from)
                if date_to:
                    where_conditions.append("DATE(processed_at) <= ?")
                    params.append(date_to)
                
                if where_conditions:
                    query += "WHERE " + " AND ".join(where_conditions) + " "
                
                query += "ORDER BY processed_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error retrieving analysis history: {e}")
            return []
    
   
    def save_processing_status(self, analysis_id: str, status: str, progress: int = 0, message: str = "") -> bool:
        """Save or update processing status."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO processing_status (
                        analysis_id, status, progress, message
                    ) VALUES (?, ?, ?, ?)
                ''', (analysis_id, status, progress, message))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving processing status: {e}")
            return False
    
    def get_processing_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get processing status by analysis ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM processing_status WHERE analysis_id = ?', (analysis_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            print(f"Error retrieving processing status: {e}")
            return None
    
    
    def get_database_stats(self, date_from: Optional[str] = None, date_to: Optional[str] = None, industry: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive database statistics for homepage with optional filters."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause based on filters
                where_conditions = []
                params = []
                
                if date_from:
                    where_conditions.append("DATE(processed_at) >= ?")
                    params.append(date_from)
                
                if date_to:
                    where_conditions.append("DATE(processed_at) <= ?")
                    params.append(date_to)
                
                if industry and industry.lower() != 'all':
                    where_conditions.append("LOWER(industry) = LOWER(?)")
                    params.append(industry)
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                stats = {}
                
                # Total records
                cursor.execute(f"SELECT COUNT(*) FROM analysis_results {where_clause}", params)
                stats['total_analyses'] = cursor.fetchone()[0]
                
                # Industry breakdown
                cursor.execute(f'''
                    SELECT industry, COUNT(*) as count, 
                           AVG(duration) as avg_duration,
                           SUM(CASE WHEN LOWER(sentiment) = 'positive' THEN 1 ELSE 0 END) as positive_count,
                           SUM(CASE WHEN LOWER(sentiment) = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                           SUM(CASE WHEN LOWER(sentiment) = 'negative' THEN 1 ELSE 0 END) as negative_count
                    FROM analysis_results 
                    {where_clause}
                    GROUP BY industry
                    ORDER BY count DESC
                ''', params)
                industry_stats = []
                for row in cursor.fetchall():
                    industry_stats.append({
                        'industry': row[0],
                        'count': row[1],
                        'avg_duration': round(row[2], 2) if row[2] else 0,
                        'positive_count': row[3],
                        'neutral_count': row[4],
                        'negative_count': row[5]
                    })
                stats['industry_breakdown'] = industry_stats
                
                # Sentiment distribution
                cursor.execute(f'''
                    SELECT sentiment, COUNT(*) as count
                    FROM analysis_results 
                    {where_clause}
                    GROUP BY sentiment
                ''', params)
                sentiment_stats = []
                for row in cursor.fetchall():
                    sentiment_stats.append({
                        'sentiment': row[0],
                        'count': row[1]
                    })
                stats['sentiment_distribution'] = sentiment_stats
                
                # Daily activity (with date filtering)
                daily_where = where_clause
                daily_params = params.copy()
                
                # If no date filter specified, default to last 30 days
                if not date_from and not date_to:
                    if where_clause:
                        daily_where += " AND processed_at >= datetime('now', '-30 days')"
                    else:
                        daily_where = "WHERE processed_at >= datetime('now', '-30 days')"
                
                cursor.execute(f'''
                    SELECT DATE(processed_at) as date, COUNT(*) as count
                    FROM analysis_results 
                    {daily_where}
                    GROUP BY DATE(processed_at)
                    ORDER BY date DESC
                    LIMIT 30
                ''', daily_params)
                daily_activity = []
                for row in cursor.fetchall():
                    daily_activity.append({
                        'date': row[0],
                        'count': row[1]
                    })
                stats['daily_activity'] = daily_activity
                
                # Quality metrics
                cursor.execute(f'''
                    SELECT 
                        AVG(quality_score) as avg_quality,
                        MIN(quality_score) as min_quality,
                        MAX(quality_score) as max_quality,
                        AVG(duration) as avg_duration,
                        AVG(participants) as avg_participants,
                        SUM(CASE WHEN LOWER(sentiment) = 'positive' THEN 1 ELSE 0 END) as total_positive,
                        SUM(CASE WHEN LOWER(sentiment) = 'negative' THEN 1 ELSE 0 END) as total_negative
                    FROM analysis_results
                    {where_clause}
                ''', params)
                row = cursor.fetchone()
                stats['quality_metrics'] = {
                    'avg_quality': round(row[0], 2) if row[0] else 0,
                    'min_quality': round(row[1], 2) if row[1] else 0,
                    'max_quality': round(row[2], 2) if row[2] else 0,
                    'avg_duration': round(row[3], 2) if row[3] else 0,
                    'avg_participants': round(row[4], 2) if row[4] else 0,
                    'total_positive': row[5] if row[5] else 0,
                    'total_negative': row[6] if row[6] else 0
                }
                
                # Recent activity
                cursor.execute(f'''
                    SELECT analysis_id, processed_at, industry, sentiment, quality_score
                    FROM analysis_results 
                    {where_clause}
                    ORDER BY processed_at DESC 
                    LIMIT 10
                ''', params)
                recent_activity = []
                for row in cursor.fetchall():
                    recent_activity.append({
                        'analysis_id': row[0],
                        'processed_at': row[1],
                        'industry': row[2],
                        'sentiment': row[3],
                        'quality_score': row[4]
                    })
                stats['recent_activity'] = recent_activity
                
                return stats
                
        except Exception as e:
            print(f"Error retrieving database stats: {e}")
            return {}
    
    def get_top_user_performance_by_sentiment(self, date_from: Optional[str] = None, date_to: Optional[str] = None, industry: Optional[str] = None) -> Dict[str, Any]:
        """Get top 5 user performance by sentiment with optional filters."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause based on filters
                where_conditions = []
                params = []
                
                if date_from:
                    where_conditions.append("DATE(ar.processed_at) >= ?")
                    params.append(date_from)
                
                if date_to:
                    where_conditions.append("DATE(ar.processed_at) <= ?")
                    params.append(date_to)
                
                if industry and industry.lower() != 'all':
                    where_conditions.append("LOWER(ar.industry) = LOWER(?)")
                    params.append(industry)
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # Get top 5 users by positive sentiment count
                cursor.execute(f'''
                    SELECT 
                        u.user_id,
                        u.username,
                        u.full_name,
                        u.role,
                        u.department,
                        COUNT(ar.analysis_id) as total_calls,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'positive' THEN 1 ELSE 0 END) as positive_count,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'negative' THEN 1 ELSE 0 END) as negative_count,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                        AVG(ar.quality_score) as avg_quality_score,
                        SUM(ar.duration) as total_duration,
                        ROUND(
                            (SUM(CASE WHEN LOWER(ar.sentiment) = 'positive' THEN 1 ELSE 0 END) * 100.0) / 
                            NULLIF(COUNT(ar.analysis_id), 0), 2
                        ) as positive_percentage
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    GROUP BY u.user_id, u.username, u.full_name, u.role, u.department
                    HAVING COUNT(ar.analysis_id) > 0
                    ORDER BY positive_count DESC, positive_percentage DESC
                    LIMIT 5
                ''', params)
                
                top_positive_users = []
                for row in cursor.fetchall():
                    top_positive_users.append({
                        'user_id': row[0],
                        'username': row[1],
                        'full_name': row[2],
                        'role': row[3],
                        'department': row[4],
                        'total_calls': row[5],
                        'positive_count': row[6],
                        'negative_count': row[7],
                        'neutral_count': row[8],
                        'avg_quality_score': round(row[9], 2) if row[9] else 0,
                        'total_duration': round(row[10], 2) if row[10] else 0,
                        'positive_percentage': row[11] if row[11] else 0
                    })
                
                # Get top 5 users by negative sentiment count (lowest is better)
                cursor.execute(f'''
                    SELECT 
                        u.user_id,
                        u.username,
                        u.full_name,
                        u.role,
                        u.department,
                        COUNT(ar.analysis_id) as total_calls,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'positive' THEN 1 ELSE 0 END) as positive_count,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'negative' THEN 1 ELSE 0 END) as negative_count,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                        AVG(ar.quality_score) as avg_quality_score,
                        SUM(ar.duration) as total_duration,
                        ROUND(
                            (SUM(CASE WHEN LOWER(ar.sentiment) = 'negative' THEN 1 ELSE 0 END) * 100.0) / 
                            NULLIF(COUNT(ar.analysis_id), 0), 2
                        ) as negative_percentage
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    GROUP BY u.user_id, u.username, u.full_name, u.role, u.department
                    HAVING COUNT(ar.analysis_id) > 0
                    ORDER BY negative_count ASC, negative_percentage ASC
                    LIMIT 5
                ''', params)
                
                top_low_negative_users = []
                for row in cursor.fetchall():
                    top_low_negative_users.append({
                        'user_id': row[0],
                        'username': row[1],
                        'full_name': row[2],
                        'role': row[3],
                        'department': row[4],
                        'total_calls': row[5],
                        'positive_count': row[6],
                        'negative_count': row[7],
                        'neutral_count': row[8],
                        'avg_quality_score': round(row[9], 2) if row[9] else 0,
                        'total_duration': round(row[10], 2) if row[10] else 0,
                        'negative_percentage': row[11] if row[11] else 0
                    })
                
                # Get top 5 users by overall performance (combination of positive sentiment and quality score)
                cursor.execute(f'''
                    SELECT 
                        u.user_id,
                        u.username,
                        u.full_name,
                        u.role,
                        u.department,
                        COUNT(ar.analysis_id) as total_calls,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'positive' THEN 1 ELSE 0 END) as positive_count,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'negative' THEN 1 ELSE 0 END) as negative_count,
                        SUM(CASE WHEN LOWER(ar.sentiment) = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                        AVG(ar.quality_score) as avg_quality_score,
                        SUM(ar.duration) as total_duration,
                        ROUND(
                            (SUM(CASE WHEN LOWER(ar.sentiment) = 'positive' THEN 1 ELSE 0 END) * 100.0) / 
                            NULLIF(COUNT(ar.analysis_id), 0), 2
                        ) as positive_percentage,
                        ROUND(
                            (AVG(ar.quality_score) * 0.6) + 
                            ((SUM(CASE WHEN LOWER(ar.sentiment) = 'positive' THEN 1 ELSE 0 END) * 100.0) / 
                             NULLIF(COUNT(ar.analysis_id), 0) * 0.4), 2
                        ) as performance_score
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    GROUP BY u.user_id, u.username, u.full_name, u.role, u.department
                    HAVING COUNT(ar.analysis_id) > 0
                    ORDER BY performance_score DESC
                    LIMIT 5
                ''', params)
                
                top_overall_performers = []
                for row in cursor.fetchall():
                    top_overall_performers.append({
                        'user_id': row[0],
                        'username': row[1],
                        'full_name': row[2],
                        'role': row[3],
                        'department': row[4],
                        'total_calls': row[5],
                        'positive_count': row[6],
                        'negative_count': row[7],
                        'neutral_count': row[8],
                        'avg_quality_score': round(row[9], 2) if row[9] else 0,
                        'total_duration': round(row[10], 2) if row[10] else 0,
                        'positive_percentage': row[11] if row[11] else 0,
                        'performance_score': row[12] if row[12] else 0
                    })
                
                return {
                    'top_positive_sentiment': top_positive_users,
                    'top_low_negative_sentiment': top_low_negative_users,
                    'top_overall_performance': top_overall_performers
                }
                
        except Exception as e:
            print(f"Error retrieving top user performance: {e}")
            return {
                'top_positive_sentiment': [],
                'top_low_negative_sentiment': [],
                'top_overall_performance': []
            }
    
    def get_available_industries(self) -> List[str]:
        """Get list of available industries (restricted to specified list)."""
        return ['eCommerce', 'Telecom', 'Healthcare', 'Travel', 'Real Estate']
    
    def get_analysis_results_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get analysis results for a specific user with pagination."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM analysis_results 
                    WHERE user_id = ?
                    ORDER BY processed_at DESC 
                    LIMIT ? OFFSET ?
                ''', (user_id, limit, offset))
                rows = cursor.fetchall()
                
                return [self._row_to_analysis_dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error retrieving analysis results for user {user_id}: {e}")
            return []
    
    def get_user_performance_metrics(self, user_id: str, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive performance metrics for a specific user/agent."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Base WHERE clause
                where_clause = "WHERE u.user_id = ?"
                params = [user_id]
                
                # Add date filters if provided
                if date_from:
                    where_clause += " AND DATE(ar.processed_at) >= ?"
                    params.append(date_from)
                if date_to:
                    where_clause += " AND DATE(ar.processed_at) <= ?"
                    params.append(date_to)
                
                # Get basic metrics
                cursor.execute(f'''
                    SELECT 
                        COUNT(ar.analysis_id) as total_calls,
                        AVG(ar.quality_score) as avg_quality_score,
                        AVG(ar.duration) as avg_call_duration,
                        SUM(ar.duration) as total_call_duration,
                        MIN(ar.processed_at) as first_call_date,
                        MAX(ar.processed_at) as last_call_date
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                ''', params)
                
                basic_metrics = dict(cursor.fetchone())
                
                # Get sentiment distribution
                cursor.execute(f'''
                    SELECT 
                        ar.overall_sentiment_label as sentiment,
                        COUNT(ar.analysis_id) as count,
                        AVG(ar.overall_sentiment_score) as avg_score
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    GROUP BY ar.overall_sentiment_label
                ''', params)
                
                sentiment_data = cursor.fetchall()
                sentiment_distribution = {}
                for row in sentiment_data:
                    sentiment_distribution[row['sentiment'] or 'neutral'] = {
                        'count': row['count'],
                        'avg_score': row['avg_score'] or 0
                    }
                
                # Get industry distribution
                cursor.execute(f'''
                    SELECT 
                        ar.industry,
                        COUNT(ar.analysis_id) as count,
                        AVG(ar.quality_score) as avg_quality
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    GROUP BY ar.industry
                ''', params)
                
                industry_data = cursor.fetchall()
                industry_distribution = {}
                for row in industry_data:
                    industry_distribution[row['industry']] = {
                        'count': row['count'],
                        'avg_quality': row['avg_quality'] or 0
                    }
                
                # Get quality score distribution
                cursor.execute(f'''
                    SELECT 
                        CASE 
                            WHEN ar.quality_score >= 8 THEN 'Excellent'
                            WHEN ar.quality_score >= 6 THEN 'Good'
                            WHEN ar.quality_score >= 4 THEN 'Fair'
                            ELSE 'Poor'
                        END as quality_category,
                        COUNT(ar.analysis_id) as count
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    GROUP BY quality_category
                ''', params)
                
                quality_data = cursor.fetchall()
                quality_distribution = {}
                for row in quality_data:
                    quality_distribution[row['quality_category']] = row['count']
                
                # Get recent performance trend (last 30 days)
                cursor.execute(f'''
                    SELECT 
                        DATE(ar.processed_at) as call_date,
                        COUNT(ar.analysis_id) as daily_calls,
                        AVG(ar.quality_score) as daily_avg_quality
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    AND DATE(ar.processed_at) >= DATE('now', '-30 days')
                    GROUP BY DATE(ar.processed_at)
                    ORDER BY call_date DESC
                ''', params)
                
                trend_data = cursor.fetchall()
                performance_trend = [dict(row) for row in trend_data]
                
                # Get top intents
                cursor.execute(f'''
                    SELECT 
                        json_extract(ar.intents_data, '$[0].intent') as top_intent,
                        COUNT(ar.analysis_id) as count
                    FROM users u
                    LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                    {where_clause}
                    AND ar.intents_data IS NOT NULL
                    GROUP BY top_intent
                    ORDER BY count DESC 
                ''', params)
                
                intent_data = cursor.fetchall()
                top_intents = [dict(row) for row in intent_data if row['top_intent']]
                
                return {
                    'user_id': user_id,
                    'basic_metrics': basic_metrics,
                    'sentiment_distribution': sentiment_distribution,
                    'industry_distribution': industry_distribution,
                    'quality_distribution': quality_distribution,
                    'performance_trend': performance_trend,
                    'top_intents': intent_data,
                    'date_range': {
                        'from': date_from,
                        'to': date_to
                    }
                }
                
        except Exception as e:
            print(f"Error retrieving user performance metrics for {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'basic_metrics': {},
                'sentiment_distribution': {},
                'industry_distribution': {},
                'quality_distribution': {},
                'performance_trend': [],
                'top_intents': []
            }
    
    def clear_all_data(self) -> bool:
        """Clear all data from tables without dropping the table structure."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear data from tables
                cursor.execute('DELETE FROM processing_status')
                cursor.execute('DELETE FROM analysis_results')
                cursor.execute('DELETE FROM users')
                
                conn.commit()
                print("All data cleared successfully")
                return True
                
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False
    
    def reset_database(self) -> bool:
        """Reset database by dropping all tables and recreating them."""
        try:
            # Drop all tables
            self.drop_all_tables()
            
            # Recreate tables
            self.init_database()
            
            print("Database reset successfully")
            return True
            
        except Exception as e:
            print(f"Error resetting database: {e}")
            return False
    
    def _insert_default_users(self):
        """Insert default users if the users table is empty."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if users table is empty
                cursor.execute('SELECT COUNT(*) FROM users')
                count = cursor.fetchone()[0]
                
                if count == 0:
                    # Insert default users
                    default_users = [                       
                        ('agent_001', 'Agent Smith', 'agent.smith@company.com', 'John Smith', 'Support', 'agent'),
                        ('agent_002', 'Agent Johnson', 'agent.johnson@company.com', 'Sarah Johnson', 'Support', 'agent'),
                        ('agent_003', 'Agent Brown', 'manager.brown@company.com', 'Michael Brown', 'Support', 'agent'),
                        ('admin_001', 'Admin User', 'admin@company.com', 'System Administrator', 'IT', 'admin'),
                    ]
                    
                    cursor.executemany('''
                        INSERT INTO users (user_id, username, email, full_name, department, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', default_users)
                    
                    conn.commit()
                    print("Default users inserted successfully")
                    
        except Exception as e:
            print(f"Error inserting default users: {e}")
    
    def get_all_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all users from the database with their call metrics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if active_only:
                    cursor.execute('''
                        SELECT 
                            u.user_id  as userId, 
                            u.username as userName, 
                            u.email, 
                            u.full_name as fullName, 
                            u.department, 
                            u.role, 
                            u.is_active as isActive, 
                            u.created_at as createdAt,
                            COALESCE(SUM(ar.duration), 0) as totalCallDuration,
                            COUNT(ar.analysis_id) as totalCalls,
                            SUM(CASE WHEN ar.sentiment = 'positive' THEN 1 ELSE 0 END) as positiveCount,
                            SUM(CASE WHEN ar.sentiment = 'negative' THEN 1 ELSE 0 END) as negativeCount,
                            SUM(CASE WHEN ar.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutralCount
                        FROM users u
                        LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                        WHERE u.is_active = 1
                        GROUP BY u.user_id, u.username, u.email, u.full_name, u.department, u.role, u.is_active, u.created_at
                        ORDER BY u.username
                    ''')
                else:
                    cursor.execute('''
                        SELECT 
                            u.user_id as userId, 
                            u.username as userName, 
                            u.email, 
                            u.full_name as fullName, 
                            u.department, 
                            u.role, 
                            u.is_active as isActive, 
                            u.created_at as createdAt,
                            COALESCE(SUM(ar.duration), 0) as totalCallDuration,
                            COUNT(ar.analysis_id) as totalCalls,
                            SUM(CASE WHEN ar.sentiment = 'positive' THEN 1 ELSE 0 END) as positiveCount,
                            SUM(CASE WHEN ar.sentiment = 'negative' THEN 1 ELSE 0 END) as negativeCount,
                            SUM(CASE WHEN ar.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutralCount
                        FROM users u
                        LEFT JOIN analysis_results ar ON u.user_id = ar.user_id
                        GROUP BY u.user_id, u.username, u.email, u.full_name, u.department, u.role, u.is_active, u.created_at
                        ORDER BY u.username
                    ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error retrieving users: {e}")
            return []
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user by user_id."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, email, full_name, department, role, is_active, created_at
                    FROM users 
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            print(f"Error retrieving user {user_id}: {e}")
            return None
    
      
    def get_topic_statistics(self, date_from: Optional[str] = None, date_to: Optional[str] = None, industry: Optional[str] = None) -> Dict[str, Any]:
        """Get topic distribution statistics from analysis results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query with optional filters
                query = '''
                    SELECT topics_data, industry, processed_at
                    FROM analysis_results 
                    WHERE topics_data IS NOT NULL AND topics_data != ''
                '''
                params = []
                
                if date_from:
                    query += ' AND processed_at >= ?'
                    params.append(date_from)
                
                if date_to:
                    query += ' AND processed_at <= ?'
                    params.append(date_to)
                
                if industry:
                    query += ' AND industry = ?'
                    params.append(industry)
                
                query += ' ORDER BY processed_at DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Process topic data
                topic_counts = {}
                topic_scores = {}
                industry_topics = {}
                total_conversations = len(rows)
                
                for row in rows:
                    try:
                        topics_data = json.loads(row[0]) if row[0] else {}
                        row_industry = row[1]
                        
                        # Extract dominant topics
                        dominant_topics = topics_data.get('dominant_topics', [])
                        topic_scores_data = topics_data.get('topic_scores', {})
                        
                        # Count dominant topics
                        for topic_info in dominant_topics:
                            if isinstance(topic_info, (list, tuple)) and len(topic_info) >= 2:
                                topic_name = topic_info[0]
                                topic_score = topic_info[1]
                            elif isinstance(topic_info, dict):
                                topic_name = topic_info.get('topic', '')
                                topic_score = topic_info.get('score', 0)
                            else:
                                continue
                            
                            if topic_name:
                                # Overall topic counts
                                if topic_name not in topic_counts:
                                    topic_counts[topic_name] = 0
                                    topic_scores[topic_name] = []
                                
                                topic_counts[topic_name] += 1
                                topic_scores[topic_name].append(topic_score)
                                
                                # Industry-specific topics
                                if row_industry not in industry_topics:
                                    industry_topics[row_industry] = {}
                                
                                if topic_name not in industry_topics[row_industry]:
                                    industry_topics[row_industry][topic_name] = 0
                                
                                industry_topics[row_industry][topic_name] += 1
                        
                        # Also process topic_scores for additional topics
                        for topic_name, score in topic_scores_data.items():
                            if score > 0.1:  # Only include topics with meaningful scores
                                if topic_name not in topic_counts:
                                    topic_counts[topic_name] = 0
                                    topic_scores[topic_name] = []
                                
                                topic_counts[topic_name] += 1
                                topic_scores[topic_name].append(score)
                    
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        print(f"Error processing topic data: {e}")
                        continue
                
                # Calculate averages and percentages
                topic_statistics = []
                for topic, count in topic_counts.items():
                    avg_score = sum(topic_scores[topic]) / len(topic_scores[topic]) if topic_scores[topic] else 0
                    percentage = (count / total_conversations * 100) if total_conversations > 0 else 0
                    
                    topic_statistics.append({
                        'topic': topic,
                        'count': count,
                        'percentage': round(percentage, 1),
                        'avg_score': round(avg_score, 3),
                        'formatted_name': topic.replace('_', ' ').title()
                    })
                
                # Sort by count (most frequent first)
                topic_statistics.sort(key=lambda x: x['count'], reverse=True)
                
                # Prepare industry breakdown
                industry_breakdown = {}
                for industry, topics in industry_topics.items():
                    industry_breakdown[industry] = [
                        {
                            'topic': topic,
                            'count': count,
                            'percentage': round(count / sum(topics.values()) * 100, 1) if sum(topics.values()) > 0 else 0,
                            'formatted_name': topic.replace('_', ' ').title()
                        }
                        for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)
                    ]
                
                return {
                    'total_conversations': total_conversations,
                    'topic_distribution': topic_statistics[:15],  # Top 15 topics
                    'industry_breakdown': industry_breakdown,
                    'total_unique_topics': len(topic_counts)
                }
                
        except Exception as e:
            print(f"Error retrieving topic statistics: {e}")
            return {
                'total_conversations': 0,
                'topic_distribution': [],
                'industry_breakdown': {},
                'total_unique_topics': 0
            }
    
    def get_topic_sentiment_analysis(self, date_from=None, date_to=None, industry=None):
        """Get topic-sentiment analysis data for dashboard with optional filters."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build the WHERE clause with filters
                where_conditions = [
                    "topics_data IS NOT NULL",
                    "participant_sentiments IS NOT NULL"
                ]
                params = []

                if date_from:
                    where_conditions.append(" DATE(processed_at) >= ?")
                    params.append(date_from)
                if date_to:
                    where_conditions.append(" DATE(processed_at) <= ?")
                    params.append(date_to) 
                
                if industry:
                    where_conditions.append("industry = ?")
                    params.append(industry)
                
                where_clause = " AND ".join(where_conditions)
                
                # Get all analysis results with topics and sentiment data
                query = f'''
                    SELECT topics_data, participant_sentiments, overall_sentiment_label, overall_sentiment_score
                    FROM analysis_results 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                '''
                print(f"qsentiment query {query}")
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                if not results:
                    return {
                        'topicSentiments': [],
                        'totalAnalyses': 0,
                        'avgSentimentScore': 0.0
                    }
                
                # Process topic-sentiment data
                topic_sentiment_map = {}
                total_sentiment_score = 0
                valid_sentiment_count = 0
                
                for topics_json, sentiments_json, overall_sentiment, sentiment_score in results:
                    try:
                        # Parse topics data 
                        if topics_json:
                            topics_data = json.loads(topics_json) if isinstance(topics_json, str) else topics_json
                            
                            # Parse sentiment data
                            if sentiments_json:
                                sentiments_data = json.loads(sentiments_json) if isinstance(sentiments_json, str) else sentiments_json
                                
                                # Extract topics from different possible structures
                                topics = []
                                if isinstance(topics_data, dict):
                                    if 'topics' in topics_data:
                                        topics = topics_data['topics']
                                    elif 'topic_scores' in topics_data:
                                        topics = list(topics_data['topic_scores'].keys())
                                    else:
                                        topics = list(topics_data.keys())
                                elif isinstance(topics_data, list):
                                    topics = [t.get('topic', str(t)) if isinstance(t, dict) else str(t) for t in topics_data]
                                
                                # Process each topic
                                for topic in topics[:5]:  # Top 5 topics
                                    topic_name = topic.replace('_', ' ').title()
                                    
                                    if topic_name not in topic_sentiment_map:
                                        topic_sentiment_map[topic_name] = {
                                            'positive': 0,
                                            'neutral': 0,
                                            'negative': 0,
                                            'total': 0
                                        }
                                    
                                    # Determine sentiment for this conversation
                                    if overall_sentiment:
                                        sentiment_label = overall_sentiment.lower()
                                        if sentiment_label in ['positive', 'satisfied', 'happy']:
                                            topic_sentiment_map[topic_name]['positive'] += 1
                                        elif sentiment_label in ['negative', 'frustrated', 'angry', 'concerned']:
                                            topic_sentiment_map[topic_name]['negative'] += 1
                                        else:
                                            topic_sentiment_map[topic_name]['neutral'] += 1
                                    else:
                                        topic_sentiment_map[topic_name]['neutral'] += 1
                                    
                                    topic_sentiment_map[topic_name]['total'] += 1
                        
                        # Track overall sentiment score
                        if sentiment_score is not None and sentiment_score > 0:
                            total_sentiment_score += sentiment_score
                            valid_sentiment_count += 1
                            
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        print(f"Error processing record: {e}")
                        continue
                
                # Convert to percentage format
                topic_sentiments = []
                for topic, counts in topic_sentiment_map.items():
                    if counts['total'] > 0:
                        topic_sentiments.append({
                            'topic': topic,
                            'positive': round((counts['positive'] / counts['total']) * 100, 1),
                            'neutral': round((counts['neutral'] / counts['total']) * 100, 1),
                            'negative': round((counts['negative'] / counts['total']) * 100, 1),
                            'total_conversations': counts['total']
                        })
                
                # Sort by total conversations (most discussed topics first)
                topic_sentiments.sort(key=lambda x: x['total_conversations'], reverse=True)
                
                avg_sentiment_score = (total_sentiment_score / valid_sentiment_count) if valid_sentiment_count > 0 else 0.0
                
                return {
                    'topicSentiments': topic_sentiments[:10],  # Top 10 topics
                    'totalAnalyses': len(results),
                    'avgSentimentScore': round(avg_sentiment_score, 2)
                }
                
        except Exception as e:
            print(f"Error in get_topic_sentiment_analysis: {e}")
            return {
                'topicSentiments': [],
                'totalAnalyses': 0,
                'avgSentimentScore': 0.0
            }
