#!/bin/bash
cd /app/
python3 init_sys.py
python3 main.py -job True -init True
# 执行一些操作...
while true; do
  sleep 10
done