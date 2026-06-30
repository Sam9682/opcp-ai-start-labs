"""Database operations for AI-StaticWebsite"""
import sqlite3
import os
from datetime import datetime

DB_PATH = '/app/data/billing.db'

def init_db():
    """Initialize database with required tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create billing configuration table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing_config (
            id INTEGER PRIMARY KEY,
            base_cost_per_second REAL DEFAULT 0.001,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create usage tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            page_url TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_seconds REAL,
            cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default billing config if not exists
    cursor.execute('SELECT COUNT(*) FROM billing_config')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO billing_config (base_cost_per_second) VALUES (0.001)')
    
    conn.commit()
    conn.close()

def log_page_visit(user_id, session_id, page_url):
    """Log start of page visit"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO usage_tracking (user_id, session_id, page_url, start_time)
        VALUES (?, ?, ?, ?)
    ''', (user_id, session_id, page_url, datetime.now()))
    
    visit_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return visit_id

def end_page_visit(visit_id):
    """End page visit and calculate cost"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get base cost
    cursor.execute('SELECT base_cost_per_second FROM billing_config LIMIT 1')
    base_cost = cursor.fetchone()[0]
    
    # Update visit with end time and cost
    cursor.execute('''
        UPDATE usage_tracking 
        SET end_time = ?, 
            duration_seconds = (julianday(?) - julianday(start_time)) * 86400,
            cost = (julianday(?) - julianday(start_time)) * 86400 * ?
        WHERE id = ?
    ''', (datetime.now(), datetime.now(), datetime.now(), base_cost, visit_id))
    
    conn.commit()
    conn.close()

def get_user_usage(user_id, days=30):
    """Get user usage statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_visits,
            COALESCE(SUM(duration_seconds), 0) as total_duration,
            COALESCE(SUM(cost), 0) as total_cost,
            DATE(created_at) as visit_date
        FROM usage_tracking 
        WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
        GROUP BY DATE(created_at)
        ORDER BY visit_date DESC
    ''', (user_id, days))
    
    daily_usage = cursor.fetchall()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_visits,
            COALESCE(SUM(duration_seconds), 0) as total_duration,
            COALESCE(SUM(cost), 0) as total_cost
        FROM usage_tracking 
        WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
    ''', (user_id, days))
    
    summary = cursor.fetchone()
    conn.close()
    
    return {
        'summary': {
            'total_visits': summary[0],
            'total_duration': summary[1],
            'total_cost': summary[2]
        },
        'daily': daily_usage
    }
