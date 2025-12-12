DRF Task Balancer

Тестовий проєкт на Django+DRF для розподілу задач між виконавцями з урахуванням пріоритетів та авто‑масштабуванням воркерів.

## First step

```
docker compose up --build
```

### URL
- Swagger UI: http://localhost:8000/api/schema/swagger-ui/
- OpenAPI schema (JSON): http://localhost:8000/api/schema/
- Django Admin: http://localhost:8000/admin/

### admin
- Username: `admin`
- Password: `admin`


### seed (демо Worker/Task)
За замовчуванням увімкнено. Керується змінними середовища
- `SEED_ON_START` (1/0, default: 1)
- `SEED_WORKERS` (default: 3)
- `SEED_TASKS` (default: 50)
- `SEED_FLUSH` (1/0, default: 0) — видалити поточні дані перед сідуванням

SEED_WORKERS=5 SEED_TASKS=100 SEED_FLUSH=1 docker compose up --build


## API
- Tasks: `GET/POST /api/tasks/`, `GET /api/tasks/{id}/`, `PATCH /api/tasks/{id}/` (лише `status` з дозволеними переходами)
- Workers: `GET/POST /api/workers/`, `GET /api/workers/{id}/`, `PATCH /api/workers/{id}/` (лише `max_concurrent_tasks`)
- Stats:
  - `GET /api/stats/summary/` — кількість задач за статусами
  - `GET /api/stats/workers/` — воркери з поточним навантаженням

## Тести
```
pytest -q
```
