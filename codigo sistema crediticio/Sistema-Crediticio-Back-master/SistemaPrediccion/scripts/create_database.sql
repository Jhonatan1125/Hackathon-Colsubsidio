/* ============================================================================
   Credit Recommendation Engine — SQL Server database creation script
   ============================================================================
   Creates the CreditEngine database and the four tables the pipeline uses:

     dbo.persons             Person profiles — the dataset schema consumed by
                             encoding/column_definitions.py (read-only for the
                             pipeline) plus contact/consent fields required by
                             the delivery layer (ROOT_IMPLEMENTATION.md §7.1
                             dual-key rule: opt-in consent + valid contact data)
     dbo.batches             Batch tracking — mirrors ingestion BatchResult
                             (lifecycle: queued → processing → completed|failed)
     dbo.batch_persons       Per-person results within a batch — mirrors the
                             worker's PersonResult records
     dbo.scheduled_messages  The outbox / Scheduled Message Store — mirrors the
                             worker's ScheduledMessage contract (what, who,
                             when, where, message; ROOT §2.1/§7.3)

   Conventions:
     - person IDs accept both formats validated by ingestion/validator.py:
       Colombian cédulas (5–11 digits) and synthetic IDs ("P" + digits)
     - multi-label dataset columns (intereses, momentos_clave, …) are stored
       as JSON arrays, e.g. '["educacion","turismo"]' — the encoding module's
       FeatureExtractor accepts list-like string representations
     - "trigger" is a reserved word in T-SQL → column is named trigger_event

   Idempotent: safe to run more than once (IF NOT EXISTS guards).
   Run with:  sqlcmd -S <server> -i create_database.sql
   ============================================================================ */

IF DB_ID(N'CreditEngine') IS NULL
BEGIN
    CREATE DATABASE CreditEngine;
END;
GO

USE CreditEngine;
GO

/* ── dbo.persons ──────────────────────────────────────────────────────────
   The raw person dataset (schema per encoding/column_definitions.py) plus
   delivery contact/consent fields. The pipeline reads this table only. */
