import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))
from config import web_QC_path

if __name__ == '__main__':
    with open('{}response.txt'.format(web_QC_path), 'w') as file:
        file.truncate()
