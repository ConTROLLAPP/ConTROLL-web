# ✅ DO NOT DELETE — Risk to star rating logic
def get_star_rating(score):
    if score >= 90:
        return 1  # 🚩 Trolls or dangerous critics
    elif score >= 75:
        return 2  # ⚠️ Concerning tone, maybe aggressive
    elif score >= 60:
        return 3  # 😐 Neutral or unknown behavior
    elif score >= 40:
        return 4  # 👍 Known, safe, professional behavior
    else:
        return 5  # 🕊️ Trusted guest, no risk indicators

def update_star_rating(name, phone=None, risk_score=50, critic_flag=False, stylometry_flags=None, confidence=75, platform_hits=0, writing_samples=0):
    """
    Enhanced star rating function using structured decision engine
    Calculates star rating based on comprehensive evaluation criteria
    """
    if stylometry_flags is None:
        stylometry_flags = []

    # Use the enhanced decision engine from conTROLL_decision_engine
    from conTROLL_decision_engine import evaluate_guest
    
    evaluation = evaluate_guest(
        confidence=confidence,
        platform_hits=platform_hits,
        stylometry_flags=len(stylometry_flags),
        writing_samples=writing_samples,
        is_critic=critic_flag,
        is_weak_critic=False
    )
    
    final_score = evaluation["risk"]
    calculated_stars = evaluation["stars"]
    reasoning = evaluation["reason"]

    print(f"⭐ Enhanced Star Rating: {calculated_stars} stars (Risk: {final_score})")
    print(f"📋 Rating Reason: {reasoning}")
    
    if critic_flag:
        print(f"🚨 Critic flag detected in evaluation")
    
    if stylometry_flags:
        print(f"🧠 Stylometry flags factored into evaluation")

    # Store rating in guest database if name provided
    if name and name != "Unknown":
        try:
            import json
            with open("guest_db.json", "r") as f:
                guest_db = json.load(f)
        except:
            guest_db = {}

        if name not in guest_db:
            guest_db[name] = {}

        guest_db[name]["star_rating"] = calculated_stars
        guest_db[name]["final_risk_score"] = final_score
        guest_db[name]["rating_reason"] = reasoning
        guest_db[name]["last_rating_update"] = "2025-06-02"
        guest_db[name]["evaluation_method"] = "enhanced_decision_engine"

        try:
            with open("guest_db.json", "w") as f:
                json.dump(guest_db, f, indent=2)
            print(f"💾 Structured star rating saved: {name} → {calculated_stars} stars")
        except Exception as e:
            print(f"⚠️ Failed to save star rating: {e}")

    return calculated_stars
