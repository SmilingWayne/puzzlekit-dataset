# This code contains several decoders for puzzle-xxx.com puzzles, 
# e.g., https://www.puzzle-shikaku.com/?size=8
# 
# This is especially helpful if you want to parse these grids
# into computer-friendly style.

from typing import Dict, Optional, Callable, List
import hashlib

def shigoki_parser(num_rows: int, num_cols: int, strs: str):
    arr = ["-" for _ in range(num_rows * num_cols)]
    i = 0
    cur_idx = 0
    while i < len(strs):
        if strs[i] in "abcdefghijklmnopqrstuvwxyz":
            for k in range(ord(strs[i]) - ord('a') + 1):
                cur_idx += 1
            i += 1
            continue
        else:
            if strs[i] in "WB":
                cur_color = strs[i].lower()
                i += 1
                cur_pre = i
                while i < len(strs) and strs[i] in "0123456789":
                    i += 1
                cur_num = strs[cur_pre: i]
                arr[cur_idx] = f"{cur_color}{cur_num}"
                cur_idx += 1
    # print(arr)
    ret_mat = [arr[idx: idx + num_cols] for idx in range(0, num_rows * num_cols, num_cols)]
    # print(ret_mat)
    headers = f"{num_rows} {num_cols}"
    contents = "\n".join([" ".join(row) for row in ret_mat])
    return f"{headers}\n{contents}"
    

def shikaku_parser(num_rows: int, num_cols: int, strs: str) -> str:
    total_cells = num_rows * num_cols
    arr = ["-" for _ in range(total_cells)]
    i = 0
    cur_idx = 0
    while i < len(strs):
        ch = strs[i]
        if 'a' <= ch <= 'z':
            step = ord(ch) - ord('a') + 1
            if cur_idx + step > total_cells:
                for row in [arr[idx: idx + num_cols] for idx in range(0, num_rows * num_cols, num_cols)]:
                    print(row)
                raise ValueError(f"Move beyond grid: cur_idx={cur_idx}, step={step}, total={total_cells}")
            cur_idx += step
            i += 1
        elif ch.isdigit():
            j = i
            while j < len(strs) and strs[j].isdigit():
                j += 1
            num_str = strs[i:j]
            if cur_idx >= total_cells:
                for row in [arr[idx: idx + num_cols] for idx in range(0, num_rows * num_cols, num_cols)]:
                    print(row)
                raise ValueError(f"Move beyond grid: cur_idx={cur_idx}, total={total_cells}")
            
            arr[cur_idx] = num_str
            cur_idx += 1
            i = j
        elif ch == '_':
            i += 1
        else:
            i += 1
    
    headers = f"{num_rows} {num_cols}"
    matrix = [arr[idx: idx + num_cols] for idx in range(0, total_cells, num_cols)]
    contents = "\n".join([" ".join(row) for row in matrix])
    return f"{headers}\n{contents}"
    

def dominos_parser(num_rows: int, num_cols: int, strs: str) -> str:
    # small bug!
    total_cells = num_rows * num_cols
    arr = ["-" for _ in range(total_cells)]
    i = 0
    cur_idx = 0
    
    while i < len(strs):
        if strs[i] == '[':
            j = i + 1
            while j < len(strs) and strs[j] != ']':
                j += 1
            if j >= len(strs):
                raise ValueError("Unmatched '['")
            num_str = strs[i+1:j]
            if not num_str.isdigit():
                raise ValueError(f"Invalid number in brackets: {num_str}")
            if cur_idx >= total_cells:
                raise ValueError(f"Too many numbers, cur_idx={cur_idx}, total_cells={total_cells}")
            arr[cur_idx] = num_str
            cur_idx += 1
            i = j + 1
        elif strs[i].isdigit():
            if cur_idx >= total_cells:
                raise ValueError(f"Too many numbers, cur_idx={cur_idx}, total_cells={total_cells}")
            arr[cur_idx] = strs[i]
            cur_idx += 1
            i += 1
        else:
            i += 1

    if cur_idx != total_cells:
        raise ValueError(f"Number of numbers ({cur_idx}) does not match total cells ({total_cells})")
    
    matrix = [arr[idx:idx+num_cols] for idx in range(0, total_cells, num_cols)]
    headers = f"{num_rows} {num_cols}"
    contents = "\n".join([" ".join(row) for row in matrix])
    return f"{headers}\n{contents}"

