# 2. Shell Scripting (Bash)

## Q1. (Beginner) What is the shebang? Why use `#!/usr/bin/env bash` instead of `#!/bin/bash`?

**Answer:**  
**Shebang**: first line `#!...` tells the kernel which interpreter to run. **#!/usr/bin/env bash**: finds `bash` in **PATH** (portable across systems where bash isn’t at /bin/bash). **#!/bin/bash**: fixed path; can break in some environments. Prefer **env** for portability.

---

## Q2. (Beginner) How do you pass arguments to a script and use them? What are `$1`, `$@`, `$#`?

**Answer:**  
**$1**, **$2**, ... = first, second argument. **$@** = all arguments (each quoted). **$#** = number of arguments. **Example**: `./script.sh foo bar` → $1=foo, $2=bar, $#=2. **Loop args**: `for arg in "$@"; do ...; done`.

---

## Q3. (Beginner) What is the difference between `$var` and `"$var"` when used in a command? When does it matter?

**Answer:**  
**$var**: word-splitting and globbing; empty or unset can remove the argument. **"$var"**: preserves one argument; spaces and empty are safe. **Example**: `var="a b"; rm $var` tries to remove "a" and "b"; `rm "$var"` tries to remove one file "a b". **Always quote** when you want one argument: `"$var"`.

---

## Q4. (Beginner) Write a script that prints "Hello, &lt;name&gt;" if one argument is given, otherwise prints "Usage: script.sh &lt;name&gt;".

**Answer:**
```bash
#!/usr/bin/env bash
if [[ $# -eq 1 ]]; then
  echo "Hello, $1"
else
  echo "Usage: $0 <name>"
  exit 1
fi
```

---

## Q5. (Intermediate) How do you check if a file exists and is readable? How do you check if a variable is non-empty?

**Answer:**  
**File**: `[[ -f /path/file ]] && [[ -r /path/file ]]` or `test -f /path/file -a -r /path/file`. **Non-empty var**: `[[ -n "${var}" ]]`. **Empty or unset**: `[[ -z "${var}" ]]`. **Best**: `[[ -n "${var:-}" ]]` to treat unset like empty.

---

## Q6. (Intermediate) Write a loop that iterates over lines in a file (e.g. server list) and runs an SSH command on each. Handle empty lines and comments.

**Answer:**
```bash
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"   # strip comment
  line="${line%"${line##*[![:space:]]}"}"  # trim
  [[ -z "$line" ]] && continue
  ssh -n "$line" "hostname"
done < servers.txt
```
**Simpler**: `grep -v '^#' servers.txt | while read -r host; do ssh -n "$host" "hostname"; done`

---

## Q7. (Intermediate) What is `set -e`? What is `set -u`? Why use them in scripts?

**Answer:**  
**set -e**: exit immediately if a command fails (non-zero). **set -u**: treat **unset** variables as error. Use both for **safer** scripts: no silent failures, no typos in variable names. **Caveat**: with `set -e`, handle expected failures explicitly (e.g. `cmd || true` or `if ! cmd; then ...`).

---

## Q8. (Intermediate) How do you capture command output into a variable? How do you capture exit code?

**Answer:**  
**Output**: `output=$(cmd)` (trimmed newline). **Exit code**: `cmd; code=$?` or `if cmd; then ...; fi`. **Both**: `output=$(cmd); code=$?`. **Preserve trailing newlines**: avoid command substitution for binary or multi-line when you need exact content; use temp file if needed.

---

## Q9. (Intermediate) Write a script that backs up a directory to a timestamped tarball and rotates old backups (keep last 5).

**Answer:**
```bash
#!/usr/bin/env bash
set -eu
BACKUP_DIR="/var/app/data"
DEST="/backups"
NAME="app-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$DEST/$NAME" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
cd "$DEST" && ls -t app-*.tar.gz | tail -n +6 | xargs -r rm --
```

---

## Q10. (Intermediate) What is the difference between `$(cmd)` and `` `cmd` ``? What is command substitution in a string?

**Answer:**  
**$(cmd)** and **`cmd`** both run `cmd` and substitute output. **$(cmd)** is preferred: nests easily (`$(cmd1 $(cmd2))`); readable. **`cmd`** is legacy; nesting is awkward. **In string**: `echo "Today is $(date)"` → output includes date.

---

## Q11. (Advanced) Production scenario: You need a script that deploys an app to 20 servers: copy artifact, restart service, then run a health check. If health check fails, rollback (restore previous artifact). Design the script structure and error handling.

**Answer:**  
(1) **Per server**: loop over host list. (2) **Pre**: copy current app to `.prev` or record version. (3) **Deploy**: copy new artifact, restart service (systemctl). (4) **Health**: `curl -sf http://localhost/health` or similar; **timeout** (e.g. 30s). (5) **On failure**: restore `.prev`, restart, **exit 1** and **abort** remaining hosts (or mark host failed and continue). (6) **set -e**; trap for cleanup. (7) **Log** each step; report success/fail per host. **Tradeoff**: Startup = script; enterprise = Ansible/CI with rollback step.

---

## Q12. (Advanced) How do you prevent a script from running multiple instances (e.g. only one backup at a time)?

