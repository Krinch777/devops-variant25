from dataclasses import dataclass
from datetime import time

DAYS = ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота')

@dataclass(frozen=True)
class Lesson:
    day: str
    start: str
    end: str
    subject: str
    group: str
    room: str

    def __post_init__(self):
        if self.day not in DAYS:
            raise ValueError('Неизвестный день недели')
        for value in (self.start, self.end):
            if len(value) != 5 or value[2] != ':':
                raise ValueError('Время должно иметь формат HH:MM')
            time.fromisoformat(value)
        if self.start >= self.end:
            raise ValueError('Окончание должно быть позже начала')
        if any(not value.strip() for value in (self.subject, self.group, self.room)):
            raise ValueError('Предмет, группа и аудитория обязательны')

class Schedule:
    def __init__(self):
        self._lessons = []

    def add(self, lesson):
        for old in self._lessons:
            overlap = old.start < lesson.end and lesson.start < old.end
            if old.day == lesson.day and overlap:
                if old.group == lesson.group or old.room == lesson.room:
                    raise ValueError('Конфликт расписания группы или аудитории')
        self._lessons.append(lesson)

    def find(self, day=None, group=None):
        return sorted((x for x in self._lessons
                       if (day is None or x.day == day)
                       and (group is None or x.group == group)),
                      key=lambda x: (DAYS.index(x.day), x.start, x.group))
