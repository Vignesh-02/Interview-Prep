# 3. System Administration (Linux)

## Q1. (Beginner) What is the role of `/etc/passwd` and `/etc/shadow`? Why is the password in shadow?

**Answer:**  
**passwd**: user account info (name, UID, GID, shell, home); **readable** by all. **shadow**: hashed passwords, aging; **readable** only by root. Passwords moved to **shadow** so hashes aren’t exposed to every user (reduces brute-force risk).

---

## Q2. (Beginner) How do you add a user without a login shell (e.g. for running a service)?

**Answer:**  
`useradd -r -s /usr/sbin/nologin appuser` (system user, no login). Or `useradd -s /usr/sbin/nologin appuser`. **-r** = system user (UID in system range). Service runs as this user; no SSH or console login.

---

## Q3. (Beginner) What is the difference between `systemctl start` and `systemctl enable`? What does `systemctl status` show?

**Answer:**  
**start**: start the unit **now**. **enable**: start at **boot**. **status**: loaded/active, recent logs, PID, memory. Use **start** + **enable** for persistent services. **status** for quick health and logs.

---

## Q4. (Beginner) How do you schedule a job to run every day at 2 AM? What is the cron syntax for "every 5 minutes"?

**Answer:**  
**Cron**: `crontab -e`; line: `0 2 * * * /path/to/script`. **Every 5 min**: `*/5 * * * * /path/to/script`. Format: minute hour day-of-month month day-of-week. **Alternative**: **systemd timer** for more control and logging.

---

## Q5. (Intermediate) What is logrotate? How would you configure it to rotate `/var/log/app.log` daily, keep 7 days, and compress old logs?

**Answer:**  
**logrotate**: rotates logs by size/time; can compress, delete, postrotate. **Config** (e.g. `/etc/logrotate.d/app`):
```
/var/log/app.log {
  daily
  rotate 7
  compress
  delaycompress
  missingok
  notifempty
  postrotate
    systemctl reload app >/dev/null 2>&1 || true
  endscript
}
```

---

## Q6. (Intermediate) How do you limit the resources (CPU, memory) a user or process can use? What tools does Linux provide?

**Answer:**  
**ulimit** (shell): `ulimit -u 100` (processes), `ulimit -v 524288` (virtual memory in KB). **systemd**: in unit file `CPUQuota=50%`, `MemoryMax=512M`. **cgroups** (v2): set limits in cgroup tree. **Docker/Kubernetes**: container limits. For **systemd services**, use **MemoryMax** and **CPUQuota** in the unit.

---

## Q7. (Intermediate) A server has high load average but CPU and memory look normal. What could cause this and how do you investigate?

**Answer:**  
**Load** = runnable + uninterruptible (e.g. I/O wait). **High load, low CPU** → **I/O wait** (disk or network). **Investigate**: `vmstat 1`, `iostat -x 1` (disk); `top` (wa = iowait); `iotop` (per-process I/O). **Fix**: optimize disk (SSD, RAID, reduce write), fix slow queries or heavy I/O processes.

---

## Q8. (Intermediate) How do you configure static IP and hostname on a modern Linux server (e.g. using netplan or NetworkManager)?

**Answer:**  
**netplan** (Ubuntu/Debian): edit `/etc/netplan/01-netcfg.yaml`:
```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses: [192.168.1.10/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8]
```
Then `netplan apply`. **Hostname**: `hostnamectl set-hostname myhost` and ensure `/etc/hosts` has the name.

---

## Q9. (Intermediate) What is the difference between `journalctl -u app` and tailing a log file? When would you use each?

**Answer:**  
**journalctl -u app**: **systemd** journal for that unit; **structured**; filter by boot, time, priority; **centralized**. **Tailing file**: app writes to file (e.g. /var/log/app.log); **format** is app-specific. Use **journalctl** for systemd-managed services; use **file** when app writes its own logs or you need a specific format (e.g. JSON for log shipper).

---

## Q10. (Intermediate) How do you verify that a package (e.g. nginx) was installed from a trusted repository and has not been tampered with?

**Answer:**  
**Source**: install from **official** repo (apt/yum); verify repo signing. **Integrity**: **dpkg -V nginx** (Debian) checks file checksums; **rpm -V nginx** (RHEL). **Package signing**: repo metadata and packages signed; apt/yum verify signatures. **Tripwire**/AIDE for file integrity if needed.

---

## Q11. (Advanced) Production scenario: You manage 100 web servers. You need to push a new config file, reload the service, and verify health. Describe your approach with and without a config management tool.

**Answer:**  
**Without** (SSH loop): list of hosts; `for host in $(cat hosts); do scp app.conf $host:/etc/app/; ssh $host 'systemctl reload app && curl -sf localhost/health'; done`; **parallel** with xargs -P or parallel. **With** (Ansible): playbook with **template** or **copy**, **service** reload, **uri** health check; run once. **Tradeoff**: Startup = script; medium/enterprise = Ansible or similar for idempotency, reporting, and secrets.

---

