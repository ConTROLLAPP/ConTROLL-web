
from flask import Flask, render_template, request, jsonify
import logging
import traceback
import json
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/alias_tools', methods=['GET'])
def alias_tools_page():
    return render_template('alias_tools.html')

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'ConTROLL Web API Running',
        'version': '2.0',
        'mri_scanner': 'Active',
        'serper_api': 'Connected'
    })

@app.route('/api/alias_tools', methods=['POST'])
def alias_tools():
    try:
        data = request.get_json()
        handle = data.get('handle', '')
        location = data.get('location', '')
        platform = data.get('platform', '')
        review_text = data.get('review_text', '')

        if not handle:
            return jsonify({'error': 'Missing handle'}), 400

        logger.info(f"🔍 Starting enhanced MRI scan for: {handle}")
        
        # Import MRI scanner here to avoid import errors
        try:
            from mri_scanner import enhanced_mri_scan
            mri_results = enhanced_mri_scan(handle, location=location)
            logger.info(f"✅ MRI scan completed for {handle}")
        except ImportError as e:
            logger.error(f"❌ MRI scanner import failed: {e}")
            return jsonify({
                'error': 'MRI scanner not available',
                'handle': handle,
                'discovered_data': {'emails': [], 'phones': [], 'profiles': []},
                'scan_summary': {'urls_scanned': 0, 'scan_complete': False}
            }), 500
        except Exception as e:
            logger.error(f"❌ MRI scan failed: {e}")
            return jsonify({
                'error': f'MRI scan failed: {str(e)}',
                'handle': handle,
                'discovered_data': {'emails': [], 'phones': [], 'profiles': []},
                'scan_summary': {'urls_scanned': 0, 'scan_complete': False}
            }), 500

        # Extract discovered data from MRI results
        discovered_emails = mri_results.get('discovered_data', {}).get('emails', [])
        discovered_phones = mri_results.get('discovered_data', {}).get('phones', [])
        discovered_profiles = mri_results.get('discovered_data', {}).get('profiles', [])

        # Determine risk and rating based on discoveries
        final_confidence = 30  # Default low confidence
        risk_score = 20  # Default low risk
        star_rating = 5  # Default high rating
        rating_reason = "No significant risk indicators found"

        # If we found contact info or profiles, increase confidence and risk
        if discovered_emails or discovered_phones:
            final_confidence = 85
            risk_score = 70
            star_rating = 2
            rating_reason = "Contact information discovered - potential reviewer tracking"
            logger.info(f"📧 Found contact info: {len(discovered_emails)} emails, {len(discovered_phones)} phones")

        # If we found multiple profiles, further increase risk
        if len(discovered_profiles) >= 2:
            risk_score = 90
            star_rating = 1
            rating_reason = "Multiple review profiles found - high risk pattern"
            logger.info(f"🚨 High risk: {len(discovered_profiles)} profiles found")

        # Try to run enhanced guest evaluation if available
        try:
            from conTROLL_decision_engine import evaluate_guest
            
            evaluation = evaluate_guest(
                confidence=final_confidence,
                platform_hits=len(discovered_profiles),
                stylometry_flags=0,  # Not available in web mode
                writing_samples=1 if review_text else 0,
                is_critic=False,  # Not determined in web mode
                is_weak_critic=False
            )
            
            risk_score = evaluation['risk']
            star_rating = evaluation['stars']
            rating_reason = evaluation['reason']
            logger.info(f"✅ Decision engine evaluation: {star_rating} stars, {risk_score} risk")
            
        except Exception as eval_error:
            logger.warning(f"⚠️ Decision engine not available: {eval_error}")
            # Keep the manual calculations above

        # Update MRI results with final evaluation
        mri_results.update({
            'risk_score': risk_score,
            'star_rating': star_rating,
            'rating_reason': rating_reason,
            'confidence_score': final_confidence,
            'handle': handle,
            'location': location,
            'platform': platform
        })

        logger.info(f"🎯 Final evaluation for {handle}: {star_rating} stars, {risk_score} risk")
        return jsonify(mri_results)

    except Exception as e:
        logger.error(f"❌ Error during alias_tools scan: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc(),
            'handle': data.get('handle', 'unknown') if 'data' in locals() else 'unknown'
        }), 500

@app.route('/api/guest/search', methods=['POST'])
def guest_search():
    try:
        data = request.get_json()
        name = data.get('name', '')
        email = data.get('email', '')
        phone = data.get('phone', '')

        if not name:
            return jsonify({'error': 'Missing guest name'}), 400

        logger.info(f"🔍 Guest search for: {name}")

        # Use MRI scanner for guest search
        try:
            from mri_scanner import enhanced_mri_scan
            results = enhanced_mri_scan(name, phone=phone, email=email)
            
            # Basic risk evaluation
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

            return jsonify({
                'name': name,
                'risk_score': risk_score,
                'star_rating': star_rating,
                'rating_reason': rating_reason,
                'emails_found': len(discovered_emails),
                'phones_found': len(discovered_phones),
                'mri_data': results
            })

        except Exception as mri_error:
            logger.error(f"❌ Guest search MRI failed: {mri_error}")
            return jsonify({
                'name': name,
                'risk_score': 20,
                'star_rating': 5,
                'rating_reason': 'Basic evaluation - MRI unavailable',
                'emails_found': 0,
                'phones_found': 0,
                'error': str(mri_error)
            })

    except Exception as e:
        logger.error(f"❌ Guest search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/review/analyze', methods=['POST'])
def analyze_review():
    try:
        data = request.get_json()
        review_text = data.get('review_text', '')
        handle = data.get('handle', '')

        if not review_text:
            return jsonify({'error': 'Missing review text'}), 400

        # Basic review analysis
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

        return jsonify({
            'tone': tone,
            'risk_score': risk_score,
            'risk_indicators_found': risk_count,
            'handle': handle,
            'analysis_complete': True
        })

    except Exception as e:
        logger.error(f"❌ Review analysis error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
