#!/usr/bin/env python3
import random
from collections import defaultdict
from variables import YEARS_SECTIONS, SUBJECTS_PER_YEAR, TEACHER_ASSIGNMENTS

# ========= CONFIG =========
# section -> list of (lab_subject, lab_teacher)
from variables import LAB_SUBJECTS, PREBOOKED, DAYS, PERIODS

MAX_THEORY_PASSES = 5
DEBUG_PLACEMENT = True  # Set to False to turn off debug prints

# ========= LAB SCHEDULER =========
class LabTimetable:
    def __init__(self, lab_subjects, teacher_busy, prebooked=None, days=DAYS, periods=PERIODS):
        self.lab_subjects = lab_subjects
        self.teacher_busy = teacher_busy
        self.days = days
        self.periods_per_day = periods
        self.prebooked = prebooked if prebooked else {}
        self.lab_schedules = {sec: {'B1': [[None]*periods for _ in range(days)],
                                    'B2': [[None]*periods for _ in range(days)]}
                              for sec in lab_subjects}

    def can_schedule_pair(self, section, b1_sub, b1_teacher, b2_sub, b2_teacher, day, start):
        if start % 2 != 0 or start > self.periods_per_day - 2:
            return False
        for p in (start, start+1):
            if self.lab_schedules[section]['B1'][day][p] or self.lab_schedules[section]['B2'][day][p]:
                return False
            if self.teacher_busy[b1_teacher][day][p] or self.teacher_busy[b2_teacher][day][p]:
                return False
            if b1_teacher in self.prebooked and (day, p) in self.prebooked[b1_teacher]:
                return False
            if b2_teacher in self.prebooked and (day, p) in self.prebooked[b2_teacher]:
                return False
        return True

    def place_lab_pair(self, section, b1_sub, b1_teacher, b2_sub, b2_teacher, day, start):
        for p in (start, start+1):
            self.lab_schedules[section]['B1'][day][p] = (b1_sub, b1_teacher)
            self.lab_schedules[section]['B2'][day][p] = (b2_sub, b2_teacher)
            self.teacher_busy[b1_teacher][day][p] = True
            self.teacher_busy[b2_teacher][day][p] = True

    def generate_lab_pairs(self):
        labs_per_day = defaultdict(lambda: defaultdict(int))
        for section, labs in self.lab_subjects.items():
            n = len(labs)
            if n < 2:
                continue
            possible_slots = [(d, s) for d in range(self.days) for s in [0, 2, 4]]
            random.shuffle(possible_slots)
            for i in range(n):
                b1_sub, b1_teacher = labs[i]
                b2_sub, b2_teacher = labs[(i+1) % n]
                placed = False
                attempts = 0
                while not placed and attempts < len(possible_slots):
                    day, start = possible_slots[attempts]
                    if labs_per_day[section][day] >= 2:
                        attempts += 1
                        continue
                    if self.can_schedule_pair(section, b1_sub, b1_teacher, b2_sub, b2_teacher, day, start):
                        self.place_lab_pair(section, b1_sub, b1_teacher, b2_sub, b2_teacher, day, start)
                        labs_per_day[section][day] += 1
                        placed = True
                    attempts += 1
                if not placed:
                    print(f"WARNING: Could not place labs {b1_sub}/{b2_sub} for {section}")

    def print_lab_timetables(self):
        day_names = ["Mon","Tue","Wed","Thu","Fri"]
        for section in sorted(self.lab_schedules.keys()):
            for batch in ('B1', 'B2'):
                print(f"\nSection {section}-{batch} Labs:")
                print("Day  " + "".join(f"P{i+1:^12}" for i in range(self.periods_per_day)))
                for d in range(self.days):
                    row = f"{day_names[d]:<4}"
                    for p in range(self.periods_per_day):
                        slot = self.lab_schedules[section][batch][d][p]
                        row += f"{(slot[0] if slot else '-'):^12}"
                    print(row)

