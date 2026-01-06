-- 0010_create_tooling_lists.sql

PRAGMA foreign_keys = ON;

-- ツーリングリスト（ワーク単位の工具セット）
CREATE TABLE IF NOT EXISTS tooling_lists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- 例: TL_00000001（採番は id_sequences を使用）
  list_code TEXT NOT NULL UNIQUE,

  title TEXT NOT NULL,
  note TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ツーリングリストの中身（ASM + tool_no）
CREATE TABLE IF NOT EXISTS tooling_list_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  tooling_list_id INTEGER NOT NULL,
  assembly_id INTEGER NOT NULL,

  -- ポケット番号（01/100/T12など運用自由）→ TEXT推奨
  tool_no TEXT NOT NULL,

  qty REAL NOT NULL DEFAULT 1,
  note TEXT,

  FOREIGN KEY(tooling_list_id) REFERENCES tooling_lists(id) ON DELETE CASCADE,
  FOREIGN KEY(assembly_id) REFERENCES assemblies(id) ON DELETE RESTRICT,

  UNIQUE(tooling_list_id, assembly_id),
  UNIQUE(tooling_list_id, tool_no)
);

CREATE INDEX IF NOT EXISTS idx_tooling_list_items_list
  ON tooling_list_items(tooling_list_id);

CREATE INDEX IF NOT EXISTS idx_tooling_list_items_asm
  ON tooling_list_items(assembly_id);

-- 採番（TL）
INSERT OR IGNORE INTO id_sequences(layer_code, next_no) VALUES
('TL', 1);
