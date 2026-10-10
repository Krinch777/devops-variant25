import argparse
import json
from pathlib import Path
from .core import DAYS, Lesson, Schedule

def main():
    parser = argparse.ArgumentParser(description='Расписание занятий')
    parser.add_argument('--file', default='schedule.json', help='JSON-файл расписания')
    parser.add_argument('--day', choices=DAYS)
    parser.add_argument('--group')
    args = parser.parse_args()
    try:
        records = json.loads(Path(args.file).read_text(encoding='utf-8'))
        if not isinstance(records, list):
            raise ValueError('Ожидается массив занятий')
        schedule = Schedule()
        for record in records:
            schedule.add(Lesson(**record))
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f'Ошибка расписания: {error}\n')
    lessons = schedule.find(args.day, args.group)
    if not lessons:
        print('Занятия не найдены')
    for lesson in lessons:
        print(f'{lesson.day} | {lesson.start}-{lesson.end} | '
              f'{lesson.subject} | {lesson.group} | ауд. {lesson.room}')
    return 0