**Answer:**  
**Lock file**: `LOCKFILE=/var/run/myapp.lock`; `exec 200>"$LOCKFILE"`; `flock -n 200 || { echo "Already running"; exit 1; }`. Or **pidfile**: write PID to file; at start check if PID exists and is running (`kill -0 $(cat pidfile)`); exit if so. **flock** is cleaner (released on script exit).

---

## Q13. (Advanced) Write a script that parses a simple key=value config file (ignore comments and blank lines) and exports variables for use in the script.

**Answer:**
```bash
config_file="${1:-config.conf}"
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="${line%"${line##*[![:space:]]}"}"
  [[ -z "$line" ]] && continue
  if [[ "$line" == *=* ]]; then
    key="${line%%=*}"; key="${key%"${key##*[![:space:]]}"}"
    val="${line#*=}"; val="${val#"${val%%[![:space:]]*}"}"
    export "$key=$val"
  fi
done < "$config_file"
```
**Simpler (if no spaces in values)**: `source <(grep -v '^#' config.conf | sed 's/^/export /')` — only if content is trusted.

---

## Q14. (Advanced) What are the pitfalls of using `for file in $(ls *.txt)`? What is the correct way to iterate over files?

**Answer:**  
**Pitfalls**: **word splitting** (filenames with spaces break); **glob** in wrong directory; **ls** parsing is fragile. **Correct**: `for file in *.txt; do [[ -e "$file" ]] || break; ...; done` or `find . -maxdepth 1 -name '*.txt' -print0 | while IFS= read -r -d '' file; do ...; done`. Prefer **find** for complex patterns or recursion.

---

## Q15. (Advanced) How do you make a script idempotent (safe to run multiple times)? Give two examples.

**Answer:**  
(1) **Create only if missing**: `[[ -d /var/app ]] || mkdir -p /var/app`. (2) **Config**: compare and update only if different: `if ! diff -q target.conf current.conf; then cp target.conf current.conf; fi`. (3) **Package**: `apt-get install -y pkg` (already installed is no-op). (4) **Service**: `systemctl start app` (already started is no-op). Design so **state** after run is the same whether run once or twice.

---

## Q16. (Advanced) Production scenario: A cron job runs a script that sometimes hangs (e.g. SSH). How do you enforce a timeout and log failures?

**Answer:**  
**Timeout**: `timeout 300 ./script.sh` (GNU coreutils) or wrap in a subshell and kill: `( ./script.sh ) & pid=$!; sleep 300; kill $pid 2>/dev/null && kill -9 $pid`. **Log**: redirect to file and capture exit: `timeout 300 ./script.sh >> /var/log/job.log 2>&1; echo $? >> /var/log/job.exit`. **Cron**: `0 * * * * timeout 300 /opt/scripts/job.sh >> /var/log/job.log 2>&1`. **Alert**: cron wrapper that checks exit code and sends alert on failure.

---

## Q17. (Advanced) What is a here-document? Write an example that writes a config file from the script.

**Answer:**  
**Here-doc**: `cmd << END` ... `END`; stdin is the lines until delimiter. **Example**:
```bash
cat > /etc/app/config.conf << 'EOF'
server_port=8080
log_level=info
EOF
```
**Quoted** `'EOF'` prevents variable expansion; unquoted allows `$var`.

---

## Q18. (Advanced) How do you safely handle paths or variables that might contain spaces or special characters in a script?

**Answer:**  
(1) **Quote** all expansions: `"$var"`, `"$1"`. (2) **Avoid** word splitting: don’t use unquoted `$var` in command position. (3) **Filenames**: use **find -print0** and **read -d ''** or **xargs -0**. (4) **Arrays** (bash): `arr=("$@")`; `"${arr[@]}"` for each element quoted. (5) **Test** with paths containing spaces and newlines.

---

## Q19. (Advanced) Write a script that reads a list of URLs from a file and checks each with curl (HTTP 200 = success). Output a summary: total, success count, failed URLs.

**Answer:**
```bash
#!/usr/bin/env bash
set -e
file="${1:?usage: $0 urls.txt}"
total=0 ok=0
failed=()
while IFS= read -r url || [[ -n "$url" ]]; do
  [[ -z "${url%%#*}" ]] && continue
  ((total++)) || true
  if curl -sf -o /dev/null -w "%{http_code}" "$url" | grep -q 200; then
    ((ok++)) || true
  else
    failed+=("$url")
  fi
done < "$file"
echo "Total: $total, OK: $ok, Failed: $((total - ok))"
printf '%s\n' "${failed[@]}"
```

---

## Q20. (Advanced) Senior red flags to avoid in shell scripts

**Answer:**  
- **Unquoted** variables (`$var` instead of `"$var"`).  
- **No set -e / set -u** (silent failures, unset vars).  
- **Parsing ls** or relying on word splitting for filenames.  
- **No timeout** for external commands (SSH, curl).  
- **Secrets** in script or command line (use env or secret store).  
- **No idempotency** for deploy/maintenance scripts.  
- **Ignoring** exit codes or not logging failures.

---

**Tradeoffs:** Startup: ad-hoc scripts, minimal checks. Medium: set -eu, logging, timeouts. Enterprise: lint (shellcheck), tests, secret management, automation tool.
