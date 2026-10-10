from pathlib import Path
import tempfile
import shutil
import zipapp

root = Path(__file__).resolve().parent
for path in (root / 'src').rglob('*.py'):
    compile(path.read_text(encoding='utf-8'), str(path), 'exec')
(root / 'dist').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as directory:
    stage = Path(directory)
    shutil.copytree(root / 'src' / 'schedule_app', stage / 'schedule_app',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    zipapp.create_archive(stage, root / 'dist' / 'schedule.pyz',
                          main='schedule_app.cli:main', compressed=True)
print('Build OK: dist/schedule.pyz')
