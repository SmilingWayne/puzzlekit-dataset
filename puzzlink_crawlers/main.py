# main.py  
"""Main function"""  
  
import asyncio  
import argparse  
from core.scraper import PuzzleScraper  

async def main():  
    # parse command line params  
    parser = argparse.ArgumentParser(  
        description='To scrap pzplus.tck.mn puzzle data'  
    )  
    parser.add_argument(  
        'puzzle_type',  
        type=str,  
        help='Name of puzzle, i.g.,  mejilink, hitori, ... '  
    )  
    parser.add_argument(  
        '-o', '--output',  
        type=str,  
        default='output',  
        help='output directory (default: output)'  
    )  
    parser.add_argument(  
        '-m', '--max-pages',  
        type=int,  
        default=None,  
        help='Maximum pages to scrap (default: no limit)'  
    )  
    parser.add_argument(  
        '-f', '--filename',  
        type=str,  
        default=None,  
        help='output file name (default: auto generate)'  
    )  
      
    args = parser.parse_args()  
      
    # create instance  
    scraper = PuzzleScraper(  
        puzzle_type=args.puzzle_type,  
        output_dir=args.output  
    )  
      
    # do the scrape  
    result = await scraper.scrape(max_pages=args.max_pages)  
      
    if result.total_scraped > 0:  
        output_path = scraper.save_to_csv(args.filename)  
        print(f"\n✅ Complete Scrap! Collect {result.total_scraped} items!")  
        print(f"📁 Data saved to: {output_path}")  
    else:  
        print("\n⚠️ No data collected.")  
      
    return result  
  
  
if __name__ == '__main__':  
    asyncio.run(main())  
