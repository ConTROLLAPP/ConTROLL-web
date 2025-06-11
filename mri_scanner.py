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

def enhanced_mri_scan(target_name: str, phone: str = None, email: str = None) -> Dict[str, Any]:
    """
    Enhanced MRI scan with deep alias expansion and clue extraction + URL scraping
    """
    print(f"🧬 Starting Enhanced MRI Scan for: {target_name}")

    clue_queue = []
    discovered_data = {
        "emails": set(),
        "phones": set(),
        "profiles": [],
        "social_links": [],
        "review_platforms": []
    }

    # Enhanced alias expansion with smart variants
    print("🔧 Phase 0: Smart Alias Expansion...")
    alias_variants = expand_alias_variants(target_name)

    # Add intelligent name completions for "Seth D."
    if "seth d" in target_name.lower():
        alias_variants.extend([
            "Seth Doria",
            "Seth Daniels", 
            "Seth Davidson",
            "Seth Davis",
            "Seth Donohue",
            "Seth D food critic",
            "Seth D yelp reviewer",
            "@sethdoria",
            "@sethdaniels"
        ])

    print(f"📝 Generated {len(alias_variants)} smart variants")

    # Phase 1: Comprehensive SERPER Discovery
    print("🔍 Phase 1: Multi-Platform Discovery...")
    all_search_results = []

    # Build comprehensive query set
    search_queries = []

    # Core identity searches
    for variant in alias_variants[:8]:  # Top 8 variants
        search_queries.extend([
            f'"{variant}" review',
            f'"{variant}" yelp',
            f'"{variant}" tripadvisor',
            f'"{variant}" google reviews',
            f'{variant} site:reddit.com',
            f'{variant} site:linkedin.com'
        ])

    # Platform-specific searches
    review_platforms = ["yelp.com", "tripadvisor.com", "google.com", "trustpilot.com", "reddit.com"]
    for platform in review_platforms:
        search_queries.append(f'"{target_name}" site:{platform}')

    print(f"🔍 Executing {len(search_queries)} targeted queries...")

    for i, query in enumerate(search_queries[:25], 1):  # Increased limit
        print(f"  🔍 Query {i}/25: {query[:50]}...")

        try:
            results = query_serper(query, num_results=5)

            if not results:
                continue

            all_search_results.extend(results)

            # Extract clues from each result
            for result in results:
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
                    discovered_data["emails"].add(found_email.lower())
                    print(f"    📧 Email found: {found_email}")

                # Phone extraction
                phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
                phones = re.findall(phone_pattern, text_content)
                for found_phone in phones:
                    clean_phone = re.sub(r'[^\d]', '', found_phone)
                    if len(clean_phone) == 10:
                        discovered_data["phones"].add(clean_phone)
                        print(f"    📞 Phone found: {found_phone}")

                # Profile URL detection
                if url and is_mri_target_url(url):
                    if is_profile_link(url):
                        discovered_data["profiles"].append({
                            "url": url,
                            "platform": extract_platform_from_url(url),
                            "source_query": query
                        })
                        print(f"    👤 Profile found: {url}")

                    # Add to clue queue for potential scraping
                    if url not in clue_queue:
                        clue_queue.append(url)

        except Exception as e:
            print(f"    ❌ Query failed: {str(e)}")
            continue

    print(f"✅ Discovery complete: {len(clue_queue)} URLs queued for analysis")

    # Phase 2: URL Scraping & Deep Content Analysis
    print("\n🕷️ Phase 2: URL Scraping & Deep Content Analysis...")

    # Scrape the most promising URLs from clue queue
    scraped_urls = 0
    max_scrapes = 8  # Limit to prevent timeout

    for url in clue_queue[:max_scrapes]:
        if is_mri_target_url(url):
            print(f"    🕷️ Scraping: {url}")
            scraped_data = scrape_contact_info(url)
            scraped_urls += 1

            # Merge scraped data
            for email in scraped_data.get("emails", []):
                discovered_data["emails"].add(email)
                print(f"      📧 Scraped email: {email}")

            for phone in scraped_data.get("phones", []):
                discovered_data["phones"].add(phone)
                print(f"      📞 Scraped phone: {phone}")

            for social in scraped_data.get("social_links", []):
                discovered_data["social_links"].append(social)
                print(f"      🔗 Scraped social: {social}")

    print(f"    ✅ Scraped {scraped_urls} URLs successfully")

    # Phase 3: Identity Clue Analysis
    print("\n🔍 Phase 3: Identity Clue Analysis...")

    # Look for identity patterns in collected data
    combined_text = " ".join([str(r) for r in all_search_results])

    # Extract potential full names
    name_patterns = [
        r'Seth\s+([A-Z][a-z]+)',  # "Seth Lastname"
        r'([A-Z][a-z]+)\s+([A-Z][a-z]+)',  # "First Last" patterns
    ]

    for pattern in name_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                full_name = " ".join(match)
            else:
                full_name = f"Seth {match}" if "seth" not in match.lower() else match

            if len(full_name.split()) >= 2 and full_name not in [target_name]:
                print(f"    🎯 Potential identity: {full_name}")

    # Convert sets to lists for JSON serialization
    discovered_data["emails"] = list(discovered_data["emails"])
    discovered_data["phones"] = list(discovered_data["phones"])

    # Phase 4: Analysis Summary
    print("\n📊 Phase 4: Analysis Summary...")
    scan_summary = {
        "total_emails_found": len(discovered_data["emails"]),
        "total_phones_found": len(discovered_data["phones"]),
        "total_profiles_found": len(discovered_data["profiles"]),
        "urls_scanned": len(all_search_results),
        "urls_scraped": scraped_urls,
        "clues_queued": len(clue_queue),
        "scan_complete": True
    }

    mri_results = {
        "target": target_name,
        "phone": discovered_data["phones"][0] if discovered_data["phones"] else phone,
        "email": discovered_data["emails"][0] if discovered_data["emails"] else email,
        "discovered_data": discovered_data,
        "scan_summary": scan_summary,
        "clue_queue": clue_queue[:10]  # Preview of top 10 URLs
    }

    print(f"🎯 Enhanced MRI Scan Complete:")
    print(f"  📧 Emails: {scan_summary['total_emails_found']}")
    print(f"  📞 Phones: {scan_summary['total_phones_found']}")
    print(f"  👤 Profiles: {scan_summary['total_profiles_found']}")
    print(f"  🌐 URLs Analyzed: {scan_summary['urls_scanned']}")
    print(f"  🕷️ URLs Scraped: {scan_summary['urls_scraped']}")

    return mri_results

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
