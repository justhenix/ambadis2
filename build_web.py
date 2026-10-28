from pathlib import Path
from shutil import copyfile

root = Path(__file__).resolve().parent
public = root / 'public'
public.mkdir(exist_ok=True)
copyfile(root / 'index.html', public / 'index.html')
