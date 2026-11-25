# Calendars {#prod.calendars}

The working time of the plant: the shifts of each weekday, and the holidays and exceptions by date. The work centers and the resources take their calendar from here, and the scheduler plans work only inside its hours.

**Where:** **Production > Calendars**, tabs **Shift schedules** and **Holidays and exceptions**.

## Shift schedules {#prod.calendars.list}

Columns: Code, Description, Shifts, Hours per week and Active. **New** creates a calendar. A calendar used by a work center or a resource cannot be deleted; deleting a calendar also deletes its own exceptions.

### Code {#prod.calendars.cCode}

Short code of the calendar (for example `DAY`, `2SHIFTS`). Required. Saved in capitals. It cannot be changed later.

### Active {#prod.calendars.lActive}

Marks a calendar no longer used.

### Description (French) {#prod.calendars.cDescFR}

Name of the calendar in French. Required.

### Description (English) {#prod.calendars.cDescEN}

Name of the calendar in English.

## Shifts {#prod.calendars.lines}

One line per shift and weekday. Two shifts of a calendar cannot overlap, also across midnight and from Sunday to Monday (*Two shifts overlap*).

### Day {#prod.calendars.lines.iWeekday}

The weekday of the shift, Monday to Sunday.

### Shift {#prod.calendars.lines.cShift}

Name of the shift (for example `DAY`, `NIGHT`). Free text, shown in the available time.

### Start {#prod.calendars.lines.cStart}

Start time, `HH:MM`.

### End {#prod.calendars.lines.cEnd}

End time, `HH:MM`. An end at or before the start ends the next day: 22:00 to 06:00 is a night shift. The shift counts on the day it starts (the night shift of Friday is Friday's).

### Break (min) {#prod.calendars.lines.iBreakMin}

Minutes of break taken off the shift. It must be shorter than the shift.

## Available time {#prod.calendars.preview}

Below the shifts of a saved calendar: the hours available each day of a week, with the holidays and exceptions, and the total for the week.

### Week of {#prod.calendars.week}

Any day of the week to show; the week starts on Monday. This week by default.

## Holidays and exceptions {#prod.calendars.calexceptions}

Columns: Date, Calendar, Description and Closed all day. Filter: Calendar. An exception replaces the shifts of the week for its date: closed (a holiday), or other hours (overtime, short day). An exception of a calendar wins over one for every calendar.

### Calendar {#prod.calendars.calexceptions.cCalendar}

The calendar of the exception. Empty = every calendar (for example a plant holiday). It cannot be changed later.

### Date {#prod.calendars.calexceptions.dDate}

The day of the exception. Required. It cannot be changed later.

### Description (French) {#prod.calendars.calexceptions.cDescFR}

What the day is, in French (for example *Fête nationale*). Required.

### Description (English) {#prod.calendars.calexceptions.cDescEN}

What the day is, in English.

### Closed all day {#prod.calendars.calexceptions.lClosed}

Checked: no work that day. Unchecked: give the hours of that day below.

### Start {#prod.calendars.calexceptions.cStart}

Start time of that day, `HH:MM`. Only when the day is not closed.

### End {#prod.calendars.calexceptions.cEnd}

End time of that day, `HH:MM`. An end at or before the start ends the next day.

### Break (min) {#prod.calendars.calexceptions.iBreakMin}

Minutes of break that day.
