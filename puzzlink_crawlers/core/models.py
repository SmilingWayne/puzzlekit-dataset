# puzzle_scraper/models.py  
"""data model definition"""  
  
from dataclasses import dataclass, field  
from typing import Optional, List  
from datetime import datetime  

@dataclass  
class PuzzleData:  
    """Single puzzle data structure"""  
    name: str                          # Puzzle name（如 mejilink001）  
    puzzle_type: str                   # Puzzle type   
    puzz_link_url: str                 # puzz.link URL  
    date: Optional[str] = None         # Release date 
    author: Optional[str] = None       # Author.  
    solves: Optional[int] = None       # Solve time.
    difficulty: Optional[int] = None   # Diffifulty.  
    source_url: Optional[str] = None   # Original link（Twitter, etc. ）  
    pzplus_url: Optional[str] = None   # pzplus URL  
    pzv_url: Optional[str] = None      # pzv.jp URL  
    has_variant_tag: bool = False      # with variant or not.
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())  
      
    def to_dict(self) -> dict:  
        """convert to dict form."""  
        return {  
            'name': self.name,  
            'puzzle_type': self.puzzle_type,  
            'puzz_link_url': self.puzz_link_url,  
            'date': self.date,  
            'author': self.author,  
            'solves': self.solves,  
            'difficulty': self.difficulty,  
            'source_url': self.source_url,  
            'pzplus_url': self.pzplus_url,  
            'pzv_url': self.pzv_url,  
            'scraped_at': self.scraped_at  
        }  

@dataclass  
class ScrapingResult:  
    """Collection."""  
    puzzle_type: str  
    total_found: int = 0  
    total_scraped: int = 0  
    total_skipped_variant: int = 0  
    total_errors: int = 0  
    puzzles: List[PuzzleData] = field(default_factory=list)  
    errors: List[str] = field(default_factory=list)  
