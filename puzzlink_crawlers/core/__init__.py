# puzzle_scraper/__init__.py  
"""Puzzle Scraper 包"""  
  
from .scraper import PuzzleScraper  
from .models import PuzzleData, ScrapingResult  
from .config import BASE_URL, HEADERS  
  
__all__ = [  
    'PuzzleScraper',  
    'PuzzleData',   
    'ScrapingResult',  
    'BASE_URL',  
    'HEADERS'  
]  
