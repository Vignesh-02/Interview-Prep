# 15. Scripting & Automation

## Q1. (Beginner) What is the shebang line? Give an example for Bash.

**Answer:**  
**Shebang**: **first** line `#!interpreter`; **tells** OS **how** to **run** the file. **Bash**: `#!/usr/bin/env bash` or `#!/bin/bash`. **Use** `env` for **portability** (finds **bash** in **PATH**). **Run**: `chmod +x script.sh` then `./script.sh`, or `bash script.sh`.

---

## Q2. (Beginner) How do you pass arguments to a script and use the first two?

**Answer:**  
**Positional**: **$1**, **$2**, ... **$#** = count; **$@** = all. **Example**: `echo "First: $1, Second: $2"`. **Call**: `./script.sh foo bar`. **Check**: `if [ $# -lt 2 ]; then echo "Usage: $0 <arg1> <arg2>"; exit 1; fi`.

---

## Q3. (Beginner) What is the difference between `$?`, `$!`, and `$$` in Bash?

**Answer:**  
**$?** = **exit** code of **last** command (0 = success). **$!** = **PID** of **last** **background** process. **$$** = **PID** of **current** script. **Use**: **$?** for **error** handling; **$!** to **wait** or **kill** background job; **$$** for **temp** files or **logs**.

---

## Q4. (Beginner) How do you run a command and exit the script on failure?

**Answer:**  
**set -e**: script **exits** on **first** non-zero **exit**. **Or** **per command**: `cmd || exit 1`. **Best**: `set -euo pipefail` (exit on error, undefined var, pipe failure). **Optional**: `set +e` for a **section** then `set -e` again.

---

## Q5. (Intermediate) Write a loop that runs a script for each file in a directory (only .log files).

**Answer:**
```bash
#!/usr/bin/env bash
set -euo pipefail
for f in /path/to/dir/*.log; do
  [ -f "$f" ] || continue
  ./process.sh "$f"
done
```
**Or** **find**: `find /path -maxdepth 1 -name '*.log' -exec ./process.sh {} \;`

---

## Q6. (Intermediate) How do you avoid "set -e" exiting on a command that you expect might fail (e.g. grep)?

**Answer:**  
**Allow** failure: `grep "pattern" file || true` (or `|| :`). **Capture** exit: `set +e; grep ...; ret=$?; set -e` then **if [ $ret -ne 0 ]**. **Best** for **grep**: `if grep -q "pattern" file; then ...; fi` (no **exit** from **grep**).

---

## Q7. (Intermediate) What is the difference between sourcing a script (`. script`) and executing it (`./script`)?

**Answer:**  
**Execute** (`./script` or `bash script`): **subshell**; **vars** and **cd** **don’t** affect **caller**. **Source** (`. script` or `source script`): **runs** in **current** shell; **vars**, **aliases**, **cd** **persist**. **Use** **source** for **env** (e.g. `. venv/bin/activate`); **execute** for **standalone** scripts.

---

## Q8. (Intermediate) How do you run 10 tasks in parallel in Bash (e.g. process 10 files), limiting to 4 at a time?

**Answer:**  
**Background** jobs + **wait**; **limit** with **counter** or **semaphore**. **Simple** (GNU parallel): `parallel -j 4 ./task.sh ::: file1 file2 ...`. **Pure Bash**: **loop**; start **background**; when **running** ≥ 4, **wait -n**; repeat. **Or** **xargs -P 4**: `printf '%s\n' file* | xargs -P 4 -I {} ./task.sh {}`.

---

## Q9. (Intermediate) How do you parse a simple key=value config file in Bash and export variables?

**Answer:**
```bash
while IFS= read -r line; do
  [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
  if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
    export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
  fi
done < config.env
```
**Or** **source** if **safe** (no code): `set -a; source config.env; set +a`.

---

## Q10. (Intermediate) How do you log with timestamp and level (e.g. INFO) in a script?

**Answer:**
```bash
log() { echo "$(date -Iseconds) [$1] $2"; }
log INFO "Starting..."
log ERROR "Failed"
```
**Or** **logger** for **syslog**: `logger -t myapp "message"`. **File**: `log INFO "msg" >> /var/log/myapp.log`.

---

## Q11. (Advanced) Production scenario: Script must deploy to 20 servers; if any fails, roll back the updated ones. Design the logic.

**Answer:**  
**Track** **updated** list; **on** **failure** **loop** over **updated** and **rollback** (e.g. **restore** previous **version** or **run** **rollback** script). **Pseudocode**: **updated=()**; for **host** in **hosts**; do **deploy** **host**; **on success** **updated+=("$host")**; **on failure** **break**; done; **if** **failed** then for **h** in **updated**; do **rollback** **h**; done; **exit 1**; fi. **Idempotent** **deploy** and **rollback**; **log** **updated** for **audit**.

