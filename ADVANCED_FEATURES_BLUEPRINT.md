# MicroBiz Advanced Features Blueprint

This document turns the 5 requested upgrades into an implementation-ready architecture for the current codebase.

Current baseline:
- Single-tenant data model keyed by `user_id`
- No Alembic revision history yet (`migrations/` is empty)
- Bot stack: `aiogram` + SQLAlchemy + APScheduler

---

## 0) Rollout Strategy

Build in this order to reduce migration risk:

1. Multi-user/tenant foundation (roles + permissions + activity logs)
2. Product profit tracking (sale line items + margin analytics)
3. Invoice/receipt generation
4. Export/backup pipeline
5. Goal tracking and target alerts

Guiding rule:
- Add `business_id` first, backfill it, then enforce `NOT NULL` and tenant-scoped queries.

---

## 1) Multi-User Role System

### 1.1 System logic

- Introduce business workspace tenancy.
- Every command resolves an active business context.
- Authorization is action-based (permission map), not just role string checks.
- Every mutating action writes an activity log entry.

Role matrix:
- `owner`: full access (members, backup, delete, export)
- `manager`: create/update + reports + exports, no destructive actions
- `staff`: sales-only operations

Suggested action map:
- `sale:create` -> owner/manager/staff
- `expense:create`, `inventory:update`, `customer:update`, `report:view`, `analytics:view` -> owner/manager
- `member:manage`, `data:delete`, `backup:manage`, `goal:manage` -> owner

### 1.2 Database schema changes

New tables:

1. `businesses`
- `id` PK
- `name` VARCHAR(200) NOT NULL
- `owner_user_id` FK -> `users.id` NOT NULL
- `currency` VARCHAR(10) DEFAULT 'Rp'
- `timezone` VARCHAR(64) DEFAULT 'UTC'
- `logo_file_id` VARCHAR(255) NULL
- `created_at`, `updated_at`

2. `business_members`
- `id` PK
- `business_id` FK -> `businesses.id` NOT NULL
- `user_id` FK -> `users.id` NOT NULL
- `role` VARCHAR(20) NOT NULL (`owner|manager|staff`)
- `status` VARCHAR(20) DEFAULT 'active'
- `invited_by` FK -> `users.id` NULL
- `created_at`, `updated_at`
- UNIQUE(`business_id`, `user_id`)

3. `activity_logs`
- `id` PK
- `business_id` FK -> `businesses.id` NOT NULL
- `actor_user_id` FK -> `users.id` NOT NULL
- `action` VARCHAR(80) NOT NULL
- `entity_type` VARCHAR(50) NOT NULL
- `entity_id` INTEGER NULL
- `metadata_json` TEXT NULL
- `created_at`

Add to existing tables:
- `sales`, `expenses`, `products`, `customers`, `transactions`
  - `business_id` FK -> `businesses.id` (backfill then NOT NULL)
  - `created_by_user_id` FK -> `users.id` NULL

Optional:
- `users.active_business_id` FK -> `businesses.id`

Indexes:
- `idx_*_business_id` for all tenant tables
- `idx_activity_logs_business_created_at`

### 1.3 Commands

- `/team`
- `/invite <telegram_id> <owner|manager|staff>`
- `/set_role <telegram_id> <owner|manager|staff>`
- `/remove_member <telegram_id>`
- `/activity [limit]`
- `/switch_business` (if multi-business membership exists)

### 1.4 Example flow

Owner:
1. `/invite 123456789 manager`
2. Bot sends: `Invite created. User must run /start to join.`
3. `/team` shows all active members and roles.

Manager attempts owner-only action:
1. `/remove_member 123456789`
2. Bot: `Permission denied: owner required.`

### 1.5 Edge cases

- Block deleting/demoting the last owner.
- Block role changes for non-members.
- Pending invites expire after configured TTL.
- Commands fail fast if active business context missing.

### 1.6 Security considerations

- All queries must include `business_id`.
- Enforce permissions in middleware before handler logic.
- Log all privilege changes in `activity_logs`.
- Redact sensitive data from logs.