# ========= THEORY SCHEDULER =========
class TheoryTimetable:
    def __init__(self, years_sections, subjects_per_year, teacher_assignments, teacher_busy, lab_schedules,
                 days=DAYS, periods_per_day=PERIODS):
        self.years_sections = years_sections
        self.subjects_per_year = subjects_per_year
        self.teacher_assignments = teacher_assignments
        self.teacher_busy = teacher_busy
        self.lab_schedules = lab_schedules
        self.days = days
        self.periods_per_day = periods_per_day
        self.section_subject_teacher = {}
        for t, pairs in teacher_assignments.items():
            for sec, subj in pairs:
                self.section_subject_teacher[(sec, subj)] = t
        self.class_schedules = {f"{y}{s}": [[None]*periods_per_day for _ in range(days)]
                                for y, sec_list in years_sections.items() for s in sec_list}

    def can_schedule(self, section, day, period, subject, debug=False):
        teacher = self.section_subject_teacher.get((section, subject))
        if not teacher:
            if debug: print(f"[NO TEACHER] {section} {subject}")
            return False
        if section in self.lab_schedules:
            if self.lab_schedules[section]['B1'][day][period] or self.lab_schedules[section]['B2'][day][period]:
                if debug: print(f"[LAB CONFLICT] {section} {subject} at {day},{period}")
                return False
        if self.class_schedules[section][day][period]:
            if debug: print(f"[CLASS OCCUPIED] {section} {subject} at {day},{period}")
            return False
        if self.teacher_busy[teacher][day][period]:
            if debug: print(f"[TEACHER BUSY] {teacher} at {day},{period} for {section} {subject}")
            return False
        if any(slot and slot[0] == subject for slot in self.class_schedules[section][day]):
            if debug: print(f"[ONCE/DAY FAIL] {section} {subject} on day {day}")
            return False
        if period > 0 and self.class_schedules[section][day][period-1] and \
           self.class_schedules[section][day][period-1][0] == subject:
            if debug: print(f"[CONSECUTIVE BEFORE] {section} {subject} at p{period}")
            return False
        if period < self.periods_per_day - 1 and self.class_schedules[section][day][period+1] and \
           self.class_schedules[section][day][period+1][0] == subject:
            if debug: print(f"[CONSECUTIVE AFTER] {section} {subject} at p{period}")
            return False
        return True

    def place_class(self, section, day, period, subject):
        teacher = self.section_subject_teacher[(section, subject)]
        self.class_schedules[section][day][period] = (subject, teacher)
        self.teacher_busy[teacher][day][period] = True

    def generate_timetable(self, max_iterations=MAX_THEORY_PASSES):
        # Build the unplaced list
        unplaced = {sec: [subj for subj, freq in self.subjects_per_year[sec[:-1]].items()
                          for _ in range(freq)]
                    for sec in self.class_schedules.keys()}
        for iteration in range(1, max_iterations+1):
            print(f"\n--- Theory Scheduling Pass {iteration} ---")
            placed_any = False
            sections_list = list(unplaced.keys())
            random.shuffle(sections_list)
            for sec in sections_list:
                if not unplaced[sec]:
                    continue
                subjects_list = unplaced[sec][:]
                random.shuffle(subjects_list)
                for subj in subjects_list:
                    placed = False
                    for day in range(self.days):
                        for period in range(self.periods_per_day):
                            if self.can_schedule(sec, day, period, subj):
                                self.place_class(sec, day, period, subj)
                                unplaced[sec].remove(subj)
                                placed = True
                                placed_any = True
                                break
                        if placed:
                            break
                    if not placed and iteration == max_iterations and DEBUG_PLACEMENT:
                        print(f"[FAIL] Could not place {subj} in {sec} — reasons:")
                        for d in range(self.days):
                            for p in range(self.periods_per_day):
                                self.can_schedule(sec, d, p, subj, debug=True)
                        print("------")
            total_left = sum(len(v) for v in unplaced.values())
            if total_left == 0 or not placed_any:
                # Before breaking, if there are still some unplaced
                if DEBUG_PLACEMENT:
                    for sec, subs in unplaced.items():
                        for subj in subs:
                            print(f"[FAIL] Could not place {subj} in {sec} — reasons:")
                            for d in range(self.days):
                                for p in range(self.periods_per_day):
                                    self.can_schedule(sec, d, p, subj, debug=True)
                            print("------")
                break
        # Final leftover messages
        for sec, subs in unplaced.items():
            for subj in subs:
                print(f"[UNPLACED] {subj} in {sec}")

# ========= MAIN =========
def main():
    random.seed(42)
    teacher_busy = defaultdict(lambda: [[False]*PERIODS for _ in range(DAYS)])

    # Step 1: Labs first
    lab_gen = LabTimetable(LAB_SUBJECTS, teacher_busy, prebooked=PREBOOKED)
    lab_gen.generate_lab_pairs()

    # Step 2: Theory in multiple passes
    theory_gen = TheoryTimetable(YEARS_SECTIONS, SUBJECTS_PER_YEAR,
                                 TEACHER_ASSIGNMENTS, teacher_busy, lab_gen.lab_schedules)
    theory_gen.generate_timetable()

    # Output labs
    lab_gen.print_lab_timetables()

    # Output combined timetable
    print("\n=== COMBINED TIMETABLE ===")
    day_names = ["Mon","Tue","Wed","Thu","Fri"]
    for sec in sorted(theory_gen.class_schedules.keys()):
        print(f"\nSection {sec}:")
        print("Day  " + "".join(f"P{i+1:^15}" for i in range(PERIODS)))
        for d in range(DAYS):
            row = f"{day_names[d]:<4}"
            for p in range(PERIODS):
                if sec in lab_gen.lab_schedules and (
                    lab_gen.lab_schedules[sec]['B1'][d][p] or
                    lab_gen.lab_schedules[sec]['B2'][d][p]
                ):
                    row += f"{'LAB':^15}"
                else:
                    slot = theory_gen.class_schedules[sec][d][p]
                    if slot:
                        row += f"{slot[0][:12]:^15}"
                    else:
                        row += f"{'-':^15}"
            print(row)

if __name__ == "__main__":
    main()
