docker exec mcp-admin python -c "
import json, os
d = '/app/configs'
for f in sorted(os.listdir(d))[:3]:
    path = os.path.join(d, f)
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            json.load(fp)
        print(f'{f}: OK')
    except Exception as e:
        print(f'{f}: FAIL - {e}')
" > /home/pxy/debug.log 2>&1

cat /home/pxy/debug.log
