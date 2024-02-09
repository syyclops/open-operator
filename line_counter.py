from pathlib import Path

def count_lines_in_directory(directory_path):
    total_lines = 0
    for path in Path(directory_path).rglob('*.py'):
        with open(path, 'r') as f:
            total_lines += sum(1 for line in f)
    return total_lines

directory_path = "openoperator/"  
print(count_lines_in_directory(directory_path))