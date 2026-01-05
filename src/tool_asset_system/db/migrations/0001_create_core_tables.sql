-- 0001_create_core_tables.sql

PRAGMA foreign_keys = ON;

-- migration管理
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- レイヤーごとの採番
CREATE TABLE IF NOT EXISTS id_sequences (
  layer_code TEXT PRIMARY KEY,
  next_no INTEGER NOT NULL
);

-- パーツ（ホルダー、カッターボディ、インサート、ねじ等の単品）
CREATE TABLE IF NOT EXISTS parts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- 例: INSERT-00000012
  asset_code TEXT NOT NULL UNIQUE,

  -- 辞書コード（DB辞書に存在する想定だが、FKはまだ強制しない）
  layer_code TEXT NOT NULL,
  category_code TEXT NOT NULL,
  category_free_text TEXT,

  -- 型番（メーカー型番）
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

  status TEXT NOT NULL DEFAULT 'active',
  note TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- 同一メーカー同一型番は一意にしたい（運用に合うなら）
  UNIQUE(maker, part_no)
);

CREATE INDEX IF NOT EXISTS idx_parts_layer  ON parts(layer_code);
CREATE INDEX IF NOT EXISTS idx_parts_cat    ON parts(category_code);
CREATE INDEX IF NOT EXISTS idx_parts_maker  ON parts(maker);
CREATE INDEX IF NOT EXISTS idx_parts_partno ON parts(part_no);

-- アセンブリ（工具セット：ホルダー+サブホルダー+ボディ+インサート等）
CREATE TABLE IF NOT EXISTS assemblies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- 例: ASM-00000001（※採番は別途でもOK）
  assembly_code TEXT NOT NULL UNIQUE,

  display_name TEXT NOT NULL,

  -- CAM/シミュ連携用の最低限メタ
  tool_overall_length REAL,   -- 全長
  tool_diameter REAL,         -- 呼び径（必要なら）
  note TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- アセンブリを構成する部品（数量も持てる）
CREATE TABLE IF NOT EXISTS assembly_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  assembly_id INTEGER NOT NULL,
  part_id INTEGER NOT NULL,
  qty REAL NOT NULL DEFAULT 1,
  role TEXT, -- HOLDER / SUB_HOLDER / BODY / INSERT / SCREW など（自由記述でOK）
  note TEXT,

  FOREIGN KEY(assembly_id) REFERENCES assemblies(id) ON DELETE CASCADE,
  FOREIGN KEY(part_id) REFERENCES parts(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_assembly_items_asm  ON assembly_items(assembly_id);
CREATE INDEX IF NOT EXISTS idx_assembly_items_part ON assembly_items(part_id);
