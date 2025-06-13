from flask import Flask, render_template, request, jsonify
from mri_scanner import enhanced_mri_scan
from conTROLL_decision_engine import evaluate_guest
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/alias_tools', methods=['POST'])
def alias_tools():
    try:
        data = request.get_json()
        alias = data.get('handle', '')
        if not alias:
            return jsonify({'error': 'Missing alias'}), 400

        logger.info(f"🔍 Starting enhanced MRI scan for: {alias}")
        mri_results = enhanced_mri_scan(alias)

        confidence = mri_results.get('confidence', 50)
        stylometry_flags = mri_results.get('stylometry_analysis', [])
        writing_samples = mri_results.get('writing_samples', [])
        is_critic = mri_results.get('is_critic', False)
        is_weak_critic = mri_results.get('is_weak_critic', False)
        platform_hits = mri_results.get('discovered_data', {}).get('review_platforms', [])

        risk, stars, reason, _ = evaluate_guest(
            confidence=confidence,
            platform_hits=platform_hits,
            stylometry_flags=stylometry_flags,
            writing_samples=writing_samples,
            is_critic=is_critic,
            is_weak_critic=is_weak_critic
        )

        logger.info(f"✅ Evaluation complete for {alias} — Stars: {stars}, Risk: {risk}")

        mri_results.update({
            'risk_score': risk,
            'star_rating': stars,
            'rating_reason': reason
        })

        return jsonify(mri_results)

    except Exception as e:
        logger.error(f"❌ Error during alias_tools scan: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
