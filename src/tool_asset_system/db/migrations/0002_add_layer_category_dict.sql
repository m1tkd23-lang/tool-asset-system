-- 0002_add_layer_category_dict.sql
PRAGMA foreign_keys = ON;
BEGIN;

-- =========================
-- Layer dictionary
-- =========================
CREATE TABLE layers (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  sort_order INTEGER NOT NULL,
  allow_free_category INTEGER NOT NULL DEFAULT 0,
  note TEXT
);

-- =========================
-- Category dictionary
-- =========================
CREATE TABLE categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  layer_code TEXT NOT NULL,
  code TEXT NOT NULL,
  label TEXT NOT NULL,
  sort_order INTEGER NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1,

  FOREIGN KEY(layer_code) REFERENCES layers(code)
    ON UPDATE CASCADE ON DELETE CASCADE,

  UNIQUE(layer_code, code)
);

-- =========================
-- Seed layers (FIXED ORDER)
-- =========================
INSERT INTO layers(code,label,sort_order,allow_free_category) VALUES
 ('HOLDER',      'ホルダー',         10, 0),
 ('TOOL_BODY',   'カッターボディ',   20, 0),
 ('INSERT',      'インサート',       30, 0),
 ('SOLID_TOOL',  'ソリッド工具',     40, 0),
 ('SUB_HOLDER',  'サブホルダー',     50, 0),
 ('SCREW',       'ねじ・クランプ',   60, 1),
 ('ACCESSORY',   '付属品',           70, 1);

-- =========================
-- Seed categories
-- =========================

-- INSERT
INSERT INTO categories(layer_code,code,label,sort_order) VALUES
 ('INSERT','MILLING_INSERT','ミーリング用',10),
 ('INSERT','TURNING_INSERT','旋削用',20),
 ('INSERT','DRILL_INSERT','穴あけ用',30);

-- TOOL_BODY
INSERT INTO categories(layer_code,code,label,sort_order) VALUES
 ('TOOL_BODY','MODULAR_HEAD','モジュラーヘッド',10),
 ('TOOL_BODY','FACE_MILL_BODY','フェイスミル',20);

-- SOLID_TOOL
INSERT INTO categories(layer_code,code,label,sort_order) VALUES
 ('SOLID_TOOL','END_MILL','エンドミル',10),
 ('SOLID_TOOL','DRILL','ドリル',20),
 ('SOLID_TOOL','REAMER','リーマ',30);

-- HOLDER
INSERT INTO categories(layer_code,code,label,sort_order) VALUES
 ('HOLDER','HSK_HOLDER','HSKホルダー',10),
 ('HOLDER','BT_HOLDER','BTホルダー',20);

-- =========================
-- Mark migration
-- =========================
INSERT INTO schema_migrations(version)
VALUES ('0002_add_layer_category_dict');

COMMIT;
