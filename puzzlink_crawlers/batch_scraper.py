# batch_scraper.py  
"""Scrap in batches."""  
  
import asyncio  
from typing import List  
from core.scraper import PuzzleScraper  
  
  
async def batch_scrape(puzzle_types: List[str], output_dir: str = "output"):  
    
    results = {}  
      
    for puzzle_type in puzzle_types:  
        print(f"\n{'='*60}")  
        print(f"Scrap puzzle: {puzzle_type}")  
        print(f"{'='*60}")  
          
        scraper = PuzzleScraper(  
            puzzle_type=puzzle_type,  
            output_dir=output_dir  
        )  
          
        result = await scraper.scrape()  
        scraper.save_to_csv()  
          
        results[puzzle_type] = result  
          
        # 不同谜题类型之间等待较长时间  
        await asyncio.sleep(5)  
      
    # 输出总汇总  
    print(f"\n{'='*60}")  
    print("Complete. Statistics:")  
    print(f"{'='*60}")  
      
    total_scraped = 0  
    for puzzle_type, result in results.items():  
        print(f"  {puzzle_type}: {result.total_scraped} items.")  
        total_scraped += result.total_scraped  
      
    print(f"\nIn total: {total_scraped} items.")  
      
    return results  
  
  
if __name__ == '__main__':  
    puzzle_types = "voxas vslither wafusuma wagiri walllogic waterwalk wblink wittgen yajikazu yajilin yajilin-regions yajisoko yajitatami yinyang yosenabe".split(" ")
    
    asyncio.run(batch_scrape(puzzle_types))  
