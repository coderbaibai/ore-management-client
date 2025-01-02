import  yaml
from pathlib import Path
with open(Path.cwd()/'config'/'config.yaml', 'r', encoding='utf-8') as f:
    gConfig = yaml.load(f.read(), Loader=yaml.FullLoader)
