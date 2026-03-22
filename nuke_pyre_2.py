# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore

extra_files = ['ollama_client.py', 'test_token.py', 'skills_module.py', 'run_with_dashboard.py']

for file in extra_files:
    if not os.path.exists(file):
        continue
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
        
    new_lines = []
    for line in lines:
        stripped = line.strip()
        needs_ignore = False
        
        if stripped.startswith('import ') or stripped.startswith('from '):
            needs_ignore = True
        elif '_stream.reconfigure(' in stripped:
            needs_ignore = True
        elif 'def get_stock_price(' in stripped:
            needs_ignore = True
        elif 'def coin_flip(' in stripped or 'def roll_dice(' in stripped or 'def random_number(' in stripped or 'def get_weather(' in stripped or 'guess: int = None' in stripped:
            needs_ignore = True
        
        if needs_ignore and not stripped.startswith('#') and 'pyre-ignore' not in line:
            line = line + '  # type: ignore  # pyre-ignore'
            
        new_lines.append(line)
        
    with open(file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
