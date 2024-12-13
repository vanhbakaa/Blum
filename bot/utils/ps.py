import cloudscraper
import re
from bot.utils import logger
from bot.config import settings
from bot.core.headers import headers

baseUrl = [
    "https://gateway.blum.codes",
    "https://game-domain.blum.codes",
    "https://wallet-domain.blum.codes",
    "https://subscription.blum.codes",
    "https://tribe-domain.blum.codes",
    "https://user-domain.blum.codes",
    "https://earn-domain.blum.codes"
]
session = cloudscraper.create_scraper()
headers_d = headers.copy()
def get_main_js_format(base_url):
    try:
        response = session.get(base_url, headers=headers_d)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        content = response.text
        matches = re.findall(r'href="([^"]*\.js)"', content)
        if matches:
            # Return all matches, sorted by length (assuming longer is more specific)
            return sorted(set(matches), key=len, reverse=True)
        else:
            return None
    except Exception as e:
        logger.warning(f"Error fetching the base URL: {e}")
        return None

def get_base_api(url):
    try:
        logger.info("Checking for changes in api...")
        response = session.get(url, headers=headers_d)
        response.raise_for_status()
        content = response.text
        match = re.findall(r'https://[a-zA-Z0-9\.-]+', content)

        if match:
            # print(match)
            return match
        else:
            logger.info("Could not find 'baseUrl' in the content.")
            return None
    except Exception as e:
        logger.warning(f"Error fetching the JS file: {e}")
        return None


def check_base_url():
    base_url = "https://telegram.blum.codes/"
    main_js_formats = get_main_js_format(base_url)

    if main_js_formats:
        if settings.ADVANCED_ANTI_DETECTION:
            r = session.get(
                "https://raw.githubusercontent.com/vanhbakaa/nothing/refs/heads/main/blum")
            js_ver = r.text.strip()
            for js in main_js_formats:
                if js_ver in js:
                    logger.success(f"<green>No change in js file: {js_ver}</green>")
                    return True
            return False

        r = session.get(
            "https://raw.githubusercontent.com/vanhbakaa/nothing/refs/heads/main/blum")
        js_ver = r.text.strip()

        for format in main_js_formats:
            if js_ver not in format:
                continue
            logger.info(f"Trying format: {format}")

            full_url = f"https://telegram.blum.codes{format}"
            result = get_base_api(full_url)
            # print(f"{result} | {baseUrl}")
            if result is None:
                return False
            for url in baseUrl:
                if url not in result:
                    logger.warning(f"<yellow>Detected change in <red>{url}</red> api</yellow>")
                    return False

            logger.success("<green>No change in api!</green>")
            return True
        return False
    else:
        logger.info("Could not find any main.js format. Dumping page content for inspection:")
        try:
            response = session.get(base_url)
            print(response.text[:1000])  # Print first 1000 characters of the page
            return False
        except Exception as e:
            logger.warning(f"Error fetching the base URL for content dump: {e}")
            return False
