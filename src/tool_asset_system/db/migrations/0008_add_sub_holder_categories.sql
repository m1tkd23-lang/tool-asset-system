-- 0008_add_sub_holder_categories.sql
PRAGMA foreign_keys = ON;

-- SUB_HOLDER 用カテゴリ（最小構成）
INSERT OR IGNORE INTO categories(code, layer_code, label, sort_order) VALUES
('SUBHOLDER_SHANK',  'SUB_HOLDER', 'シャンク', 10),
('SUBHOLDER_ARBOR',  'SUB_HOLDER', 'アーバー', 20);
