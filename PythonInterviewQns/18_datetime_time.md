# 18. datetime and Working with Time

## Q1. (Easy) What is the difference between `datetime.date`, `datetime.time`, and `datetime.datetime`?

**Answer:**  
**date** — year, month, day (no time). **time** — hour, minute, second, microsecond (no date; can have tzinfo). **datetime** — date and time combined; can have tzinfo. Use **date** for “calendar day,” **time** for “time of day,” **datetime** for a specific moment or “day + time.”

---

## Q2. (Easy) How do you get the current date and time? In UTC?

**Answer:**  
**`datetime.datetime.now()`** — local date and time. **`datetime.datetime.utcnow()`** — UTC but **naive** (no tzinfo); deprecated in favor of timezone-aware. Prefer **`datetime.datetime.now(datetime.timezone.utc)`** for UTC **aware** datetime, or **`datetime.datetime.now(tz=...)`** with a proper tz.

---

## Q3. (Easy) How do you format a datetime as a string? Parse a string into a datetime?

**Answer:**  
**Format:** **`dt.strftime(format)`** — e.g. `dt.strftime("%Y-%m-%d %H:%M")`. **Parse:** **`datetime.datetime.strptime(s, format)`** — e.g. `strptime("2024-01-15", "%Y-%m-%d")`. Format codes: %Y year, %m month, %d day, %H %M %S, etc.

---

## Q4. (Medium) What is a “naive” vs “aware” datetime? Why does it matter?

**Answer:**  
**Naive** — no timezone info; interpreted as local or “don’t know.” **Aware** — has **tzinfo** set; represents a moment in a timezone. Mixing naive and aware or doing math across DST can be wrong. Prefer **aware** for storage and computation; use **datetime.timezone** or **zoneinfo** (3.9+).

---

## Q5. (Medium) How do you add or subtract time from a datetime? What type is the result of subtraction of two datetimes?

**Answer:**  
Use **timedelta**: **`dt + datetime.timedelta(days=1, hours=2)`**. Subtraction of two **datetime**s gives a **timedelta**. Subtraction of **datetime - timedelta** gives datetime. **timedelta** supports days, seconds, microseconds (internal normalization).

---

## Q6. (Medium) What is `time.time()`? What does it return and what is it good for?

**Answer:**  
**time.time()** returns **seconds since the epoch** (float; platform-dependent epoch, usually Unix). Good for **elapsed time** (difference of two calls), **timing**, and as a simple “now” for ordering. Not for human-readable date/time — use **datetime** for that.

---

## Q7. (Medium) How do you convert a datetime to a different timezone? (Python 3.9+ zoneinfo)

**Answer:**  
With **zoneinfo**: **`from zoneinfo import ZoneInfo; dt_utc = dt_local.astimezone(ZoneInfo("UTC"))`**. Or **`dt.astimezone(ZoneInfo("America/New_York"))`**. **astimezone** converts to the target zone; if the datetime is naive, it’s assumed to be local time (Python 3.6+). Prefer storing in UTC and converting to local for display.

---

## Q8. (Tough) Why is `datetime.utcnow()` discouraged? What should you use instead?

**Answer:**  
**utcnow()** returns a **naive** datetime (no tzinfo), so you lose the fact that it’s UTC. That leads to bugs when you mix with aware datetimes or do DST math. Use **`datetime.now(datetime.timezone.utc)`** or **`datetime.now(ZoneInfo("UTC"))`** to get an **aware** UTC datetime.

---

## Q9. (Tough) What is the difference between calendar time (wall clock) and monotonic time? When to use each?

**Answer:**  
**Calendar time** (e.g. **time.time()**) can jump backward (NTP, user change). **Monotonic time** (e.g. **time.monotonic()**) never goes backward; good for **elapsed time** and **timers**. Use monotonic for measuring duration; use calendar/time for “what time is it” and human-facing timestamps.

---

## Q10. (Tough) How do you compute “number of days between two dates” correctly (ignoring time)? What about “business days”?

**Answer:**  
**Days between:** Use **date** (not datetime): **`(d2 - d1).days`** — gives integer days. For **business days** (exclude weekends/holidays), iterate from d1 to d2 and count days where **weekday()** not in (5, 6) or use a library (e.g. **pandas.bdate_range**) or maintain a set of holidays and skip those too.
