PRAGMA foreign_keys = ON;

-- レイヤー辞書
CREATE TABLE IF NOT EXISTS layers (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  sort_order INTEGER NOT NULL,
  allow_free_category INTEGER NOT NULL DEFAULT 0  -- 0/1
);

-- カテゴリ辞書（レイヤー配下）
CREATE TABLE IF NOT EXISTS categories (
  code TEXT PRIMARY KEY,
  layer_code TEXT NOT NULL,
  label TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,

  -- FKは付けても良いが、まずは運用優先で付けない選択もOK
  FOREIGN KEY(layer_code) REFERENCES layers(code) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_categories_layer ON categories(layer_code);

-- レイヤー投入（あなた指定の順）
INSERT OR IGNORE INTO layers(code,label,sort_order,allow_free_category) VALUES
('HOLDER','ホルダー',10,0),
('TOOL_BODY','カッターボディ',20,0),
('INSERT','インサート',30,0),
('SOLID_TOOL','ソリッド工具',40,0),
('SUB_HOLDER','サブホルダー',50,0),
('SCREW','ねじ・クランプ',60,1),
('ACCESSORY','付属品',70,1);

-- 採番初期値（必要なレイヤーだけ入れてOK）
INSERT OR IGNORE INTO id_sequences(layer_code,next_no) VALUES
('HOLDER',1),
('TOOL_BODY',1),
('INSERT',1),
('SOLID_TOOL',1),
('SUB_HOLDER',1),
('SCREW',1),
('ACCESSORY',1);

-- カテゴリ最小セット例（まずは最小。増やすのはINSERT追加だけ）
INSERT OR IGNORE INTO categories(code,layer_code,label,sort_order) VALUES
('MILLING_INSERT','INSERT','ミーリング用インサート',10),
('TURNING_INSERT','INSERT','旋削用インサート',20),

('MODULAR_HEAD','TOOL_BODY','モジュラーヘッド',10),
('MILLING_BODY','TOOL_BODY','ミーリングカッターボディ',20),

('COLLET_CHUCK','HOLDER','コレットチャック',10),
('HYD_CHUCK','HOLDER','ハイドロチャック',20),

('SOLID_ENDMILL','SOLID_TOOL','ソリッドエンドミル',10),
('SOLID_DRILL','SOLID_TOOL','ソリッドドリル',20);
