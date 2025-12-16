import os
import sys
import tokenize
import io

TARGET_DIRS = ["src", "scripts"]
TARGET_FILES = ["config.py", "logging_config.py", "verify_chroma.py"]

def get_comment_ranges(source):
    """
    Returns a list of (start_index, end_index) for all comments.
    """
    comment_ranges = []
    try:
        tokens = tokenize.tokenize(io.BytesIO(source.encode('utf-8')).readline)
        
        
        lines = source.splitlines(keepends=True)
        
        line_offsets = [0]
        current_offset = 0
        for line in lines:
            current_offset += len(line)
            line_offsets.append(current_offset)
            
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                s_row, s_col = tok.start
                e_row, e_col = tok.end
                
                
                start_idx = line_offsets[s_row - 1] + s_col
                end_idx = line_offsets[e_row - 1] + e_col
                
                comment_ranges.append((start_idx, end_idx))
    except tokenize.TokenError:
        print("Token error, skipping")
    except Exception as e:
        print(f"Error parsing: {e}")
        
    return comment_ranges

def remove_comments_from_file(filepath):
    print(f"Processing {filepath}...")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
            
        ranges = get_comment_ranges(source)
        
        if not ranges:
            return

        
        ranges.sort(reverse=True)
        
        new_source = list(source)
        count = 0
        for start, end in ranges:
            
            
            
            
            del new_source[start:end]
            count += 1
            
        final_text = "".join(new_source)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_text)
            
        print(f"Removed {count} comments.")

    except Exception as e:
        print(f"Failed to process {filepath}: {e}")

def main():
    
    for f in TARGET_FILES:
        if os.path.exists(f):
            remove_comments_from_file(os.path.abspath(f))
            
    
    base_dir = os.getcwd()
    for d in TARGET_DIRS:
        target_path = os.path.join(base_dir, d)
        if not os.path.exists(target_path):
            continue
            
        for root, dirs, files in os.walk(target_path):
            for file in files:
                if file.endswith(".py"):
                    remove_comments_from_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
