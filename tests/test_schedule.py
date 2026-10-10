import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from schedule_app.core import Lesson, Schedule

EXPECTED = [
    ('Понедельник', '10:00', '10:50', 'Дизайн-мышление и лидерство', 'ИС', 'ГМК 122'),
    ('Понедельник', '11:05', '11:55', 'Дизайн-мышление и лидерство', 'ИС', 'ГМК 122'),
    ('Пятница', '15:25', '16:15', 'IT инфраструктура', 'ИС', 'ГУК 310'),
    ('Суббота', '15:25', '16:15', 'Прикладные аспекты DevOps', 'ИС', 'ГУК 315'),
    ('Суббота', '16:30', '17:20', 'Прикладные аспекты DevOps', 'ИС', 'ГУК 315'),
    ('Суббота', '17:30', '18:20', 'Прикладные аспекты DevOps', 'ИС', 'ГУК 315'),
    ('Суббота', '18:30', '19:20', 'Прикладные аспекты DevOps', 'ИС', 'ГУК 310а'),
]
FIELDS = ('day', 'start', 'end', 'subject', 'group', 'room')

class ScheduleTests(unittest.TestCase):
    def lesson(self, **changes):
        values = dict(zip(FIELDS, EXPECTED[3]))
        values.update(changes)
        return Lesson(**values)

    def load_schedule(self):
        schedule = Schedule()
        for record in json.loads((ROOT / 'schedule.json').read_text(encoding='utf-8')):
            schedule.add(Lesson(**record))
        return schedule

    def test_json_matches_all_seven_lessons(self):
        records = json.loads((ROOT / 'schedule.json').read_text(encoding='utf-8'))
        self.assertEqual(records, [dict(zip(FIELDS, row)) for row in EXPECTED])

    def test_filter_actual_schedule(self):
        schedule = self.load_schedule()
        self.assertEqual(len(schedule.find(group='ИС')), 7)
        self.assertEqual(len(schedule.find(day='Понедельник')), 2)
        self.assertEqual(len(schedule.find(day='Пятница')), 1)
        self.assertEqual(len(schedule.find(day='Суббота')), 4)
        self.assertEqual(schedule.find(day='Вторник'), [])

    def test_sort_actual_schedule(self):
        schedule = Schedule()
        for row in reversed(EXPECTED):
            schedule.add(Lesson(*row))
        self.assertEqual(schedule.find(), [Lesson(*row) for row in EXPECTED])

    def test_group_conflict(self):
        schedule = Schedule()
        schedule.add(self.lesson())
        with self.assertRaises(ValueError):
            schedule.add(self.lesson(start='16:00', end='16:50', room='310а'))

    def test_room_conflict(self):
        schedule = Schedule()
        schedule.add(self.lesson())
        with self.assertRaises(ValueError):
            schedule.add(self.lesson(group='ТЕСТОВАЯ ГРУППА'))

    def test_adjacent_allowed(self):
        schedule = Schedule()
        schedule.add(self.lesson())
        schedule.add(self.lesson(start='16:15', end='17:05'))
        self.assertEqual(len(schedule.find()), 2)

    def test_parallel_allowed(self):
        schedule = Schedule()
        schedule.add(self.lesson())
        schedule.add(self.lesson(group='ТЕСТОВАЯ ГРУППА', room='310а'))
        self.assertEqual(len(schedule.find()), 2)

    def test_invalid_fields(self):
        for changes in ({'day':'Ошибка'}, {'start':'25:00'},
                        {'end':'15:00'}, {'subject':' '}, {'start':'9:00'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.lesson(**changes)

    def run_app(self, *args):
        return subprocess.run([sys.executable, '-X', 'utf8',
                               str(ROOT / 'dist/schedule.pyz'), *args],
                              cwd=ROOT, capture_output=True, text=True, encoding='utf-8')

    def assert_output(self, expected, *args):
        result = self.run_app(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [f'{d} | {s}-{e} | {subject} | {group} | ауд. {room}'
                 for d, s, e, subject, group, room in expected]
        self.assertEqual(result.stdout.splitlines(), lines)

    def test_cli_full_schedule(self):
        self.assert_output(EXPECTED)

    def test_cli_monday(self):
        self.assert_output(EXPECTED[:2], '--day', 'Понедельник', '--group', 'ИС')

    def test_cli_friday(self):
        self.assert_output(EXPECTED[2:3], '--day', 'Пятница', '--group', 'ИС')

    def test_cli_saturday_and_room_310a(self):
        self.assert_output(EXPECTED[3:], '--day', 'Суббота', '--group', 'ИС')

    def test_empty_result(self):
        result = self.run_app('--group', 'НЕСУЩЕСТВУЮЩАЯ ГРУППА')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Занятия не найдены')

    def test_invalid_input_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{broken', encoding='utf-8')
            result = self.run_app('--file', str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn('Ошибка расписания', result.stderr)

if __name__ == '__main__':
    unittest.main()
