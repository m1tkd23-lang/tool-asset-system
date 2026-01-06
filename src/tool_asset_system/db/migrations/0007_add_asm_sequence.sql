-- 0007_add_asm_sequence.sql
PRAGMA foreign_keys = ON;

-- assemblies 用の採番を id_sequences に統一
-- assembly_code は ASM_00000001 形式
INSERT OR IGNORE INTO id_sequences(layer_code, next_no) VALUES
('ASM', 1);