def masyu_parser(num_rows: int, num_cols: int, strs: str) -> str:
    arr = ["-" for _ in range(num_rows * num_cols)]
    i = 0
    cur_idx = 0
    while i < len(strs):
        if strs[i] in "abcdefghijklmnopqrstuvwxyz":
            for k in range(ord(strs[i]) - ord('a') + 1):
                cur_idx += 1
            i += 1
            continue
        else:
            if strs[i] in "WB":
                cur_color = strs[i].lower()
                arr[cur_idx] = f"{cur_color}"
                cur_idx += 1
                i += 1
    # print(arr)
    ret_mat = [arr[idx: idx + num_cols] for idx in range(0, num_rows * num_cols, num_cols)]
    # print(ret_mat)
    headers = f"{num_rows} {num_cols}"
    contents = "\n".join([" ".join(row) for row in ret_mat])
    return f"{headers}\n{contents}"


def starbattle_parser(num_rows: int, num_cols: int, strs: str) -> str:
    arr = strs.split(",")
    total_cells = num_rows * num_cols
    matrix = [arr[idx:idx+num_cols] for idx in range(0, total_cells, num_cols)]
    headers = f"{num_rows} {num_cols}"
    contents = "\n".join([" ".join(row) for row in matrix])
    return f"{headers}\n{contents}"

def battleship_parser(cols_top: List[int], rows_left: List[int], strs: str) -> str:
    # fill it on you own
    # cols_top = [2,9,5,4,6,8,6,5,11,2,5,3,2,13,2,5,11,5,10,7,5,4,9,6,2,3,10,1,2,2]
    # rows_left = [8,4,6,2,1,7,7,9,5,4,5,6,3,17,3,5,4,10,4,15,3,2,2,15,3,8,1,2,2,2]
    # o6f4g6a4b3zr4n5zt2s6a2b4m6b4zn6c4r2m5h3h5w1c5d2l3d2z6d0zc0a6c2a4b6f4zg3h1c1i3d5s1k5m4a5zh2a5m2q0b6zf5p2b2zzj6a2b4b2a4j1b4zk4j5zq4ze6n1a1x
    num_rows = len(rows_left)
    num_cols = len(cols_top)
    arr = ["-" for _ in range(num_rows * num_cols)]
    i = 0
    cur_idx = 0
    while i < len(strs):
        if strs[i] in "abcdefghijklmnopqrstuvwxyz":
            for k in range(ord(strs[i]) - ord('a') + 1):
                cur_idx += 1
            i += 1
            continue
        else:
            
            if strs[i] in "0123456":
                if strs[i] == "0":   arr[cur_idx] = "x"
                elif strs[i] == "1": arr[cur_idx] = "o"
                elif strs[i] == "2": arr[cur_idx] = "m"
                elif strs[i] == "3": arr[cur_idx] = "n"
                elif strs[i] == "4": arr[cur_idx] = "e"
                elif strs[i] == "5": arr[cur_idx] = "s"
                elif strs[i] == "6": arr[cur_idx] = "w"
                cur_idx += 1
                i += 1
    # print(arr)
    ret_mat = [arr[idx: idx + num_cols] for idx in range(0, num_rows * num_cols, num_cols)]
    headers = f"{num_rows} {num_cols} 9 8 7 6 5 4 3 2 1"
    rows_cols = f"{' '.join(map(lambda x: str(x), cols_top))}\n{' '.join(map(lambda x: str(x), rows_left))}"
    contents = "\n".join([" ".join(row) for row in ret_mat])
    return f"{headers}\n{rows_cols}\n{contents}"

def puzzle_to_dict(
    puzzle_type: str,  # 谜题类型，如 "dominos", "shikaku" 等
    num_rows: int,
    num_cols: int,
    compressed_str: str,
    difficulty: int = 0,
    source: str = "",
    parser_func: Optional[Callable] = None
) -> Dict[str, str]:
    """
    """
    
    parsers = {
        "shigoki": shigoki_parser,
        "shikaku": shikaku_parser,
        "dominos": dominos_parser,
        "masyu": masyu_parser,
        "starbattle": starbattle_parser,
        "battleship": battleship_parser
    }
    
    if parser_func is None:
        if puzzle_type not in parsers:
            raise ValueError(f"Unknown puzzle type: {puzzle_type}")
        parser_func = parsers[puzzle_type]
    
    problem_str = parser_func(num_rows, num_cols, compressed_str)
    hash_str = hashlib.md5(problem_str.encode()).hexdigest()[:8]
    puzzle_id = f"{puzzle_type}{hash_str}_{num_rows}x{num_cols}"
    
    return {
        "id": puzzle_id,
        "source": source,
        "problem": problem_str
    }
    
