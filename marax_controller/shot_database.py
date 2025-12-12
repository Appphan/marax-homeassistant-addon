#!/usr/bin/env python3
"""
Shot Database Management
Stores and retrieves shot data from SQLite database
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from shot_analytics import calculate_shot_analytics

logger = logging.getLogger(__name__)

# Database path - use /config for Home Assistant addon persistence
DB_PATH = Path('/config/marax_shots.db')

def init_database():
    """Initialize the shot database with schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create shots table
        c.execute('''
            CREATE TABLE IF NOT EXISTS shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shot_number INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                device_id TEXT,
                total_time REAL,
                total_weight REAL,
                grind_weight REAL,
                ratio REAL,
                profile_id INTEGER,
                profile_name TEXT,
                phase_count INTEGER,
                pre_infusion_time REAL,
                time_to_first_drip REAL,
                peak_flow REAL,
                average_flow REAL,
                flow_stability REAL,
                peak_pressure REAL,
                average_pressure REAL,
                pre_infusion_pressure REAL,
                pressure_stability REAL,
                coffee_temp INTEGER,
                steam_temp INTEGER,
                target_weight_reached BOOLEAN,
                weight_deviation REAL,
                extraction_yield REAL,
                phase_metrics TEXT,
                phase_transitions TEXT,
                time_series_data TEXT,
                analytics_data TEXT,
                quality_score REAL,
                extraction_yield_percent REAL,
                estimated_tds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP,
                source TEXT DEFAULT 'esp32'
            )
        ''')
        
        # Add analytics columns if they don't exist (for existing databases)
        try:
            c.execute('ALTER TABLE shots ADD COLUMN analytics_data TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            c.execute('ALTER TABLE shots ADD COLUMN quality_score REAL')
        except sqlite3.OperationalError:
            pass
        
        try:
            c.execute('ALTER TABLE shots ADD COLUMN extraction_yield_percent REAL')
        except sqlite3.OperationalError:
            pass
        
        try:
            c.execute('ALTER TABLE shots ADD COLUMN estimated_tds REAL')
        except sqlite3.OperationalError:
            pass
        
        # Create indexes for fast queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_shots_timestamp ON shots(timestamp DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_shots_profile ON shots(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_shots_shot_number ON shots(shot_number)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_shots_created_at ON shots(created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_shots_quality_score ON shots(quality_score DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_shots_extraction_yield ON shots(extraction_yield_percent)')
        
        conn.commit()
        conn.close()
        logger.info("Shot database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize shot database: {e}")
        raise

def save_shot(shot_data):
    """Save a shot to the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if shot already exists (by shot_number and timestamp)
        c.execute('SELECT id FROM shots WHERE shot_number = ? AND timestamp = ?',
                  (shot_data.get('shot_number'), shot_data.get('timestamp')))
        existing = c.fetchone()
        
        if existing:
            logger.info(f"Shot {shot_data.get('shot_number')} already exists, skipping")
            conn.close()
            return existing[0]
        
        # Extract nested data
        flow_data = shot_data.get('flow', {})
        pressure_data = shot_data.get('pressure', {})
        temp_data = shot_data.get('temperature', {})
        target_data = shot_data.get('target', {})
        
        # Calculate advanced analytics
        try:
            analytics = calculate_shot_analytics(shot_data)
            analytics_json = json.dumps(analytics)
            quality_score = analytics.get('quality', {}).get('overall_score', 0)
            extraction_yield_percent = analytics.get('extraction', {}).get('extraction_yield_percent', 0)
            estimated_tds = analytics.get('extraction', {}).get('estimated_tds', 0)
        except Exception as e:
            logger.warning(f"Error calculating analytics for shot {shot_data.get('shot_number')}: {e}")
            analytics_json = None
            quality_score = None
            extraction_yield_percent = None
            estimated_tds = None
        
        c.execute('''
            INSERT INTO shots (
                shot_number, timestamp, total_time, total_weight, grind_weight, ratio,
                profile_id, profile_name, phase_count,
                pre_infusion_time, time_to_first_drip, peak_flow, average_flow, flow_stability,
                peak_pressure, average_pressure, pre_infusion_pressure, pressure_stability,
                coffee_temp, steam_temp,
                target_weight_reached, weight_deviation, extraction_yield,
                phase_metrics, time_series_data, analytics_data, quality_score,
                extraction_yield_percent, estimated_tds, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            shot_data.get('shot_number'),
            shot_data.get('timestamp'),
            shot_data.get('total_time'),
            shot_data.get('total_weight'),
            shot_data.get('grind_weight'),
            shot_data.get('ratio'),
            shot_data.get('profile_id'),
            shot_data.get('profile_name'),
            shot_data.get('phase_count'),
            flow_data.get('pre_infusion_time'),
            flow_data.get('time_to_first_drip'),
            flow_data.get('peak'),
            flow_data.get('average'),
            flow_data.get('stability'),
            pressure_data.get('peak'),
            pressure_data.get('average'),
            pressure_data.get('pre_infusion'),
            pressure_data.get('stability'),
            temp_data.get('coffee'),
            temp_data.get('steam'),
            target_data.get('achieved'),
            target_data.get('deviation'),
            shot_data.get('extraction_yield'),
            json.dumps(shot_data.get('phases', [])),
            json.dumps(shot_data.get('data', [])),
            analytics_json,
            quality_score,
            extraction_yield_percent,
            estimated_tds,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        shot_id = c.lastrowid
        conn.close()
        
        logger.info(f"Saved shot {shot_data.get('shot_number')} to database (ID: {shot_id})")
        return shot_id
    except Exception as e:
        logger.error(f"Error saving shot: {e}")
        raise

def get_shots(limit=50, offset=0, profile_id=None, date_from=None, date_to=None):
    """Retrieve shots from database with optional filters"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT * FROM shots WHERE 1=1"
        params = []
        
        if profile_id is not None:
            query += " AND profile_id = ?"
            params.append(profile_id)
        
        if date_from:
            if isinstance(date_from, datetime):
                date_from = int(date_from.timestamp())
            query += " AND timestamp >= ?"
            params.append(date_from)
        
        if date_to:
            if isinstance(date_to, datetime):
                date_to = int(date_to.timestamp())
            query += " AND timestamp <= ?"
            params.append(date_to)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        # Convert rows to dictionaries and parse JSON fields
        shots = []
        for row in rows:
            shot = dict(row)
            # Parse JSON fields
            if shot['phase_metrics']:
                try:
                    shot['phase_metrics'] = json.loads(shot['phase_metrics'])
                except:
                    shot['phase_metrics'] = []
            else:
                shot['phase_metrics'] = []
                
            if shot['time_series_data']:
                try:
                    shot['time_series_data'] = json.loads(shot['time_series_data'])
                except:
                    shot['time_series_data'] = []
            else:
                shot['time_series_data'] = []
            
            # Parse analytics data
            if shot.get('analytics_data'):
                try:
                    shot['analytics'] = json.loads(shot['analytics_data'])
                except:
                    shot['analytics'] = None
            else:
                shot['analytics'] = None
                
            shots.append(shot)
        
        return shots
    except Exception as e:
        logger.error(f"Error retrieving shots: {e}")
        raise

def get_shot(shot_id):
    """Get a single shot by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM shots WHERE id = ?", (shot_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        shot = dict(row)
        # Parse JSON fields
        if shot['phase_metrics']:
            try:
                shot['phase_metrics'] = json.loads(shot['phase_metrics'])
            except:
                shot['phase_metrics'] = []
        else:
            shot['phase_metrics'] = []
            
        if shot['time_series_data']:
            try:
                shot['time_series_data'] = json.loads(shot['time_series_data'])
            except:
                shot['time_series_data'] = []
        else:
            shot['time_series_data'] = []
        
        # Parse analytics data
        if shot.get('analytics_data'):
            try:
                shot['analytics'] = json.loads(shot['analytics_data'])
            except:
                shot['analytics'] = None
        else:
            shot['analytics'] = None
        
        return shot
    except Exception as e:
        logger.error(f"Error retrieving shot {shot_id}: {e}")
        raise

def get_shot_stats(profile_id=None, date_from=None, date_to=None):
    """Get comprehensive aggregate statistics for shots"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        query = """SELECT 
            COUNT(*) as count,
            AVG(total_time) as avg_time,
            MIN(total_time) as min_time,
            MAX(total_time) as max_time,
            AVG(total_weight) as avg_weight,
            MIN(total_weight) as min_weight,
            MAX(total_weight) as max_weight,
            AVG(peak_pressure) as avg_peak_pressure,
            AVG(average_pressure) as avg_avg_pressure,
            AVG(peak_flow) as avg_peak_flow,
            AVG(average_flow) as avg_avg_flow,
            AVG(flow_stability) as avg_flow_stability,
            AVG(pressure_stability) as avg_pressure_stability,
            AVG(quality_score) as avg_quality_score,
            AVG(extraction_yield_percent) as avg_extraction_yield,
            AVG(estimated_tds) as avg_tds,
            SUM(CASE WHEN target_weight_reached = 1 THEN 1 ELSE 0 END) as target_achieved_count
            FROM shots WHERE 1=1"""
        params = []
        
        if profile_id is not None:
            query += " AND profile_id = ?"
            params.append(profile_id)
        
        if date_from:
            if isinstance(date_from, datetime):
                date_from = int(date_from.timestamp())
            query += " AND timestamp >= ?"
            params.append(date_from)
        
        if date_to:
            if isinstance(date_to, datetime):
                date_to = int(date_to.timestamp())
            query += " AND timestamp <= ?"
            params.append(date_to)
        
        c.execute(query, params)
        row = c.fetchone()
        conn.close()
        
        count = row[0] or 0
        target_achieved = row[17] or 0
        
        return {
            'count': count,
            'avg_time': round(row[1] or 0, 2),
            'min_time': round(row[2] or 0, 2),
            'max_time': round(row[3] or 0, 2),
            'avg_weight': round(row[4] or 0, 2),
            'min_weight': round(row[5] or 0, 2),
            'max_weight': round(row[6] or 0, 2),
            'avg_peak_pressure': round(row[7] or 0, 2),
            'avg_avg_pressure': round(row[8] or 0, 2),
            'avg_peak_flow': round(row[9] or 0, 2),
            'avg_avg_flow': round(row[10] or 0, 2),
            'avg_flow_stability': round(row[11] or 0, 2),
            'avg_pressure_stability': round(row[12] or 0, 2),
            'avg_quality_score': round(row[13] or 0, 2),
            'avg_extraction_yield': round(row[14] or 0, 2),
            'avg_tds': round(row[15] or 0, 3),
            'target_achieved_count': target_achieved,
            'target_achieved_percent': round((target_achieved / count * 100) if count > 0 else 0, 1)
        }
    except Exception as e:
        logger.error(f"Error getting shot stats: {e}")
        raise


def get_best_shots(limit=10, profile_id=None):
    """Get best shots by quality score"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT * FROM shots WHERE quality_score IS NOT NULL"
        params = []
        
        if profile_id is not None:
            query += " AND profile_id = ?"
            params.append(profile_id)
        
        query += " ORDER BY quality_score DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        shots = []
        for row in rows:
            shot = dict(row)
            if shot.get('analytics_data'):
                try:
                    shot['analytics'] = json.loads(shot['analytics_data'])
                except:
                    shot['analytics'] = None
            shots.append(shot)
        
        return shots
    except Exception as e:
        logger.error(f"Error getting best shots: {e}")
        raise


def get_trend_data(days=30, profile_id=None):
    """Get trend data for the last N days"""
    try:
        from datetime import timedelta
        date_from = datetime.now() - timedelta(days=days)
        timestamp_from = int(date_from.timestamp())
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        query = """SELECT 
            DATE(datetime(timestamp, 'unixepoch')) as date,
            COUNT(*) as count,
            AVG(quality_score) as avg_quality,
            AVG(extraction_yield_percent) as avg_ey,
            AVG(total_time) as avg_time,
            AVG(total_weight) as avg_weight
            FROM shots 
            WHERE timestamp >= ?"""
        params = [timestamp_from]
        
        if profile_id is not None:
            query += " AND profile_id = ?"
            params.append(profile_id)
        
        query += " GROUP BY DATE(datetime(timestamp, 'unixepoch')) ORDER BY date DESC"
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        trends = []
        for row in rows:
            trends.append({
                'date': row[0],
                'count': row[1],
                'avg_quality': round(row[2] or 0, 1),
                'avg_extraction_yield': round(row[3] or 0, 1),
                'avg_time': round(row[4] or 0, 1),
                'avg_weight': round(row[5] or 0, 1)
            })
        
        return trends
    except Exception as e:
        logger.error(f"Error getting trend data: {e}")
        raise

def delete_shot(shot_id):
    """Delete a shot from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("DELETE FROM shots WHERE id = ?", (shot_id,))
        conn.commit()
        deleted = c.rowcount > 0
        conn.close()
        
        if deleted:
            logger.info(f"Deleted shot {shot_id}")
        else:
            logger.warning(f"Shot {shot_id} not found for deletion")
        
        return deleted
    except Exception as e:
        logger.error(f"Error deleting shot {shot_id}: {e}")
        raise

