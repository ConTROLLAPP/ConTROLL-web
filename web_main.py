from flask import Flask, render_template, request, jsonify
from mri_scanner import enhanced_mri_scan
from conTROLL_decision_engine import evaluate_guest
import logging
import traceback
import traceback

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/alias_tools', methods=['GET', 'POST'])
def alias_tools():
    if request.method == 'GET':
        return jsonify({"error": "GET method not supported on this route"}), 405
    
    try:
        data = request.get_json()
        handle = data.get('handle', '')
        extracted_phone = data.get('phone', None)
        
        if not handle:
            return jsonify({'error': 'Missing handle'}), 400

        logger.info(f"🔍 Starting enhanced MRI scan for: {handle}")
        mri_results = enhanced_mri_scan(handle)

        confidence = mri_results.get('confidence', 50)
        stylometry_flags = mri_results.get('stylometry_analysis', [])
        writing_samples = mri_results.get('writing_samples', [])
        is_critic = mri_results.get('is_critic', False)
        is_weak_critic = mri_results.get('is_weak_critic', False)
        platform_hits = mri_results.get('platform_hits', [])

        risk_score, star_rating, rating_reason, _ = evaluate_guest(
            confidence,
            platform_hits,
            stylometry_flags,
            writing_samples,
            is_critic,
            is_weak_critic
        )

        logger.info(f"✅ Evaluation complete for {handle} — Stars: {star_rating}, Risk: {risk_score}")

        mri_results.update({
            'risk_score': risk_score,
            'star_rating': star_rating,
            'rating_reason': rating_reason
        })

        return jsonify(mri_results)

    except Exception as e:
        logger.error(f"❌ Error during alias_tools scan: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
