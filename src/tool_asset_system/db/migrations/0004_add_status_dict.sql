-- 0004_add_status_dict.sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS statuses (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1
);

INSERT OR IGNORE INTO statuses(code,label,sort_order,is_active) VALUES
('ACTIVE','運用中',10,1),
('ARCHIVED','参照のみ（論理削除）',20,1),
('OBSOLETE','廃番',30,1),
('PROVISIONAL','暫定',40,1);
