# 9. String and Date Functions

## Q1. (Beginner) Name three string functions and what they do (e.g. CONCAT, LENGTH, SUBSTRING).

**Answer:**  
**CONCAT(a, b)** or **a || b** — concatenate. **LENGTH(str)** — character length (use CHAR_LENGTH for characters, LENGTH for bytes in some DBs). **SUBSTRING(str FROM start FOR len)** or **SUBSTR(str, start, len)** — extract substring. Others: **UPPER**, **LOWER**, **TRIM**, **REPLACE**.

---

## Q2. (Beginner) How do you get the current date and time in SQL? Do all databases use the same function?

**Answer:**  
**PostgreSQL**: **CURRENT_DATE**, **CURRENT_TIME**, **CURRENT_TIMESTAMP**, **NOW()**. **MySQL**: **CURDATE()**, **NOW()**, **CURRENT_TIMESTAMP()**. **Oracle**: **SYSDATE**, **CURRENT_DATE** (session time zone). So no single standard; use the appropriate function per DB. Backend: prefer sending timestamps in UTC and converting in app or DB.

---

## Q3. (Intermediate) How do you extract part of a date (year, month, day)? Give PostgreSQL and MySQL examples.

**Answer:**  
**PostgreSQL**: **EXTRACT(YEAR FROM date_col)**, **DATE_PART('month', date_col)**. Or **date_col::date** and then extract. **MySQL**: **YEAR(date_col)**, **MONTH(date_col)**, **DAY(date_col)**. **Oracle**: **EXTRACT(YEAR FROM date_col)**. Standard: **EXTRACT** is widely supported.

---

## Q4. (Intermediate) Write a query that finds rows where a string column contains a substring (e.g. “error”). How do you make it case-insensitive?

**Answer:**  
**WHERE col LIKE '%error%'**. Case-insensitive: **PostgreSQL** — **WHERE col ILIKE '%error%'** or **LOWER(col) LIKE '%error%'**; **MySQL** — **WHERE col LIKE '%error%'** (collation can be case-insensitive) or **LOWER(col) LIKE '%error%'**; **Oracle** — **LOWER(col) LIKE '%error%'**. **LIKE** with leading **%** cannot use index for prefix search; full-text search is better for large-scale text search.

---

## Q5. (Intermediate) How do you format a date as a string (e.g. “YYYY-MM-DD” or “DD/MM/YYYY”)? Which function in PostgreSQL, MySQL, Oracle?

**Answer:**  
**PostgreSQL**: **TO_CHAR(date_col, 'YYYY-MM-DD')**. **MySQL**: **DATE_FORMAT(date_col, '%Y-%m-%d')**. **Oracle**: **TO_CHAR(date_col, 'YYYY-MM-DD')**. Format codes differ (e.g. MySQL uses %Y, others use YYYY). Backend: often better to return a date/timestamp type and format in application code for locale and consistency.

---

## Q6. (Advanced) How do you compute the difference between two dates (e.g. days, months)? Compare PostgreSQL, MySQL, Oracle.

**Answer:**  
**PostgreSQL**: **date2 - date1** gives interval; **EXTRACT(DAY FROM (date2 - date1))** or **(date2::date - date1::date)** for integer days. **MySQL**: **DATEDIFF(date2, date1)** for days; **TIMESTAMPDIFF(MONTH, date1, date2)**. **Oracle**: **date2 - date1** for days (numeric); **MONTHS_BETWEEN(date2, date1)**. Syntax differs; use the appropriate function per DB.

---

## Q7. (Advanced) Write a query that returns “last day of month” for a given date column in a portable way (or give per-DB).

**Answer:**  
**PostgreSQL**: **DATE_TRUNC('month', date_col) + INTERVAL '1 month' - INTERVAL '1 day'** or **(DATE_TRUNC('month', date_col) + INTERVAL '1 month - 1 day')::date**. **MySQL**: **LAST_DAY(date_col)**. **Oracle**: **LAST_DAY(date_col)**. Use LAST_DAY where available; otherwise use date arithmetic.

---

## Q8. (Advanced) Production scenario: Logs are stored with a `message` text column. You need to find recent rows where the message contains a user-provided search term (case-insensitive). The table is large. What SQL would you use, and what would you tell the backend/ops team about indexing and alternatives?

**Answer:**  
**WHERE LOWER(message) LIKE LOWER('%' || $term || '%')** (parameterize **$term**). This predicate is **not sargable** (function on column, leading wildcard), so an index on **message** usually cannot be used. Options: (1) **Full-text search** (PostgreSQL **tsvector**/ **to_tsquery**, MySQL **FULLTEXT**); (2) **Triggers** to maintain a normalized/search column and index that; (3) **External search** (Elasticsearch). Tell backend: use parameterized query to avoid injection; for large scale, move to FTS or search service rather than LIKE.

---

## Q9. (Advanced) What is TRIM and how do you trim leading/trailing spaces or a specific character?

**Answer:**  
**TRIM(str)** or **TRIM(BOTH FROM str)** — trim spaces. **TRIM(LEADING 'x' FROM str)** — remove leading 'x'. **LTRIM**/ **RTRIM** in some DBs for left/right only. **PostgreSQL**: **TRIM(BOTH ',' FROM str)**. Use for cleaning user input or fixed-width data before comparison or storage.

---

## Q10. (Advanced) How do you concatenate with a separator (e.g. comma-separated list of values from rows)? Which DB has STRING_AGG / GROUP_CONCAT?

**Answer:**  
**PostgreSQL**: **STRING_AGG(col, ',')** with **GROUP BY**. **MySQL**: **GROUP_CONCAT(col SEPARATOR ',')**. **Oracle**: **LISTAGG(col, ',') WITHIN GROUP (ORDER BY col)**. **SQL Server**: **STRING_AGG** (2017+). Use for “all values in one row per group” (e.g. list of tags per post). Watch length limits (GROUP_CONCAT has max length; STRING_AGG can be large).
