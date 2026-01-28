# puzzle_scraper/parser.py  
"""HTML parser module"""  
  
import re  
from typing import Optional, Tuple, List  
from bs4 import BeautifulSoup  
from playwright.async_api import Locator, Page  
  
from .models import PuzzleData  
from .logger import setup_logger  
  
logger = setup_logger(__name__)  
  
  
class PuzzleParser:  
    """HTML Parser"""  
      
    @staticmethod  
    def parse_difficulty_info(title_text: str) -> Tuple[Optional[int], Optional[int]]:  
        """
        Args:  
            title_text: 如 "solves: 1723, difficulty: 5"  
          
        Returns:  
            (solves, difficulty) 元组  
        """  
        solves = None  
        difficulty = None  
          
        try:  
            # 匹配 solves  
            solves_match = re.search(r'solves:\s*(\d+)', title_text)  
            if solves_match:  
                solves = int(solves_match.group(1))  
              
            # 匹配 difficulty  
            diff_match = re.search(r'difficulty:\s*(\d+)', title_text)  
            if diff_match:  
                difficulty = int(diff_match.group(1))  
        except Exception as e:  
            logger.debug(f"解析难度信息失败: {e}")  
          
        return solves, difficulty  
      
    @staticmethod  
    async def parse_puzzle_element(  
        element: Locator,   
        puzzle_type: str,   
        idx: int  
    ) -> Optional[PuzzleData]:  
        """  
        解析单个谜题元素  
          
        Args:  
            element: Playwright Locator 对象  
            puzzle_type: 谜题类型名称  
            idx: 索引号  
          
        Returns:  
            PuzzleData 对象，如果是 variant 则返回 None  
        """  
        try:  
            # 获取元素的 HTML 内容  
            html_content = await element.inner_html()  
            soup = BeautifulSoup(html_content, 'html.parser')  
              
            # 检查是否有 variant 标签  
            variant_tag = soup.find('span', class_='tag-variant')  
            if variant_tag:  
                logger.debug(f"跳过 variant 谜题 (idx={idx})")  
                return None  
              
            # 获取 puzz.link URL  
            puzz_link_anchor = soup.find('a', class_='lpl')  
            if not puzz_link_anchor:  
                logger.warning(f"未找到 puzz.link URL (idx={idx})")  
                return None  
              
            puzz_link_url = puzz_link_anchor.get('href', '')  
              
            # 获取日期  
            date_span = soup.find('span', class_='date')  
            date = date_span.get_text(strip=True) if date_span else None  
              
            # 获取作者  
            author_span = soup.find('span', class_='author')  
            author = None  
            if author_span:  
                # 获取作者名称，排除 filterplus 链接的文本  
                author_text = author_span.get_text(strip=True)  
                # 移除末尾的 "+"  
                author = author_text.rstrip('+').strip()  
              
            # 获取难度信息  
            puzzle_type_span = soup.find('span', class_='puzzletype')  
            solves, difficulty = None, None  
            if puzzle_type_span and puzzle_type_span.get('title'):  
                solves, difficulty = PuzzleParser.parse_difficulty_info(  
                    puzzle_type_span.get('title')  
                )  
              
            # Get source link  
            source_link = soup.find('a', class_='longlink')  
            source_url = source_link.get('href', '') if source_link else None  
              
            # Get pzplus url.
            pzplus_anchor = soup.find('a', class_='lpzp')  
            pzplus_url = pzplus_anchor.get('href', '') if pzplus_anchor else None  
            if pzplus_url and pzplus_url.startswith('/'):  
                pzplus_url = f"https://pzplus.tck.mn{pzplus_url}"  
            
            pzv_anchor = soup.find('a', class_='lpzv')  
            pzv_url = pzv_anchor.get('href', '') if pzv_anchor else None  
            
            puzzle_name = f"{puzzle_type}{idx:04d}"  
              
            return PuzzleData(  
                name=puzzle_name,  
                puzzle_type=puzzle_type,  
                puzz_link_url=puzz_link_url,  
                date=date,  
                author=author,  
                solves=solves,  
                difficulty=difficulty,  
                source_url=source_url,  
                pzplus_url=pzplus_url,  
                pzv_url=pzv_url,  
                has_variant_tag=False  
            )  
              
        except Exception as e:  
            logger.error(f"Fail to parse puzzle element: (idx={idx}): {e}")  
            return None  
      
    @staticmethod  
    async def get_puzzle_elements(page: Page) -> List[Locator]:  
        """  
        Get all puzzle element.  
          
        Args:  
            page: Playwright Page object  
          
        Returns:  
            List of puzzle element  
        """  
        # Wait fot tweets element.
        await page.wait_for_selector('ul.tweets', timeout=10000)  
          
        # Get all puzzle element.
        elements = page.locator('ul.tweets li.pzvpuzzle')  
        count = await elements.count()  
          
        return [elements.nth(i) for i in range(count)]  
