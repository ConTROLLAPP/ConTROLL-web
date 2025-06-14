from flask import Flask, request, jsonify, render_template
from mri_scanner import enhanced_mri_scan
from conTROLL_decision_engine import evaluate_guest
import logging
import traceback

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/alias_tools", methods=["GET", "POST"])
def alias_tools():
    if request.method == "POST":
        try:
            handle = request.form.get("handle")

            if not handle:
                return render_template("alias_tools.html", results={"error": "Missing alias or handle"})

            logging.info(f"🔍 Starting MRI scan for alias: {handle}")
            mri_results = enhanced_mri_scan(handle)

            # Extract details for guest evaluation
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
            return render_template("alias_tools.html", results=mri_results)

        except Exception as e:
            logging.error(f"❌ Error during alias tool processing: {e}")
            return render_template("alias_tools.html", results={
                "error": str(e),
                "trace": traceback.format_exc()
            })

    # GET method: show the form
    return render_template("alias_tools.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
