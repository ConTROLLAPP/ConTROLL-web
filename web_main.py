
from flask import Flask, render_template, request, jsonify
import logging
import traceback
import json
import os
import sys

app = Flask(__name__)

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

sys.stdout.flush()
sys.stderr.flush()

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    if request.is_json:
        logger.info(f"JSON Data: {request.get_json(silent=True)}")

@app.route('/', methods=['GET'])
def index():
    logger.info("Index route accessed")
    return render_template('index.html')

@app.route('/alias_tools', methods=['GET'])
def alias_tools_page():
    return render_template('alias_tools.html')

@app.route('/guest_tools', methods=['GET'])
def guest_tools_page():
    return render_template('guest_tools.html')

@app.route('/review_tools', methods=['GET'])
def review_tools_page():
    return render_template('review_tools.html')

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'ConTROLL Web API Running',
        'version': '2.0',
        'mri_scanner': 'Active',
        'serper_api': 'Connected'
    })

@app.route('/api/alias_tools', methods=['POST'])
def handle_alias_investigation():
    try:
        if request.is_json:
            data = request.get_json()
            handle = data.get('handle', '').strip()
            location = data.get('location', '').strip()
            platform = data.get('platform', '').strip()
            review_text = data.get('review_text', '').strip()
            response_type = 'json'
        else:
            handle = request.form.get('handle', '').strip()
            location = request.form.get('location', '').strip()
            platform = request.form.get('platform', '').strip()
            review_text = request.form.get('review_text', '').strip()
            response_type = 'html'

        if not handle:
            return jsonify({'error': 'Handle is required'}), 400

        logger.info(f"🔍 Starting enhanced MRI scan for: {handle}")

        from mri_scanner import enhanced_mri_scan
        mri_results = enhanced_mri_scan(handle, location=location)

        discovered_emails = mri_results.get('discovered_data', {}).get('emails', [])
        discovered_phones = mri_results.get('discovered_data', {}).get('phones', [])
        discovered_profiles = mri_results.get('discovered_data', {}).get('profiles', [])

        final_confidence = 30
        risk_score = 20
        star_rating = 5
        rating_reason = "No significant risk indicators found"

        if discovered_emails or discovered_phones:
            final_confidence = 85
            risk_score = 70
            star_rating = 2
            rating_reason = "Contact information discovered - potential reviewer tracking"

        if len(discovered_profiles) >= 2:
            risk_score = 90
            star_rating = 1
            rating_reason = "Multiple review profiles found - high risk pattern"

        mri_results.update({
            'risk_score': risk_score,
            'star_rating': star_rating,
            'rating_reason': rating_reason,
            'confidence_score': final_confidence
        })

        if response_type == 'json':
            return jsonify({'success': True, 'results': mri_results})
        else:
            return render_template('alias_mri.html', results=mri_results)

    except Exception as e:
        logger.error(f"❌ Alias investigation error: {str(e)}")
        logger.error(traceback.format_exc())
        if request.is_json:
            return jsonify({'success': False, 'error': f'Investigation failed: {str(e)}'}), 500
        else:
            return render_template("alias_mri.html", results={'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 ConTROLL Web API starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
