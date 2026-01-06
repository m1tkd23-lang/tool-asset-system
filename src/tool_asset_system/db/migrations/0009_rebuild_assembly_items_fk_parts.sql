-- 0009_rebuild_assembly_items_fk_parts.sql
PRAGMA foreign_keys = OFF;
BEGIN;

ALTER TABLE assembly_items RENAME TO assembly_items_old;

CREATE TABLE assembly_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  assembly_id INTEGER NOT NULL,
  part_id INTEGER NOT NULL,
  qty REAL NOT NULL DEFAULT 1,
  role TEXT,
  note TEXT,

  FOREIGN KEY(assembly_id) REFERENCES assemblies(id) ON DELETE CASCADE,
  FOREIGN KEY(part_id) REFERENCES parts(id) ON DELETE RESTRICT
);

INSERT INTO assembly_items(
  id, assembly_id, part_id, qty, role, note
)
SELECT
  id, assembly_id, part_id, qty, role, note
FROM assembly_items_old;

DROP TABLE assembly_items_old;

CREATE INDEX IF NOT EXISTS idx_assembly_items_asm  ON assembly_items(assembly_id);
CREATE INDEX IF NOT EXISTS idx_assembly_items_part ON assembly_items(part_id);

COMMIT;
PRAGMA foreign_keys = ON;
