import pandas as pd
import os
from pathlib import Path

def merge_puzzle_data(input_folder='output', output_file='merged_puzzles.csv'):
    """
    合并output文件夹中所有CSV文件，提取指定列
    
    Args:
        input_folder: 包含CSV文件的文件夹路径
        output_file: 合并后的输出文件路径
    """
    input_path = Path(input_folder)
    csv_files = list(input_path.glob('*.csv'))
    
    if not csv_files:
        print(f"在文件夹 '{input_folder}' 中未找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    required_columns = [
        'name', 
        'puzzle_type', 
        'puzz_link_url', 
        'author', 
        'solves', 
        'difficulty', 
        'scraped_at'
    ]
    
    all_data = []
    processed_files = 0
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"警告: 文件 '{csv_file.name}' 缺少列: {missing_cols}")
                continue
            
            df_subset = df[required_columns].copy()
            
            all_data.append(df_subset)
            processed_files += 1
            
            print(f"已处理: {csv_file.name} ({len(df_subset)} 行)")
            
        except Exception as e:
            print(f"处理文件 '{csv_file.name}' 时出错: {e}")
    
    if not all_data:
        print("没有成功读取任何文件")
        return
    
    merged_df = pd.concat(all_data, ignore_index=True)
    
    initial_count = len(merged_df)
    merged_df = merged_df.drop_duplicates(
        subset=['name', 'puzz_link_url'], 
        keep='first'
    )
    final_count = len(merged_df)
    
    merged_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n合并完成!")
    print(f"处理了 {processed_files}/{len(csv_files)} 个文件")
    print(f"合并后总行数: {initial_count}")
    print(f"去重后行数: {final_count}")
    print(f"已保存到: {output_file}")
    
    print(f"\n数据预览 (前5行):")
    print(merged_df.head())
    
    print(f"\n谜题类型统计:")
    print(merged_df['puzzle_type'].value_counts().head(10))
    
    return merged_df

if __name__ == "__main__":
    merge_puzzle_data()
    