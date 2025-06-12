import os
import requests
import json
from typing import Dict, List, Any
from search_utils import query_serper

# Load secrets from secrets.json
try:
    with open("secrets.json") as f:
        secrets = json.load(f)
except FileNotFoundError:
    print("⚠️ secrets.json not found, falling back to environment variables")
    secrets = {
        "SERPER_API_KEY": os.environ.get('SERPER_API_KEY', '1d67ed1df4aee6acf1491b1bbcbdf82b545473cf'),
        "PUPPETEER_ENDPOINT": "https://controll-puppeteer.onrender.com/scrape",
        "GITHUB_TOKEN": os.environ.get('GITHUB_TOKEN', '')
    }

def expand_alias_variants(alias: str) -> List[str]:
    """
    Generate possible name variations for an alias like 'Seth D.'
    """
    variants = [alias]  # Always include original

    # Handle initials like "Seth D."
    alias_parts = alias.strip().split()
    if len(alias_parts) == 2 and alias_parts[1].endswith('.'):
        first_name = alias_parts[0]
        initial = alias_parts[1].replace('.', '').upper()

        # Common surname expansions by initial
        surname_map = {
            'D': ["Doria", "Daniels", "Davidson", "Davis", "Donohue", "Dunn", "Dalton"],
            'P': ["Potash", "Patterson", "Phillips", "Powell", "Parker", "Peterson"],
            'B': ["Brown", "Baker", "Bell", "Bennett", "Brooks", "Butler"],
            'S': ["Schraier", "Smith", "Scott", "Stewart", "Sullivan", "Sanders"],
            'M': ["Miller", "Moore", "Martin", "Martinez", "Murphy", "Mitchell"]
        }

        if initial in surname_map:
            for surname in surname_map[initial]:
                variants.append(f"{first_name} {surname}")
                variants.append(f"{first_name.lower()}{surname.lower()}")  # For email/username searches
                variants.append(f"@{first_name.lower()}{surname.lower()}")  # Social media handles

    # Add social media variations
    base_name = alias.replace('.', '').replace(' ', '').lower()
    variants.extend([
        f"@{base_name}",
        f"{base_name}",
        f"{alias} blogger",
        f"{alias} writer",
        f"{alias} reviewer"
    ])

    print(f"🔧 Expanded '{alias}' into {len(variants)} variants")
    return list(set(variants))  # Remove duplicates

def scrape_contact_info(url: str) -> Dict[str, List[str]]:
    """
    Scrape a URL for contact information using Puppeteer endpoint
    """
    try:
        puppeteer_endpoint = secrets.get("PUPPETEER_ENDPOINT", "https://controll-puppeteer.onrender.com/scrape")

        response = requests.post(puppeteer_endpoint, json={
            "url": url,
            "waitFor": 2000,
            "extractText": True
        }, timeout=10)

        if response.status_code != 200:
            return {"emails": [], "phones": [], "profiles": [], "social_links": []}

        data = response.json()
        content = data.get("content", "")

        # Extract contact information from scraped content
        import re

        discovered = {
            "emails": [],
            "phones": [],
            "profiles": [],
            "social_links": []
        }

        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content, re.IGNORECASE)
        discovered["emails"] = list(set([email.lower() for email in emails]))

        # Phone extraction
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
            r'\b\d{10}\b'
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, content)
            for phone in phones:
                clean_phone = re.sub(r'[^\d]', '', phone)
                if len(clean_phone) == 10:
                    discovered["phones"].append(clean_phone)

        discovered["phones"] = list(set(discovered["phones"]))

        # Social media links
        social_patterns = [
            r'https?://(?:www\.)?(?:facebook|twitter|instagram|linkedin|youtube)\.com/[^\s<>"\']+',
            r'@[A-Za-z0-9_]+(?:\s|$)',
        ]

        for pattern in social_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            discovered["social_links"].extend(matches)

        discovered["social_links"] = list(set(discovered["social_links"]))

        return discovered

    except Exception as e:
        print(f"    ❌ Scraping failed for {url}: {str(e)}")
        return {"emails": [], "phones": [], "profiles": [], "social_links": []}

