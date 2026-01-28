# batch_scraper.py  
"""批量爬取多种谜题"""  
  
import asyncio  
from typing import List  
from core.scraper import PuzzleScraper  
  
  
async def batch_scrape(puzzle_types: List[str], output_dir: str = "output"):  
    """  
    批量爬取多种谜题  
      
    Args:  
        puzzle_types: 谜题类型列表  
        output_dir: 输出目录  
    """  
    results = {}  
      
    for puzzle_type in puzzle_types:  
        print(f"\n{'='*60}")  
        print(f"开始爬取: {puzzle_type}")  
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
    print("批量爬取完成汇总")  
    print(f"{'='*60}")  
      
    total_scraped = 0  
    for puzzle_type, result in results.items():  
        print(f"  {puzzle_type}: {result.total_scraped} 个谜题")  
        total_scraped += result.total_scraped  
      
    print(f"\n总计: {total_scraped} 个谜题")  
      
    return results  
  
  
# 使用示例  
if __name__ == '__main__':  
    # 要爬取的谜题类型列表  
    puzzle_types = [  
        'mejilink',  
        'slitherlink',  
        'nurikabe',  
        # 添加更多谜题类型...  
    ]  
      
    asyncio.run(batch_scrape(puzzle_types))  
