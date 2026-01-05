-- 0001_create_core_tables.sql
PRAGMA foreign_keys = ON;
BEGIN;

-- =========================
-- Parts
-- =========================
CREATE TABLE parts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  layer_code TEXT NOT NULL,
  category_code TEXT,
  category_free_text TEXT,

  part_no TEXT NOT NULL,
  display_name TEXT NOT NULL,
  maker TEXT NOT NULL,
  maker_part_name TEXT,

  stock_qty REAL NOT NULL DEFAULT 0,
  stock_unit TEXT NOT NULL DEFAULT 'EA',
  pack_qty REAL,
  unit_price REAL,
  supplier TEXT,
  lead_time_days INTEGER,
  min_stock_qty REAL,

  status TEXT NOT NULL DEFAULT 'active',
  note TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  UNIQUE(part_no, maker)
);

-- =========================
-- Assemblies
-- =========================
CREATE TABLE assemblies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  assembly_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,

  tool_diameter REAL,
  tool_length REAL,

  status TEXT NOT NULL DEFAULT 'active',
  note TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- Assembly BOM
-- =========================
CREATE TABLE assembly_parts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  assembly_id INTEGER NOT NULL,
  part_id INTEGER NOT NULL,
  quantity REAL NOT NULL DEFAULT 1,
  role TEXT,

  FOREIGN KEY(assembly_id) REFERENCES assemblies(id) ON DELETE CASCADE,
  FOREIGN KEY(part_id) REFERENCES parts(id) ON DELETE RESTRICT,

  UNIQUE(assembly_id, part_id)
);

-- =========================
-- Stock logs
-- =========================
CREATE TABLE stock_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  part_id INTEGER NOT NULL,
  delta_qty REAL NOT NULL,
  reason TEXT,
  ref TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY(part_id) REFERENCES parts(id) ON DELETE RESTRICT
);

-- =========================
-- Mark migration
-- =========================
INSERT INTO schema_migrations(version)
VALUES ('0001_create_core_tables');

COMMIT;
