-- 0006_add_validation_triggers.sql

PRAGMA foreign_keys = ON;

-- category_code NULL許可は layer.allow_free_category=1 の時だけ
CREATE TRIGGER IF NOT EXISTS trg_parts_category_null_allowed_ins
BEFORE INSERT ON parts
FOR EACH ROW
WHEN NEW.category_code IS NULL
BEGIN
  SELECT
    CASE
      WHEN (
        SELECT allow_free_category FROM layers WHERE code = NEW.layer_code
      ) = 1
      THEN NULL
      ELSE RAISE(ABORT, 'category_code is required for this layer')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_parts_category_null_allowed_upd
BEFORE UPDATE OF category_code, layer_code ON parts
FOR EACH ROW
WHEN NEW.category_code IS NULL
BEGIN
  SELECT
    CASE
      WHEN (
        SELECT allow_free_category FROM layers WHERE code = NEW.layer_code
      ) = 1
      THEN NULL
      ELSE RAISE(ABORT, 'category_code is required for this layer')
    END;
END;

-- category_code があるなら辞書に存在し、layer_code と一致すること
CREATE TRIGGER IF NOT EXISTS trg_parts_category_exists_ins
BEFORE INSERT ON parts
FOR EACH ROW
WHEN NEW.category_code IS NOT NULL
BEGIN
  SELECT
    CASE
      WHEN EXISTS(
        SELECT 1 FROM categories
        WHERE code = NEW.category_code AND layer_code = NEW.layer_code
      )
      THEN NULL
      ELSE RAISE(ABORT, 'category_code not found in categories for the given layer')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_parts_category_exists_upd
BEFORE UPDATE OF category_code, layer_code ON parts
FOR EACH ROW
WHEN NEW.category_code IS NOT NULL
BEGIN
  SELECT
    CASE
      WHEN EXISTS(
        SELECT 1 FROM categories
        WHERE code = NEW.category_code AND layer_code = NEW.layer_code
      )
      THEN NULL
      ELSE RAISE(ABORT, 'category_code not found in categories for the given layer')
    END;
END;

-- status は statuses 辞書に存在すること（大文字正規化前提）
CREATE TRIGGER IF NOT EXISTS trg_parts_status_exists_ins
BEFORE INSERT ON parts
FOR EACH ROW
BEGIN
  SELECT
    CASE
      WHEN EXISTS(SELECT 1 FROM statuses WHERE code = NEW.status)
      THEN NULL
      ELSE RAISE(ABORT, 'invalid status')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_parts_status_exists_upd
BEFORE UPDATE OF status ON parts
FOR EACH ROW
BEGIN
  SELECT
    CASE
      WHEN EXISTS(SELECT 1 FROM statuses WHERE code = NEW.status)
      THEN NULL
      ELSE RAISE(ABORT, 'invalid status')
    END;
END;

