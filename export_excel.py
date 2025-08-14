import pandas as pd
from timetable import SchoolTimetableGenerator
from variables import YEARS_SECTIONS, SUBJECTS_PER_YEAR, TEACHER_ASSIGNMENTS, PREBOOKED

def export_to_excel():
    # Create generator object
    gen = SchoolTimetableGenerator(
        YEARS_SECTIONS,
        SUBJECTS_PER_YEAR,
        TEACHER_ASSIGNMENTS,
        # prebooked=PREBOOKED   # uncomment if feature used
    )
    gen.generate_timetable()

    # Prepare day names
    day_names = ["Mon","Tue","Wed","Thu","Fri"]

    # --- CLASS TIMETABLES ---
    class_writer = {}
    for section in sorted(gen.class_schedules.keys()):
        df_data = []
        for d in range(gen.days):
            row = []
            for p in range(gen.periods_per_day):
                slot = gen.class_schedules[section][d][p]
                row.append(f"{slot[0]} ({slot[1]})" if slot else "-")
            df_data.append(row)
        df = pd.DataFrame(df_data, columns=[f"Period {i+1}" for i in range(gen.periods_per_day)])
        df.insert(0, "Day", day_names[:gen.days])
        class_writer[section] = df

    # --- TEACHER TIMETABLES ---
    teacher_writer = {}
    for teacher in sorted(gen.teacher_assignments.keys()):
        df_data = []
        for d in range(gen.days):
            row = []
            for p in range(gen.periods_per_day):
                found = "-"
                for section, sched in gen.class_schedules.items():
                    slot = sched[d][p]
                    if slot and slot[1] == teacher:
                        found = f"{section}:{slot[0]}"
                        break
                row.append(found)
            df_data.append(row)
        df = pd.DataFrame(df_data, columns=[f"Period {i+1}" for i in range(gen.periods_per_day)])
        df.insert(0, "Day", day_names[:gen.days])
        teacher_writer[teacher] = df

    # Write to Excel
    with pd.ExcelWriter("timetable_export.xlsx", engine="openpyxl") as writer:
        for sec, df in class_writer.items():
            df.to_excel(writer, sheet_name=f"Class_{sec}", index=False)
        for t, df in teacher_writer.items():
            safe_name = t[:25]  # Excel sheet name limit
            df.to_excel(writer, sheet_name=f"Teacher_{safe_name}", index=False)

    print("✅ Timetable exported to timetable_export.xlsx")

if __name__ == "__main__":
    export_to_excel()
