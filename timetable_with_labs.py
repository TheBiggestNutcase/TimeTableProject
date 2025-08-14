#!/usr/bin/env python3
import random
from collections import defaultdict

# Example: section -> list of (subject, teacher)
LAB_SUBJECTS = {
    '3A': [('DSA-Lab', 'T_DSA_A'), ('OS-Lab', 'T_OS_A'), ('DBMS-Lab', 'T_DBMS_A')],
    '3B': [('DSA-Lab', 'T_DSA_B'), ('OS-Lab', 'T_OS_B'), ('DBMS-Lab', 'T_DBMS_B')],
}

# Optional: prebooked slots (teacher -> list of (day, period))
# day: 0=Mon..4=Fri, period: 0..5
PREBOOKED = {
    # 'T_DSA_A': [(0,0)],  # Mon Period 1 blocked
}

DAYS = 5
PERIODS = 6

class LabTimetableGenerator:
    def __init__(self, lab_subjects, prebooked=None, days=DAYS, periods=PERIODS):
        self.lab_subjects = lab_subjects
        self.days = days
        self.periods_per_day = periods
        self.prebooked = prebooked if prebooked else {}

        # Lab timetable per section/batch
        self.lab_schedules = {}
        # Teacher availability
        self.teacher_busy = defaultdict(lambda: [[False] * periods for _ in range(days)])

        for section in lab_subjects:
            self.lab_schedules[section] = {
                'B1': [[None] * periods for _ in range(days)],
                'B2': [[None] * periods for _ in range(days)]
            }

    def can_schedule_pair(self, section,
                          b1_sub, b1_teacher,
                          b2_sub, b2_teacher,
                          day, start_period):
        """Check both concurrent labs can be placed."""
        if start_period % 2 != 0 or start_period > self.periods_per_day - 2:
            return False

        for p in (start_period, start_period+1):
            # Batch slot free?
            if self.lab_schedules[section]['B1'][day][p] is not None:
                return False
            if self.lab_schedules[section]['B2'][day][p] is not None:
                return False
            # Teachers free?
            if self.teacher_busy[b1_teacher][day][p]:
                return False
            if self.teacher_busy[b2_teacher][day][p]:
                return False
            # Prebooked check
            if b1_teacher in self.prebooked and (day, p) in self.prebooked[b1_teacher]:
                return False
            if b2_teacher in self.prebooked and (day, p) in self.prebooked[b2_teacher]:
                return False
        return True

    def place_lab_pair(self, section,
                       b1_sub, b1_teacher,
                       b2_sub, b2_teacher,
                       day, start_period):
        """Assign both labs for that block."""
        for p in (start_period, start_period+1):
            self.lab_schedules[section]['B1'][day][p] = (b1_sub, b1_teacher)
            self.lab_schedules[section]['B2'][day][p] = (b2_sub, b2_teacher)
            self.teacher_busy[b1_teacher][day][p] = True
            self.teacher_busy[b2_teacher][day][p] = True

    def generate_lab_pairs(self):
        """Schedule labs with rotation, random days, and max 2/day."""
        labs_per_day = defaultdict(lambda: defaultdict(int))  # section -> day -> count

        for section, labs in self.lab_subjects.items():
            n = len(labs)
            if n < 2:
                print(f"WARNING: Section {section} has less than 2 labs, skipping")
                continue

            # Possible (day,start) options shuffled for variety
            possible_slots = [(d, s) for d in range(self.days) for s in [0, 2, 4]]
            random.shuffle(possible_slots)

            for i in range(n):
                b1_sub, b1_teacher = labs[i]
                b2_sub, b2_teacher = labs[(i+1) % n]
                placed = False
                attempts = 0

                while not placed and attempts < len(possible_slots):
                    day, start = possible_slots[attempts % len(possible_slots)]
                    # Limit per section per day
                    if labs_per_day[section][day] >= 2:
                        attempts += 1
                        continue
                    if self.can_schedule_pair(section, b1_sub, b1_teacher,
                                               b2_sub, b2_teacher, day, start):
                        self.place_lab_pair(section, b1_sub, b1_teacher,
                                            b2_sub, b2_teacher, day, start)
                        labs_per_day[section][day] += 1
                        placed = True
                    attempts += 1

                if not placed:
                    print(f"WARNING: Could not place {b1_sub}/{b2_sub} for {section}")

    def print_lab_timetables(self):
        """Display timetable for each batch."""
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        for section in sorted(self.lab_schedules.keys()):
            for batch in ('B1', 'B2'):
                print(f"\nSection {section}-{batch} Lab Timetable")
                print("Day  " + "".join(f"P{i+1:^15}" for i in range(self.periods_per_day)))
                for d in range(self.days):
                    row = f"{day_names[d]:<4}"
                    for p in range(self.periods_per_day):
                        slot = self.lab_schedules[section][batch][d][p]
                        row += f"{(slot[0] if slot else '-'):^15}"
                    print(row)

    def print_teacher_lab_timetables(self):
        """Display teachers' lab schedules."""
        teachers = set()
        for sec_data in self.lab_schedules.values():
            for batch_matrix in sec_data.values():
                for day in batch_matrix:
                    for slot in day:
                        if slot:
                            teachers.add(slot[1])

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        for teacher in sorted(teachers):
            print(f"\nTeacher {teacher} Lab Timetable")
            print("Day  " + "".join(f"P{i+1:^15}" for i in range(self.periods_per_day)))
            for d in range(self.days):
                row = f"{day_names[d]:<4}"
                for p in range(self.periods_per_day):
                    found = "-"
                    for section, sec_data in self.lab_schedules.items():
                        for batch, matrix in sec_data.items():
                            slot = matrix[d][p]
                            if slot and slot[1] == teacher:
                                found = f"{section}-{batch}:{slot[0][:8]}"
                    row += f"{found:^15}"
                print(row)


if __name__ == "__main__":
    random.seed(42)
    gen = LabTimetableGenerator(LAB_SUBJECTS, prebooked=PREBOOKED)
    gen.generate_lab_pairs()
    gen.print_lab_timetables()
    gen.print_teacher_lab_timetables()
