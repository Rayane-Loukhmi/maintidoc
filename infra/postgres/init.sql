-- Schéma PostgreSQL MaintiDoc (données de démonstration)
-- Les identifiants sont fictifs.

CREATE TABLE IF NOT EXISTS documents (
    document_id     TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    revision        TEXT NOT NULL,
    sha256          TEXT,
    page_count      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS elements (
    element_id      TEXT PRIMARY KEY,
    document_id     TEXT REFERENCES documents(document_id),
    page            INTEGER NOT NULL,
    element_type    TEXT NOT NULL CHECK (element_type IN ('text','table','image','ocr')),
    content         TEXT,
    figure_id       TEXT,
    access_group    TEXT DEFAULT 'maintenance'
);

CREATE TABLE IF NOT EXISTS maintenance_history (
    id              SERIAL PRIMARY KEY,
    equipment_id    TEXT NOT NULL,
    ticket          TEXT NOT NULL,
    intervention    DATE NOT NULL,
    asset           TEXT,
    summary         TEXT,
    status          TEXT DEFAULT 'clos'
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id       TEXT PRIMARY KEY,
    equipment_id    TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    status          TEXT DEFAULT 'open',
    approved_by     TEXT,
    approval_token  TEXT,
    idempotency_key TEXT UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ticket_drafts (
    draft_id        TEXT PRIMARY KEY,
    equipment_id    TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_token  TEXT PRIMARY KEY,
    draft_id        TEXT REFERENCES ticket_drafts(draft_id),
    content_hash    TEXT NOT NULL,
    approver        TEXT NOT NULL,
    approved_at     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,
    action          TEXT NOT NULL,
    payload         JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

INSERT INTO documents (document_id, title, revision, page_count)
VALUES ('SAN-MAN-001', 'Manuel de maintenance SAN - SAN-LAB 2000', '1.1', 9)
ON CONFLICT (document_id) DO NOTHING;

INSERT INTO maintenance_history (equipment_id, ticket, intervention, asset, summary, status)
VALUES
    ('SAN-LAB-2000', 'INC-104', '2026-09-18', 'Fabric A', 'Perte temporaire de chemin HBA1 ; surveillance', 'clos'),
    ('SAN-LAB-2000', 'INC-117', '2026-10-02', 'Disque B03', 'Pré-alerte ; examen du groupe de protection', 'clos'),
    ('SAN-LAB-2000', 'INC-125', '2026-10-20', 'Volume VOL-DB', 'Capacité à 88 % ; analyse de tendance', 'ouvert'),
    ('SAN-LAB-2000', 'INC-130', '2026-10-25', 'Contrôleur B', 'Événement non reproductible ; suivi', 'ouvert')
ON CONFLICT DO NOTHING;
