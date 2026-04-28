import httpx
import json
# ВПИШИ СВОИ ДАННЫЕ ↓↓↓
partner = "700mJof3FEjjw2Kj9f3I"
user = "0d6d8a18573c3f74c7a1794181079eb5"
company_id = "486659"

phone = "79960418888"
# ВПИШИ СВОИ ДАННЫЕ ↑↑↑

BASE = "https://api.yclients.com/api/v1"



headers = {
    "Authorization": f"Bearer {partner}, User {user}",
    "Accept": "application/vnd.api.v2+json",
    "Content-Type": "application/json",
}

r = httpx.get(
    f"https://api.yclients.com/api/v1/company/{company_id}/staff",
    headers=headers,
)
 
print(f"Status: {r.status_code}\n")
 
if r.status_code != 200:
    print(r.text[:500])
    exit(1)
 
staff = r.json().get("data", [])
print(f"Всего мастеров: {len(staff)}\n")
 
# Полная информация — чтобы понять, кто есть кто
print("=" * 70)
print("ДЕТАЛЬНО (для справки):")
print("=" * 70)
for s in staff:
    fired = " [УВОЛЕН]" if s.get("fired") else ""
    hidden = " [СКРЫТ]" if s.get("hidden") else ""
    spec = s.get("specialization", "") or ""
    print(f"  id={s['id']:>8}  name={s.get('name', ''):<30}  spec={spec}{fired}{hidden}")
 
# Заготовка для config.py — копируешь и правишь имена
print("\n" + "=" * 70)
print("ШАБЛОН ДЛЯ config.py (скопируй и впиши имена для опроса):")
print("=" * 70)
print()
print("STAFF_NAMES = {")
for s in staff:
    if s.get("fired") or s.get("hidden"):
        continue  # пропускаем уволенных и скрытых
    print(f"    {s['id']}: \"\",  # {s.get('name', '')}")
print("}")