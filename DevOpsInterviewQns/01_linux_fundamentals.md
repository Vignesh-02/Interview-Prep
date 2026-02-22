# 1. Linux Fundamentals

## Q1. (Beginner) What is the difference between a process and a thread? How do you list running processes?

**Answer:**  
A **process** is an instance of a program with its own memory space; a **thread** is a unit of execution within a process (shared memory). **List processes**: `ps aux`, `ps -ef`, or `top` / `htop`. **By name**: `pgrep -a nginx` or `ps aux | grep nginx`.

---

## Q2. (Beginner) What do these commands do: `chmod 755 script.sh`, `chown deploy:deploy file`, `umask 022`?

**Answer:**  
**chmod 755**: owner = rwx (7), group = r-x (5), others = r-x (5); file executable. **chown deploy:deploy**: set owner and group to user `deploy`. **umask 022**: default permission for new files = 666 - 022 = 644 (files), dirs 777 - 022 = 755. So new files are rw-r--r--, dirs rwxr-xr-x.

---

## Q3. (Beginner) How do you find files modified in the last 7 days? How do you find and delete empty directories?

**Answer:**  
**Modified in 7 days**: `find /var/app -type f -mtime -7`. **Empty dirs**: `find /var/app -type d -empty`; **delete**: `find /var/app -type d -empty -delete` (use with care).

---

## Q4. (Beginner) What is the difference between `kill` and `kill -9`? When would you use each?

**Answer:**  
**kill** (default SIGTERM, 15): asks the process to **terminate gracefully** (cleanup, flush). **kill -9** (SIGKILL): **force** kill; process cannot catch it. Use **kill** first; use **kill -9** only if the process does not exit after SIGTERM. Prefer graceful shutdown in production (e.g. let the app close connections).

---

## Q5. (Intermediate) How do you check disk usage by directory and find the largest files? Write the commands.

**Answer:**  
**By directory**: `du -sh /var/*` or `du -h --max-depth=1 /var`. **Largest files**: `find /var -type f -exec du -h {} + | sort -rh | head -20`. Or `ncdu /var` (interactive). **Production**: `du -sh /var/log/*` to find log hogs.

---

## Q6. (Intermediate) What are file descriptors 0, 1, 2? How do you redirect stderr to stdout and then to a file?

**Answer:**  
**0** = stdin, **1** = stdout, **2** = stderr. **Redirect stderr to stdout, then both to file**: `cmd > out.log 2>&1` or `cmd &> out.log`. **Append**: `cmd >> out.log 2>&1`. **Separate files**: `cmd > out.log 2> err.log`.

---

## Q7. (Intermediate) How do you run a command in the background and later bring it to foreground? How do you disconnect it from the terminal so it keeps running?

**Answer:**  
**Background**: run command, then `Ctrl+Z` then `bg`, or suffix with `&`. **Foreground**: `fg` or `fg %1`. **Disconnect and keep running**: `nohup cmd &` or `disown` after bg, or use **screen** / **tmux**: `tmux new -s mysession`, run cmd, detach with `Ctrl+B D`; reattach with `tmux attach -t mysession`.

---

## Q8. (Intermediate) What is the difference between hard link and symbolic link? When would you use each?

**Answer:**  
**Hard link**: same inode; same file, another name; cannot cross filesystems; deleting one doesn’t remove data until all links are gone. **Symlink**: pointer to path; can cross filesystems; broken if target is removed. **Use symlink** for shortcuts, version switches (e.g. `java -> java-11`). **Use hard link** rarely (e.g. backup without copy).

---

## Q9. (Intermediate) Write a one-liner to count the number of lines in all `.log` files under `/var/log` that contain the word "ERROR".

**Answer:**  
`grep -rh "ERROR" /var/log/*.log 2>/dev/null | wc -l`  
Or count per file: `grep -c "ERROR" /var/log/*.log 2>/dev/null`

---

## Q10. (Intermediate) How do you verify which binary will run when you type `java`? How do you list all installed versions of that command?

**Answer:**  
**Which**: `which java` (first in PATH). **Full resolution**: `type -a java` or `command -v java`. **List versions**: `update-alternatives --list java` (Debian/Ubuntu) or `ls /usr/lib/jvm` (or wherever JDKs are).

---

## Q11. (Advanced) Production scenario: A server has 100% CPU. How do you identify the process and thread causing it, and what next steps do you take?

**Answer:**  
(1) **Process**: `top` (sort by CPU, %CPU) or `ps aux --sort=-%cpu | head -5`. (2) **Threads**: `top -H -p <PID>` or `ps -eLf | grep <PID>`. (3) **Stack**: `pid -p <PID> -e thread apply all bt` or `cat /proc/<PID>/stack`. (4) **Next**: capture **thread dump** (Java: jstack); **profile** (perf, flame graph); check **recent deploys** and **metrics**. (5) **Mitigate**: scale, restart, or rollback; set **limits** (cgroups) to prevent one process from starving others. **Senior**: "I’d get PID from top, then thread dump or perf to see what’s burning CPU; then correlate with deploy and decide rollback or fix."

---

