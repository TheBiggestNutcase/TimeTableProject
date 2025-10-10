
# 📅 Automatic Timetable Generator (To Be Updated)

This project **automatically generates** class, lab, and teacher timetables based on predefined subjects, teachers, and rules — and exports them to **Excel** with clean formatting.

Designed for **schools, colleges, and departments**, it ensures there are **no teacher overlaps** and lab sessions are **always in proper paired periods**.

---

## ✨ Features

When you run this project, it:
- Places **theory classes** and **lab pairs** without scheduling conflicts.
- Makes sure:
  - Teachers are never double-booked.
  - Labs happen in correct period pairs (e.g., P1+P2, P3+P4).
  - Classes don’t repeat the same subject back-to-back in a single day.
  - Subject periods are fairly distributed in the week.
- Creates an **Excel workbook** with these sheets:
  1. **Teachers_Subjects** → Teacher–Subject–Class mapping.
  2. **Years_Subjects** → Subjects for each year with weekly frequency.
  3. **Lab_Timetables** → Separate schedules for B1 and B2 batches.
  4. **Theory_Timetables** → Only theory periods.
  5. **Merged_Timetables** → Combined lab and theory periods.
  6. **Teacher_Timetables** → Timetables for each teacher.

---

## 📂 Project Files

| File | Purpose |
|------|---------|
| `variables.py` | Stores all input data — classes, years, subjects, teacher assignments, lab subjects, and scheduling rules. |
| `generate_timetable.py` | Handles the timetable generation logic — decides period placements. |
| `export_excel.py` | Runs the generator and **exports the results** to Excel with formatting. |

---

## 🛠 Setup Instructions (First-Time Use)

You’ll need **Python 3** installed.

1. **Install Python**
   - [Download here](https://www.python.org/downloads/) for Windows (tick “Add to PATH” while installing).
   - Mac/Linux usually comes with Python, but ensure it's v3.x.

2. **Download this project**
   - Place `variables.py`, `generate_timetable.py`, and `export_excel.py` in the same folder.

3. **Install Required Python Packages**
   Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux) inside your project folder and run:
```

pip install pandas openpyxl

```

---

## 🚀 How to Run It

1. Open **Command Prompt/Terminal** in the folder with the three files.
2. Type:
```

python export_excel.py

```
3. Wait for the message:
```

✅ Timetable exported to timetable_export.xlsx with formatting \& Pylance-clean code.

```
4. Check the file `timetable_export.xlsx` in the same folder.

---

## 📊 Understanding the Excel Output

### **1. Teachers_Subjects**
Shows **which teacher teaches which subject for which class**.

| Class | Teacher      | Subject                          |
|-------|--------------|----------------------------------|
| 3A    | X1           | MATHEMATICS FOR COMPUTER SCIENCE |
| 3A    | SHWETHA K R  | DIGITAL DESIGN & COMPUTER ORG    |

---

### **2. Years_Subjects**
List of subjects and how many periods per week they have.

| Year | Subject                          | Frequency |
|------|-----------------------------------|-----------|
| 3    | MATHEMATICS FOR COMPUTER SCIENCE | 5         |
| 3    | OPERATING SYSTEM                  | 3         |

---

### **3. Lab_Timetables**
Separate tables for **B1** and **B2** batches so labs run without conflicts.

---

### **4. Theory_Timetables**
Shows only theory class periods for each section.

---

### **5. Merged_Timetables**
The complete timetable for each class combining **theory + lab periods**.

---

### **6. Teacher_Timetables**
The personal timetable for each teacher.

---

## ⚙ Customizing the Timetable

Edit `variables.py` to:
- Change subjects and frequencies → `SUBJECTS_PER_YEAR`
- Change teacher assignments → `TEACHER_ASSIGNMENTS`
- Change lab subjects → `LAB_SUBJECTS`
- Block specific teacher periods → add to `PREBOOKED`

After edits, re-run:
```

python export_excel.py

```
to update the timetable.

---

## 🛡 Troubleshooting

- **`[UNPLACED]` messages** → Some subjects couldn’t be fit without breaking constraints. Reduce workload or free up slots.
- **Excel won’t open** → Ensure `openpyxl` and `pandas` are installed.
- **Wrong timetable** → Check `variables.py` for incorrect teacher or subject codes.

---

## 📌 Example Run

```

\$ python export_excel.py

--- Pass 1 (relax=False) ---
--- Pass 2 (relax=False) ---
...
✅ Timetable exported to timetable_export.xlsx with formatting \& Pylance-clean code.

```

Open your new **timetable_export.xlsx** and you’re done! 🎉

---

## 👨‍💻 Notes
- All scheduling is automatic based on **randomized placement** with rules applied.
- The more accurate `variables.py` is, the better the generated timetable.
- Completely **no coding** is needed beyond editing `variables.py`.

---