IF OBJECT_ID(N'dbo.persons', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.persons (
        cedula                                   NVARCHAR(20)   NOT NULL,
        nombre                                   NVARCHAR(200)  NOT NULL,
        correo                                   NVARCHAR(320)  NULL,
        direccion                                NVARCHAR(300)  NULL,
        fecha_nacimiento                         DATE           NULL,
        telefono                                 NVARCHAR(30)   NULL,

        /* Consent flags — delivery dual-key rule (ROOT §7.1) */
        consent_whatsapp                         BIT            NOT NULL CONSTRAINT DF_persons_consent_wa DEFAULT (0),
        consent_email                            BIT            NOT NULL CONSTRAINT DF_persons_consent_em DEFAULT (0),

        /* Numeric features (encoding: NUMERIC_COLS) */
        edad                                     INT            NOT NULL,
        ingresos                                 DECIMAL(18, 2) NOT NULL,
        score_datacredito                        INT            NULL,
        num_creditos_activos                     INT            NOT NULL CONSTRAINT DF_persons_creditos DEFAULT (0),
        deuda_total_acumulada_cop                DECIMAL(18, 2) NOT NULL CONSTRAINT DF_persons_deuda DEFAULT (0),
        cuota_mensual_total_cop                  DECIMAL(18, 2) NOT NULL CONSTRAINT DF_persons_cuota DEFAULT (0),
        capacidad_endeudamiento_disponible_pct   DECIMAL(5, 2)  NOT NULL CONSTRAINT DF_persons_capacidad DEFAULT (0),

        /* One-hot feature (encoding: ONEHOT_COLS) — statutory wage tiers */
        categoria_afiliacion                     NVARCHAR(1)    NOT NULL,

        /* Ordinal feature (encoding: ORDINAL_COLS / ORDINAL_ORDER) */
        mora_maxima_historica                    NVARCHAR(12)   NOT NULL CONSTRAINT DF_persons_mora DEFAULT (N'0_DIAS'),

        /* Multi-label features (encoding: MULTILABEL_COLS) — JSON arrays */
        area_trabajo                             NVARCHAR(500)  NULL,
        intereses                                NVARCHAR(500)  NULL,
        preferencias                             NVARCHAR(500)  NULL,
        momentos_clave                           NVARCHAR(500)  NULL,
        composicion_familiar                     NVARCHAR(500)  NULL,
        historial_creditos                       NVARCHAR(500)  NULL,

        /* Training label (encoding: TARGET_COL) — NULL outside training data */
        producto_colsubsidio_target              NVARCHAR(60)   NULL,

        created_at                               DATETIME2(3)   NOT NULL CONSTRAINT DF_persons_created DEFAULT (SYSUTCDATETIME()),
        updated_at                               DATETIME2(3)   NOT NULL CONSTRAINT DF_persons_updated DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_persons PRIMARY KEY CLUSTERED (cedula),
        CONSTRAINT CK_persons_categoria CHECK (categoria_afiliacion IN (N'A', N'B', N'C', N'D')),
        CONSTRAINT CK_persons_mora CHECK (mora_maxima_historica IN (N'0_DIAS', N'30_DIAS', N'60_DIAS', N'90_MAS_DIAS')),
        CONSTRAINT CK_persons_area_json CHECK (area_trabajo IS NULL OR ISJSON(area_trabajo) = 1),
        CONSTRAINT CK_persons_intereses_json CHECK (intereses IS NULL OR ISJSON(intereses) = 1),
        CONSTRAINT CK_persons_preferencias_json CHECK (preferencias IS NULL OR ISJSON(preferencias) = 1),
        CONSTRAINT CK_persons_momentos_json CHECK (momentos_clave IS NULL OR ISJSON(momentos_clave) = 1),
        CONSTRAINT CK_persons_familia_json CHECK (composicion_familiar IS NULL OR ISJSON(composicion_familiar) = 1),
        CONSTRAINT CK_persons_historial_json CHECK (historial_creditos IS NULL OR ISJSON(historial_creditos) = 1)
    );
END;
GO

/* ── dbo.batches ──────────────────────────────────────────────────────────
   Batch tracking — the batch_id is the job tracking ID (ROOT §8). The
   report column stores the worker's BatchReport summary as JSON. */
IF OBJECT_ID(N'dbo.batches', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.batches (
        /* Opaque app-generated ID (lowercase uuid4 from the ingestion queue).
           NVARCHAR, not UNIQUEIDENTIFIER: pyodbc reads UNIQUEIDENTIFIER back
           UPPERCASED, which would break Python-side equality with the IDs
           the application issues and echoes to API clients. */
        batch_id       NVARCHAR(36)     NOT NULL,
        status         NVARCHAR(12)     NOT NULL CONSTRAINT DF_batches_status DEFAULT (N'queued'),
        total_count    INT              NOT NULL CONSTRAINT DF_batches_count DEFAULT (0),
        report         NVARCHAR(MAX)    NULL,
        created_at     DATETIME2(3)     NOT NULL CONSTRAINT DF_batches_created DEFAULT (SYSUTCDATETIME()),
        started_at     DATETIME2(3)     NULL,
        finished_at    DATETIME2(3)     NULL,

        CONSTRAINT PK_batches PRIMARY KEY CLUSTERED (batch_id),
        CONSTRAINT CK_batches_status CHECK (status IN (N'queued', N'processing', N'completed', N'failed')),
        CONSTRAINT CK_batches_report_json CHECK (report IS NULL OR ISJSON(report) = 1)
    );
END;
GO

/* ── dbo.batch_persons ────────────────────────────────────────────────────
   Per-person outcome inside a batch (worker PersonResult). result_status
   is NULL while the batch is still queued/processing. No FK to persons:
   a submitted ID may legitimately not exist (person_not_found). */
IF OBJECT_ID(N'dbo.batch_persons', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.batch_persons (
        batch_id       NVARCHAR(36)     NOT NULL,
        cedula         NVARCHAR(20)     NOT NULL,
        result_status  NVARCHAR(20)     NULL,
        detail         NVARCHAR(1000)   NULL,  -- PersonResult.detail carries exception text; keep generous

        CONSTRAINT PK_batch_persons PRIMARY KEY CLUSTERED (batch_id, cedula),
        CONSTRAINT FK_batch_persons_batch FOREIGN KEY (batch_id) REFERENCES dbo.batches (batch_id) ON DELETE CASCADE,
        CONSTRAINT CK_batch_persons_status CHECK (
            result_status IS NULL
            OR result_status IN (N'processed', N'person_not_found', N'no_offer', N'error')
        )
    );
END;
GO

/* ── dbo.scheduled_messages ───────────────────────────────────────────────
   The outbox / Scheduled Message Store (ROOT §2.1/§7.3): what, who, when,
   where and the message itself, plus the structured offer terms so the
   dispatcher has offer data without parsing message_text. Status lifecycle
   per ROOT §7.3: scheduled → pending → sent. */
IF OBJECT_ID(N'dbo.scheduled_messages', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.scheduled_messages (
        message_id       BIGINT           NOT NULL IDENTITY (1, 1),
        batch_id         NVARCHAR(36)     NULL,
        cedula           NVARCHAR(20)     NOT NULL,
        product_id       NVARCHAR(50)     NOT NULL,

        /* Structured offer terms (deterministic engine output). NULL today:
           the worker's ScheduledMessage contract does not carry numeric
           terms yet (they travel inside message_text) — populated once the
           offer envelope gains numeric fields (see worker plan). */
        amount_cop       DECIMAL(18, 2)   NULL,
        annual_rate_pct  DECIMAL(6, 3)    NULL,
        term_months      INT              NULL,
        cuota_cop        DECIMAL(18, 2)   NULL,

        channel          NVARCHAR(20)     NOT NULL,
        contact_window   NVARCHAR(12)     NOT NULL,
        trigger_event    NVARCHAR(100)    NOT NULL CONSTRAINT DF_msgs_trigger DEFAULT (N'inmediato'),
        message_text     NVARCHAR(MAX)    NOT NULL,
        message_source   NVARCHAR(10)     NOT NULL CONSTRAINT DF_msgs_source DEFAULT (N'template'),
        status           NVARCHAR(10)     NOT NULL CONSTRAINT DF_msgs_status DEFAULT (N'scheduled'),
        created_at       DATETIME2(3)     NOT NULL CONSTRAINT DF_msgs_created DEFAULT (SYSUTCDATETIME()),
        sent_at          DATETIME2(3)     NULL,

        /* batch_id is a plain indexed column (no FK): batches currently live
           in the in-memory ingestion queue, so a dbo.batches row may not
           exist when a message is stored. Restore the FK when batch
           persistence (a DB-backed BatchQueue) lands. */
        CONSTRAINT PK_scheduled_messages PRIMARY KEY CLUSTERED (message_id),
        CONSTRAINT FK_msgs_person FOREIGN KEY (cedula) REFERENCES dbo.persons (cedula),
        CONSTRAINT CK_msgs_channel CHECK (channel IN (N'whatsapp', N'sms', N'email', N'app', N'callcenter', N'branch')),
        CONSTRAINT CK_msgs_window CHECK (contact_window IN (N'morning', N'midday', N'afternoon', N'night')),
        CONSTRAINT CK_msgs_source CHECK (message_source IN (N'llm', N'template')),
        CONSTRAINT CK_msgs_status CHECK (status IN (N'scheduled', N'pending', N'sent'))
    );
END;
GO

/* ── Indexes ──────────────────────────────────────────────────────────────
   - dispatcher poll: pending work by status + contact window (ROOT §2.1
     "Checks for messages in their send window")
   - message lookups by person and by batch */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_msgs_status_window' AND object_id = OBJECT_ID(N'dbo.scheduled_messages'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_msgs_status_window
        ON dbo.scheduled_messages (status, contact_window)
        INCLUDE (cedula, channel, message_text);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_msgs_cedula' AND object_id = OBJECT_ID(N'dbo.scheduled_messages'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_msgs_cedula
        ON dbo.scheduled_messages (cedula);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_msgs_batch' AND object_id = OBJECT_ID(N'dbo.scheduled_messages'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_msgs_batch
        ON dbo.scheduled_messages (batch_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_batches_status' AND object_id = OBJECT_ID(N'dbo.batches'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_batches_status
        ON dbo.batches (status);
END;
GO

PRINT N'CreditEngine database objects created (or already present).';
GO
