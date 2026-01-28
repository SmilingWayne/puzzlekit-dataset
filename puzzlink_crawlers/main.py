# main.py  
"""主程序入口"""  
  
import asyncio  
import argparse  
from core.scraper import PuzzleScraper  
  
  
async def main():  
    # 解析命令行参数  
    parser = argparse.ArgumentParser(  
        description='爬取 pzplus.tck.mn 逻辑谜题数据'  
    )  
    parser.add_argument(  
        'puzzle_type',  
        type=str,  
        help='谜题类型名称，如 mejilink, slitherlink 等'  
    )  
    parser.add_argument(  
        '-o', '--output',  
        type=str,  
        default='output',  
        help='输出目录 (默认: output)'  
    )  
    parser.add_argument(  
        '-m', '--max-pages',  
        type=int,  
        default=None,  
        help='最大爬取页数 (默认: 无限制)'  
    )  
    parser.add_argument(  
        '-f', '--filename',  
        type=str,  
        default=None,  
        help='输出文件名 (默认: 自动生成)'  
    )  
      
    args = parser.parse_args()  
      
    # 创建爬虫实例  
    scraper = PuzzleScraper(  
        puzzle_type=args.puzzle_type,  
        output_dir=args.output  
    )  
      
    # 执行爬取  
    result = await scraper.scrape(max_pages=args.max_pages)  
      
    # 保存结果  
    if result.total_scraped > 0:  
        output_path = scraper.save_to_csv(args.filename)  
        print(f"\n✅ 爬取完成! 共采集 {result.total_scraped} 个谜题")  
        print(f"📁 数据已保存到: {output_path}")  
    else:  
        print("\n⚠️ 没有采集到任何数据")  
      
    # 返回结果供进一步处理  
    return result  
  
  
if __name__ == '__main__':  
    asyncio.run(main())  
