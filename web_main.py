from flask import Flask, request, jsonify, render_template
from mri_scanner import enhanced_mri_scan
from conTROLL_decision_engine import evaluate_guest
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/alias_tools", methods=["POST"])
def alias_tools():
    try:
        data = request.json
        handle = data.get("handle")

        if not handle:
            return jsonify({"error": "Missing handle"}), 400

        logging.info(f"🔍 Starting MRI scan for alias: {handle}")
        mri_results = enhanced_mri_scan(handle)

        # Extract details for guest evaluation if possible
        phone = mri_results.get("phone")
        email = mri_results.get("email")
        stylometry = mri_results.get("stylometry_analysis", [])
        critic_flag = mri_results.get("is_critic", False)
        weak_critic_flag = mri_results.get("is_weak_critic", False)
        confidence = mri_results.get("confidence", 50)
        platforms = mri_results.get("discovered_data", {}).get("review_platforms", [])
        samples = mri_results.get("writing_samples", [])

        logging.info("🔎 Running guest risk evaluation...")
        risk, stars, reason, confidence = evaluate_guest(
            confidence=confidence,
            platform_hits=platforms,
            stylometry_flags=stylometry,
            writing_samples=samples,
            is_critic=critic_flag,
            is_weak_critic=weak_critic_flag
        )

        mri_results.update({
            "risk_score": risk,
            "star_rating": stars,
            "rating_reason": reason,
            "confidence": confidence
        })

        logging.info(f"✅ Evaluation complete for {handle}: Risk {risk}, Stars {stars}")
        return jsonify(mri_results)

    except Exception as e:
        logging.error(f"❌ Error during alias tool processing: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
