#!/usr/bin/env python3
import random
from collections import defaultdict

class SchoolTimetableGenerator:
    def __init__(self, years_sections, subjects_per_year, teacher_assignments,
                 prebooked=None, days=5, periods_per_day=6):
        self.years_sections = years_sections
        self.subjects_per_year = subjects_per_year
        self.teacher_assignments = teacher_assignments
        self.days = days
        self.periods_per_day = periods_per_day
        self.prebooked = prebooked if prebooked else {}

        # Build (section, subject) → teacher map
        self.section_subject_teacher = {}
        for teacher, pairs in teacher_assignments.items():
            for section, subject in pairs:
                if (section, subject) in self.section_subject_teacher:
                    raise ValueError(f"Duplicate teacher assignment for {section} - {subject}")
                self.section_subject_teacher[(section, subject)] = teacher

        # Class schedules: section → 2D array (day × period)
        self.class_schedules = {}
        self.teacher_busy = defaultdict(lambda: [[False]*periods_per_day for _ in range(days)])

        for year, secs in years_sections.items():
            for sec in secs:
                sec_key = f"{year}{sec}"
                self.class_schedules[sec_key] = [[None]*periods_per_day for _ in range(days)]

    def can_schedule(self, section, day, period, subject):
        teacher = self.section_subject_teacher.get((section, subject))
        if not teacher:
            return False
        # Already a class in that slot for the section
        if self.class_schedules[section][day][period] is not None:
            return False
        # Teacher already teaching at this time
        if self.teacher_busy[teacher][day][period]:
            return False
        # Pre-booked (teacher blocked) slot?
        if teacher in self.prebooked and (day, period) in self.prebooked[teacher]:
            return False
        # Subject should appear only once per day per section
        if any(slot and slot[0] == subject for slot in self.class_schedules[section][day]):
            return False
        # Avoid consecutive same subject in section
        if period > 0 and self.class_schedules[section][day][period-1] and \
           self.class_schedules[section][day][period-1][0] == subject:
            return False
        if period < self.periods_per_day-1 and self.class_schedules[section][day][period+1] and \
           self.class_schedules[section][day][period+1][0] == subject:
            return False
        return True

    def teacher_gap_score(self, teacher, day, period):
        """Scoring function that prefers free gaps around teacher classes."""
        score = 0
        if period == 0 or not self.teacher_busy[teacher][day][period-1]:
            score += 1
        if period == self.periods_per_day-1 or not self.teacher_busy[teacher][day][period+1]:
            score += 1
        # Optional: Bonus for first-hour preference
        # if period == 0:
        #     score += 0.5
        return score

    def place_class(self, section, day, period, subject):
        teacher = self.section_subject_teacher[(section, subject)]
        self.class_schedules[section][day][period] = (subject, teacher)
        self.teacher_busy[teacher][day][period] = True

    def generate_timetable(self):
        print("Generating timetable...")
        for section in sorted(self.class_schedules.keys()):
            year = section[:-1]
            subjects = self.subjects_per_year[year]
            needed = []
            for subj, freq in subjects.items():
                needed.extend([subj]*freq)
            random.shuffle(needed)

            for subj in needed:
                teacher = self.section_subject_teacher.get((section, subj))
                placed = False
                best_slot = None
                best_score = -1

                # Random start point to vary pattern
                start_day = random.randint(0, self.days - 1)
                start_period = random.randint(0, self.periods_per_day - 1)

                for di in range(self.days):
                    day = (start_day + di) % self.days
                    for pi in range(self.periods_per_day):
                        period = (start_period + pi) % self.periods_per_day
                        if self.can_schedule(section, day, period, subj):
                            score = self.teacher_gap_score(teacher, day, period)
                            if score > best_score:
                                best_score = score
                                best_slot = (day, period)
                                if score == 2:
                                    break
                    if best_score == 2:
                        break

                if best_slot:
                    self.place_class(section, best_slot[0], best_slot[1], subj)
                    placed = True

                if not placed:
                    print(f"WARNING: Could not place {subj} in {section}")

    def print_class_timetables(self):
        print("\nCLASS TIMETABLES:")
        day_names = ["Mon","Tue","Wed","Thu","Fri"]
        for section in sorted(self.class_schedules.keys()):
            print(f"\nSection {section}:")
            print("Day  " + "".join(f"P{i+1:^8}" for i in range(self.periods_per_day)))
            for d in range(self.days):
                row = f"{day_names[d]:<4}"
                for p in range(self.periods_per_day):
                    slot = self.class_schedules[section][d][p]
                    row += f"{(slot[0][:6] if slot else '-'):^8}"
                print(row)

    def print_teacher_timetables(self):
        print("\nTEACHER TIMETABLES:")
        day_names = ["Mon","Tue","Wed","Thu","Fri"]
        for teacher in sorted(self.teacher_assignments.keys()):
            print(f"\nTeacher {teacher}:")
            print("Day  " + "".join(f"P{i+1:^8}" for i in range(self.periods_per_day)))
            for d in range(self.days):
                row = f"{day_names[d]:<4}"
                for p in range(self.periods_per_day):
                    if teacher in self.prebooked and (d, p) in self.prebooked[teacher]:
                        found = "BLOCK"
                    else:
                        found = "-"
                        for section, sched in self.class_schedules.items():
                            slot = sched[d][p]
                            if slot and slot[1] == teacher:
                                found = f"{section}:{slot[0][:4]}"
                                break
                    row += f"{found:^8}"
                print(row)

# ===========================
# === VARIABLES ======
from variables import TEACHER_ASSIGNMENTS, YEARS_SECTIONS, SUBJECTS_PER_YEAR, PREBOOKED

# ===========================
def main():
    gen = SchoolTimetableGenerator(
        YEARS_SECTIONS, SUBJECTS_PER_YEAR, TEACHER_ASSIGNMENTS, prebooked=PREBOOKED
    )
    gen.generate_timetable()
    gen.print_class_timetables()
    gen.print_teacher_timetables()

if __name__ == "__main__":
    random.seed(42)
    main()
