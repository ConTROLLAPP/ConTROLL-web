
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

def enhanced_mri_scan(target_name: str, phone: str = None, email: str = None) -> Dict[str, Any]:
    """
    Enhanced MRI scan using Puppeteer server with Cheerio + Regex extraction
    """
    print(f"🧬 Starting Enhanced MRI Scan for: {target_name}")

    mri_results = {
        "target": target_name,
        "phone": phone,
        "email": email,
        "discovered_data": {
            "emails": set(),
            "phones": set(),
            "profiles": [],
            "social_links": [],
            "review_platforms": []
        },
        "scan_summary": {}
    }

    # Phase 0: Alias Expansion
    print("🔧 Phase 0: Alias Expansion...")
    alias_variants = expand_alias_variants(target_name)
    print(f"📝 Generated {len(alias_variants)} alias variants: {alias_variants[:5]}...")

    # Phase 1: SERPER Discovery with Expanded Aliases
    print("🔍 Phase 1: SERPER Discovery...")
    search_queries = []
    
    # Add queries for each alias variant
    for variant in alias_variants[:5]:  # Limit to top 5 variants
        search_queries.extend([
            f'"{variant}" review',
            f'"{variant}" yelp',
            f'"{variant}" restaurant',
            f'{variant} site:reddit.com',
            f'{variant} site:yelp.com',
            f'{variant} site:tripadvisor.com',
            f'{variant} site:medium.com',
            f'{variant} site:trustpilot.com'
        ])

    # Add original target queries
    search_queries.extend([
        f'"{target_name}" review',
        f'"{target_name}" yelp',
        f'"{target_name}" restaurant',
        f'{target_name} site:reddit.com',
        f'{target_name} site:yelp.com',
        f'{target_name} site:tripadvisor.com'
    ])

    if phone:
        search_queries.append(f'"{phone}" review')
    if email:
        search_queries.append(f'"{email}" review')

    discovered_urls = []
    total_queries = len(search_queries)
    print(f"🔍 Executing {total_queries} SERPER queries...")
    
    for i, query in enumerate(search_queries[:20], 1):  # Limit to 20 queries to avoid exhaustion
        print(f"  🔍 Query {i}/{min(total_queries, 20)}: {query}")
        
        try:
            results = query_serper(query, num_results=5)
            
            if not results:
                print(f"    ❌ No results returned")
                continue
                
            print(f"    ✅ Got {len(results)} results")
            
            for result in results:
                # Handle both string snippets and dict results from SERPER
                if isinstance(result, dict):
                    url = result.get('link', '')
                    if url and is_mri_target_url(url):
                        discovered_urls.append(url)
                        print(f"    📍 Target URL found: {url[:60]}...")
                elif isinstance(result, str):
                    # Extract URLs from string snippets using regex
                    import re
                    url_pattern = r'https?://[^\s<>"\']+(?:[^\s<>"\'.,;!?])'
                    urls = re.findall(url_pattern, result)
                    for url in urls:
                        if is_mri_target_url(url):
                            discovered_urls.append(url)
                            print(f"    📍 URL extracted from snippet: {url[:60]}...")
                            
                    # Also look for domain-specific patterns in text
                    domain_patterns = {
                        'yelp.com': r'yelp\.com/biz/[\w\-]+',
                        'tripadvisor.com': r'tripadvisor\.com/Restaurant_Review[\w\-]+',
                        'reddit.com': r'reddit\.com/r/[\w]+/comments/[\w]+',
                        'google.com': r'google\.com/maps/place/[\w\-\+%]+'
                    }
                    
                    for domain, pattern in domain_patterns.items():
                        matches = re.findall(pattern, result, re.IGNORECASE)
                        for match in matches:
                            full_url = f"https://{match}"
                            if is_mri_target_url(full_url):
                                discovered_urls.append(full_url)
                                print(f"    🎯 Pattern-matched URL: {full_url[:60]}...")
                else:
                    print(f"    ⚠️ Skipping unexpected result type: {type(result)}")
                    
        except Exception as e:
            print(f"    ❌ SERPER query failed: {str(e)}")
            continue

    # Phase 2: Enhanced Puppeteer Scraping
    print(f"\n🧬 Phase 2: Enhanced Scraping ({len(discovered_urls)} URLs)...")
    puppeteer_url = secrets["PUPPETEER_ENDPOINT"]

    for i, target_url in enumerate(discovered_urls[:5]):  # Limit to 5 URLs for testing
        print(f"  🌐 Scraping {i+1}/{min(len(discovered_urls), 5)}: {target_url[:50]}...")

        try:
            response = requests.get(puppeteer_url, params={
                'url': target_url,
                'extractData': 'true',
                'waitFor': 3000
            }, timeout=30)

            if response.status_code == 200:
                data = response.json()
                extracted = data.get('extractedData', {})

                # Collect discovered data
                if extracted.get('emails'):
                    mri_results["discovered_data"]["emails"].update(extracted['emails'])

                if extracted.get('phones'):
                    mri_results["discovered_data"]["phones"].update(extracted['phones'])

                # Analyze links for profiles
                for link_obj in extracted.get('links', []):
                    url = link_obj.get('url', '')
                    if is_profile_link(url):
                        mri_results["discovered_data"]["profiles"].append({
                            "url": url,
                            "text": link_obj.get('text', ''),
                            "source": target_url
                        })

                print(f"    ✅ Extracted: {len(extracted.get('emails', []))} emails, {len(extracted.get('phones', []))} phones")

        except Exception as e:
            print(f"    ❌ Scraping failed: {str(e)}")

    # Convert sets to lists for JSON serialization
    mri_results["discovered_data"]["emails"] = list(mri_results["discovered_data"]["emails"])
    mri_results["discovered_data"]["phones"] = list(mri_results["discovered_data"]["phones"])

    # Phase 3: Analysis Summary
    print("\n📊 Phase 3: Analysis Summary...")
    mri_results["scan_summary"] = {
        "total_emails_found": len(mri_results["discovered_data"]["emails"]),
        "total_phones_found": len(mri_results["discovered_data"]["phones"]),
        "total_profiles_found": len(mri_results["discovered_data"]["profiles"]),
        "urls_scanned": len(discovered_urls),
        "scan_complete": True
    }

    print(f"🎯 MRI Scan Complete:")
    print(f"  📧 Emails: {mri_results['scan_summary']['total_emails_found']}")
    print(f"  📞 Phones: {mri_results['scan_summary']['total_phones_found']}")
    print(f"  👤 Profiles: {mri_results['scan_summary']['total_profiles_found']}")

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

if __name__ == "__main__":
    # Test with Seth D.
    print("🧪 Testing Enhanced MRI Scanner...")
    results = enhanced_mri_scan("Seth D.", phone="9174505555")

    # Save results
    with open('mri_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("💾 Results saved to mri_test_results.json")
