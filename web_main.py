from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import time
from datetime import datetime
import traceback
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    return render_template('index.html')

@app.route('/guest_tools')
def guest_tools():
    return render_template('guest_tools.html')

@app.route('/alias_tools', methods=['GET', 'POST'])
def alias_tools():
    if request.method == 'POST':
        handle = request.form.get('handle')
        location = request.form.get('location')
        platform = request.form.get('platform')
        review_text = request.form.get('review_text')

        # Enhanced logging for all scan attempts
        logging.info(f"🚀 Starting Enhanced MRI for alias: {handle}")
        logging.info(f"📍 Location: {location}")
        logging.info(f"🌐 Platform: {platform}")
        logging.info(f"📝 Review text length: {len(review_text) if review_text else 0} characters")

        try:
            print(f"👁️ MRI Triggered for alias: {handle}")
            logging.info(f"👁️ MRI Triggered for alias: {handle}")
            
            # Extract phone from review text if possible
            extracted_phone = None
            if review_text:
                import re
                phone_matches = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', review_text)
                if phone_matches:
                    extracted_phone = phone_matches[0]
                    logging.info(f"📞 Extracted phone from review: {extracted_phone}")
            
            # PHASE 1: Enhanced MRI scan with full investigation logic
            print("📡 Starting enhanced MRI scan...")
            print(f"📊 Input parameters: handle='{handle}', location='{location}', platform='{platform}'")
            
            try:
                logging.info(f"🔍 Calling enhanced_mri_scan with parameters:")
                logging.info(f"   - alias: {handle}")
                logging.info(f"   - phone: {extracted_phone}")
                logging.info(f"   - location: {location}")
                logging.info(f"   - source_platform: {platform}")
                logging.info(f"   - review_text length: {len(review_text) if review_text else 0}")
                
                # Run full investigation with all parameters
                mri_results = enhanced_mri_scan(
                    alias=handle,
                    phone=extracted_phone,
                    location=location,
                    source_platform=platform,
                    review_text=review_text,
                    verbose=True
                )
                print("✅ MRI scan completed without errors")
                logging.info("✅ MRI scan completed without errors")
                logging.info(f"📊 MRI Results Summary:")
                logging.info(f"   - Emails found: {len(mri_results.get('discovered_data', {}).get('emails', []))}")
                logging.info(f"   - Phones found: {len(mri_results.get('discovered_data', {}).get('phones', []))}")
                logging.info(f"   - Profiles found: {len(mri_results.get('discovered_data', {}).get('profiles', []))}")
                logging.info(f"   - URLs scanned: {mri_results.get('scan_summary', {}).get('urls_scanned', 0)}")
                
                # Log full MRI results for debugging
                logging.info("🔍 Complete MRI Results:")
                logging.info(json.dumps(mri_results, indent=2))
                
                # PHASE 2: Enhanced analysis and risk scoring
                from conTROLL_decision_engine import evaluate_guest
                
                # Extract discovered contact info
                best_email = mri_results['discovered_data']['emails'][0] if mri_results['discovered_data']['emails'] else None
                best_phone = mri_results['discovered_data']['phones'][0] if mri_results['discovered_data']['phones'] else extracted_phone
                
                # Extract parameters for evaluation
                confidence = mri_results.get('confidence_score', 75)
                platform_hits = len(mri_results.get('discovered_data', {}).get('profiles', []))
                stylometry_flags = len(mri_results.get('stylometry_analysis', {}).get('flags', []))
                writing_samples = len(mri_results.get('discovered_data', {}).get('writing_samples', []))
                is_critic = mri_results.get('critic_detected', False)
                is_weak_critic = False
                
                # Run full evaluation with discovered data
                evaluation = evaluate_guest(
                    confidence,
                    platform_hits,
                    stylometry_flags,
                    writing_samples,
                    is_critic,
                    is_weak_critic
                )
                
                # Merge evaluation results into MRI results
                mri_results['risk_score'] = evaluation.get('risk', 50)
                mri_results['star_rating'] = evaluation.get('stars', 3)
                mri_results['rating_reason'] = evaluation.get('reason', 'Standard evaluation')
                mri_results['confidence'] = evaluation.get('confidence', 75)
                
                # PHASE 3: Stylometry analysis if review text provided
                if review_text and len(review_text) > 50:
                    from search_utils import run_stylometry_analysis
                    stylometry_results = run_stylometry_analysis(review_text, handle)
                    mri_results['stylometry_analysis'] = stylometry_results
                
                print(f"\n🧬 Complete MRI Analysis Results for {handle}:")
                print(f"📧 Emails discovered: {len(mri_results.get('discovered_data', {}).get('emails', []))}")
                print(f"📞 Phones discovered: {len(mri_results.get('discovered_data', {}).get('phones', []))}")
                print(f"👤 Profiles discovered: {len(mri_results.get('discovered_data', {}).get('profiles', []))}")
                print(f"⭐ Star Rating: {mri_results.get('star_rating', 'N/A')}/5")
                print(f"⚠️ Risk Score: {mri_results.get('risk_score', 'N/A')}")
                print(f"🌐 URLs scanned: {mri_results.get('scan_summary', {}).get('urls_scanned', 0)}")
                
            except Exception as e:
                print(f"❌ MRI scan exception: {e}")
                logging.error(f"❌ MRI scan exception: {e}")
                logging.error("❌ Full traceback:")
                logging.error(traceback.format_exc())
                
                mri_results = {
                    'error': str(e),
                    'trace': traceback.format_exc(),
                    'handle': handle,
                    'location': location,
                    'platform': platform,
                    'star_rating': 3,
                    'risk_score': 50,
                    'rating_reason': f'Scan failed: {str(e)}'
                }
                logging.info(f"🔄 Fallback results created: {json.dumps(mri_results, indent=2)}")
            
        except Exception as e:
            print(f"❌ Complete investigation failed: {e}")
            logging.error(f"❌ Complete investigation failed: {e}")
            logging.error("❌ Complete investigation traceback:")
            logging.error(traceback.format_exc())
            
            mri_results = {
                'error': str(e),
                'trace': traceback.format_exc(),
                'handle': handle,
                'location': location,
                'platform': platform,
                'star_rating': 3,
                'risk_score': 50,
                'rating_reason': f'Investigation failed: {str(e)}'
            }
            logging.info(f"🔄 Final fallback results: {json.dumps(mri_results, indent=2)}")

        print("🔬 COMPLETE MRI INVESTIGATION RESULT:", json.dumps(mri_results, indent=2))
        logging.info("🔬 COMPLETE MRI INVESTIGATION RESULT:")
        logging.info(json.dumps(mri_results, indent=2))
        
        logging.info(f"📤 Rendering template with results for alias: {handle}")
        return render_template('alias_tools.html', results=mri_results)

    return render_template('alias_tools.html')

@app.route('/review_tools')
def review_tools():
    return render_template('review_tools.html')

@app.route('/api/guest/search', methods=['POST'])
def guest_search():
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    phone = request.form.get('phone', '')

    try:
        result = run_full_guest_search(name=name, email=email, phone=phone)
        star_rating = get_star_rating(name, email, phone)
        guest_note = get_shared_notes(name, email, phone)
        global_alert = check_shared_guest_alert(name, email, phone)
        shared_guest_count = get_shared_guest_count(name, email, phone)

        return render_template('guest_tools.html',
                               result=result,
                               star_rating=star_rating,
                               guest_note=guest_note,
                               global_alert=global_alert,
                               shared_guest_count=shared_guest_count)

    except Exception as e:
        return render_template('guest_tools.html',
                               result={'error': str(e), 'trace': traceback.format_exc()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