---

## Q12. (Advanced) How do you make a script robust to spaces in paths and empty arguments?

**Answer:**  
**Quote** **all** **vars**: `"$var"`, `"$1"`. **Loop** over **files**: `for f in /path/*; do ... "$f" ...`. **Default**: `"${1:-default}"`. **Arrays**: `"${arr[@]}"`. **set -u** (undefined = error). **Avoid** **word** **split** and **globbing** when **unintended**: **assign** to **array**; **use** **"$@"** for **args**.

---

## Q13. (Advanced) What is the purpose of a lock file (e.g. flock) in automation? Show usage.

**Answer:**  
**Prevent** **concurrent** runs (e.g. **cron** overlap). **flock**: `flock -n /var/run/myscript.lock -c "./myscript.sh"` (**-n** = fail if **locked**); or **inside** script: `exec 200>/var/run/myscript.lock; flock -n 200 || exit 1`. **Single** **instance** per **lock** file.

---

## Q14. (Advanced) Production scenario: Cron job runs a script that sometimes hangs. How do you enforce a timeout and log?

**Answer:**  
**timeout**: `timeout 300 ./script.sh >> /var/log/script.log 2>&1` (kill after **5** min). **Cron**: `0 * * * * timeout 300 /opt/script.sh >> /var/log/script.log 2>&1`. **Or** **wrapper**: `timeout 300 bash -c './script.sh' ...`. **Alert** if **script** **exits** **124** (timeout). **Better**: **fix** **script** to **not** hang; **timeout** as **safety**.

---

## Q15. (Advanced) How do you retry a command N times with exponential backoff in Bash?

**Answer:**
```bash
retries=5
delay=2
for i in $(seq 1 $retries); do
  if cmd; then exit 0; fi
  echo "Attempt $i failed, waiting ${delay}s"
  sleep $delay
  delay=$((delay * 2))
done
exit 1
```

---

## Q16. (Advanced) When would you choose Python/Go over Bash for automation?

**Answer:**  
**Bash**: **glue** (calls, **short** scripts, **cron**), **portability** on **Linux**. **Python/Go**: **complex** logic, **parsing** (JSON, APIs), **libraries**, **testing**, **cross-platform**, **concurrency**. **Choose** **Python/Go** when: **many** **deps**, **API** clients, **structured** data, **long** maintenance; **Bash** when **simple** and **ops**-oriented.

---

## Q17. (Advanced) How do you test Bash scripts (e.g. unit test style)?

**Answer:**  
**bats** (Bash **Automated** **Testing** **System**): **test** **files**; **run** script and **assert** **output**/exit. **shunit2**: **similar**. **Manual**: **run** with **test** **inputs**; **assert** **$?** and **output**. **CI**: **run** **bats** in **pipeline**. **Best**: **small** **functions**; **source** and **test**; **mock** **external** (e.g. **curl**) if needed.

---

## Q18. (Advanced) Production scenario: Script is used in CI and locally; it needs different config (e.g. API URL) per environment. How do you design it?

**Answer:**  
**Env** **var**: `API_URL="${API_URL:-https://default}"`; **set** in **CI** (vars) and **locally** (`.env` or **export**). **Config** **file**: **path** from **env** (`CONFIG_FILE="${CONFIG_FILE:-./config.env}"`); **CI** **injects** **path**. **No** **hardcode**; **document** **required** **vars**; **fail** **fast** if **missing** (`set -u` and **check** **required** vars).

---

## Q19. (Advanced) How do you avoid race conditions when multiple cron jobs write to the same file?

**Answer:**  
**Lock**: **flock** so only **one** writer at a time. **Write** to **temp** then **rename** (atomic on same **FS**): `echo "data" > "$file.tmp"; mv "$file.tmp" "$file"`. **Append**: **multiple** appends are **OK** (order may vary); **or** **flock** for **append**. **Separate** **files** per **job** (e.g. **timestamp** or **hostname**) then **merge** if needed.

---

## Q20. (Advanced) Senior red flags to avoid in scripting and automation

**Answer:**  
- **Unquoted** **vars** (spaces, **empty** break).  
- **No** **set -euo pipefail** (silent **failures**).  
- **No** **timeout** for **long**/external **calls**.  
- **No** **lock** for **cron** (overlap).  
- **Secrets** in **script** or **args** (use **env**/vault).  
- **No** **idempotency** (re-run **breaks** state).  
- **No** **logging** or **error** **messages**.  
- **Bash** for **complex** logic (prefer **Python**/Go).

---

**Tradeoffs:** Startup: simple Bash, cron. Medium: locks, timeout, env-based config, some tests. Enterprise: tests, retries, logging, consider Python/Go for complex flows.
