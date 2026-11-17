# Docker-POC

React (frontend) → Flask (API) → MySQL (DB), each running in its own container.

| Part | Folder | Image | Pushed to ECR? |
|---|---|---|---|
| Frontend | `frontend/` | `frontend:v1` (React built, served by nginx) | Yes |
| API | `api/` | `api:v1` (Flask + gunicorn) | Yes |
| DB | — | Official `mysql:8.0` | No (RDS in AWS) |

---

## Running the API locally

```
docker run -d                           → container in the background
  --name api                            → container name
  --network poc-net                     → same network as db
  -p 5000:5000                          → PC 5000 → container 5000
  -e DB_HOST=db                         → MySQL container name (the building)
  -e DB_USER=appuser                    → MySQL user
  -e DB_PASSWORD=apppass                → MySQL password
  -e DB_NAME=appdb                      → database inside MySQL (the room)
  -e CORS_ORIGINS=http://localhost:3000 → allow the frontend page
  api:v1                                → image to run
```

---

## How the API connects to the DB in AWS (RDS created by Terraform)

The API connects to RDS **the same way it connects to the local MySQL container: through the `DB_*` environment variables.**
Only the values change. The `api:v1` image and the code stay the same. This is why `app.py` uses `os.getenv(...)` instead of hardcoded values.

### Local vs AWS

| Env var | Local (Docker) | AWS (RDS via Terraform) |
|---|---|---|
| `DB_HOST` | `db` (container name) | RDS endpoint, e.g. `poc-db.abc123.ap-south-1.rds.amazonaws.com` |
| `DB_PORT` | `3306` | `3306` |
| `DB_NAME` | `appdb` | `appdb` |
| `DB_USER` | `appuser` | `appuser` |
| `DB_PASSWORD` | `apppass` (typed in the command) | Stored in **AWS Secrets Manager**, never typed by hand |

### 1. Terraform creates RDS and outputs its address

```hcl
resource "aws_db_instance" "mysql" {
  identifier                  = "poc-db"
  engine                      = "mysql"
  engine_version              = "8.0"
  instance_class              = "db.t3.micro"
  allocated_storage           = 20
  db_name                     = "appdb"      # like MYSQL_DATABASE
  username                    = "appuser"    # like MYSQL_USER
  manage_master_user_password = true         # AWS generates the password and stores it in Secrets Manager
  vpc_security_group_ids      = [aws_security_group.rds.id]
  db_subnet_group_name        = aws_db_subnet_group.private.name
  publicly_accessible         = false        # not reachable from the internet
}

output "db_endpoint" {
  value = aws_db_instance.mysql.address      # this becomes DB_HOST
}
```

### 2. Networking: security group (replaces `--network poc-net`)

RDS sits in a **private subnet**. Its security group allows port 3306 **only from the API**:

```hcl
resource "aws_security_group_rule" "api_to_rds" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds.id
  source_security_group_id = aws_security_group.api.id   # only the API can connect
}
```

### 3. Password in Secrets Manager

Nobody writes the DB password in code, Git or commands. AWS/Terraform stores it in **Secrets Manager**.

### 4. Values passed into the API container (replaces `-e`)

- **ECS:** the task definition sets `DB_HOST` = RDS endpoint and reads `DB_PASSWORD` from Secrets Manager.
- **EKS (Kubernetes):** a `ConfigMap` holds `DB_HOST`, a `Secret` holds `DB_PASSWORD` (often synced from Secrets Manager with External Secrets Operator), and the Deployment passes them to the pod as env vars.

### The full picture

```
Terraform creates:  RDS MySQL  +  security group  +  secret
                        │               │                │
                   endpoint        allows API       password
                        ▼               ▼                ▼
API container  ◀── DB_HOST       (network access)   DB_PASSWORD
(same api:v1 image built locally)
```

### Local → AWS mapping

| Local | AWS |
|---|---|
| Container name `db` | RDS endpoint |
| `-e DB_PASSWORD=...` | Secrets Manager |
| `-e ...` in `docker run` | ECS task definition / Kubernetes ConfigMap + Secret |
| `--network poc-net` | VPC + security group |
| Workbench → `localhost:3307` | Workbench → bastion host (SSH tunnel) → RDS |

---

## Note: creating tables

In this POC, the API creates the `items` table at startup (`init_db()` in `app.py`). This is a shortcut.
In industry, tables are created and changed with **database migrations**: versioned SQL files kept in Git (e.g. **Alembic** for Flask), run as a CI/CD step before deploying a new API version. Changes are not made by hand in Workbench.
