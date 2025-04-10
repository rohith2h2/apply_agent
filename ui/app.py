"""
Flask Application
================
This module contains the Flask application for the Job Application Agent UI.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import logging

logger = logging.getLogger(__name__)

def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config (dict, optional): Application configuration. Defaults to None.
        
    Returns:
        Flask: The configured Flask application.
    """
    app = Flask(
        __name__, 
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')
    )
    
    # Enable CORS
    CORS(app)
    
    # Load default configuration
    app.config.update({
        'SECRET_KEY': os.urandom(24),
        'SESSION_TYPE': 'filesystem',
        'DEBUG': False,
    })
    
    # Override with provided config
    if config:
        app.config.update({
            'SECRET_KEY': config.get('secret_key', app.config['SECRET_KEY']),
            'DEBUG': config.get('debug', app.config['DEBUG']),
        })
    
    # Store for learning sessions
    # In a production app, this would be a database
    learning_sessions = {}
    active_session = None
    
    # Register routes
    @app.route('/')
    def index():
        """Render the main application page."""
        return render_template('index.html')
    
    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        """Handle user profile updates."""
        if request.method == 'POST':
            # TODO: Save user profile data
            return redirect(url_for('index'))
        return render_template('profile.html')
    
    @app.route('/learning', methods=['GET'])
    def learning():
        """Render the learning mode page."""
        return render_template('learning.html')
    
    @app.route('/applications', methods=['GET'])
    def applications():
        """Render the applications tracking page."""
        # TODO: Load applications data
        return render_template('applications.html', applications=[])
    
    # Chrome Extension API Endpoints
    
    @app.route('/api/start-learning', methods=['POST'])
    def start_learning():
        """API endpoint to start the learning process from the Chrome extension."""
        nonlocal active_session
        
        try:
            data = request.json
            session_id = data.get('session_id')
            url = data.get('url')
            page_title = data.get('page_title')
            
            if not session_id or not url:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields'
                })
            
            # Store session data
            active_session = {
                'session_id': session_id,
                'url': url,
                'page_title': page_title,
                'start_time': data.get('start_time'),
                'events': [],
                'fields': {}
            }
            
            learning_sessions[session_id] = active_session
            
            logger.info(f"Started learning session: {session_id} for {url}")
            
            return jsonify({
                'status': 'success',
                'message': 'Learning session started',
                'session_id': session_id
            })
            
        except Exception as e:
            logger.error(f"Error starting learning session: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    @app.route('/api/finish-learning', methods=['POST'])
    def finish_learning():
        """API endpoint to finish the learning process from the Chrome extension."""
        nonlocal active_session
        
        try:
            data = request.json
            session_id = data.get('session_id')
            session_data = data.get('session_data')
            
            if not session_id or not session_data:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields'
                })
            
            # Update session with complete data
            learning_sessions[session_id] = session_data
            
            # Clear active session if it matches
            if active_session and active_session['session_id'] == session_id:
                active_session = None
            
            logger.info(f"Finished learning session: {session_id} with {len(session_data.get('fields', []))} fields")
            
            # Save session data to disk
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'learning_sessions')
            os.makedirs(data_dir, exist_ok=True)
            
            with open(os.path.join(data_dir, f"{session_id}.json"), 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return jsonify({
                'status': 'success',
                'message': 'Learning session completed',
                'session_id': session_id
            })
            
        except Exception as e:
            logger.error(f"Error finishing learning session: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    @app.route('/api/learning-sessions', methods=['GET'])
    def get_learning_sessions():
        """API endpoint to get all learning sessions."""
        try:
            sessions_list = []
            
            # Convert sessions to a list with basic info
            for session_id, session in learning_sessions.items():
                sessions_list.append({
                    'session_id': session_id,
                    'url': session.get('url'),
                    'page_title': session.get('page_title'),
                    'date': session.get('startTime') or session.get('start_time'),
                    'fields_count': len(session.get('fields', {})),
                })
            
            return jsonify({
                'status': 'success',
                'sessions': sessions_list
            })
            
        except Exception as e:
            logger.error(f"Error getting learning sessions: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    @app.route('/api/learning-status', methods=['GET'])
    def get_learning_status():
        """API endpoint to get the current learning status."""
        try:
            return jsonify({
                'status': 'success',
                'active_session': active_session is not None,
                'session_id': active_session['session_id'] if active_session else None,
                'sessions_completed': len(learning_sessions),
                'fields_learned': sum(len(session.get('fields', {})) for session in learning_sessions.values()),
                'agent_status': 'Training' if len(learning_sessions) < 3 else 'Trained',
                'last_trained': None  # TODO: Store last trained timestamp
            })
            
        except Exception as e:
            logger.error(f"Error getting learning status: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    @app.route('/api/active-learning-session', methods=['GET'])
    def get_active_learning_session():
        """API endpoint to get the active learning session."""
        try:
            if not active_session:
                return jsonify({
                    'status': 'success',
                    'active_session': False
                })
            
            return jsonify({
                'status': 'success',
                'active_session': True,
                'session_id': active_session['session_id'],
                'url': active_session['url'],
                'page_title': active_session['page_title'],
                'start_time': active_session['start_time']
            })
            
        except Exception as e:
            logger.error(f"Error getting active learning session: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    @app.route('/api/analyze-learning', methods=['POST'])
    def analyze_learning():
        """API endpoint to analyze the learning data and generate patterns."""
        try:
            # In a real app, this would use the AI model to analyze the data
            # and generate patterns for different form fields
            
            # For now, just return success with mock data
            return jsonify({
                'status': 'success',
                'message': 'Learning data analyzed successfully',
                'patterns': {
                    'name': {
                        'pattern_type': 'direct',
                        'value': 'Full Name'
                    },
                    'email': {
                        'pattern_type': 'direct',
                        'value': 'email@example.com'
                    },
                    'cover_letter': {
                        'pattern_type': 'template',
                        'template': 'I am writing to express my interest in the {position} role at {company}...'
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error analyzing learning data: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}", exc_info=True)
        return render_template('500.html'), 500
    
    return app 