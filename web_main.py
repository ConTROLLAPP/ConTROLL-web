from flask import Flask, request, jsonify
from mri_scanner import enhanced_mri_scan
from conTROLL_decision_engine import evaluate_guest

import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return "🔬 ConTROLL MRI Web API is running."

@app.route('/alias_tools', methods=['POST'])
def alias_tools():
    try:
        data = request.get_json()
        handle = data.get("handle", "").strip()
        phone = data.get("phone", "")
        email = data.get("email", "")
        location = data.get("location", "unknown")
        platform = data.get("platform", "unknown")

        if not handle:
            return jsonify({"error": "Missing alias/handle"}), 400

        logging.info(f"🎯 Starting MRI scan for: {handle}")
        mri_results = enhanced_mri_scan(handle)

        risk, stars, reason, confidence = evaluate_guest(
            confidence=mri_results.get("confidence", 50),
            platform_hits=mri_results.get("discovered_data", {}).get("review_platforms", []),
            stylometry_flags=mri_results.get("stylometry_analysis", []),
            writing_samples=mri_results.get("writing_samples", []),
            is_critic=mri_results.get("is_critic", False),
            is_weak_critic=mri_results.get("is_weak_critic", False)
        )

        full_response = {
            "target": handle,
            "email": mri_results.get("email"),
            "phone": mri_results.get("phone"),
            "risk_score": risk,
            "star_rating": stars,
            "rating_reason": reason,
            "confidence": confidence,
            "clue_queue": mri_results.get("clue_queue", []),
            "discovered_data": mri_results.get("discovered_data", {}),
            "stylometry_analysis": mri_results.get("stylometry_analysis", []),
            "scan_summary": mri_results.get("scan_summary", {})
        }

        logging.info(f"✅ MRI scan complete for {handle}")
        return jsonify(full_response)

    except Exception as e:
        logging.exception("❌ Error during MRI scan:")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
