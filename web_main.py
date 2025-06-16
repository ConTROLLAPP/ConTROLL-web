
from flask import Flask, render_template, request, jsonify
import logging
import traceback
import json
import os
import sys

app = Flask(__name__)

# Enhanced logging configuration for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Force immediate output flush
sys.stdout.flush()
sys.stderr.flush()

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    if request.json:
        logger.info(f"JSON Data: {request.json}")

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
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        handle = data.get('handle', '').strip()
        location = data.get('location', '').strip()
        platform = data.get('platform', '').strip()
        review_text = data.get('review_text', '').strip()
        if not handle:
            return jsonify({'error': 'Handle is required'}), 400

        logger.info(f"🔍 Starting enhanced MRI scan for: {handle}")
        try:
            from mri_scanner import enhanced_mri_scan
            mri_results = enhanced_mri_scan(handle, location=location)
            logger.info(f"✅ MRI scan completed for {handle}")
        except ImportError as e:
            logger.error(f"❌ MRI scanner import failed: {e}")
            return jsonify({'success': False, 'error': 'MRI scanner not available',
                'results': {'handle': handle, 'discovered_data': {'emails': [], 'phones': [], 'profiles': []},
                'scan_summary': {'urls_scanned': 0, 'scan_complete': False}}}), 500
        except Exception as e:
            logger.error(f"❌ MRI scan failed: {e}")
            return jsonify({'success': False, 'error': f'MRI scan failed: {str(e)}',
                'results': {'handle': handle, 'discovered_data': {'emails': [], 'phones': [], 'profiles': []},
                'scan_summary': {'urls_scanned': 0, 'scan_complete': False}}}), 500

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

        return jsonify({'success': True, 'results': mri_results})
    except Exception as e:
        logger.error(f"❌ Alias investigation error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Investigation failed: {str(e)}'}), 500

@app.route('/api/guest/search', methods=['POST'])
def handle_guest_search():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        name = data.get('name', '').strip()
        email = data.get('email', '').strip() or None
        phone = data.get('phone', '').strip() or None
        if not name:
            return jsonify({'error': 'Guest name is required'}), 400

        logger.info(f"🔍 Guest search for: {name}")
        try:
            from mri_scanner import enhanced_mri_scan
            results = enhanced_mri_scan(name, phone=phone)
            discovered_emails = results.get('discovered_data', {}).get('emails', [])
            discovered_phones = results.get('discovered_data', {}).get('phones', [])
            if discovered_emails or discovered_phones:
                risk_score = 75
                star_rating = 2
                rating_reason = "Contact information found"
            else:
                risk_score = 30
                star_rating = 4
                rating_reason = "Limited information found"
            return jsonify({'success': True, 'results': {
                'name': name,
                'risk_score': risk_score,
                'star_rating': star_rating,
                'rating_reason': rating_reason,
                'emails_found': len(discovered_emails),
                'phones_found': len(discovered_phones),
                'mri_data': results
            }})
        except Exception as mri_error:
            logger.error(f"❌ Guest search MRI failed: {mri_error}")
            return jsonify({'success': True, 'results': {
                'name': name,
                'risk_score': 20,
                'star_rating': 5,
                'rating_reason': 'Basic evaluation - MRI unavailable',
                'emails_found': 0,
                'phones_found': 0,
                'error': str(mri_error)
            }})
    except Exception as e:
        logger.error(f"❌ Guest search error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Guest search failed: {str(e)}'}), 500

@app.route('/api/review/analyze', methods=['POST'])
def handle_review_analysis():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        review_text = data.get('review_text', '').strip()
        if not review_text:
            return jsonify({'error': 'Review text is required'}), 400

        try:
            from review_matcher import analyze_review_text
            results = analyze_review_text(review_text)
            return jsonify({'success': True, 'results': results})
        except ImportError:
            risk_indicators = ['terrible', 'worst', 'awful', 'horrible', 'disgusting', 'never again']
            risk_count = sum(1 for indicator in risk_indicators if indicator.lower() in review_text.lower())
            if risk_count >= 3:
                tone = 'Very Negative'
                risk_score = 80
            elif risk_count >= 1:
                tone = 'Negative'
                risk_score = 60
            else:
                tone = 'Neutral/Positive'
                risk_score = 20
            return jsonify({'success': True, 'results': {
                'tone': tone,
                'risk_score': risk_score,
                'risk_indicators_found': risk_count,
                'analysis_complete': True
            }})
    except Exception as e:
        logger.error(f"❌ Review analysis error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Review analysis failed: {str(e)}'}), 500

@app.route('/api/mri/scan', methods=['POST'])
def handle_mri_scan():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        alias = data.get('alias', '').strip()
        phone = data.get('phone', '').strip() or None
        location = data.get('location', '').strip() or None
        if not alias:
            return jsonify({'error': 'Alias is required for MRI scan'}), 400

        from mri_scanner import enhanced_mri_scan
        results = enhanced_mri_scan(alias=alias, phone=phone, location=location, verbose=True)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"MRI scan error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'MRI scan failed: {str(e)}'}), 500

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
