
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import time
from datetime import datetime
import traceback

# Import ConTROLL modules
from review_matcher import analyze_review_text, analyze_full_review_block
from search_utils import run_full_guest_search, generate_platform_queries, extract_clue_phrases, query_serper, extract_identity_clues, compare_identity_styles, calculate_weighted_confidence, scrape_contact_info
from star_rating import get_star_rating, update_star_rating
from guest_storage import save_guest_from_review
from guest_queue import add_to_guest_queue
from guest_notes import get_shared_notes, add_guest_note, check_global_alert
from conTROLL_decision_engine import evaluate_guest
from shared_guest_alerts import add_shared_guest_profile, check_shared_guest_alert, get_shared_guest_count
from api_usage_tracker import check_api_quota
from mri_scanner import enhanced_mri_scan

app = Flask(__name__)
app.secret_key = 'controll_web_secret_key_2025'

def load_guest_db():
    try:
        with open("guest_db.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_guest_db(data):
    with open("guest_db.json", "w") as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    try:
        # Check API quota
        quota_status = check_api_quota()
        
        # Check guest database size
        guest_db = load_guest_db()
        guest_count = len(guest_db)
        
        # Check shared alerts
        shared_count = get_shared_guest_count()
        
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'guest_count': guest_count,
            'shared_alerts': shared_count,
            'api_quota': quota_status
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/guest-tools')
def guest_tools():
    """Guest tools page"""
    return render_template('guest_tools.html')

@app.route('/api/guest/search', methods=['POST'])
def guest_search():
    """Search for guest profile"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip() or None
        phone = data.get('phone', '').strip() or None
        
        if not name:
            return jsonify({'error': 'Guest name is required'}), 400
        
        # Run enhanced MRI scan for guest investigation
        print(f"🚀 Launching enhanced MRI scan for guest profile: {name}")
        
        try:
            mri_results = enhanced_mri_scan(name, phone=phone, email=email)
            
            # Extract key data for evaluation
            discovered_emails = mri_results['discovered_data']['emails']
            discovered_phones = mri_results['discovered_data']['phones']
            discovered_profiles = mri_results['discovered_data']['profiles']
            
            # Use MRI results or fallback to provided data
            best_email = discovered_emails[0] if discovered_emails else email
            best_phone = discovered_phones[0] if discovered_phones else phone
            
            # Build results structure
            results = {
                'name': name,
                'email': best_email,
                'phone': best_phone,
                'matched_platforms': [],
                'stylometry_flags': [],
                'confidence_score': 85 if (discovered_emails or discovered_phones) else 30,
                'writing_samples_found': 0,
                'influencer_flag': False,
                'mri_scan_summary': mri_results['scan_summary']
            }
            
        except Exception as e:
            print(f"❌ MRI scan failed: {e}")
            # Fallback to legacy guest search
            results = run_full_guest_search(name=name, email=email, phone=phone, verbose=True)
        
        # Use structured decision engine for evaluation
        evaluation = evaluate_guest(
            confidence=results.get('confidence_score', 0),
            platform_hits=len(results.get('matched_platforms', [])),
            stylometry_flags=len(results.get('stylometry_flags', [])),
            writing_samples=results.get('writing_samples_found', 0),
            is_critic=bool(results.get('influencer_flag')),
            is_weak_critic=False
        )
        
        # Store evaluation results
        guest_db = load_guest_db()
        if name not in guest_db:
            guest_db[name] = {}
        
        guest_db[name].update({
            "final_risk_score": evaluation['risk'],
            "star_rating": evaluation['stars'],
            "rating_reason": evaluation['reason'],
            "last_evaluation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "evaluation_method": "enhanced_decision_engine_web",
            "email": best_email,
            "phone": best_phone
        })
        save_guest_db(guest_db)
        
        return jsonify({
            'success': True,
            'guest': {
                'name': name,
                'email': best_email,
                'phone': best_phone,
                'risk_score': evaluation['risk'],
                'star_rating': evaluation['stars'],
                'rating_reason': evaluation['reason'],
                'writing_samples': results.get('writing_samples_found', 0),
                'stylometry_flags': len(results.get('stylometry_flags', [])),
                'platform_matches': len(results.get('matched_platforms', [])),
                'influencer_flag': results.get('influencer_flag'),
                'mri_scan_summary': results.get('mri_scan_summary', {})
            }
        })
        
    except Exception as e:
        print(f"❌ Guest search error: {e}")
        return jsonify({'error': f'Guest search failed: {str(e)}'}), 500

@app.route('/api/guest/note', methods=['POST'])
def add_guest_note_api():
    """Add note to guest"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        note = data.get('note', '').strip()
        
        if not name or not note:
            return jsonify({'error': 'Name and note are required'}), 400
        
        add_guest_note(name, note)
        return jsonify({'success': True, 'message': 'Note added successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to add note: {str(e)}'}), 500

@app.route('/api/guest/rating', methods=['POST'])
def update_guest_rating():
    """Update guest star rating"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        stars = int(data.get('stars', 0))
        
        if not name or not (1 <= stars <= 5):
            return jsonify({'error': 'Valid name and star rating (1-5) required'}), 400
        
        update_star_rating(name, stars)
        return jsonify({'success': True, 'message': 'Star rating updated successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to update rating: {str(e)}'}), 500

@app.route('/review-tools')
def review_tools():
    """Review analysis tools page"""
    return render_template('review_tools.html')

@app.route('/api/review/analyze', methods=['POST'])
def analyze_review():
    """Analyze review text"""
    try:
        data = request.get_json()
        review_text = data.get('review_text', '').strip()
        
        if not review_text:
            return jsonify({'error': 'Review text is required'}), 400
        
        # Analyze the review
        results = analyze_review_text(review_text)
        
        return jsonify({
            'success': True,
            'analysis': {
                'tone': results.get('tone', 'Unknown'),
                'risk_score': results.get('risk_score', 0),
                'sentiment': results.get('sentiment', 'neutral'),
                'flags': results.get('flags', [])
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/review/investigate', methods=['POST'])
def investigate_review():
    """Full review investigation with MRI scanning"""
    try:
        data = request.get_json()
        handle = data.get('handle', '').strip()
        location = data.get('location', '').strip()
        platform = data.get('platform', '').strip()
        review_text = data.get('review_text', '').strip()
        
        if not all([handle, review_text]):
            return jsonify({'error': 'Handle and review text are required'}), 400
        
        # Run comprehensive investigation using MRI scanner
        from main import run_full_review_investigation
        
        investigation_results = run_full_review_investigation(handle, location, platform, review_text)
        
        # Save investigation results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"web_investigation_{handle.replace(' ', '_')}_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(investigation_results, f, indent=2)
        
        return jsonify({
            'success': True,
            'investigation': {
                'target': handle,
                'location': location,
                'platform': platform,
                'risk_score': investigation_results['risk_score'],
                'star_rating': investigation_results['star_rating'],
                'rating_reason': investigation_results.get('rating_reason', 'No specific reason'),
                'evidence_found': investigation_results['evidence_found'],
                'stylometry_analysis': investigation_results.get('stylometry_analysis', {}),
                'tone_analysis': investigation_results.get('tone_analysis', {}),
                'mri_data': investigation_results.get('mri_data', {}),
                'filename': filename
            }
        })
        
    except Exception as e:
        print(f"❌ Review investigation error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Investigation failed: {str(e)}'}), 500

@app.route('/alias-tools')
def alias_tools():
    """Alias investigation tools page"""
    return render_template('alias_tools.html')

@app.route('/api/alias/investigate', methods=['POST'])
def investigate_alias():
    """Deep alias investigation"""
    try:
        data = request.get_json()
        handle = data.get('handle', '').strip()
        location = data.get('location', '').strip()
        platform = data.get('platform', '').strip()
        review_text = data.get('review_text', '').strip()
        
        if not handle:
            return jsonify({'error': 'Handle is required'}), 400
        
        # Import the alias investigation function
        from main import investigate_alias as main_investigate_alias
        
        # Run enhanced MRI scan for alias investigation
        print(f"🚀 Launching enhanced MRI scan for alias investigation: {handle}")
        
        try:
            # Extract phone from review text if possible
            extracted_phone = None
            if review_text:
                import re
                phone_matches = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', review_text)
                if phone_matches:
                    extracted_phone = phone_matches[0]
            
            # Run enhanced MRI scan
            mri_results = enhanced_mri_scan(handle, phone=extracted_phone)
            
            # Extract key data
            discovered_emails = mri_results['discovered_data']['emails']
            discovered_phones = mri_results['discovered_data']['phones']
            discovered_profiles = mri_results['discovered_data']['profiles']
            
            best_email = discovered_emails[0] if discovered_emails else None
            best_phone = discovered_phones[0] if discovered_phones else extracted_phone
            
            # Set risk score based on discoveries
            if discovered_emails or discovered_phones:
                final_risk_score = 85  # High risk if contact info found
            else:
                final_risk_score = 50  # Medium risk for unresolved aliases
            
            # Build investigation results
            investigation_results = {
                'handle': handle,
                'location': location,
                'platform': platform,
                'review_text': review_text,
                'most_likely_name': 'Unknown',  # Will be updated if identity found
                'confidence_score': 50 if (discovered_emails or discovered_phones) else 20,
                'risk_score': final_risk_score,
                'email': best_email,
                'phone': best_phone,
                'stylometry_flags': [],
                'matched_platforms': [],
                'mri_scan_summary': mri_results['scan_summary']
            }
            
            # Save detailed MRI results
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"web_alias_investigation_{handle.replace(' ', '_')}_{timestamp}.json"
            
            with open(filename, "w") as f:
                json.dump(mri_results, f, indent=2)
            
        except Exception as e:
            print(f"❌ MRI scan failed: {e}")
            # Fallback to basic investigation
            investigation_results = {
                'handle': handle,
                'location': location,
                'platform': platform,
                'review_text': review_text,
                'most_likely_name': 'Unknown',
                'confidence_score': 20,
                'risk_score': 30,
                'email': None,
                'phone': None,
                'stylometry_flags': [],
                'matched_platforms': []
            }
        
        return jsonify({
            'success': True,
            'investigation': investigation_results
        })
        
    except Exception as e:
        print(f"❌ Alias investigation error: {e}")
        return jsonify({'error': f'Investigation failed: {str(e)}'}), 500

@app.route('/api/guests/list')
def list_guests():
    """Get list of all guests"""
    try:
        guest_db = load_guest_db()
        guests = []
        
        for name, data in guest_db.items():
            guests.append({
                'name': name,
                'risk_score': data.get('final_risk_score', data.get('risk_score', 0)),
                'star_rating': data.get('star_rating', 5),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'last_evaluation': data.get('last_evaluation', 'Unknown')
            })
        
        # Sort by risk score descending
        guests.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return jsonify({'success': True, 'guests': guests})
        
    except Exception as e:
        return jsonify({'error': f'Failed to load guests: {str(e)}'}), 500

@app.route('/api/cold-reviews/match', methods=['POST'])
def match_cold_reviews():
    """Match cold reviews to identities"""
    try:
        # Load cold review pool
        try:
            with open("cold_match_pool.json", "r") as f:
                cold_reviews = json.load(f)
        except FileNotFoundError:
            return jsonify({'success': True, 'message': 'No cold reviews found', 'matched': 0})
        
        if not cold_reviews:
            return jsonify({'success': True, 'message': 'Cold review pool is empty', 'matched': 0})
        
        matched_count = 0
        processed_count = 0
        
        # Process first 10 reviews
        for review in cold_reviews[:10]:
            processed_count += 1
            
            # Extract review data
            if isinstance(review, str):
                review_text = review
                handle = "Unknown"
            elif isinstance(review, dict):
                review_text = review.get("text", review.get("review", ""))
                handle = review.get("handle", "Unknown")
            else:
                continue
            
            if not review_text or len(review_text) < 20 or handle.lower() == "unknown":
                continue
            
            try:
                # Run guest search for matching
                results = run_full_guest_search(handle, location="", review_text=review_text, verbose=False)
                
                if results and results.get("confidence", 0) >= 70:
                    matched_count += 1
                    
                    # Save to guest database
                    identity = results.get("name", handle)
                    save_guest_from_review(
                        text=review_text,
                        phone=results.get("phone", ""),
                        email=results.get("email", ""),
                        full_name=identity,
                        alias=handle,
                        risk_score=results.get("risk", 0),
                        platform="Cold Review Match"
                    )
                    
            except Exception as e:
                print(f"⚠️ Cold review matching error: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Processed {processed_count} reviews, matched {matched_count}',
            'matched': matched_count,
            'processed': processed_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Cold review matching failed: {str(e)}'}), 500

@app.route('/templates/<template_name>')
def serve_template(template_name):
    """Serve HTML templates"""
    return render_template(template_name)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("🌐 Starting ConTROLL Web Interface...")
    print("🔗 Access the web interface at: http://0.0.0.0:5000")
    print("🚀 ConTROLL Web Server with MRI integration is ready!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

