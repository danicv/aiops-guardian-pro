from pathlib import Path
import json, py_compile
root=Path(__file__).resolve().parents[1]; errors=[]
for p in root.rglob('*.py'):
    try: py_compile.compile(str(p),doraise=True)
    except Exception as e: errors.append(f'Python {p}: {e}')
for p in root.rglob('*.json'):
    try: json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'JSON {p}: {e}')
for rel in ['README.md','frontend/package.json','backend/app/orchestrator.py','mcp-server/server.py','infra/terraform/main.tf','observability/otel/otel-sidecar.yaml','docs/architecture.md']:
    if not (root/rel).exists(): errors.append(f'Missing {rel}')
if errors:
    print('\n'.join(errors)); raise SystemExit(1)
print('Static project validation passed.')
