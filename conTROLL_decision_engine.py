def evaluate_guest(confidence, platform_hits, stylometry_flags, writing_samples, is_critic=False, is_weak_critic=False):
    """
    Assigns a risk score and star rating to a guest based on search findings.

    Returns a dictionary:
    {
        "risk": 0–100,
        "stars": 1–5,
        "reason": "Explanation of why this rating was chosen"
    }
    """
    risk = 0
    reason = []

    # Base Risk from Confidence
    if confidence < 30:
        risk += 20
        reason.append("Low confidence")
    elif confidence < 70:
        risk += 10
        reason.append("Medium confidence")
    else:
        reason.append("High confidence")

    # Critic/Influencer Flag
    if is_critic:
        risk += 40
        reason.append("Confirmed critic")
    elif is_weak_critic:
        risk += 20
        reason.append("Possible critic")

    # Platform Match Bonus
    if isinstance(platform_hits, list):
        platform_count = len(platform_hits)
    else:
        platform_count = platform_hits or 0

    if platform_count >= 5:
        risk += 20
        reason.append("Found on 5+ platforms")
    elif platform_count >= 3:
        risk += 10
        reason.append("Found on 3–4 platforms")
    elif platform_count >= 1:
        risk += 5
        reason.append("Found on 1–2 platforms")

    # Stylometry Flags
    if isinstance(stylometry_flags, list):
        stylometry_count = len(stylometry_flags)
    else:
        stylometry_count = stylometry_flags or 0

    if stylometry_count >= 2:
        risk += 20
        reason.append("Stylometric aggression detected")
    elif stylometry_count == 1:
        risk += 10
        reason.append("Tone flag detected")

    # Volume of Writing Samples
    if isinstance(writing_samples, list) and len(writing_samples) >= 10:
        risk += 10
        reason.append("High writing volume")

    # Clamp risk to 100 max
    risk = min(risk, 100)

    # Star Rating Logic
    if risk >= 85:
        stars = 1
    elif risk >= 60:
        stars = 2
    elif risk >= 40:
        stars = 3
    elif risk >= 20:
        stars = 4
    else:
        stars = 5

    return {
        "risk": risk,
        "stars": stars,
        "reason": ", ".join(reason)
    }
