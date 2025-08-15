import pandas as pd
import random
from collections import defaultdict
from timetable_with_labs_and_theory import LabTimetable, TheoryTimetable, LAB_SUBJECTS, PREBOOKED, DAYS, PERIODS
from variables import YEARS_SECTIONS, SUBJECTS_PER_YEAR, TEACHER_ASSIGNMENTS

def export_to_excel(filename="timetable_export.xlsx"):
    random.seed(42)
    teacher_busy = defaultdict(lambda: [[False]*PERIODS for _ in range(DAYS)])

    # 1. Generate the timetables
    lab_gen = LabTimetable(LAB_SUBJECTS, teacher_busy, prebooked=PREBOOKED)
    lab_gen.generate_lab_pairs()
    theory_gen = TheoryTimetable(YEARS_SECTIONS, SUBJECTS_PER_YEAR, TEACHER_ASSIGNMENTS, teacher_busy, lab_gen.lab_schedules)
    theory_gen.generate_timetable()

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # --- Sheet 1: Teachers & Subjects ---
        teacher_subjects = []
        for teacher, assignments in TEACHER_ASSIGNMENTS.items():
            for sec, subj in assignments:
                teacher_subjects.append([teacher, sec, subj])
        df_teachers = pd.DataFrame(teacher_subjects, columns=["Teacher", "Section", "Subject"])
        df_teachers.to_excel(writer, sheet_name="Teachers_Subjects", index=False)

        # --- Sheet 2: Years & Subjects ---
        year_subjects = []
        for year, subs in SUBJECTS_PER_YEAR.items():
            for subj, freq in subs.items():
                year_subjects.append([year, subj, freq])
        df_years = pd.DataFrame(year_subjects, columns=["Year", "Subject", "Frequency"])
        df_years.to_excel(writer, sheet_name="Years_Subjects", index=False)

        # --- Sheet 3: Lab timetables for classes ---
        lab_rows = []
        for section in sorted(lab_gen.lab_schedules):
            lab_rows.append([f"{section} - B1"])
            lab_rows.append(["Day"] + [f"P{i+1}" for i in range(PERIODS)])
            for d in range(DAYS):
                row = [day_names[d]]
                for p in range(PERIODS):
                    slot = lab_gen.lab_schedules[section]['B1'][d][p]
                    row.append(slot[0] if slot else "-")  # subject only
                lab_rows.append(row)
            lab_rows.append([])  # Blank line
            lab_rows.append([f"{section} - B2"])
            lab_rows.append(["Day"] + [f"P{i+1}" for i in range(PERIODS)])
            for d in range(DAYS):
                row = [day_names[d]]
                for p in range(PERIODS):
                    slot = lab_gen.lab_schedules[section]['B2'][d][p]
                    row.append(slot[0] if slot else "-")
                lab_rows.append(row)
            lab_rows.extend([[], [], [], []])  # 3-4 blank rows between classes

        pd.DataFrame(lab_rows).to_excel(writer, sheet_name="Lab_Timetables", index=False, header=False)

        # --- Sheet 4: Theory timetables for classes ---
        theory_rows = []
        for section in sorted(theory_gen.class_schedules):
            theory_rows.append([f"{section}"])
            theory_rows.append(["Day"] + [f"P{i+1}" for i in range(PERIODS)])
            for d in range(DAYS):
                row = [day_names[d]]
                for p in range(PERIODS):
                    slot = theory_gen.class_schedules[section][d][p]
                    row.append(slot[0] if slot else "-")  # subject only
                theory_rows.append(row)
            theory_rows.extend([[], [], [], []])  # 3-4 blank rows between classes

        pd.DataFrame(theory_rows).to_excel(writer, sheet_name="Theory_Timetables", index=False, header=False)

        # --- Sheet 5: Teacher timetables ---
        teacher_tt_rows = []
        for teacher in sorted(TEACHER_ASSIGNMENTS.keys()):
            teacher_tt_rows.append([teacher])
            teacher_tt_rows.append(["Day"] + [f"P{i+1}" for i in range(PERIODS)])
            for d in range(DAYS):
                row = [day_names[d]]
                for p in range(PERIODS):
                    found = "-"
                    # Check labs first
                    for section, batches in lab_gen.lab_schedules.items():
                        for batch, sched in batches.items():
                            slot = sched[d][p]
                            if slot and slot[1] == teacher:
                                found = f"{section}-{batch}:{slot}"
                                break
                        if found != "-":
                            break
                    # If no lab, check theory
                    if found == "-":
                        for section, sched in theory_gen.class_schedules.items():
                            slot = sched[d][p]
                            if slot and slot[1] == teacher:
                                found = f"{section}:{slot}"
                                break
                    row.append(found)
                teacher_tt_rows.append(row)
            teacher_tt_rows.extend([[], [], [], []])  # 3-4 blank rows between teachers

        pd.DataFrame(teacher_tt_rows).to_excel(writer, sheet_name="Teacher_Timetables", index=False, header=False)

    print(f"✅ Timetable exported to {filename}")


if __name__ == "__main__":
    export_to_excel()