## Q12. (Advanced) How do you perform a kernel upgrade with minimal downtime? What about rolling back?

**Answer:**  
(1) **Install** new kernel (apt/yum); **don’t** reboot. (2) **Reboot** during maintenance window; boot **new** kernel. (3) **Rollback**: reboot and choose **previous** kernel from GRUB; or set **default** kernel in GRUB and reboot. **Minimal downtime**: use **live patching** (e.g. Canonical Livepatch, kpatch) where supported for critical fixes without reboot.

---

## Q13. (Advanced) What is the difference between soft and hard limits (ulimit)? How do they affect a process?

**Answer:**  
**Soft**: current limit; process can **increase** up to **hard** (if permitted). **Hard**: ceiling; only root can raise. **Reaching soft**: process can get signal (e.g. SIGXFSZ for file size) or ENOENT; can raise own soft up to hard. **Reaching hard**: operation fails (e.g. cannot open more files). Set **hard** high enough for legitimate use; **soft** for default policy.

---

## Q14. (Advanced) How do you set up SSH key-based auth and disable password auth for a production server?

**Answer:**  
(1) **Client**: `ssh-keygen -t ed25519 -f ~/.ssh/mykey`; copy **public** to server. (2) **Server**: `mkdir -p ~/.ssh; echo "pubkey" >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys`. (3) **Disable password**: in `/etc/ssh/sshd_config`, `PasswordAuthentication no`, `ChallengeResponseAuthentication no`, `UsePAM no` (or keep PAM for other uses); `systemctl reload sshd`. **Test** with key in **new** session before closing current one.

---

## Q15. (Advanced) Production scenario: Disk I/O is very high and the app is slow. How do you identify which process is causing it and what type of I/O?

**Answer:**  
(1) **Per-process**: `iotop -o` (needs root) or `pidstat -d 1`. (2) **Per device**: `iostat -x 1` (await, %util). (3) **What files**: `lsof -p <PID>` or **/proc/<PID>/fd**. (4) **Type**: read vs write from iostat/pidstat; **strace** or **bpftrace** for syscalls if needed. (5) **Mitigate**: tune app (buffer, batch), move data to faster disk, or scale.

---

## Q16. (Advanced) How do you implement centralized time sync (NTP) for a fleet of servers? Why does it matter for distributed systems?

**Answer:**  
**NTP**: install **chrony** or **ntpd**; point to **internal** NTP server or pool (e.g. `pool.ntp.org`). **Config** (chrony): `server ntp.internal iburst`; `allow` for internal clients. **Distributed systems**: **ordering** of events, **TTLs**, **certificates** (validity); skew can cause duplicate or missed processing. **Enterprise**: stratum-1 or GPS-backed NTP; monitor offset.

---

## Q17. (Advanced) What is the purpose of `/etc/security/limits.conf`? Give an example of raising the open-file limit for the app user.

**Answer:**  
**limits.conf**: sets **PAM** limits (open files, processes, etc.) per user/group at **login**. **Example**: `appuser soft nofile 65535`, `appuser hard nofile 65535`. **Apply** at new login (not to already running processes). **systemd** can override with **LimitNOFILE** in the unit. Use for services that need many connections (e.g. load balancer, app server).

---

## Q18. (Advanced) How do you create a read-only filesystem or mount a partition read-only for recovery/maintenance?

**Answer:**  
**Remount**: `mount -o remount,ro /` or `mount -o remount,ro /data`. **At boot**: in **fstab** use `ro` instead of `rw`. **Recovery**: boot single-user or live CD; mount root **ro** to inspect; remount **rw** only if needed for fix. **Read-only root**: some distros support; useful for immutable infra.

---

## Q19. (Advanced) Production scenario: You need to patch 200 servers (security updates) with a 2-hour maintenance window. No orchestration tool. How do you plan and execute with minimal risk?

**Answer:**  
(1) **Staging**: test patch on **staging** first; verify app. (2) **Batches**: group by role (e.g. 20 web, 10 DB); patch **one batch**; verify health before next. (3) **Rolling**: take batch out of LB; patch (`apt update && apt upgrade -y`); reboot if needed; health check; back in LB. (4) **Script**: loop over host list; SSH, patch, reboot (if needed), wait, health check; **abort** batch on failure. (5) **Rollback**: keep list of packages; reinstall previous versions if critical issue. **Document** and use **maintenance window** comms.

---

## Q20. (Advanced) Senior red flags to avoid in system administration

**Answer:**  
- **Manual one-off** changes without docs or automation.  
- **No backup** before major changes or patches.  
- **Patching** all servers at once (no rolling, no staging).  
- **Root** or shared accounts for daily ops.  
- **No log rotation** or **resource limits** (ulimit, cgroups).  
- **Ignoring** time sync (NTP) in distributed setups.  
- **No monitoring** (disk, load, service health).  
- **Weak** or password-based SSH (prefer keys, disable password).

---

**Tradeoffs:** Startup: manual + scripts. Medium: config management, monitoring, backups. Enterprise: automation, patch policy, audit, least privilege.