---

## 2) Data Export & Backup

### 2.1 System logic

- Export requests create async jobs.
- Worker generates artifacts and sends via Telegram when done.
- Weekly backup job runs per-business with retention policy.
- Backups are encrypted and integrity-checked.

### 2.2 Database schema changes

1. `export_jobs`
- `id` PK
- `business_id` FK NOT NULL
- `requested_by_user_id` FK NOT NULL
- `export_type` VARCHAR(40) NOT NULL (`pdf_report|csv_sales|csv_expenses|csv_inventory|csv_customers`)
- `params_json` TEXT NULL
- `status` VARCHAR(20) NOT NULL (`queued|running|completed|failed`)
- `file_path` TEXT NULL
- `checksum` VARCHAR(128) NULL
- `error_message` TEXT NULL
- `expires_at` DATETIME NULL
- `created_at`, `started_at`, `completed_at`

2. `backup_settings`
- `business_id` PK/FK
- `enabled` BOOLEAN DEFAULT FALSE
- `day_of_week` INTEGER DEFAULT 0
- `time_local` VARCHAR(5) DEFAULT '22:00'
- `retention_days` INTEGER DEFAULT 56
- `destination` VARCHAR(255) DEFAULT 'local'
- `updated_at`

3. `backup_artifacts`
- `id` PK
- `business_id` FK NOT NULL
- `period_start`, `period_end`
- `file_path` TEXT NOT NULL
- `checksum` VARCHAR(128) NOT NULL
- `encrypted` BOOLEAN DEFAULT TRUE
- `created_at`

### 2.3 Commands

- `/export`
- `/export sales csv 2026-03-01 2026-03-31`
- `/export report weekly pdf`
- `/backup_now`
- `/backup_settings`
- `/backup_on <day> <HH:MM>`
- `/backup_off`

### 2.4 Example flow

Manager:
1. `/export sales csv 2026-03-01 2026-03-31`
2. Bot: `Export queued (job #482).`
3. Bot later sends CSV file.

Owner:
1. `/backup_on sunday 22:00`
2. Bot: `Weekly encrypted backup enabled.`

### 2.5 Edge cases

- Empty datasets: export headers-only file.
- Very large exports: stream writer + chunking.
- Duplicate request spam: de-duplicate by request hash window.
- Worker crash: stuck jobs auto-mark `failed` after timeout.

### 2.6 Security considerations

- Export: owner/manager only.
- Backup config: owner only.
- Encrypt backup files at rest.
- Signed temporary links if external storage is used.
- Never include secrets in exported JSON metadata.

---

## 3) Product Profit Tracking

### 3.1 System logic

- Compute profit per sale line, not only per sale total.
- Snapshot cost at sale-time to preserve historical correctness.
- Margin alerts trigger when margin below product threshold.

Formulas:
- `revenue = quantity * unit_price`
- `cogs = quantity * cost_price_snapshot`
- `profit = revenue - cogs`
- `margin_pct = (profit / revenue) * 100` (if `revenue > 0`)

### 3.2 Database schema changes

Enhance `products`:
- `cost_price` FLOAT NULL (or rename `purchase_price` -> `cost_price`)
- `min_margin_pct` FLOAT DEFAULT 10.0

New `sale_items`:
- `id` PK
- `sale_id` FK -> `sales.id` NOT NULL
- `business_id` FK NOT NULL
- `product_id` FK -> `products.id` NULL
- `item_name` VARCHAR(200) NOT NULL
- `quantity` INTEGER NOT NULL
- `unit_price` FLOAT NOT NULL
- `cost_price_snapshot` FLOAT NOT NULL
- `line_revenue` FLOAT NOT NULL
- `line_cogs` FLOAT NOT NULL
- `line_profit` FLOAT NOT NULL
- `margin_pct` FLOAT NOT NULL
- `created_at`

Enhance `sales`:
- `total_revenue` FLOAT NULL
- `total_profit` FLOAT NULL

