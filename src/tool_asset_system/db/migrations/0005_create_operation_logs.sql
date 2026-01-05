-- 0005_create_operation_logs.sql

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS operation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  action TEXT NOT NULL,                 -- e.g. PART_UPDATE / PART_ARCHIVE / PART_ADD
  target_type TEXT NOT NULL,            -- e.g. PART
  target_code TEXT NOT NULL,            -- e.g. INSERT_00000001

  actor TEXT NOT NULL DEFAULT 'unknown', -- CLIなら username / os.getlogin など

  reason TEXT,                          -- archive理由など
  patch_json TEXT,                      -- 変更内容（入力）
  before_json TEXT,                     -- 変更前スナップショット
  after_json TEXT,                      -- 変更後スナップショット

  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_operation_logs_target
  ON operation_logs(target_type, target_code);

CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at
  ON operation_logs(created_at);
