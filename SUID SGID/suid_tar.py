# !/usr/bin/env python3
import os, subprocess

# Этот скрипт запускается с правами root из‑за SUID‑бита, но очищает аргументы и не задаёт полные пути (возможна подстановка)
subprocess.call("tar -cf /tmp/backup.tar /home/user", shell=True)