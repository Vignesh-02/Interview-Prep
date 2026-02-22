# 12. Configuration Management (Ansible)

## Q1. (Beginner) What is configuration management? What problem does it solve?

**Answer:**  
**Config management**: **automate** **configuration** of **servers** (packages, files, services) from **declarative** definitions. **Solves**: **consistency** (no manual drift); **repeatability**; **documentation** (code); **scale** (many servers). **Tools**: Ansible, Chef, Puppet.

---

## Q2. (Beginner) What is the difference between Ansible and Terraform? When would you use both?

**Answer:**  
**Terraform**: **provision** **infra** (VMs, networks, buckets); **cloud** APIs. **Ansible**: **configure** **inside** (packages, files, users); **SSH** or **agentless**. **Use both**: **Terraform** to **create** instances; **Ansible** to **configure** them (or **packer** for image). **Alternative**: **Terraform** + **user_data** or **config** in image (Packer + Ansible).

---

## Q3. (Beginner) What is an Ansible playbook vs role? What is an inventory?

**Answer:**  
**Playbook**: **YAML** file; **list** of **plays** (hosts + **tasks**). **Role**: **reusable** unit (tasks, vars, templates); **called** from playbook. **Inventory**: **list** of **hosts** (and **groups**); **vars** per host/group. **Use** roles for **reuse** (e.g. "nginx" role).

---

## Q4. (Beginner) How do you run a playbook against a specific host group? How do you limit to one host?

**Answer:**  
**Group**: playbook **hosts: web** (runs on **web** group). **Limit**: `ansible-playbook play.yml --limit hostname` or `--limit "web[0]"`. **Ad-hoc**: `ansible web -m ping` or `ansible web -a "systemctl status nginx"`.

---

## Q5. (Intermediate) Write a minimal Ansible task that installs nginx and ensures it is started and enabled.

**Answer:**
```yaml
- name: Install and start nginx
  ansible.builtin.package:
    name: nginx
    state: present
  become: yes
- name: Enable and start nginx
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: yes
  become: yes
```

---

## Q6. (Intermediate) What is Ansible idempotency? Why is it important?

**Answer:**  
**Idempotency**: **running** the same playbook **multiple** times has the **same** effect as **once**; **no** duplicate or **wrong** state. **How**: **modules** are **designed** that way (e.g. **package** state=present; **file** state=directory). **Important**: **safe** re-runs; **recovery**; **no** "only run once" hacks. **Avoid** **shell** for things a **module** can do (shell may not be idempotent).

---

## Q7. (Intermediate) What are Ansible facts? How do you use them in a playbook?

**Answer:**  
**Facts**: **gathered** info about host (OS, IP, memory); **ansible_facts** or **vars** (e.g. `ansible_distribution`, `ansible_default_ipv4.address`). **Use**: **condition** (`when: ansible_os_family == "Debian"`), **templates** (`{{ ansible_hostname }}`). **Gather**: **gather_facts: yes** (default); **disable** with **gather_facts: no** if not needed (faster).

---

## Q8. (Intermediate) What is an Ansible vault? How do you encrypt a vars file and use it in a play?

**Answer:**  
**Vault**: **encrypt** **sensitive** files (vars, playbooks). **Encrypt**: `ansible-vault encrypt secrets.yml`; **edit**: `ansible-vault edit secrets.yml`. **Use**: `ansible-playbook play.yml --ask-vault-pass` or **env** `ANSIBLE_VAULT_PASSWORD_FILE`. **In play**: **vars_files** with vault file; **vars** are **decrypted** at runtime. **CI**: **password** from **secret** store.

---

## Q9. (Intermediate) How do you run a task only on a specific OS (e.g. install package for Debian vs RHEL)?

**Answer:**  
**when**: `when: ansible_os_family == "Debian"` (use **package** module with **name**; **package** maps to apt/yum). **Or** **block** with **when**; **or** **include_tasks** per OS. **Example**:
```yaml
- name: Install on Debian
  ansible.builtin.apt:
    name: nginx
    state: present
  when: ansible_os_family == "Debian"
  become: yes
- name: Install on RHEL
  ansible.builtin.yum:
    name: nginx
    state: present
  when: ansible_os_family == "RedHat"
  become: yes
```

---

## Q10. (Intermediate) What is an Ansible handler? When is it run?

**Answer:**  
**Handler**: **task** that runs only when **notified** (e.g. "restart nginx"); **run** at **end** of play (per host), **once** per handler even if **notified** multiple times. **Use**: **restart** service when **config** **changes** (notify from **template** or **copy** task). **Flush**: **meta: flush_handlers** to run **mid-play** if needed.

---

## Q11. (Advanced) Production scenario: You need to patch 100 servers (apt update, upgrade) and restart only if kernel was updated. How do you design the playbook?

**Answer:**  
(1) **Tasks**: **apt update**; **apt upgrade** with **cache_valid_time** (optional). (2) **Check** if **kernel** upgraded: **register** output of **apt list --upgradable** or **check** if **/boot** changed; **notify** **handler** "reboot if kernel". (3) **Handler**: **reboot** (with **wait_for** to come back) or **notify** team for **manual** window. (4) **Batch**: **serial** (e.g. 10 at a time) to avoid **all** rebooting at once. **Example**: use **apt** module; **register**; **when** kernel in list → **notify** reboot handler; **serial: 10**.

---

## Q12. (Advanced) What is Ansible dynamic inventory? When would you use it?

