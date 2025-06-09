def analyze_full_review_block(review_block):
    lines = review_block.strip().split('\n')
    results = []

    for line in lines:
        if line.strip():
            result = analyze_review_text(line)
            results.append(result)

    return results

def detect_literary_stylometry(text):
    triggers = [
        "like a serpent", "coiled", "in the dust", "betrayal", "promise held", "lay before me",
        "the light failed", "nothingness", "rubble", "fate", "abyss", "metaphor", "dusk", "withered", 
        "unforgiving", "ashen", "echoed", "forgotten", "godless", "tumbled", "scorched", "mythic",
        "language held weight", "the silence stretched", "as if"
    ]
    lowered = text.lower()
    matched = [phrase for phrase in triggers if phrase in lowered]
    score = len(matched)
    return score, matched

def analyze_full_review_block(text):
    """Analyze a full review block that includes handle and review text"""
    # Try different separators
    for separator in [': ', '. ']:
        if separator in text:
            handle, review_text = text.split(separator, 1)
            result = analyze_review_text(review_text)
            result['handle'] = handle.strip()
            result['original_text'] = review_text
            return result

    raise ValueError("Review must be in format: '<handle>: <review text>' or '<handle>. <review text>'")

def save_review_to_fingerprint(alias, review_text):
    """Cache review text as fingerprint sample for future matching"""
    import json
    try:
        with open("review_fingerprints.json", "r") as f:
            fingerprints = json.load(f)
    except FileNotFoundError:
        fingerprints = {}

    if alias not in fingerprints:
        fingerprints[alias] = []
    
    if review_text not in fingerprints[alias]:
        fingerprints[alias].append(review_text)

    with open("review_fingerprints.json", "w") as f:
        json.dump(fingerprints, f, indent=2)

    print(f"🧠 Fingerprint sample saved for {alias}")

def analyze_review_text(text):
    """Analyze review text for tone, risk indicators, and patterns"""
    text_lower = text.lower()

    positive_indicators = ['great', 'excellent', 'wonderful', 'amazing', 'fantastic', 'love', 'perfect', 'best']
    negative_indicators = ['terrible', 'awful', 'worst', 'horrible', 'disgusting', 'never again', 'waste']
    concern_indicators = ['but', 'however', 'unfortunately', 'disappointed']

    positive_count = sum(1 for word in positive_indicators if word in text_lower)
    negative_count = sum(1 for word in negative_indicators if word in text_lower)
    concern_count = sum(1 for word in concern_indicators if word in text_lower)

    # Calculate base risk score
    risk_score = max(0, (negative_count * 20) + (concern_count * 10) - (positive_count * 5))
    risk_score = min(risk_score, 100)

    # DO NOT DELETE — Stylometry Boost Triggers
    trigger_phrases = [
        "i really wanted to like this place but",
        "i usually don't write bad reviews but",
        "me thinks not",
        "hard pass",
        "i heard great things about this place but",
        # PATCH 3: Expanded stylometric triggers
        "overhyped",
        "used to be good",
        "won't be coming back",
        "save your money",
        "service was non-existent",
        "not worth the hype",
        "i won't be back",
        "overpriced and underwhelming",
        "should have listened",
        "service was terrible",
        "waited over an hour",
        "cold and greasy",
        "not as advertised",
        "wouldn't recommend"
    ]
    
    stylometric_triggers_found = [tp for tp in trigger_phrases if tp in text_lower]
    stylometric_trigger_found = len(stylometric_triggers_found) > 0
    
    if stylometric_trigger_found:
        risk_score += 15
        risk_score = min(risk_score, 100)
        print("🧠 Stylometric trigger phrase detected. Risk score increased.")
        
        # PATCH 3: Boost if multiple triggers hit
        if len(stylometric_triggers_found) >= 2:
            risk_score += 10
            print("🔥 Stylometric pattern match: Negative reviewer language")

    # Determine tone
    if negative_count > positive_count:
        tone = "Negative"
    elif positive_count > negative_count:
        tone = "Positive"
    else:
        tone = "Neutral"

    return {
        'tone': tone,
        'risk_score': risk_score,
        'negative_indicators': negative_count,
        'positive_indicators': positive_count,
        'concern_indicators': concern_count,
        'stylometric_trigger': stylometric_trigger_found,
        'stylometric_triggers_found': stylometric_triggers_found
    }
