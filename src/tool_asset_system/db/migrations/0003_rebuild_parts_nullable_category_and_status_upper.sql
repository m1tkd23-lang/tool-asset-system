-- 0003_rebuild_parts_nullable_category_and_status_upper.sql
PRAGMA foreign_keys = OFF;

BEGIN;

-- 既存partsを退避
ALTER TABLE parts RENAME TO parts_old;

-- 新partsを作成（category_code を NULL 可に）
CREATE TABLE parts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  asset_code TEXT NOT NULL UNIQUE,

  layer_code TEXT NOT NULL,
  category_code TEXT,                 -- NULL 許可（layer.allow_free_category=1 の時だけ許容は TRIGGER で担保）
  category_free_text TEXT,

  part_no TEXT NOT NULL,

  maker TEXT NOT NULL,
  maker_part_name TEXT,

  display_name TEXT NOT NULL,

  stock_qty REAL NOT NULL DEFAULT 0,
  stock_unit TEXT NOT NULL DEFAULT 'EA',

  pack_qty REAL,
  unit_price REAL,
  supplier TEXT,
  lead_time_days INTEGER,
  min_stock_qty REAL,

  status TEXT NOT NULL DEFAULT 'ACTIVE',  -- 大文字に統一
  note TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  UNIQUE(maker, part_no)
);

-- データ移行（status を大文字化）
INSERT INTO parts(
  id,
  asset_code,
  layer_code, category_code, category_free_text,
  part_no,
  maker, maker_part_name,
  display_name,
  stock_qty, stock_unit,
  pack_qty, unit_price, supplier, lead_time_days, min_stock_qty,
  status, note,
  created_at, updated_at
)
SELECT
  id,
  asset_code,
  layer_code, category_code, category_free_text,
  part_no,
  maker, maker_part_name,
  display_name,
  stock_qty, stock_unit,
  pack_qty, unit_price, supplier, lead_time_days, min_stock_qty,
  UPPER(COALESCE(status, 'ACTIVE')) AS status,
  note,
  created_at, updated_at
FROM parts_old;

DROP TABLE parts_old;

-- インデックス復元
CREATE INDEX IF NOT EXISTS idx_parts_layer  ON parts(layer_code);
CREATE INDEX IF NOT EXISTS idx_parts_cat    ON parts(category_code);
CREATE INDEX IF NOT EXISTS idx_parts_maker  ON parts(maker);
CREATE INDEX IF NOT EXISTS idx_parts_partno ON parts(part_no);

COMMIT;

PRAGMA foreign_keys = ON;
