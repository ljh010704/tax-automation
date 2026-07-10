import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\tax-automation\gui\entity_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()
print(content[:3000])
