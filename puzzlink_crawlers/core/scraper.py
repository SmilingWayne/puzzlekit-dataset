# puzzle_scraper/scraper.py  
"""核心爬虫模块"""  
  
import asyncio  
import random  
import csv  
from pathlib import Path  
from typing import List, Set, Optional  
from datetime import datetime  
  
from playwright.async_api import async_playwright, Browser, Page, BrowserContext  
  
from .config import (  
    BASE_URL, HEADERS, MIN_WAIT_TIME, MAX_WAIT_TIME,   
    PAGE_TIMEOUT, MAX_RETRIES  
)  
from .models import PuzzleData, ScrapingResult  
from .parser import PuzzleParser  
from .logger import setup_logger, get_log_filename  
  
  
class PuzzleScraper:  
    """谜题爬虫主类"""  
      
    def __init__(self, puzzle_type: str, output_dir: str = "output"):  
        """  
        初始化爬虫  
          
        Args:  
            puzzle_type: 谜题类型名称  
            output_dir: 输出目录  
        """  
        self.puzzle_type = puzzle_type  
        self.output_dir = Path(output_dir)  
        self.output_dir.mkdir(parents=True, exist_ok=True)  
          
        # 创建日志目录  
        Path("logs").mkdir(exist_ok=True)  
          
        # 设置 logger  
        log_file = get_log_filename(puzzle_type)  
        self.logger = setup_logger(f"scraper_{puzzle_type}", log_file)  
          
        # 解析器  
        self.parser = PuzzleParser()  
          
        # 已收集的 URL 集合（用于去重）  
        self.collected_urls: Set[str] = set()  
          
        # 爬取结果  
        self.result = ScrapingResult(puzzle_type=puzzle_type)  
          
        # 全局索引  
        self.global_idx = 1  
      
    def _get_target_url(self) -> str:  
        """构建目标 URL"""  
        return f"{BASE_URL}?type={self.puzzle_type}&generated=any"  
      
    async def _random_delay(self, min_time: float = None, max_time: float = None):  
        """随机延迟"""  
        min_t = min_time or MIN_WAIT_TIME  
        max_t = max_time or MAX_WAIT_TIME  
        delay = random.uniform(min_t, max_t)  
        self.logger.debug(f"等待 {delay:.2f} 秒...")  
        await asyncio.sleep(delay)  
      
    async def _setup_browser(self) -> tuple[Browser, BrowserContext]:  
        """设置浏览器"""  
        playwright = await async_playwright().start()  
          
        browser = await playwright.chromium.launch(  
            headless=True,  # 设为 False 可以看到浏览器操作  
        )  
          
        context = await browser.new_context(  
            extra_http_headers=HEADERS,  
            viewport={'width': 1920, 'height': 1080},  
            user_agent=HEADERS['User-Agent']  
        )  
          
        return browser, context, playwright  
      
    async def _click_older_button(self, page: Page) -> bool:  
        """  
        点击 "older »" 按钮  
          
        Returns:  
            是否成功点击（如果按钮不存在或禁用则返回 False）  
        """  
        try:  
            # 查找所有 paging 区域  
            paging_spans = page.locator('span.paging')  
              
            if await paging_spans.count() == 0:  
                self.logger.info("未找到分页区域")  
                return False  
              
            # 获取第一个分页区域中的 "older »" 按钮  
            first_paging = paging_spans.first  
            older_button = first_paging.locator('button', has_text='older »')  
              
            if await older_button.count() == 0:  
                self.logger.info("未找到 'older »' 按钮")  
                return False  
              
            # 检查按钮是否禁用  
            is_disabled = await older_button.is_disabled()  
            if is_disabled:  
                self.logger.info("'older »' 按钮已禁用，已到达最后一页")  
                return False  
              
            # 点击按钮  
            await older_button.click()  
            self.logger.info("已点击 'older »' 按钮")  
              
            # 等待页面更新  
            await page.wait_for_load_state('networkidle', timeout=PAGE_TIMEOUT)  
            await self._random_delay(1.0, 2.0)  
              
            return True  
              
        except Exception as e:  
            self.logger.error(f"点击 'older »' 按钮失败: {e}")  
            return False  
      
    async def _scrape_current_page(self, page: Page) -> List[PuzzleData]:  
        """  
        爬取当前页面的所有谜题  
          
        Returns:  
            当前页面的谜题数据列表  
        """  
        puzzles = []  
          
        try:  
            elements = await self.parser.get_puzzle_elements(page)  
            self.logger.info(f"当前页面找到 {len(elements)} 个谜题元素")  
              
            for element in elements:  
                try:  
                    puzzle = await self.parser.parse_puzzle_element(  
                        element,   
                        self.puzzle_type,   
                        self.global_idx  
                    )  
                      
                    if puzzle is None:  
                        # variant 谜题  
                        self.result.total_skipped_variant += 1  
                        self.logger.debug(f"跳过 variant 谜题")  
                        continue  
                      
                    # 检查是否重复  
                    if puzzle.puzz_link_url in self.collected_urls:  
                        self.logger.debug(f"跳过重复谜题: {puzzle.puzz_link_url}")  
                        continue  
                      
                    # 添加到结果  
                    self.collected_urls.add(puzzle.puzz_link_url)  
                    puzzles.append(puzzle)  
                    self.global_idx += 1  
                      
                    self.logger.info(  
                        f"✓ 已采集: {puzzle.name} | "  
                        f"作者: {puzzle.author or 'N/A'} | "  
                        f"难度: {puzzle.difficulty or 'N/A'}"  
                    )  
                      
                except Exception as e:  
                    self.result.total_errors += 1  
                    error_msg = f"处理谜题元素时出错: {e}"  
                    self.result.errors.append(error_msg)  
                    self.logger.error(error_msg)  
                    continue  
                      
        except Exception as e:  
            self.result.total_errors += 1  
            error_msg = f"爬取当前页面失败: {e}"  
            self.result.errors.append(error_msg)  
            self.logger.error(error_msg)  
          
        return puzzles  
      
    async def scrape(self, max_pages: int = None) -> ScrapingResult:  
        """  
        执行爬取  
          
        Args:  
            max_pages: 最大爬取页数，None 表示爬取所有页面  
          
        Returns:  
            爬取结果  
        """  
        self.logger.info(f"=" * 60)  
        self.logger.info(f"开始爬取谜题类型: {self.puzzle_type}")  
        self.logger.info(f"目标 URL: {self._get_target_url()}")  
        self.logger.info(f"=" * 60)  
          
        browser = None  
        playwright = None  
          
        try:  
            browser, context, playwright = await self._setup_browser()  
            page = await context.new_page()  
              
            # 设置超时  
            page.set_default_timeout(PAGE_TIMEOUT)  
              
            # 访问目标页面  
            target_url = self._get_target_url()  
            self.logger.info(f"正在访问: {target_url}")  
              
            await page.goto(target_url)  
            await page.wait_for_load_state('networkidle')  
            await self._random_delay()  
              
            page_num = 1  
              
            while True:  
                self.logger.info(f"-" * 40)  
                self.logger.info(f"正在处理第 {page_num} 页")  
                  
                # 爬取当前页面  
                puzzles = await self._scrape_current_page(page)  
                self.result.puzzles.extend(puzzles)  
                self.result.total_scraped += len(puzzles)  
                  
                self.logger.info(  
                    f"第 {page_num} 页完成: "  
                    f"本页采集 {len(puzzles)} 个, "  
                    f"累计 {self.result.total_scraped} 个"  
                )  
                  
                # 检查是否达到最大页数  
                if max_pages and page_num >= max_pages:  
                    self.logger.info(f"已达到最大页数限制 ({max_pages})")  
                    break  
                  
                # 随机延迟  
                await self._random_delay()  
                  
                # 尝试点击下一页  
                if not await self._click_older_button(page):  
                    self.logger.info("没有更多页面了")  
                    break  
                  
                page_num += 1  
              
            self.result.total_found = (  
                self.result.total_scraped +   
                self.result.total_skipped_variant  
            )  
              
        except Exception as e:  
            self.result.total_errors += 1  
            error_msg = f"爬取过程出现严重错误: {e}"  
            self.result.errors.append(error_msg)  
            self.logger.error(error_msg)  
              
        finally:  
            if browser:  
                await browser.close()  
            if playwright:  
                await playwright.stop()  
          
        # 输出汇总  
        self._log_summary()  
          
        return self.result  
      
    def _log_summary(self):  
        """输出爬取汇总"""  
        self.logger.info(f"=" * 60)  
        self.logger.info(f"爬取完成汇总")  
        self.logger.info(f"=" * 60)  
        self.logger.info(f"谜题类型: {self.puzzle_type}")  
        self.logger.info(f"总共发现: {self.result.total_found} 个谜题")  
        self.logger.info(f"成功采集: {self.result.total_scraped} 个")  
        self.logger.info(f"跳过(variant): {self.result.total_skipped_variant} 个")  
        self.logger.info(f"错误数量: {self.result.total_errors} 个")  
          
        if self.result.errors:  
            self.logger.warning("错误详情:")  
            for error in self.result.errors[:10]:  # 只显示前10个错误  
                self.logger.warning(f"  - {error}")  
      
    def save_to_csv(self, filename: str = None) -> str:  
        """  
        保存结果到 CSV 文件  
          
        Args:  
            filename: 文件名，如果为 None 则自动生成  
          
        Returns:  
            保存的文件路径  
        """  
        if not filename:  
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  
            filename = f"{self.puzzle_type}_{timestamp}.csv"  
          
        filepath = self.output_dir / filename  
          
        if not self.result.puzzles:  
            self.logger.warning("没有数据可保存")  
            return str(filepath)  
          
        # CSV 字段  
        fieldnames = [  
            'name', 'puzzle_type', 'puzz_link_url', 'date', 'author',  
            'solves', 'difficulty', 'source_url', 'pzplus_url',   
            'pzv_url', 'scraped_at'  
        ]  
          
        try:  
            with open(filepath, 'w', newline='', encoding='utf-8') as f:  
                writer = csv.DictWriter(f, fieldnames=fieldnames)  
                writer.writeheader()  
                  
                for puzzle in self.result.puzzles:  
                    writer.writerow(puzzle.to_dict())  
              
            self.logger.info(f"数据已保存到: {filepath}")  
              
        except Exception as e:  
            self.logger.error(f"保存 CSV 失败: {e}")  
          
        return str(filepath)  
