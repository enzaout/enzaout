# CapCut MCP (Windows)

שרת MCP שנותן ל-Claude לקרוא ולערוך פרויקטים של CapCut שעל המחשב שלך.
CapCut לא מציע API, ולכן השרת עורך ישירות את קובצי הפרויקט (JSON).
הגישה מבוססת על הלקחים של [capcut-kit](https://github.com/matt-j-penny/capcut-kit).

## התקנה (פעם אחת)

1. התקן Python 3.10 ומעלה מ-python.org וסמן "Add to PATH".
2. פתח PowerShell והרץ:
   ```powershell
   pip install mcp
   ```
3. חבר את השרת ל-Claude:
   - **Claude Code:**
     ```powershell
     claude mcp add capcut -- python C:\path\to\capcut-mcp\server.py
     ```
   - **Claude Desktop:** ב-Settings → Developer → Edit Config, הוסף:
     ```json
     {
       "mcpServers": {
         "capcut": { "command": "python", "args": ["C:\\path\\to\\capcut-mcp\\server.py"] }
       }
     }
     ```
     ואז הפעל את Claude Desktop מחדש.

אם הפרויקטים שלך לא נמצאים בתיקייה הרגילה
(`%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`), בדוק את המיקום
בהגדרות של CapCut והגדר אותו במשתנה הסביבה `CAPCUT_DRAFTS`.

## כלים

| כלי | מה הוא עושה |
|---|---|
| `list_projects` | מציג את כל הפרויקטים |
| `read_timeline` | מסכם את ציר הזמן: ערוצים, קליפים, זמנים וטקסטים |
| `backup_project` | מגבה פרויקט |
| `add_text` | מוסיף טקסט או כתובית בסגנון של טקסט שכבר קיים בפרויקט |
| `trim_clip` | משנה את האורך של קליפ |
| `remove_segment` | מוחק קליפ או טקסט |

לדוגמה: "תוסיף את הכתובית 'שלום' בשנייה 3 בפרויקט X".

## חשוב לדעת

- **CapCut ייסגר אוטומטית לפני כל עריכה.** אם הוא פתוח בזמן הכתיבה, הוא דורס את השינויים. אחרי העריכה, פתח אותו מחדש.
- **לפני כל עריכה נשמר גיבוי** בתיקייה `%USERPROFILE%\capcut-mcp-backups`. כדי לחזור לגרסה קודמת, העתק את התיקייה מהגיבוי בחזרה לתיקיית הפרויקטים.
- `add_text` דורש שיהיה בפרויקט לפחות טקסט אחד, בכל סגנון שהוא. הטקסט הזה משמש כתבנית לגופן ולסגנון.
- זה כלי לא רשמי, ועדכון של CapCut עלול לשבור אותו.
