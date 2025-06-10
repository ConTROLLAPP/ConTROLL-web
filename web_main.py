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

        try:
            mri_results = enhanced_mri_scan(
                alias=handle,
                location=location,
                platform=platform,
                review=review_text,
                verbose=True
            )
        except Exception as e:
            mri_results = {
                'error': str(e),
                'trace': traceback.format_exc()
            }

        return render_template('alias_tools.html', results=mri_results)

    return render_template('alias_tools.html')

@app.route('/review_tools')
def review_tools():
    return render_template('review_tools.html')
