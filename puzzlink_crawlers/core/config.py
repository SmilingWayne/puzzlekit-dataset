# puzzle_scraper/config.py  
"""Config files."""  

BASE_URL = "https://pzplus.tck.mn/db"  
  
HEADERS = {  
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",  
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",  
    'Accept-Encoding': "gzip, deflate, br",  
    'Accept-Language': "en-US,en;q=0.9",  
    'Connection': "keep-alive",  
}

MIN_WAIT_TIME = 1.5
MAX_WAIT_TIME = 4.0
PAGE_TIMEOUT = 30000  

MAX_RETRIES = 3  
