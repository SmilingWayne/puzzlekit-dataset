import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from Core.core import BasePuzzleCrawler, PuzzleItem

class PipelineCrawler(BasePuzzleCrawler):
    
    def parse_index(self, html_content: str) -> List[Dict]:
        soup = BeautifulSoup(html_content, 'html.parser')
        container = soup.find('div', id='index-1')
        
        if not container:
            self.logger.warning("Index container #index-1 not found.")
            return []

        results = []
        for link in container.find_all('a'):
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if href and text:
                # Custom logic to classify links as you did before
                link_type = 'class_sv' if 'sv' in link.get('class', []) else 'other'
                results.append({
                    'href': self.config.base_url + href if not href.startswith('http') else href, 
                    'text': text, 
                    'type': link_type
                })
        
        # You can add your `filter_and_classify_results` logic here if needed
        return results

    def parse_puzzle_detail(self, html_content: str, metadata: Dict) -> Optional[PuzzleItem]:
        text = metadata.get('text', 'unknown')
        link_type = metadata.get('type')

        # Define Regex patterns based on type
        if link_type == "class_sv":
            patterns = {
                
                'grids': r"(?<=\[problem\]\n)(.*?)(?=\[solution\])",
                'sol': r"(?<=\[solution\]\n)(.*?)(?=\[moves\])"
            }
        else:
            patterns = {
                
                'grids': r"(?<=\[problem\]\n)(.*?)(?=\[solution\])",
                'sol': r"(?<=\[solution\]\n)(.*?)(?=\[end\])"
            }

        try:
            
            grids_match = re.search(patterns['grids'], html_content, re.DOTALL)
            
            sol_match = re.search(patterns['sol'], html_content, re.DOTALL)

            if not all([grids_match, sol_match]):
                self.logger.warning(f"Regex mismatch for {text}")
                return None

            # Process data
            solution_raw = sol_match.group().strip()
            # cols_raw = cols_match.group().strip()
            # rows_raw = rows_match.group().strip()
            # areas_raw = areas_match.group().strip()
            grids_raw = grids_match.group().strip()
            
            rows_list = solution_raw.strip().split("\n")
            num_rows = len(rows_list)
            num_cols = len(rows_list[0].split()) if num_rows > 0 else 0
            # Determine max char for puzzle definition
            
            rows_list = solution_raw.strip().split("\n")
            sol_mat = [row.strip().split(" ") for row in rows_list]
            curmax = 0
            rows = []
            cols = []
            for i in range(num_rows):
                val = 0
                for j in range(num_cols):
                    if sol_mat[i][j] != "-":
                        val += 1
                rows.append(val)
            
            for j in range(num_rows):
                val = 0
                for i in range(num_cols):
                    if sol_mat[i][j] != "-":
                        val += 1
                cols.append(val)
            cols_raw = " ".join(map(str, cols))
            rows_raw = " ".join(map(str, rows))
            
            header = f"{num_rows} {num_cols}"
            problem_str = f"{header}\n{cols_raw}\n{rows_raw}\n{grids_raw}"
            solution_str = f"{header}\n{solution_raw}"
            
            puzzle_id = f"{text}_{num_rows}x{num_cols}"

            return PuzzleItem(
                id=puzzle_id,
                difficulty=0, # Placeholder
                source_url=metadata.get('href', ''),
                problem=problem_str,
                solution=solution_str,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Error parsing detail for {text}: {e}")
            return None