#!/usr/bin/env python3
import random
from collections import defaultdict
from typing import Optional, Tuple
from variables import YEARS_SECTIONS, SUBJECTS_PER_YEAR, TEACHER_ASSIGNMENTS

# ------------ CONFIG -------------
from variables import LAB_SUBJECTS, PREBOOKED, DAYS, PERIODS

MAX_THEORY_PASSES = 10
DEBUG_PLACEMENT = True


# ------------ LAB SCHEDULER -------------
class LabTimetable:
    def __init__(self, lab_subjects, teacher_busy, prebooked=None):
        self.lab_subjects = lab_subjects
        self.teacher_busy = teacher_busy
        self.days = DAYS
        self.periods_per_day = PERIODS
        self.prebooked = prebooked if prebooked else {}
        self.lab_schedules: dict[str, dict[str, list[list[Optional[Tuple[str, str]]]]]] = {
            sec: {'B1': [[None]*PERIODS for _ in range(DAYS)],
                  'B2': [[None]*PERIODS for _ in range(DAYS)]}
            for sec in lab_subjects
        }

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
            if len(labs) < 2:
                continue
            slots = [(d, s) for d in range(self.days) for s in [0, 2, 4]]
            random.shuffle(slots)
            for i in range(len(labs)):
                subj1, t1 = labs[i]
                subj2, t2 = labs[(i+1) % len(labs)]
                placed = False
                for day, start in slots:
                    if labs_per_day[section][day] >= 2:
                        continue
                    if self.can_schedule_pair(section, subj1, t1, subj2, t2, day, start):
                        self.place_lab_pair(section, subj1, t1, subj2, t2, day, start)
                        labs_per_day[section][day] += 1
                        placed = True
                        break
                if not placed:
                    print(f"WARNING: Could not place labs {subj1}/{subj2} for {section}")

    def print_lab_timetables(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        for section in sorted(self.lab_schedules):
            for batch in ('B1', 'B2'):
                print(f"\nSection {section}-{batch} Labs:")
                print("Day  " + "".join(f"P{i+1:^12}" for i in range(self.periods_per_day)))
                for d in range(self.days):
                    row = f"{days[d]:<4}"
                    for p in range(self.periods_per_day):
                        slot = self.lab_schedules[section][batch][d][p]
                        row += f"{(slot[0] if slot else '-'):^12}"
                    print(row)


# ------------ THEORY SCHEDULER -------------
class TheoryTimetable:
    def __init__(self, years_sections, subjects_per_year, teacher_assignments, teacher_busy, lab_schedules):
        self.years_sections = years_sections
        self.subjects_per_year = subjects_per_year
        self.teacher_assignments = teacher_assignments
        self.teacher_busy = teacher_busy
        self.lab_schedules = lab_schedules
        self.days = DAYS
        self.periods_per_day = PERIODS
        self.section_subject_teacher: dict[Tuple[str, str], str] = {}
        for t, pairs in teacher_assignments.items():
            for sec, subj in pairs:
                self.section_subject_teacher[(sec, subj)] = t
        self.class_schedules: dict[str, list[list[Optional[Tuple[str, str]]]]] = {
            f"{y}{s}": [[None]*PERIODS for _ in range(DAYS)]
            for y, secs in years_sections.items() for s in secs
        }

    def can_schedule(self, section, day, period, subject, relax_rules=False, debug=False):
        teacher = self.section_subject_teacher.get((section, subject))
        if not teacher:
            if debug: print(f"[NO TEACHER] {section} {subject}")
            return False
        if section in self.lab_schedules and (self.lab_schedules[section]['B1'][day][period] or
                                              self.lab_schedules[section]['B2'][day][period]):
            if debug: print(f"[LAB CONFLICT] {section} {subject} at {day},{period}")
            return False
        if self.class_schedules[section][day][period]:
            if debug: print(f"[CLASS OCCUPIED] {section} {subject} at {day},{period}")
            return False
        if self.teacher_busy[teacher][day][period]:
            if debug: print(f"[TEACHER BUSY] {teacher} at {day},{period}")
            return False
        if not relax_rules:
            if any(slot and slot[0] == subject for slot in self.class_schedules[section][day]):
                if debug: print(f"[ONCE/DAY FAIL] {section} {subject} on day {day}")
                return False
            if period > 0 and self.class_schedules[section][day][period-1] and \
               self.class_schedules[section][day][period-1][0] == subject:
                if debug: print(f"[CONSEC BEFORE] {section} {subject} at {period}")
                return False
            if period < self.periods_per_day-1 and self.class_schedules[section][day][period+1] and \
               self.class_schedules[section][day][period+1][0] == subject:
                if debug: print(f"[CONSEC AFTER] {section} {subject} at {period}")
                return False
        return True

    def place_class(self, section, day, period, subject):
        teacher = self.section_subject_teacher[(section, subject)]
        self.class_schedules[section][day][period] = (subject, teacher)
        self.teacher_busy[teacher][day][period] = True

    def generate_timetable(self, max_iterations=MAX_THEORY_PASSES):
        unplaced = {sec: [sub for sub, freq in self.subjects_per_year[sec[:-1]].items() for _ in range(freq)]
                    for sec in self.class_schedules}
        for iteration in range(1, max_iterations+1):
            relax = iteration > max_iterations // 2
            print(f"\n--- Pass {iteration} (relax={relax}) ---")
            placed_any = False
            sections = list(unplaced.keys())
            random.shuffle(sections)
            for sec in sections:
                random.shuffle(unplaced[sec])
                for subj in list(unplaced[sec]):
                    day_periods = [(d, p) for d in range(self.days) for p in range(self.periods_per_day)]
                    random.shuffle(day_periods)
                    for d, p in day_periods:
                        if self.can_schedule(sec, d, p, subj, relax_rules=relax):
                            self.place_class(sec, d, p, subj)
                            unplaced[sec].remove(subj)
                            placed_any = True
                            break
            if not placed_any:
                break
        self.post_repair(unplaced)
        for sec, subs in unplaced.items():
            for subj in subs:
                print(f"[UNPLACED] {subj} in {sec}")
                if DEBUG_PLACEMENT:
                    for d in range(self.days):
                        for p in range(self.periods_per_day):
                            self.can_schedule(sec, d, p, subj, relax_rules=True, debug=True)

    def post_repair(self, unplaced):
        """Try to fill by swapping or placing in any open slot."""
        for sec in list(unplaced.keys()):
            for subj in list(unplaced[sec]):  # copy so it's safe to modify original
                teacher = self.section_subject_teacher.get((sec, subj))
                if not teacher:
                    continue
                placed = False
                for d in range(self.days):
                    for p in range(self.periods_per_day):
                        if self.can_schedule(sec, d, p, subj, relax_rules=True):
                            self.place_class(sec, d, p, subj)
                            if subj in unplaced[sec]:  # ✅ avoid ValueError
                                unplaced[sec].remove(subj)
                            placed = True
                            break
                        else:
                            # Try swap only if this slot is empty in target section
                            for other_sec in self.class_schedules:
                                other_slot = self.class_schedules[other_sec][d][p]
                                if other_slot is not None:
                                    o_subj, _ = other_slot
                                    if (self.can_schedule(sec, d, p, subj, relax_rules=True) and
                                        self.can_schedule(other_sec, d, p, o_subj, relax_rules=True)):
                                        self.class_schedules[sec][d][p] = (subj, teacher)
                                        if subj in unplaced[sec]:  # ✅ avoid ValueError
                                            unplaced[sec].remove(subj)
                                        placed = True
                                        break
                            if placed:
                                break
                    if placed:
                        break



# ------------ MAIN -------------
def main():
    random.seed(42)
    teacher_busy = defaultdict(lambda: [[False]*PERIODS for _ in range(DAYS)])

    # 1. Schedule labs
    lab_gen = LabTimetable(LAB_SUBJECTS, teacher_busy, prebooked=PREBOOKED)
    lab_gen.generate_lab_pairs()

    # 2. Schedule theory
    theory_gen = TheoryTimetable(YEARS_SECTIONS, SUBJECTS_PER_YEAR,
                                 TEACHER_ASSIGNMENTS, teacher_busy, lab_gen.lab_schedules)
    theory_gen.generate_timetable()

    # 3. Print labs
    lab_gen.print_lab_timetables()

    # 4. Final merged timetable
    print("\n=== FINAL COMBINED TIMETABLE ===")
    days = ["Mon","Tue","Wed","Thu","Fri"]
    for sec in sorted(theory_gen.class_schedules):
        print(f"\nSection {sec}:")
        print("Day  " + "".join(f"P{i+1:^15}" for i in range(PERIODS)))
        for d in range(DAYS):
            row = f"{days[d]:<4}"
            for p in range(PERIODS):
                if sec in lab_gen.lab_schedules and (
                    lab_gen.lab_schedules[sec]['B1'][d][p] or lab_gen.lab_schedules[sec]['B2'][d][p]
                ):
                    row += f"{'LAB':^15}"
                else:
                    slot = theory_gen.class_schedules[sec][d][p]
                    row += f"{slot[0][:12] if slot else '-':^15}"
            print(row)

if __name__ == "__main__":
    main()
