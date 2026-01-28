# puzzle_scraper/models.py  
"""数据模型定义"""  
  
from dataclasses import dataclass, field  
from typing import Optional, List  
from datetime import datetime  
  
  
@dataclass  
class PuzzleData:  
    """单个谜题的数据结构"""  
    name: str                          # 谜题名称（如 mejilink001）  
    puzzle_type: str                   # 谜题类型  
    puzz_link_url: str                 # puzz.link URL  
    date: Optional[str] = None         # 发布日期  
    author: Optional[str] = None       # 作者  
    solves: Optional[int] = None       # 解题次数  
    difficulty: Optional[int] = None   # 难度  
    source_url: Optional[str] = None   # 原始来源链接（Twitter等）  
    pzplus_url: Optional[str] = None   # pzplus URL  
    pzv_url: Optional[str] = None      # pzv.jp URL  
    has_variant_tag: bool = False      # 是否有 variant 标签  
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())  
      
    def to_dict(self) -> dict:  
        """转换为字典格式"""  
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
    """爬取结果汇总"""  
    puzzle_type: str  
    total_found: int = 0  
    total_scraped: int = 0  
    total_skipped_variant: int = 0  
    total_errors: int = 0  
    puzzles: List[PuzzleData] = field(default_factory=list)  
    errors: List[str] = field(default_factory=list)  
