CREATE TABLE diary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    category TEXT,
    created_at TEXT
);

-- Tạo bảng ảo FTS5 để tìm kiếm toàn văn bản
CREATE VIRTUAL TABLE diary_fts USING fts5(
    title,
    content,
    content='diary',
    content_rowid='id'
);

-- Trigger để cập nhật bảng ảo khi có bản ghi mới
CREATE TRIGGER diary_ai AFTER INSERT ON diary BEGIN
    INSERT INTO diary_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
END;

-- Trigger để cập nhật bảng ảo khi sửa bản ghi
CREATE TRIGGER diary_au AFTER UPDATE ON diary BEGIN
    UPDATE diary_fts SET title = new.title, content = new.content WHERE rowid = old.id;
END;

-- Trigger để xóa bản ghi khỏi bảng ảo
CREATE TRIGGER diary_ad AFTER DELETE ON diary BEGIN
    DELETE FROM diary_fts WHERE rowid = old.id;
END;