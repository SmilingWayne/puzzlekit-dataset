# puzzle_scraper/scraper.py  
"""Core scraper module."""  
  
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
    """Main class"""  
      
    def __init__(self, puzzle_type: str, output_dir: str = "output"):  
        """  
        Initialize.  
          
        Args:  
            puzzle_type: type.
            output_dir: output directory.  
        """  
        self.puzzle_type = puzzle_type  
        self.output_dir = Path(output_dir)  
        self.output_dir.mkdir(parents=True, exist_ok=True)  
          
        # Logger directory.
        Path("logs").mkdir(exist_ok=True)  
          
        # setup logger  
        log_file = get_log_filename(puzzle_type)  
        self.logger = setup_logger(f"scraper_{puzzle_type}", log_file)  
          
        # parser  
        self.parser = PuzzleParser()  
          
        # Collected url collections.
        self.collected_urls: Set[str] = set()  
          
        # result.  
        self.result = ScrapingResult(puzzle_type=puzzle_type)  
          
        # global index (for index marker)  
        self.global_idx = 1  
      
    def _get_target_url(self) -> str:  
        """Target URL"""  
        return f"{BASE_URL}?type={self.puzzle_type}&generated=any"  
      
    async def _random_delay(self, min_time: float = None, max_time: float = None):  
        """Random delay"""  
        min_t = min_time or MIN_WAIT_TIME  
        max_t = max_time or MAX_WAIT_TIME  
        delay = random.uniform(min_t, max_t)  
        self.logger.debug(f"Delayed for {delay:.2f} seconds...")  
        await asyncio.sleep(delay)  
      
    async def _setup_browser(self) -> tuple[Browser, BrowserContext]:  
        """Setup browser"""  
        playwright = await async_playwright().start()  
          
        browser = await playwright.chromium.launch(  
            headless=True,
        )  
          
        context = await browser.new_context(  
            extra_http_headers=HEADERS,  
            viewport={'width': 1920, 'height': 1080},  
            user_agent=HEADERS['User-Agent']  
        )  
          
        return browser, context, playwright  
      
    async def _click_older_button(self, page: Page) -> bool:  
        """  
        Click "older »" buttom
          
        Returns:  
            Success or not?
        """  
        try:  
            paging_spans = page.locator('span.paging')  
              
            if await paging_spans.count() == 0:  
                self.logger.info("Unable to find page split area.")  
                return False  
              
            first_paging = paging_spans.first  
            older_button = first_paging.locator('button', has_text='older »')  
              
            if await older_button.count() == 0:  
                self.logger.info("Fail to find 'older »' button!")  
                return False  
                
            is_disabled = await older_button.is_disabled()  
            if is_disabled:  
                self.logger.info("'older »' is disabled. Reach last page.")  
                return False  
              
            await older_button.click()  
            self.logger.info("Successfully click 'older »' button")  
            await page.wait_for_load_state('networkidle', timeout=PAGE_TIMEOUT)  
            await self._random_delay(1.0, 2.0)  
              
            return True  
              
        except Exception as e:  
            self.logger.error(f"Fail to click 'older »' Button: {e}")  
            return False  
      
    async def _scrape_current_page(self, page: Page) -> List[PuzzleData]:  
        
        puzzles = []  
          
        try:  
            elements = await self.parser.get_puzzle_elements(page)  
            self.logger.info(f"Find {len(elements)} puzzle element on this page.")  
              
            for element in elements:  
                try:  
                    puzzle = await self.parser.parse_puzzle_element(  
                        element,   
                        self.puzzle_type,   
                        self.global_idx  
                    )  
                      
                    if puzzle is None:  

                        self.result.total_skipped_variant += 1  
                        self.logger.debug(f"Skip variant puzzle.")  
                        continue  
                      
                    if puzzle.puzz_link_url in self.collected_urls:  
                        self.logger.debug(f"Skip duplicated: {puzzle.puzz_link_url}")  
                        continue  
                      
                    self.collected_urls.add(puzzle.puzz_link_url)  
                    puzzles.append(puzzle)  
                    self.global_idx += 1  
                      
                    self.logger.info(  
                        f"✓ Collected: {puzzle.name} | "  
                        f"Author: {puzzle.author or 'N/A'} | "  
                        f"Difficulty: {puzzle.difficulty or 'N/A'}"  
                    )  
                      
                except Exception as e:  
                    self.result.total_errors += 1  
                    error_msg = f"Error when dealing with element: {e}"  
                    self.result.errors.append(error_msg)  
                    self.logger.error(error_msg)  
                    continue  
                      
        except Exception as e:  
            self.result.total_errors += 1  
            error_msg = f"Fail to scrap current page: {e}"  
            self.result.errors.append(error_msg)  
            self.logger.error(error_msg)  
          
        return puzzles  
      
    async def scrape(self, max_pages: int = None) -> ScrapingResult:  

        self.logger.info(f"=" * 60)  
        self.logger.info(f"Start puzzle type: {self.puzzle_type}")  
        self.logger.info(f"Target URL: {self._get_target_url()}")  
        self.logger.info(f"=" * 60)  
          
        browser = None  
        playwright = None  
          
        try:  
            browser, context, playwright = await self._setup_browser()  
            page = await context.new_page()  

            page.set_default_timeout(PAGE_TIMEOUT)  

            target_url = self._get_target_url()  
            self.logger.info(f"Browsing: {target_url}")  
              
            await page.goto(target_url)  
            await page.wait_for_load_state('networkidle')  
            await self._random_delay()  
              
            page_num = 1  
              
            while True:  
                self.logger.info(f"-" * 40)  
                self.logger.info(f"Processing Page {page_num}~")  
                  
                puzzles = await self._scrape_current_page(page)  
                self.result.puzzles.extend(puzzles)  
                self.result.total_scraped += len(puzzles)  
                  
                self.logger.info(  
                    f"Finish Page {page_num} : "  
                    f"Collect {len(puzzles)} items, "  
                    f"In total {self.result.total_scraped} items."  
                )  
                  
                if max_pages and page_num >= max_pages:  
                    self.logger.info(f"Reach maximum page limit ({max_pages})")  
                    break  

                await self._random_delay()  
                  
                if not await self._click_older_button(page):  
                    self.logger.info("No more pages.")  
                    break  
                  
                page_num += 1  
              
            self.result.total_found = (  
                self.result.total_scraped +   
                self.result.total_skipped_variant  
            )  
              
        except Exception as e:  
            self.result.total_errors += 1  
            error_msg = f"Error when scraping: {e}"  
            self.result.errors.append(error_msg)  
            self.logger.error(error_msg)  
              
        finally:  
            if browser:  
                await browser.close()  
            if playwright:  
                await playwright.stop()  
          
        self._log_summary()  
        return self.result  
      
    def _log_summary(self):  
        self.logger.info(f"=" * 60)  
        self.logger.info(f"Analytics:")  
        self.logger.info(f"=" * 60)  
        self.logger.info(f"Types: {self.puzzle_type}")  
        self.logger.info(f"Found: {self.result.total_found} items.")  
        self.logger.info(f"✅ Get: {self.result.total_scraped} items.")  
        self.logger.info(f"☑️ Skip variant: {self.result.total_skipped_variant} items.")  
        self.logger.info(f"❌ Failure: {self.result.total_errors} items.")  
          
        if self.result.errors:  
            self.logger.warning("Error in detail:")  
            for error in self.result.errors[:10]:  
                self.logger.warning(f"  - {error}")  
      
    def save_to_csv(self, filename: str = None) -> str:  
        
        if not filename:  
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  
            filename = f"{self.puzzle_type}_{timestamp}.csv"  
          
        filepath = self.output_dir / filename  
          
        if not self.result.puzzles:  
            self.logger.warning("No data to save to csv.")  
            return str(filepath)  
          
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
              
            self.logger.info(f"Saved to: {filepath}")  
              
        except Exception as e:  
            self.logger.error(f"Failed when saving CSV: {e}")  
          
        return str(filepath)  