### 3.3 Commands

- `/set_cost <product> <amount>`
- `/product_profit [today|weekly|monthly|custom]`
- `/top_profit_products [period]`
- `/margin_alerts`
- `/margin_threshold <product> <percent>`

### 3.4 Example flow

Manager:
1. `/set_cost Bread 3500`
2. Staff records: `/sale 3x 5000 Bread`
3. Bot: `Sale saved. Profit: Rp 4,500 (30.0% margin).`
4. Owner: `/top_profit_products monthly`

### 3.5 Edge cases

- Missing cost price: warn and require confirmation.
- Non-catalog item sales: allow with `product_id=NULL`.
- Refunds/returns: support negative quantity or reversal entries.
- Zero or negative revenue lines: guard divide-by-zero in margin.

### 3.6 Security considerations

- Cost updates restricted to owner/manager.
- Profit analytics visibility configurable (owner-only or owner+manager).
- Prevent post-hoc edits to cost snapshots.

---

## 4) Invoice / Receipt Generator

### 4.1 System logic

- On sale commit, generate invoice entity and renderable payload.
- Support output formats: PDF + image.
- Branding fields sourced from business profile (`name`, `logo_file_id`).
- Optional customer phone included when available.

### 4.2 Database schema changes

1. `invoices`
- `id` PK
- `business_id` FK NOT NULL
- `sale_id` FK -> `sales.id` NOT NULL
- `invoice_number` VARCHAR(50) NOT NULL
- `customer_name` VARCHAR(200) NULL
- `customer_phone` VARCHAR(30) NULL
- `subtotal` FLOAT NOT NULL
- `tax` FLOAT DEFAULT 0
- `total` FLOAT NOT NULL
- `currency` VARCHAR(10) NOT NULL
- `status` VARCHAR(20) DEFAULT 'issued' (`issued|void`)
- `pdf_path` TEXT NULL
- `image_path` TEXT NULL
- `created_by_user_id` FK NOT NULL
- `created_at`
- UNIQUE(`business_id`, `invoice_number`)

2. `invoice_items`
- `id` PK
- `invoice_id` FK NOT NULL
- `description` VARCHAR(255) NOT NULL
- `qty` INTEGER NOT NULL
- `unit_price` FLOAT NOT NULL
- `line_total` FLOAT NOT NULL

### 4.3 Commands

- `/invoice <sale_id>`
- `/invoice_last`
- `/invoice_pdf <sale_id>`
- `/invoice_image <sale_id>`
- `/set_business <name>`
- `/set_logo` (photo upload)
- `/receipt_mode <auto|manual>`

### 4.4 Example flow

Staff records a sale:
1. Bot stores sale and invoice draft.
2. Bot asks: `Send receipt? [PDF] [Image] [Skip]`
3. User taps `PDF`.
4. Bot sends branded PDF receipt.

### 4.5 Edge cases

- No logo configured -> text-only template fallback.
- Invalid logo format/size -> validation error.
- Sale voided after invoice -> mark invoice `void`.
- Re-download request -> reuse generated artifact if present.

### 4.6 Security considerations

- Receipt retrieval restricted by `business_id`.
- No raw file-system path disclosure in chat.
- Sanitize text fields to avoid template injection.

---

## 5) Business Goal Tracking

### 5.1 System logic

- One active monthly revenue goal per business per month.
- Progress evaluated daily against expected pace.
- Alert owner/manager when behind threshold.

Core metrics:
- `progress_pct = mtd_revenue / target * 100`
- `expected_pct = elapsed_days / total_days * 100`
- `gap_pct = progress_pct - expected_pct`

### 5.2 Database schema changes

1. `business_goals`
- `id` PK
- `business_id` FK NOT NULL
- `goal_type` VARCHAR(30) NOT NULL (`monthly_revenue`)
- `period_start` DATE NOT NULL
- `period_end` DATE NOT NULL
- `target_amount` FLOAT NOT NULL
- `status` VARCHAR(20) DEFAULT 'active'
- `created_by_user_id` FK NOT NULL
- `created_at`, `updated_at`
- UNIQUE(`business_id`, `goal_type`, `period_start`)

