#!/usr/bin/env python3
"""
Profile Database Management
Stores and retrieves brew profiles from SQLite database
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Database path - use /config for Home Assistant addon persistence
DB_PATH = Path('/config/marax_profiles.db')

def init_database():
    """Initialize the profile database with schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create profiles table
        c.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER UNIQUE,
                profile_name TEXT NOT NULL,
                technique TEXT,
                default_dose REAL,
                default_yield REAL,
                default_ratio REAL,
                enabled BOOLEAN DEFAULT 1,
                phase_count INTEGER DEFAULT 0,
                phases_data TEXT,
                synced_to_esp32 BOOLEAN DEFAULT 0,
                synced_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for fast queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_profiles_profile_id ON profiles(profile_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_profiles_name ON profiles(profile_name)')
        
        conn.commit()
        conn.close()
        
        logger.info("Profile database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing profile database: {e}")
        raise

def save_profile(profile_data: Dict[str, Any]) -> int:
    """Save or update a profile in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        profile_id = profile_data.get('profile_id') or profile_data.get('id')
        
        # If no profile_id provided, get next available ID
        if profile_id is None:
            profile_id = get_next_profile_id()
            logger.info(f"Auto-assigned profile_id in database function: {profile_id}")
        
        # Ensure profile_id is an integer (should never be None at this point)
        try:
            profile_id = int(profile_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid profile_id: {profile_id}, auto-assigning new ID")
            profile_id = get_next_profile_id()
        
        profile_name = profile_data.get('profileName') or profile_data.get('name', 'Unnamed Profile')
        technique = profile_data.get('technique', '')
        default_dose = profile_data.get('defaultDose', 18.0)
        default_yield = profile_data.get('defaultYield', 36.0)
        default_ratio = profile_data.get('defaultRatio', 2.0)
        enabled = profile_data.get('enabled', True)
        phases = profile_data.get('phases', [])
        phase_count = len(phases)
        
        # Store phases as JSON
        phases_json = json.dumps(phases)
        
        # Check if profile with this ID already exists (only if profile_id is not None)
        existing = None
        if profile_id is not None:
            c.execute('SELECT id FROM profiles WHERE profile_id = ?', (profile_id,))
            existing = c.fetchone()
        
        if existing:
            # Update existing profile
            c.execute('''
                UPDATE profiles SET
                    profile_name = ?,
                    technique = ?,
                    default_dose = ?,
                    default_yield = ?,
                    default_ratio = ?,
                    enabled = ?,
                    phase_count = ?,
                    phases_data = ?,
                    synced_to_esp32 = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE profile_id = ?
            ''', (profile_name, technique, default_dose, default_yield, default_ratio,
                  enabled, phase_count, phases_json, profile_id))
            profile_db_id = existing[0]
            logger.info(f"Updated profile {profile_id} ({profile_name}) in database")
        else:
            # Insert new profile
            c.execute('''
                INSERT INTO profiles (
                    profile_id, profile_name, technique, default_dose, default_yield,
                    default_ratio, enabled, phase_count, phases_data, synced_to_esp32
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (profile_id, profile_name, technique, default_dose, default_yield,
                  default_ratio, enabled, phase_count, phases_json))
            profile_db_id = c.lastrowid
            logger.info(f"Saved new profile {profile_id} ({profile_name}) to database")
        
        conn.commit()
        conn.close()
        
        return profile_db_id
    except Exception as e:
        logger.error(f"Error saving profile: {e}")
        raise

def get_profile(profile_id: int) -> Optional[Dict[str, Any]]:
    """Get a single profile by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM profiles WHERE profile_id = ?', (profile_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        profile = dict(row)
        # Parse phases JSON
        if profile['phases_data']:
            try:
                profile['phases'] = json.loads(profile['phases_data'])
            except:
                profile['phases'] = []
        else:
            profile['phases'] = []
        
        # Convert to expected format
        result = {
            'id': profile['profile_id'],
            'profile_id': profile['profile_id'],
            'profileName': profile['profile_name'],
            'name': profile['profile_name'],
            'technique': profile['technique'],
            'defaultDose': profile['default_dose'],
            'defaultYield': profile['default_yield'],
            'defaultRatio': profile['default_ratio'],
            'enabled': bool(profile['enabled']),
            'phaseCount': profile['phase_count'],
            'phase_count': profile['phase_count'],
            'phases': profile['phases'],
            'synced_to_esp32': bool(profile['synced_to_esp32'])
        }
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        raise

def get_all_profiles() -> List[Dict[str, Any]]:
    """Get all profiles from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM profiles ORDER BY profile_id ASC')
        rows = c.fetchall()
        conn.close()
        
        profiles = []
        for row in rows:
            profile = dict(row)
            # Parse phases JSON
            if profile['phases_data']:
                try:
                    profile['phases'] = json.loads(profile['phases_data'])
                except:
                    profile['phases'] = []
            else:
                profile['phases'] = []
            
            # Convert to expected format
            result = {
                'id': profile['profile_id'],
                'profile_id': profile['profile_id'],
                'profileName': profile['profile_name'],
                'name': profile['profile_name'],
                'technique': profile['technique'],
                'defaultDose': profile['default_dose'],
                'defaultYield': profile['default_yield'],
                'defaultRatio': profile['default_ratio'],
                'enabled': bool(profile['enabled']),
                'phaseCount': profile['phase_count'],
                'phase_count': profile['phase_count'],
                'phases': profile['phases'],
                'synced_to_esp32': bool(profile['synced_to_esp32'])
            }
            profiles.append(result)
        
        return profiles
    except Exception as e:
        logger.error(f"Error retrieving profiles: {e}")
        raise

def delete_profile(profile_id: int) -> bool:
    """Delete a profile from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('DELETE FROM profiles WHERE profile_id = ?', (profile_id,))
        deleted = c.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if deleted:
            logger.info(f"Deleted profile {profile_id} from database")
        else:
            logger.warning(f"Profile {profile_id} not found in database")
        
        return deleted
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        raise

def mark_synced(profile_id: int):
    """Mark a profile as synced to ESP32"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            UPDATE profiles SET
                synced_to_esp32 = 1,
                synced_at = CURRENT_TIMESTAMP
            WHERE profile_id = ?
        ''', (profile_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Marked profile {profile_id} as synced to ESP32")
    except Exception as e:
        logger.error(f"Error marking profile as synced: {e}")
        raise

def get_next_profile_id() -> int:
    """Get the next available profile ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('SELECT MAX(profile_id) FROM profiles')
        result = c.fetchone()
        conn.close()
        
        if result[0] is None:
            return 0
        return result[0] + 1
    except Exception as e:
        logger.error(f"Error getting next profile ID: {e}")
        return 0

