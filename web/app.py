import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
from config import settings

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def create_app(signal_engine=None, po_trader=None):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    class CustomJSONProvider(app.json_provider_class):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
            
    app.json = CustomJSONProvider(app)
    
    CORS(app)
    app.config['SECRET_KEY'] = 'pocket_secret_key'
    
    socketio = SocketIO(app, cors_allowed_origins="*")
    app.socketio = socketio
    
    @app.route('/')
    def index():
        return render_template('dashboard.html')

    @app.route('/api/signals')
    def get_signals():
        timeframe = request.args.get('timeframe', 'M5')
        signals = signal_engine.scan_all(timeframe) if signal_engine else []
        return jsonify(signals)
        
    @app.route('/api/signals/all')
    def get_all_signals():
        signals = signal_engine.scan_all_timeframes() if signal_engine else {}
        return jsonify(signals)
        
    @app.route('/api/history')
    def get_history():
        history = signal_engine.get_history() if signal_engine else []
        return jsonify(history)
        
    @app.route('/api/trades')
    def get_trades():
        trades = po_trader.trade_history if po_trader else []
        return jsonify(trades)
        
    @app.route('/api/stats')
    def get_stats():
        stats = signal_engine.get_stats() if signal_engine else {}
        stats.update({
            'martingale_max_steps': settings.MARTINGALE_MAX_STEPS,
            'martingale_multiplier': settings.MARTINGALE_MULTIPLIER,
            'base_amount': settings.MARTINGALE_BASE_AMOUNT,
            'po_is_demo': settings.PO_IS_DEMO,
            'po_connected': po_trader.is_connected if po_trader else False,
            'min_confidence': settings.SIGNAL_MEDIUM_THRESHOLD
        })
        return jsonify(stats)
        
    @app.route('/charts/<path:filename>')
    def serve_chart(filename):
        charts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'charts')
        return send_from_directory(charts_dir, filename)

    @socketio.on('connect')
    def handle_connect():
        print("Müştəri qoşuldu")

    def emit_new_signal(data):
        socketio.emit('new_signal', data)
        
    app.emit_new_signal = emit_new_signal
    
    return app
