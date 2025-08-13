#!/usr/bin/env python3
"""
Cloud API Endpoints
REST API endpoints for cloud-based ZK biometric device communication
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Blueprint, request, jsonify, current_app
from functools import wraps

from cloud_config import get_cloud_config, get_device_config, get_all_devices
from cloud_connector import get_cloud_connector
from database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for cloud API
cloud_api = Blueprint('cloud_api', __name__, url_prefix='/api/cloud')

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Remove 'Bearer ' prefix if present
        if api_key.startswith('Bearer '):
            api_key = api_key[7:]
        
        # Validate API key
        config = get_cloud_config()
        if api_key != config.api_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_organization(f):
    """Decorator to require organization ID"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id:
            return jsonify({'error': 'Organization ID required'}), 400
        
        # Validate organization ID
        config = get_cloud_config()
        if org_id != config.organization_id:
            return jsonify({'error': 'Invalid organization ID'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@cloud_api.route('/status', methods=['GET'])
@require_api_key
def get_cloud_status():
    """Get cloud connector status"""
    try:
        connector = get_cloud_connector()
        config = get_cloud_config()
        devices = get_all_devices()
        
        # Get device statuses
        device_statuses = []
        for device in devices:
            if device.cloud_enabled:
                status = connector.get_device_status(device.device_id)
                device_statuses.append({
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'local_ip': device.local_ip,
                    'status': status['status'],
                    'last_sync': device.last_sync,
                    'user_count': status.get('user_count', 0)
                })
        
        return jsonify({
            'success': True,
            'cloud_connector_running': connector.running,
            'websocket_connected': connector.websocket is not None and 
                                 connector.websocket.sock and 
                                 connector.websocket.sock.connected,
            'last_heartbeat': connector.last_heartbeat.isoformat() if connector.last_heartbeat else None,
            'message_queue_size': len(connector.message_queue),
            'device_count': len(device_statuses),
            'devices': device_statuses,
            'config': {
                'api_base_url': config.api_base_url,
                'websocket_url': config.websocket_url,
                'auto_sync': config.auto_sync,
                'sync_interval': config.sync_interval
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cloud status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices', methods=['GET'])
@require_api_key
@require_organization
def get_devices():
    """Get all configured devices"""
    try:
        devices = get_all_devices()
        connector = get_cloud_connector()
        
        device_list = []
        for device in devices:
            status = connector.get_device_status(device.device_id)
            device_list.append({
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'local_ip': device.local_ip,
                'local_port': device.local_port,
                'cloud_enabled': device.cloud_enabled,
                'sync_interval': device.sync_interval,
                'last_sync': device.last_sync,
                'status': status
            })
        
        return jsonify({
            'success': True,
            'devices': device_list,
            'total_count': len(device_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/sync', methods=['POST'])
@require_api_key
@require_organization
def sync_device(device_id):
    """Trigger sync for a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        if not device_config.cloud_enabled:
            return jsonify({'success': False, 'error': 'Device cloud sync disabled'}), 400
        
        connector = get_cloud_connector()
        connector._sync_device(device_config)
        
        return jsonify({
            'success': True,
            'message': f'Sync triggered for device {device_id}',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error syncing device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/users', methods=['GET'])
@require_api_key
@require_organization
def get_device_users(device_id):
    """Get users from a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        connector = get_cloud_connector()
        zk_device = connector._get_device_connection(device_config)
        
        if not zk_device:
            return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
        
        users = zk_device.get_users()
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'users': users,
            'user_count': len(users),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting users from device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/attendance', methods=['GET'])
@require_api_key
@require_organization
def get_device_attendance(device_id):
    """Get attendance records from a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        # Get query parameters
        since = request.args.get('since')
        limit = int(request.args.get('limit', 100))
        
        since_time = None
        if since:
            try:
                since_time = datetime.fromisoformat(since)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid since parameter format'}), 400
        
        connector = get_cloud_connector()
        zk_device = connector._get_device_connection(device_config)
        
        if not zk_device:
            return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
        
        # Get attendance records
        if since_time:
            records = zk_device.get_new_attendance_records(since_time)
        else:
            records = zk_device.get_attendance_records()
        
        # Limit results
        if limit and len(records) > limit:
            records = records[:limit]
        
        # Convert datetime objects to ISO format
        formatted_records = []
        for record in records:
            formatted_record = record.copy()
            if 'timestamp' in formatted_record:
                formatted_record['timestamp'] = formatted_record['timestamp'].isoformat()
            formatted_records.append(formatted_record)
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'records': formatted_records,
            'record_count': len(formatted_records),
            'since': since,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting attendance from device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/command', methods=['POST'])
@require_api_key
@require_organization
def send_device_command(device_id):
    """Send command to a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'success': False, 'error': 'Command required'}), 400
        
        command = data['command']
        connector = get_cloud_connector()
        
        # Handle different commands
        if command == 'clear_attendance':
            zk_device = connector._get_device_connection(device_config)
            if not zk_device:
                return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
            
            success = zk_device.clear_attendance()
            return jsonify({
                'success': success,
                'device_id': device_id,
                'command': command,
                'message': 'Attendance cleared' if success else 'Failed to clear attendance',
                'timestamp': datetime.now().isoformat()
            })
        
        elif command == 'enroll_user':
            user_id = data.get('user_id')
            name = data.get('name')
            
            if not user_id or not name:
                return jsonify({'success': False, 'error': 'user_id and name required'}), 400
            
            zk_device = connector._get_device_connection(device_config)
            if not zk_device:
                return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
            
            result = zk_device.enroll_user(user_id, name)
            return jsonify({
                'success': result['success'],
                'device_id': device_id,
                'command': command,
                'message': result['message'],
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
        
        elif command == 'delete_user':
            user_id = data.get('user_id')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'user_id required'}), 400
            
            zk_device = connector._get_device_connection(device_config)
            if not zk_device:
                return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
            
            success = zk_device.delete_user(user_id)
            return jsonify({
                'success': success,
                'device_id': device_id,
                'command': command,
                'message': f'User {user_id} deleted' if success else f'Failed to delete user {user_id}',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
        
        else:
            return jsonify({'success': False, 'error': f'Unknown command: {command}'}), 400
        
    except Exception as e:
        logger.error(f"Error sending command to device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/attendance/upload', methods=['POST'])
@require_api_key
@require_organization
def upload_attendance():
    """Upload attendance records to cloud database"""
    try:
        data = request.get_json()
        if not data or 'records' not in data:
            return jsonify({'success': False, 'error': 'Records required'}), 400
        
        records = data['records']
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id required'}), 400
        
        # Validate device exists
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        # Process records
        processed_count = 0
        errors = []
        
        db = get_db()
        
        for record in records:
            try:
                # Validate required fields
                required_fields = ['user_id', 'timestamp', 'verification_type']
                for field in required_fields:
                    if field not in record:
                        errors.append(f"Missing field {field} in record")
                        continue
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(record['timestamp'])
                except ValueError:
                    errors.append(f"Invalid timestamp format: {record['timestamp']}")
                    continue
                
                # Check if record already exists
                existing = db.execute('''
                    SELECT id FROM cloud_attendance_log
                    WHERE device_id = ? AND user_id = ? AND timestamp = ?
                ''', (device_id, record['user_id'], timestamp)).fetchone()
                
                if existing:
                    continue  # Skip duplicate
                
                # Insert record
                db.execute('''
                    INSERT INTO cloud_attendance_log
                    (device_id, user_id, timestamp, verification_type, punch_code, status, verify_method, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_id,
                    record['user_id'],
                    timestamp,
                    record['verification_type'],
                    record.get('punch_code', 0),
                    record.get('status', 0),
                    record.get('verify_method', 0),
                    datetime.now()
                ))
                
                processed_count += 1
                
            except Exception as e:
                errors.append(f"Error processing record: {str(e)}")
        
        db.commit()
        
        return jsonify({
            'success': True,
            'processed_count': processed_count,
            'total_records': len(records),
            'errors': errors,
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error uploading attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/config', methods=['GET'])
@require_api_key
def get_cloud_config_api():
    """Get cloud configuration"""
    try:
        config = get_cloud_config()
        
        # Return safe configuration (no sensitive data)
        safe_config = {
            'cloud_provider': config.cloud_provider,
            'api_base_url': config.api_base_url,
            'websocket_url': config.websocket_url,
            'mqtt_broker': config.mqtt_broker,
            'mqtt_port': config.mqtt_port,
            'organization_id': config.organization_id,
            'connection_timeout': config.connection_timeout,
            'retry_attempts': config.retry_attempts,
            'heartbeat_interval': config.heartbeat_interval,
            'use_ssl': config.use_ssl,
            'verify_ssl': config.verify_ssl,
            'encryption_enabled': config.encryption_enabled,
            'auto_sync': config.auto_sync,
            'sync_interval': config.sync_interval,
            'batch_size': config.batch_size,
            'local_backup': config.local_backup,
            'backup_retention_days': config.backup_retention_days
        }
        
        return jsonify({
            'success': True,
            'config': safe_config
        })
        
    except Exception as e:
        logger.error(f"Error getting cloud config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ZK Biometric Cloud API'
    })

# Error handlers
@cloud_api.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@cloud_api.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