**Answer:**  
**Dynamic inventory**: **script** or **plugin** that **returns** **inventory** **JSON** from **source** (e.g. **AWS** EC2, **K8s**). **Use**: **cloud** or **CMDB** as **source of truth**; **no** manual **host** list; **tags**/labels for **groups**. **AWS**: **ec2.py** or **aws_ec2** plugin; **groups** by **tag**. **Use** when **hosts** **change** often (auto-scaling).

---

## Q13. (Advanced) How do you avoid Ansible overwriting local changes (e.g. a config file that admins sometimes edit)?

**Answer:**  
(1) **Don’t** manage that file in Ansible (manage **only** what you own). (2) **Template** to **different** file; **copy** to **actual** if **not** present (first run only). (3) **Backup**: **backup=yes** on **copy**/template; **restore** from backup if **needed**. (4) **Policy**: **no** manual edit of **managed** files; **override** via **vars** or **override** file. (5) **Check** mode (**--check**) to **preview** changes. **Best**: **centralize** config in Ansible; **discourage** manual edits; **document** override process.

---

## Q14. (Advanced) Production scenario: Playbook runs against 50 hosts; one host fails (e.g. SSH timeout). How do you make the playbook continue and report failures at the end?

**Answer:**  
**ignore_errors: yes** on **critical** task (not ideal — masks real errors). **Better**: **default** is **stop** on first failure per host; **run** with **strategy: free** (parallel) or **max_fail_percentage** to allow **some** failures. **Report**: **register** result; **end** play with **summary** task that **fails** if **any** host had **failed** (loop over hostvars and check **result**). **Blocks**: **rescue** block to **record** failure and **continue**. **Rescue** + **always** to **summary**; **fail** in **always** if **any** failed.

---

## Q15. (Advanced) What is Ansible Galaxy? How do you use a role from Galaxy in a playbook?

**Answer:**  
**Galaxy**: **repository** of **roles** (and collections). **Install**: `ansible-galaxy role install author.role_name` or **requirements.yml** with **roles**; `ansible-galaxy install -r requirements.yml`. **Use**: **roles:** in playbook: `- author.role_name` or **role** in **tasks**. **Collections**: `ansible-galaxy collection install namespace.collection`.

---

## Q16. (Advanced) How do you test Ansible playbooks (e.g. in CI) without touching production?

**Answer:**  
(1) **Check mode**: `ansible-playbook play.yml --check --diff` (dry-run). (2) **Molecule**: **test** roles with **containers** or **VMs**; **converge** then **verify** (testinfra). (3) **CI**: run **against** **staging** or **test** inventory. (4) **Lint**: **ansible-lint**. **Best**: **Molecule** for **roles**; **staging** run for **full** playbook; **lint** in CI.

---

## Q17. (Advanced) What is the difference between Ansible pull and push mode? When would you use pull?

**Answer:**  
**Push**: **control** node **SSH** to hosts and **runs** tasks (default). **Pull**: **hosts** **run** **ansible-pull** (cron or systemd); **pull** playbook from **Git** and **run** **locally**. **Use pull**: **ephemeral** or **no** stable **control** node; **scale** (no SSH from one place). **Tradeoff**: **push** = central **control**; **pull** = **decentralized**, **simpler** network.

---

## Q18. (Advanced) Production scenario: You need to deploy an app (copy artifact, install deps, restart systemd service) to 3 tiers (web, app, db) with different config per tier. How do you structure inventory and playbook?

**Answer:**  
**Inventory**: **groups** web, app, db; **group_vars**: `web.yml`, `app.yml`, `db.yml` (e.g. **app_port**, **env**). **Playbook**: **one** play with **hosts: all** and **roles** (e.g. **app** role); **role** uses **vars** (from **group_vars**). **Or** **separate** plays per group with **vars**. **Artifact**: **delegate_to** or **fetch** from **build** host; **copy** to **each** host. **Service**: **template** unit or **copy** config; **notify** **handler** restart. **Result**: **one** playbook; **different** **vars** per **group**.

---

## Q19. (Advanced) How do you ensure secrets (e.g. DB URL) in Ansible are not logged or exposed?

**Answer:**  
(1) **Vault** for **vars** files; **no_log: yes** on **tasks** that use **sensitive** vars (suppress **task** output). (2) **Vars** with **sensitive** name (e.g. **db_password**) may be **masked** in **newer** Ansible. (3) **Vault** from **CI** (password from secret store). (4) **Don’t** pass **secrets** as **cli** **extra vars** in **plain** text. (5) **Consider** **external** (Vault, cloud) and **fetch** in **task** (e.g. **uri** to Vault); **don’t** store in **repo** even **encrypted** if policy says no.

---

## Q20. (Advanced) Senior red flags to avoid with Ansible

**Answer:**  
- **Non-idempotent** tasks (raw shell for config; use **modules**).  
- **Secrets** in **plain** vars or **repo** (use **vault** or **external**).  
- **No** **handlers** for **restart** (config change without restart).  
- **Running** as **root** everywhere (use **become** only where needed).  
- **No** **tags** or **limits** (can’t run **subset**).  
- **Huge** monolithic playbook (use **roles**).  
- **No** **testing** (lint, Molecule, staging).  
- **Ignoring** **failures** without **reporting** (no **rescue**/summary).

---

**Tradeoffs:** Startup: ad-hoc or simple playbook. Medium: roles, vault, staging. Enterprise: dynamic inventory, CI, Molecule, separate envs.