## Q12. (Advanced) Production scenario: Disk is full on a production app server. Walk through your diagnostic and remediation steps without taking the app down.

**Answer:**  
(1) **Where**: `df -h`; `du -sh /*` or `du -h --max-depth=1 /` to find full partition. (2) **Large dirs**: `du -sh /var/* /tmp/* /home/*`; often **/var/log** or **/tmp**. (3) **Large files**: `find /var -type f -size +100M -exec ls -lh {} \;`. (4) **Remediate**: **truncate** large log (e.g. `truncate -s 0 /var/log/app.log`) or **rotate** (logrotate); **remove** old logs/temp; **don’t** delete app binaries. (5) **Prevent**: configure **logrotate**, **disk alerts**, and **cleanup** jobs. **Tradeoff**: Startup = manual cleanup; enterprise = automated rotation, monitoring, and quotas.

---

## Q13. (Advanced) What are cgroups and namespaces? How do they relate to containers?

**Answer:**  
**cgroups** (control groups): limit and account **CPU**, **memory**, **I/O** per group of processes. **Namespaces**: isolate **PID**, **network**, **mount**, **UTS**, **IPC**, **user** so a process sees its own view. **Containers** (Docker, etc.) use **both**: cgroups for limits; namespaces for isolation. So containers are processes with restricted resources and isolated namespaces.

---

## Q14. (Advanced) How do you secure a Linux server for a production workload? List at least five concrete steps.

**Answer:**  
(1) **SSH**: key-only auth; disable root login; non-default port optional. (2) **Firewall**: ufw/iptables allow only needed ports (e.g. 22, 80, 443). (3) **Updates**: unattended-upgrades or regular patching. (4) **Users**: least privilege; no shared root; sudo only where needed. (5) **Services**: run as non-root; restrict to specific user. (6) **Files**: minimal permissions; no world-writable dirs in sensitive paths. (7) **Audit**: auditd or logging for critical changes.

---

## Q15. (Advanced) Write a command to list all listening TCP ports and the process owning each.

**Answer:**  
`ss -tlnp` or `netstat -tlnp` (requires root or capability for PID). **With process**: `ss -tlnp` shows Process column. **Alternative**: `lsof -iTCP -sTCP:LISTEN -P -n`.

---

## Q16. (Advanced) What is the difference between `sudo` and `su`? When would you use `sudo -u appuser cmd`?

**Answer:**  
**su**: switch user (default root); you get that user’s full login. **sudo**: run **one** command as another user (often root) per your sudoers entry. **sudo -u appuser cmd**: run `cmd` as `appuser` (e.g. deploy script that must touch app-owned files). Prefer **sudo** for audit and least privilege; avoid shared root.

---

## Q17. (Advanced) Production scenario: You have 50 web servers. You need to apply a security patch and restart the app on each without a full outage. Describe your approach (no automation tool required; assume SSH).

**Answer:**  
(1) **Rolling**: patch and restart **one at a time** (or small batch) so load balancer always has healthy nodes. (2) **Steps per host**: SSH, `sudo apt update && sudo apt install -y <patch>`, restart app, **health check** (curl localhost/health), then next host. (3) **Script**: loop over host list; run remote commands via `ssh host '...'`; abort if health check fails. (4) **Rollback**: keep previous package version; if issues, reinstall old and restart. **Enterprise**: use Ansible or similar for idempotent, logged runs; **startup**: manual or simple script.

---

## Q18. (Advanced) How do you persist a service across reboots (systemd)? Write a minimal unit file that runs a script and restarts on failure.

**Answer:**  
**systemd unit** (e.g. `/etc/systemd/system/myapp.service`):

```ini
[Unit]
Description=My App
After=network.target

[Service]
Type=simple
ExecStart=/opt/app/start.sh
Restart=on-failure
RestartSec=5
User=appuser

[Install]
WantedBy=multi-user.target
```

Then: `sudo systemctl daemon-reload`, `sudo systemctl enable myapp`, `sudo systemctl start myapp`.

---

## Q19. (Advanced) What is inode exhaustion? How do you detect and fix it?

**Answer:**  
**Inode exhaustion**: filesystem has no free **inodes** (each file/dir uses one); `df -i` shows IUsage 100% even if disk space is free. **Cause**: many small files (e.g. small logs, cache). **Detect**: `df -i`; `find /path -type f | wc -l`. **Fix**: delete or archive small files; move to another filesystem; increase inodes at mkfs time (not after). **Prevent**: limit small file creation (e.g. log aggregation, cleanup job).

---

## Q20. (Advanced) Senior red flags to avoid in Linux production

**Answer:**  
- **Running as root** for app or cron.  
- **kill -9** as first choice (use graceful shutdown).  
- **No disk or inode monitoring** (full disk = outage).  
- **World-writable** dirs or sensitive files.  
- **No log rotation** (disk fill).  
- **Manual one-off changes** without documentation or automation.  
- **Ignoring** resource limits (ulimit, cgroups) for runaway processes.

---

**Tradeoffs:** Startup: manual SSH, basic hardening. Medium: config management, monitoring, logrotate. Enterprise: automation, patch policy, audit, least privilege.