def enhanced_mri_scan(alias, location=None, platform=None, review=None, verbose=False):
    """
    Enhanced MRI scan with diagnostic logging and flow verification
    """
    print(f"🔬 Starting Enhanced MRI Scan for: {alias}", flush=True)

    discovered_data = {
        "emails": [],
        "phones": [],
        "profiles": [],
        "social_links": [],
        "review_platforms": []
    }

    clue_queue = []
    urls_scraped = 0

    try:
        # Import required functions
        from search_utils import generate_platform_queries, extract_identity_clues
        
        queries = generate_platform_queries(alias, location, [])
        print(f"🧠 Generated {len(queries)} queries", flush=True)

        all_results = []
        for i, query in enumerate(queries, 1):
            print(f"🔍 Executing query {i}/{len(queries)}: {query[:50]}...", flush=True)
            try:
                result = query_serper(query, num_results=5)
                if result:
                    all_results.extend(result)
                    print(f"    ✅ Query returned {len(result)} results", flush=True)
                else:
                    print(f"    ⚠️ Query returned no results", flush=True)
            except Exception as query_error:
                print(f"    ❌ Query failed: {str(query_error)}", flush=True)
                continue
                
        print(f"🔍 SERPER returned {len(all_results)} total results", flush=True)

        # Extract URLs and contact info from results
        for i, result in enumerate(all_results):
            print(f"📊 Processing result {i+1}/{len(all_results)}", flush=True)
            
            text_content = ""
            url = ""

            if isinstance(result, dict):
                text_content = f"{result.get('title', '')} {result.get('snippet', '')}"
                url = result.get('link', '')
            elif isinstance(result, str):
                text_content = result
                # Extract URLs from text
                import re
                url_pattern = r'https?://[^\s<>"\']+(?:[^\s<>"\'.,;!?])'
                urls = re.findall(url_pattern, result)
                url = urls[0] if urls else ""

            # Extract contact information from text
            import re

            # Email extraction
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text_content)
            for found_email in emails:
                discovered_data["emails"].append(found_email.lower())
                print(f"    📧 Email found: {found_email}", flush=True)

            # Phone extraction
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, text_content)
            for found_phone in phones:
                clean_phone = re.sub(r'[^\d]', '', found_phone)
                if len(clean_phone) == 10:
                    discovered_data["phones"].append(clean_phone)
                    print(f"    📞 Phone found: {found_phone}", flush=True)

            # Profile URL detection
            if url and is_mri_target_url(url):
                if is_profile_link(url):
                    discovered_data["profiles"].append({
                        "url": url,
                        "platform": extract_platform_from_url(url),
                        "source_query": f"Query {i+1}"
                    })
                    print(f"    👤 Profile found: {url}", flush=True)

                # Add to clue queue for potential scraping
                if url not in clue_queue:
                    clue_queue.append(url)
                    print(f"    🧩 URL added to clue queue: {url}", flush=True)

        print(f"🧩 Clue Queue populated with {len(clue_queue)} URLs", flush=True)

        # Phase 2: URL Scraping
        print(f"🕷️ Starting URL scraping phase...", flush=True)
        max_scrapes = min(8, len(clue_queue))  # Limit to prevent timeout
        
        for i, url in enumerate(clue_queue[:max_scrapes], 1):
            print(f"🧪 [{i}/{max_scrapes}] Scraping URL: {url}", flush=True)
            
            try:
                scraped = scrape_contact_info(url)
                urls_scraped += 1
                
                if scraped:
                    emails_found = scraped.get("emails", [])
                    phones_found = scraped.get("phones", [])
                    profiles_found = scraped.get("profiles", [])
                    
                    discovered_data["emails"].extend(emails_found)
                    discovered_data["phones"].extend(phones_found)
                    discovered_data["profiles"].extend(profiles_found)
                    
                    print(f"    ✅ Scraped: {len(emails_found)} emails, {len(phones_found)} phones, {len(profiles_found)} profiles", flush=True)
                else:
                    print(f"    ⚠️ No data scraped from URL", flush=True)
                    
            except Exception as scrape_error:
                print(f"    ❌ Scraping failed: {str(scrape_error)}", flush=True)
                continue

    except Exception as e:
        print(f"❌ Error in MRI scan: {str(e)}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)

    # Remove duplicates
    discovered_data["emails"] = list(set(discovered_data["emails"]))
    discovered_data["phones"] = list(set(discovered_data["phones"]))

    print(f"🧬 MRI Scan Completed for {alias}", flush=True)
    print(f"📊 Final Results:", flush=True)
    print(f"  📧 Emails: {len(discovered_data['emails'])}", flush=True)
    print(f"  📞 Phones: {len(discovered_data['phones'])}", flush=True)
    print(f"  👤 Profiles: {len(discovered_data['profiles'])}", flush=True)
    print(f"  🕷️ URLs Scraped: {urls_scraped}", flush=True)

    return {
        "target": alias,
        "phone": discovered_data["phones"][0] if discovered_data["phones"] else None,
        "email": discovered_data["emails"][0] if discovered_data["emails"] else None,
        "discovered_data": discovered_data,
        "scan_summary": {
            "scan_complete": True,
            "total_emails_found": len(discovered_data["emails"]),
            "total_phones_found": len(discovered_data["phones"]),
            "total_profiles_found": len(discovered_data["profiles"]),
            "urls_scanned": len(clue_queue),
            "urls_scraped": urls_scraped,
            "clues_queued": len(clue_queue)
        },
        "clue_queue": clue_queue
    }

def is_mri_target_url(url: str) -> bool:
    """Check if URL is worth MRI scanning"""
    target_domains = [
        'yelp.com', 'tripadvisor.com', 'google.com/maps',
        'reddit.com', 'facebook.com', 'instagram.com',
        'linkedin.com', 'twitter.com', 'opentable.com',
        'trustpilot.com', 'foursquare.com', 'zomato.com',
        'grubhub.com', 'seamless.com', 'doordash.com'
    ]
    return any(domain in url.lower() for domain in target_domains)

def is_profile_link(url: str) -> bool:
    """Check if URL appears to be a user profile"""
    profile_indicators = [
        '/user/', '/profile/', '/users/', '/member/',
        'yelp.com/user_details', 'reddit.com/user/',
        'facebook.com/', 'instagram.com/', 'linkedin.com/in/'
    ]
    return any(indicator in url.lower() for indicator in profile_indicators)

def extract_platform_from_url(url: str) -> str:
    """Extract platform name from URL"""
    if 'yelp.com' in url:
        return 'Yelp'
    elif 'tripadvisor.com' in url:
        return 'TripAdvisor'
    elif 'google.com' in url:
        return 'Google'
    elif 'reddit.com' in url:
        return 'Reddit'
    elif 'linkedin.com' in url:
        return 'LinkedIn'
    elif 'facebook.com' in url:
        return 'Facebook'
    elif 'trustpilot.com' in url:
        return 'Trustpilot'
    else:
        return 'Unknown'

if __name__ == "__main__":
    # Test with Seth D.
    print("🧪 Testing Enhanced MRI Scanner...")
    results = enhanced_mri_scan("Seth D.", phone="9174505555")

    # Save results
    with open('mri_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("💾 Results saved to mri_test_results.json")