2. `goal_alerts`
- `id` PK
- `goal_id` FK NOT NULL
- `alert_date` DATE NOT NULL
- `alert_type` VARCHAR(20) NOT NULL (`behind|on_track|achieved`)
- `message` TEXT NOT NULL
- `created_at`
- UNIQUE(`goal_id`, `alert_date`, `alert_type`)

Optional optimization:
- `daily_metrics` (`business_id`, `metric_date`, `sales_total`, `expense_total`, `profit_total`)

### 5.3 Commands

- `/goal_set <amount>`
- `/goal_status`
- `/goal_progress`
- `/goal_history`
- `/goal_cancel`

### 5.4 Example flow

Owner:
1. `/goal_set 5000000`
2. Bot: `Goal set: Rp 5,000,000 for March 2026.`
3. `/goal_status`
4. Bot: `Progress 38%, expected 45%, behind by 7%.`
5. Evening alert triggered if still behind.

### 5.5 Edge cases

- Reject non-positive goals.
- If goal is created mid-month, define pace policy explicitly (prorated or full-month).
- Prevent duplicate active monthly goals.
- Handle no-sales scenario with clear guidance.

### 5.6 Security considerations

- Goal set/cancel owner-only.
- Alerts sent only to owner/manager.
- Deduplicate alerts by unique constraint.

---

## 6) Middleware and Service Refactor Plan

### 6.1 New middleware chain

1. `AuthMiddleware`: resolve user
2. `BusinessContextMiddleware`: resolve `active_business_id`
3. `PermissionMiddleware`: enforce action permissions
4. `ActivityMiddleware` (or explicit utility): append logs for writes

### 6.2 Service modules to add

- `app/services/permissions.py`
- `app/services/activity_logger.py`
- `app/services/exporter.py`
- `app/services/backup.py`
- `app/services/invoice_renderer.py`
- `app/services/goals.py`

---

## 7) Alembic Migration Plan (Suggested)

Create sequential revisions:

1. `001_create_businesses_and_members`
2. `002_add_business_id_to_domain_tables_nullable`
3. `003_backfill_business_id_from_user_id`
4. `004_make_business_id_not_null_add_indexes`
5. `005_create_activity_logs`
6. `006_create_sale_items_and_profit_fields`
7. `007_create_invoices_and_invoice_items`
8. `008_create_export_jobs_backup_tables`
9. `009_create_goals_and_goal_alerts`
10. `010_constraints_retention_and_safety_indexes`

For SQLite environments, avoid complex `ALTER` patterns in one step; use table-copy strategy where needed.

---

## 8) Testing Strategy

Add test suites by feature:

- `tests/test_permissions.py`
- `tests/test_activity_logs.py`
- `tests/test_profit_tracking.py`
- `tests/test_invoice_generation.py`
- `tests/test_export_jobs.py`
- `tests/test_goals.py`

Critical regression checks:
- Cross-tenant read/write isolation
- Permission denial for forbidden actions
- Profit snapshot immutability
- Goal alert deduplication

---

## 9) Minimum Viable Deliverables per Sprint

Sprint 1:
- Business tenancy + roles + permission middleware + activity logs

Sprint 2:
- Profit tracking with `sale_items` + analytics command set

Sprint 3:
- Invoice generation + file delivery + business branding

Sprint 4:
- Export jobs + weekly encrypted backups + retention cleanup

Sprint 5:
- Monthly goals + progress/behind alerts + history views

---

## 10) Immediate Next Implementation Task

Start with feature foundation:

1. Add `businesses`, `business_members`, `activity_logs` models
2. Add `business_id` to core domain tables (nullable first)
3. Backfill `business_id` from existing `user_id` ownership
4. Add `BusinessContextMiddleware` + permission checks
5. Update all CRUD filters from `user_id`-only to `business_id`-scoped

Once this is merged, all other features become straightforward extensions.