if __name__ == "__main__":
    # ====> shingoki 
    # 41 by 41
    # target_str = "cW3cW6fW2fB5aB2oW6aW2cB2aB2bB3aB4B2bB2eB2bB2B4B2cB4fB4lB2bB3cW4aB2dW2cB4eB5W3kB2bB3bW3B3dW3aB3B3cW2bW3W4cB3B3aB4cB3cW3bB6fW2fB4fB4cW3dW2cB4bB4aB2aB2bB3B2dB5eB2aW4eB2cB4B3cW4bB5B7gB2dB6aB4bB2eB3fB6W2B3bB7kB2gW2aB3dW5hW4cW2W5aB2bW2bW3dB2aB4aW2W4cB2jB4aB2aW4dB3bW3dB2W3B5cW3gW2gW4W5gB3bW2bB3bW2dB6bW2aB5aB2dB5W6aB4eB4iW2aB2B3cB3jB2aB4aB4cB4W3cB3fB8fW3aW3aB2aW5cB5aB2bW3bW3kB11hB9fW3aB3eW2eB8cW2eB3eW2dB4dW2W3hW2dW2dW3iW3aW2aB4eB2eB3bW3W3bW3iW3fW4nB2bW2B5cB3bW2bB2fB3W3bW5mB2cB5cB4W4bW2aW2bB2W3bB2B2W2bW3fB5aB3bW2cW3dW2W3bB3dW2bB4aB2aB2aB2gB3jW2bW2jW3dB2eB8W2aB4eB2B5bB3kW2hB2B5B4aB2bW2bB4hW3bB5W3cB4eB4W5B5dB2hW2B4bB4fB6bW4fB2bB3cW3aB2bB2bB4bB5aB2eW15aB2aB3aB3gB3bW3dW2dB4qB2dB2aW3fW3B5bB8fB7jW7cW3bB2gB4aB2dB4kW4bW2B3W3gW4jB3B3B4bW2bB4cW3gB3cB3eW2gB4bW3bB3bB4bB5eB9dW2fW11gW2B2nW2cW8dW3fW13fW7dW3cW2aW2B2bW4hW4aW4aW2gW11B2B4W9B2hB2hB2B2bW6gB2nW2cB2bB2aW2aB2cW2fB4uB3bB3gB2gW2aW3aB4lB9cW4dW2cB2bB3cB9aB7bW2cW4lB5W3W3hB2bB3B2W2B2bB5oW2aB7aW4eB3aB6aB6W2jW4aB3B2B2B4cB7mB2W2cB2bW2aW3lB4cB5gB5B4kW2eB3gB2dB4dB2hW3cW5kB4aB5B6gW2eB2W3bB2aW2bW3B3cW2bW2fB7B2bW3bB3dW4aB4B4fB3eW3bB3eW7p"
    # 26 by 26
    # target_str = "wW7gW6aW3aW2iB2B2B2eW4iW3aW2bW2B3gW7rB6cB3cB4dB2dB4aB4aB5B2B3iW3aB3B5eW3lB4W2fW4aB6cB2B2bB3cW4bW4bW6cW5eW2dB4lB4bB4gB2hW5dB3dW3aW4B4W2bB2dB3bW3eW2aW3hW3cB6cW4cB3eB4cW2B3fW4bB2dB3fW2cB10bB5cB3W3gW4dB2cB8bB5aW2eW2aW2bW2aB2rW2cB4cW3cB4aB2cB3cB8gW4gW3hB3bW4bB2bB2oB2kB3B2bB3bB3cW7dW6W6bW3B2aB4bB2aW3pB4eB2bB4iB3eB3cW2cW4eB6W2aB2dB2eB3aB4bB3aB2eB4bW2eW2mB5eB3aB3B4dB2aB2bW3fB2aW3bW3hW5bB3dB3W3W4B11eB4eW8m"
    # 36 by 36
    # target_str = "eW9gB4bW9hB5aW4eW4bB2hW2bB2W2cW7hB3bB2aB3cB4aB2lB4bB2aW5fB3rB4cB6dW3aW2B3dB3W2bB4bW2bB2aB2cB2hB5cW3bW2B3cB2B2hB4B4aB6W4B3iB5eB3bB2B2dW3W3gB4cB6B4gB3eB4W2cB5bB4bB3jB3aB6W5cW3eW2bW3eW4aB7bB2dW2B3hB2gB2eB2cB2fB5fB2cW2cW3W4bB3bB4eB2bB4gB5dB5B3cW3gW5aW5bB2gB3W3cW3dB3W2eB3fW2cB3dB2hB3aW4bB5hW5W4bB3W3W3B5bB2B3B4bB4B2B5bW2hW3cB3aB2bW4fB4lB4bB4W2B3B2lB4eB2fW3fB3bB2dB2cB6bB2B4aW3B3hW4bW2B5aB2bW2eB7cB6bW3eW3eB3W3cW3eB3B3bW4W2aB2dW3sB5eB2B3eB4dB2gB4W2cB7mB7B4aB3qW6eW4aB3aB5fW2cB6bW4dB3aB2dW5dB5eB2dW3aW2iW3cB2cW4dB2aB2aB4B2bB3dB5kB2B2aW3gB4eW2iW7hB3fW3aW3W2bB3eB2B2gW3cW5B3dB2gB3aB2gB4jB5fB3cB2aW2dB3B4iB7bB3W2B2B5cW2W4eW2B3aW3eB3cB3fW7aB8dB3nB5dW2B3aB5dB5B2eB3dB6bB4W2aB2bB4aB2B4W2iW5bB2aW3aW5aB3uW2fB3B2jW7aB2eB6W3dW5bB4cW7jB3iW2hW2lW5dB3W3W5aW2aW3cB2cB5aB6eW3W6eB2W2bB5gB2aB4dB2bB3cB3aW3dB2B3fW3B5fB7dB3cB2B2B2dW3pW3b"
    
    # ====> shsikaku
    # 50 x 40
    # target_str = "a12j8b3d5g13h4k3zc30_3f15q7a9b4a2_2e3f2p18b2zb4_2b3a7h2n144zzzj24b8_6_2s5zzzt2m26zj144i13r2_9zl6zi3zzo84l5a4zj2a4f13zj17zj5b7e4d2_3r4_40zg8b2w5zo69h2q87u2zh2ze2b5d10_42a10w69c3c8zh3b3zo18b84d3_6_63t4_2n3x2a9zd5k2a2_2zc2a2b3zj3_10b4a2a8_12za17_2g5_3x16i2d8y36h2j2za14k2y9i12v2zm2p2c4u6b7u288s10g2zd2g10zd5l2a4_5s16p4u4b14g60d18zzi2f20c5d2_2b6p17c9b3o3b"
    
    # ====> dominos
    # 41 by 42
    # target_str = "3[30][25]7[21][26][13][17][25][12][13]6[19]6[16][38][19][34][35][32][29][36][18][36][30][17]0[28][19]4[25][26][17]4[33][30][36][26]9[37][10][32][24][30][19][35][30]44[36][32][31][24][15]38[18]0[34][29][22][17][29][14]55[16][15][22][23][38][19][11]1[37][22][17][31][39][23][15][13][30][11][33][13]8[16][16]39[20]0[31][39]7[32]3[13][23]528[36][14][27][17][28][13]5[27][35][36][19]6[23]3[21][13][11][24][37][15][33]367[22][28][34]11[22][11][26][14][23][33][14][15]6[25][11]45[40][32][34]7[37][30][30][37][25][29][14][21][40][28][14]8[24][30][21]1[30][19][31][31][30][14][23][38][31][30][33][39][15]4[38][34][25][31][11][26][39][40][33][12]5[26]9[15][28][21][10]3[36][14][10][10][33][19][23][17][20][30]7[32][10][13][40][20][21][24][26][38]0[11][29][10][33][10][26][39][14]0[22][10][18][11][35][15][21][22][27][21][37]4[36]4[17]2[36][40]7[19][24][10][14][18][14][10][22][35][19]9[40][31][40]40[10][24]0[32]2[16][12][36][31][19][17]4[22][28][22]6[18][10]46[29]539[14][30][17][35]5[11][14][25][16][22][20][38][21][11][22][34][33]7[17][23]2[15]6[27]1[27][17][37][13][16][20][27][36]97[10][40]24[17][31]9[25][17][12][21][26][28][38][17]60[33][13][28][40][14][19][33][36][16][33][27][12][12]0[23][11][11]9[25][24][37][20][30][15][40]25[35]7[21][16][37][37][38][24][10][26][39][21]2[35][21][36][16][28][25][28]144[40][25][10][30][21][25][37][25][14]0[31][28]3[18][32]16[36][11][23][17][19][33][40][10]99[30][20][31][18][20][16]2[12][19][34][35][21]9[15][33][18][34][23][11][31]9[28][33]6[22][38][16]9[36][36]2[40][18][16][26]01[12][14][40][14][36][37]7[39]73[33][37][17]3[33][12][11][25][30][33][35]0[16][12][29]9[20]6[10][25][12]22[26]9[18][12][13][34][29]8[11][27]4[14][37][23][20]1[38][32][31][38][15][35][15][39]0[30][23]40[12][23][17][17][30][27][29][34]5[21][14][34]5[23][18][17][30]7[39][38]88[32][34]37816[30][19]2[35][23][33][23]7[26][32][32][18][26][19][20][33][28]2[24][17][35][19][20][28]8388[15][32]9[18][39][17][24][28][15][29]1[15]1[20][31][36]85[10][29][24]5[10][39][27][18][20]6686[29][17]2[21][11][24][15]5[15][16][37][34][38][32]4[30][10][33][27][20]87[18][39][11]6[14]37[25][20]77[32]19[37][38]45[39][29][40][34][23][28]1[27][33][34][37]07[32][13]2[35][15]40[23]52[34]1[27]3[15][37][16][27][31][13][28][40]6[36][11]7[38]70375[31][21][33]522[20][12][18][24]9[13][40][31][26][10][25][36][30]2[26][34][26][34]0[26]4[35]4[13][39][16][24][36][15]1[23][15][19]3[29][27][39][32][23]5[39][25]07[29][29]5[24][32][30][22][35][32][40][38][37]6[12]753[30][20][34][13][20][26][37][22][34][11][39][35][39][18]8[26][17][26][30][31][25][35][16][27][34][15][16]7[15]70[24][26][34][19][26]5[35][31]7[18]2[36]6[25]0[38][18][33]1[38][10][10]9[24]28[34][32][26][33][35][38]273[20][23][21][36][40][22][29][37][21]9[28]52[12][34][36][34][10][25][20][16][40][27][34][28][36][21][28][15]3[22]6[38][15][32][12][39][13][25]5[28][22][20]64[39][40][31][36][32][20][30][26]0[15][38][31]5[38][12]4[28][18]86[29][35][27][21]408[14]52[24]5[26][16][26][26][18][16][15][28][31][31]9[29][12]3[31][11][27]77[22]56[12][38][29][35]2[28][18]7[12][37][16]3[31][15][36][18]1[16]1[39][13]0[40][35][11][12][22][34]2[29][16][21][11][13][37][10][38][38][13][17][39][37][22]43[28]4[34][19][17]8[33][33][23][38][20]7[23][40][24]19[40][32]53[19]98[39][24][11][32][23][17]5[32][19][31]9[14][33]3[39][22]60[26][37][35][22][19][32]6[26][32][18][35][17][22][13][24]96[19][37][37][15][28][10][22][36]58[12][32]2[13]1[10][31][12][35][26]4[13][38][10][13]5[12][37]8[24][13][15][13][39][19]0[18][18][38]5[14][20][19][11][19][23][13]8[32][35][29]2[37][31][24][37][29]0[27][34]1[13][35][29][40][21][14][20]9[40][21][10][18][21][19]51[39][14]3[38][29][36][40][10]7[30][15][33][25]33[13][25]68[32][20]9[34]8[18][17][18][37]12[28]48[30]5[27][25][25]36[25]3[24][12][36][19][16]8[22][40][25]100[23][25]2[21][23][28][38][24]3[18][30][35][27][33][22][14][14][15][27][30][24][34]6[11][14]4[22][14]1[21][27][28][29][29][19][11]15[28][38][12][22][23][15][12][12][40][19][20][13][36][35][23][35]0[16][31][27][19]93[36][23][17]4[20][16]8[29]3[39][17][13][39][23]7[31][22][37][22][29][32][23]9[10][18][15][32][31][31][37][33][14]0[30][30][36]2[39][17][31][21][20]1[15][37][26][29][16][36]3[26][33]0[21]8[23][25][12]876[18][33][18][14][33][14][26]4[13][30]06[40][17]2[14][12][21][36][30][28][22][36][14][10][38][17][30][19][35][29][21][12][38]21174[19][34]0[28][23][40][12][34][24][28][32][10][16][20][27][19][24][39][35][24][34][37][36][16][29][28][27]9[21][36]80[11][38]88[33]5[10][16][11][24][17][17][39][32][30][25][19][10][20][33]86[27][14]1[17]9[32][25][22][11][20][31][40][38][23][32][34][15][40][28][24]3[24]5[29]1[11]2[36]1[19][13]3[12][39][18]6[18]8[23][11][33][40]2[20][14]67[18]9[17]3[20]7[21]980[13][22][27][39][11]2[34][28][14][27][22][30][26]76[38]2[16][16]4[24][29][12][23][18][35]7[17][16][29][16][10][32][13]1[28][38][29]0[19][16][35][12][15][25][20][29]8[34][13]6[37][20][35][10]1[13][12][23][20][38][26][25][21][31][38][32][19]1[39][14][22]3[10][27]3[31][10][39][30][21][27][28][22][13][27][24][39][24][34][20][36][40][17]029[15][31][27]4[37][21]4[25][21]5[30][27][16][16][22][14][17][18][24]559[13][27][13][21][27][14][13][11][29][11][15][35][40]8[40]9[26][32]3[10][36][16][14][31][10]93[40][27][38][19][33][25][31][26][34][20][33][21][29]1[38]10[24]8[39][23]4[11][34][26][24][12][40][27]0[24]50[12][28]2[19]1[21][35]94[25]8[34][27][23][17][39][15]7[11][15]8[30][33][31]4[18][32]9[25][32][10][29]7[11][25]4[29][25][40][40][11][37][23]4[33][12][27]61[39][26][16][18]4[29][34]6[39][18][35][27]1[11]6[24][28][20][22][25][21]2[22]2[37][39]9[31][28]3[16]0[26][12][28][35][22][26][13][40][25][20][37][12][19][22]649[33][14][37]2[38][37][11][39][35]98[35][32]16[11][18][24][36]"
    # 31 by 32
    # target_str = "[25][12]89[22]03[24]5[17]9[14][18][21]7[13][15][19][18][27][17][11][24][18]5[22]48[19][23][19][28][22]857[15]2[13][26]42[25]625[28]7[16][27][14]3[10][11][19][14]66[17][11][17][29]8[27]34[21][13][11][26]8[26][20][10]7[26][26][20]0[23][23][25][29][12][28]5[14][24]3154[14]46[11][14][29][18]8[27][16]0[13][26][17][23][17]7[15]8[12][29][14]4[19]80266[10][18][30][16][21][13][20][14][29][24]6[15]92[13][27][28][28]8[30][30][24][15][17][12][16][10][18][13]9[13][28][20][23][30][15][10][30][27][21]8[17]8[22]38[21][22][24][10][19][12]0[14][17][26][11][11][11]5[15]9[26][10][12]8[13][23]1[27][20][14]5[18]0[22][14]0[11][16][26]8[16][13][26][12]67[30][17]6[12][16]27[15]59[15][19]1[21]0[25][23][29][16][25][26]3[10]5[21][17][18]39[30][23]9[29][19][18][16]26[18][11]1[21][17]3[17][21][16][10]2920[16]14[11][16][30][18][10][29][23]72[28]2[21][20][29]225[19][12][27][12]6[23][20][10][16][17][19]3[15]83[19][27]18[10][18]2[22][22][25][14][28][14]13[15][28][13]0[22][30][10][24][20][30][29][19][16]5[29][21][26][19][19][14][28][24][25][16][24]99366[23][23][29][25][18][30]1[28][21]3[24][27][20][22][12][24]9[25]0[12]016[19]6[16][11][29][11]2468[21]1[20]81[18]1[28][11][22]952[15][21][22][18][18]5[14]3041[17][30][23][14]1[15][21][24]51[14][24][26][10][28]6[13][17][17][12][15]2[13][13]1[16][19]8[29][11][26][30][10]95[25][24][25][30]0[23][21][19][27][27][23][28][29]2[10][26][26]0[29]5[10][23]1[10]33[12]8[25]7[20][17]1[13]2[12][14][27]8[15][17][19][28][26][26]44[25][18]90[27]43[11][11][19][30][23][27][21]5[22][26][22][14][30][21]9[26]207[25][18]7[16][27][11][28][15][22][10][12]7[15][19]40[24][28]5[28][15][20][14][28][16]819[24]37[20]7[23][10][19][21][15]3[30][14]7[23][30][16][26][20][25]2[18][23]48[11][18]3[27]9[30][20]24764[25][22][28][28][26][12]8[12][24]97[11]7472[20][29][13][29][25][15][14][11]6[24]0[29][27][12]4[16][27][30]0[22][22]1[26][26][27][10][20]2[30]1[11][22][17][17][16]36[23]6[23]4[30]3[13][13][14][27]6[12]3[27][20]09[17][26][19][25]7[21][13][22]74[13][20]5[30][30][24]417[15][21][13][21][21][10]1[19]9[10][13]544[19][14]07[27][24][16][20][22][10][29]5[21][15]5[14][20][14][12][19][24][27]2[27]59[20]7[11]5[29][13][29][15][25][13][11][19]45[17][18][26]60[30][13][16]09[16]524[25][14][20][24][24]89[10]5[12][21]3[22]6[25][10][19]4[10]8[23][25]7[21][12]1[11][14][12][25][13][22][23][18]6[25][25]60[14][26][17][30]9[11]9[15]53[18][21]02[10][29][20][12][24][15][14][22][25]12[27][22][17][17]3[29][17]6[24][12]16914[16][28]2[19][19]7[20][18][20][29][21][12][15]0[17][28][16][18][13][18][13]718[11][17][27][28][25][19][26][25][16][30][22][17][22][29][30][22][14][11][29][23][18][21][29]4[23][29][28][22][10][29][18]17[15]7[24]3[26][24]5[23][25]3[17][12][15]99[23][24][22][21][28]4[23][13][23]3[18]5[12]4[30]9[29][15]7[29][20]668[16][16]7[24]9[22][28][28][10][28]48[20][23][12][26][22]2[30][15][18][11][24][15][16][20][20][27][27]390[25]83[20]8[27]6[15][16][12]4[27]1[14]10[10]0[13][26]7[13][26][17]1[21][11][21]2[23]00[11]2[30][25]8[24][28][19][20]5[13][25]3[10]6[30][19][28][27][24][18][12][18][28][11]"
    
    
    # ====> masyu
    # 35 x 35
    # target_str = "cBbBWbBBdWcBbWcBbWbWaWWfWeBbWWcWWbWcBfWbWcWbWWfWlWbBaWdWeBeBaWaBeBaWhBaBWaWWaWbBjWbBbBkBbWfBbBaWmWcWaWdWBaWdWWbWWbBcBaBbBeWgWaWhWaBdBbBaWaWaWaBbWgBbWbBdWeBdWbWWaWcBcBbWeWWjWcWbBeWdWWgWlBfBcWdWcBcWbBBcWaBaBiWaWaWbBaWbWbWaWaBjBaWWWaWaWWWhBaWeWWhWeWbWbWcBaWdWdWWcBcWaWgWaWcWaWaWWaWbWaWaBbWgWeBaWWaWgWaBaWfBbWdWcWeWlWdBWaWdBaWaWcWbBBgWWaWaWaWaWaWaWcBcWaWaWaBbBkWWiWaWdBgBaWaBaWcWcBcWeWaBdBeWdWaBWWcWcBbBWcWaBbWhBmWaBbWWbWcWWaBaBWaWBWaWBaBbBcWfWgWcBiBcWWaWaWdBWWBeWhBfWbWBWaWcWgBaWcBaWaBbWdWdWfWWbBaWcWBWiWaWgBbBWcWBfBaBWbBfBgWcWeBgWeBdBaBbWaBWcWdBeWaWbWeBhBcWaWbWaBbWdBbWaBhWcWbWfWmBdBaWdWcWbBeB"
    # 40 x 40
    # target_str = "cWcBfWhBcWbBcBaWdWaWBcWBbWaWaBbBbWfWeWbBaWnWbWdBcWWaBaWiWbWcBcWfWbWaWdWcBaWdWiBWaWWaWBeBbWaWBWaBbBaWdBcWbBhWBsWdBeWWaWWbWdWBcWaWaWbBfWWaWaWWfWWaWbWaWbWbWcWbWWfWgWhBeBbWjWbWWWaWcWcBBcWbBcBbWBWbWaBWaWWWdWcWbWiBgWBiWbWbBfBbBaWbBBaWaWfWbWeWgBaBcWaWjBaWbWcBBbWbBbWiWaWWBcBfBgWbBbWlWbWaBdBeBfWbWbWWBaBbWkBcWWgWeWeBWcBaBfBWaWeBaBWWbBfBWbWhBdWfBfWaBaBWWbBcBcBBaWdWbBbWaWWdWbWaWdWdWWeWWcWWjBaBfBWhWWeBdBbWcWfBfWaWaBbWBcBdWBaWfWdWiBbWfWaWbWWcBeWbBbWWbBbBbWaWcBbWWbWcWbBaWaWcBdBdWbWbBfWdWjBcBcBeWaBcWeWcWcWbWaWaBdWdWdWaWbWBWaBcWaBcWbWWbWaWdWbWWeBfBbBcBaWaWaWbWcBbBaBdBcWaWcWaBcWdBWdWaWaWBoWgBaWdWbWfWbBaBaBaBcWWWbWbWbWaWfWBdWbBbBbBdWaBaBaWhBcWbBaBbWcBdWaBhWbBcBaWaWbWcWbWaBaBbBaWbBbWeWbBcWbWaWaWcWcWcWaWdWdBdBcWeWWeWcWcBhBdWgBdWaWWgBbBbBcBaBaBeBbWcBaWaWBbWpWWeBaWcWdWfBbBfBaWaWaWcWeWdWbWcWcBdBeWe"
    
    # ====> starbattle
    # target_str = "1,1,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,3,1,2,2,2,2,2,2,2,4,4,4,2,5,5,5,3,3,3,3,3,3,1,1,2,2,2,2,2,2,4,6,4,4,4,5,5,5,5,5,3,3,3,1,1,2,2,2,6,6,6,4,6,4,7,5,5,5,3,3,3,3,3,8,1,1,1,2,6,6,6,6,6,6,4,7,7,7,7,3,3,8,8,3,8,1,1,6,6,6,6,6,6,6,6,4,7,7,7,7,3,3,8,8,3,8,1,6,6,6,9,6,6,6,6,6,7,7,7,7,7,7,8,8,8,8,8,1,6,6,6,9,6,9,9,9,6,7,7,7,7,10,8,8,8,8,8,8,1,1,9,9,9,9,9,7,7,7,7,7,10,10,10,8,8,8,8,8,11,1,12,12,12,12,12,12,7,7,7,13,7,10,14,10,8,8,11,11,11,11,12,12,12,12,12,12,13,13,13,7,13,7,10,14,10,14,11,11,14,14,11,12,12,12,12,12,15,15,15,13,13,13,13,10,14,14,14,14,14,14,14,11,12,12,12,12,15,15,15,15,15,15,15,13,10,14,10,10,14,14,14,14,11,12,12,12,15,15,15,15,15,15,15,15,13,10,10,10,14,14,14,14,14,14,12,12,12,16,15,15,15,15,15,15,15,15,15,10,17,17,14,14,14,18,14,12,16,16,16,16,16,15,15,15,15,15,17,17,17,17,14,14,14,14,18,14,12,19,19,16,15,15,15,20,15,15,15,17,21,17,21,14,14,14,14,18,14,19,19,19,16,16,16,15,20,15,17,17,17,21,21,21,21,21,18,18,18,14,19,19,19,19,19,19,19,20,20,21,21,21,21,21,21,21,21,21,21,18,18,19,19,19,19,19,19,19,19,20,20,20,20,21,21,21,21,21,21,21,21,18,19,19,19,19,19,19,19,20,20,21,21,21,21,21,21,21,21,21,21,18,18"
    # ret = puzzle_to_dict("starbattle", 21, 21, target_str)
    # # ret = masyu_parser(35, 35, target_str)
    target_str = "o6f4g6a4b3zr4n5zt2s6a2b4m6b4zn6c4r2m5h3h5w1c5d2l3d2z6d0zc0a6c2a4b6f4zg3h1c1i3d5s1k5m4a5zh2a5m2q0b6zf5p2b2zzj6a2b4b2a4j1b4zk4j5zq4ze6n1a1x"
    ret = puzzle_to_dict("battleship", 
        [2,9,5,4,6,8,6,5,11,2,5,3,2,13,2,5,11,5,10,7,5,4,9,6,2,3,10,1,2,2], 
        [8,4,6,2,1,7,7,9,5,4,5,6,3,17,3,5,4,10,4,15,3,2,2,15,3,8,1,2,2,2], target_str)
    print(ret)
    


    


