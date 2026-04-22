/*
  Schéma SQL Server - Gestion d'Énergie Solaire Domestique (Solar)
  Version 1.1 - Avril 2026
  Idempotent : sécurisé contre les ré-exécutions (IF NOT EXISTS sur tout)
*/

SET NOCOUNT ON;
GO

-- -------------------------------------------------------
-- BASE DE DONNÉES
-- -------------------------------------------------------
IF DB_ID(N'solar') IS NULL
    CREATE DATABASE solar;
GO

USE solar;
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO


/* =========================
   TABLES DE CONFIGURATIONS
   ========================= */

-- Table : Créneaux horaires d'une journée (jour, soir, nuit)
-- NOTE : Pas de contrainte StartHour < EndHour pour permettre créneaux traversant minuit (ex: nuit 19h-6h)
IF OBJECT_ID(N'dbo.TimeSlot', N'U') IS NULL
BEGIN
    CREATE TABLE TimeSlot (
        TimeSlotId  TINYINT        IDENTITY PRIMARY KEY,
        SlotName    NVARCHAR(50)   NOT NULL UNIQUE,
        StartHour   TINYINT        NOT NULL,
        EndHour     TINYINT        NOT NULL,
        Description NVARCHAR(200)  NULL,
        CreatedAt   DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT CK_TimeSlot_Hours CHECK (StartHour >= 0 AND StartHour < 24 AND EndHour > 0 AND EndHour <= 24)
    );
END;
GO

-- Table : Configuration du système (tension secteur, paramètres globaux)
IF OBJECT_ID(N'dbo.SystemConfiguration', N'U') IS NULL
BEGIN
    CREATE TABLE SystemConfiguration (
        ConfigId                  INT            IDENTITY PRIMARY KEY,
        GridVoltageV              DECIMAL(8,2)   NOT NULL DEFAULT 230.0,
        SolarPanelEfficiencyPct   DECIMAL(5,2)   NOT NULL DEFAULT 40.0,
        BatteryOvercapacityPct    DECIMAL(5,2)   NOT NULL DEFAULT 50.0,
        Description               NVARCHAR(300)  NULL,
        IsActive                  BIT            NOT NULL DEFAULT 1,
        CreatedAt                 DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt                 DATETIME2(0)   NULL,

        CONSTRAINT CK_SystemConfig_Voltage      CHECK (GridVoltageV > 0),
        CONSTRAINT CK_SystemConfig_Efficiency   CHECK (SolarPanelEfficiencyPct > 0 AND SolarPanelEfficiencyPct <= 100),
        CONSTRAINT CK_SystemConfig_Overcapacity CHECK (BatteryOvercapacityPct > 0)
    );
END;
GO

-- Index unique filtré : une seule config active à la fois
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.SystemConfiguration')
      AND name = N'UQ_SystemConfig_OneActive'
)
    CREATE UNIQUE INDEX UQ_SystemConfig_OneActive
    ON SystemConfiguration(IsActive)
    WHERE IsActive = 1;
GO


/* =========================
   TABLES MATÉRIELS
   ========================= */

-- Table : Type d'appareils électriques (catégories)
IF OBJECT_ID(N'dbo.DeviceType', N'U') IS NULL
BEGIN
    CREATE TABLE DeviceType (
        DeviceTypeId TINYINT        IDENTITY PRIMARY KEY,
        TypeName     NVARCHAR(50)   NOT NULL UNIQUE,
        Category     NVARCHAR(100)  NOT NULL,
        Description  NVARCHAR(250)  NULL,
        CreatedAt    DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

-- Table : Appareils électriques présents dans la maison
IF OBJECT_ID(N'dbo.Device', N'U') IS NULL
BEGIN
    CREATE TABLE Device (
        DeviceId         INT            IDENTITY PRIMARY KEY,
        DeviceCode       NVARCHAR(50)   NOT NULL UNIQUE,
        DeviceName       NVARCHAR(120)  NOT NULL,
        DeviceTypeId     TINYINT        NOT NULL,
        PowerW           DECIMAL(10,2)  NOT NULL,
        Description      NVARCHAR(250)  NULL,
        InstallationDate DATE           NOT NULL,
        Status           NVARCHAR(20)   NOT NULL DEFAULT N'ACTIF',
        CreatedAt        DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_Device_DeviceType FOREIGN KEY (DeviceTypeId)
            REFERENCES DeviceType(DeviceTypeId),

        CONSTRAINT CK_Device_Power  CHECK (PowerW > 0),
        CONSTRAINT CK_Device_Status CHECK (Status IN (N'ACTIF', N'INACTIF', N'MAINTEN'))
    );
END;
GO

-- Table : Programme d'utilisation des appareils par créneau horaire
IF OBJECT_ID(N'dbo.DeviceUsageSchedule', N'U') IS NULL
BEGIN
    CREATE TABLE DeviceUsageSchedule (
        UsageScheduleId BIGINT        IDENTITY PRIMARY KEY,
        DeviceId        INT           NOT NULL,
        TimeSlotId      TINYINT       NOT NULL,
        DailyUsageHours DECIMAL(5,2)  NOT NULL,
        UsageStartTime  TIME          NULL,
        UsageEndTime    TIME          NULL,
        IsEnabled       BIT           NOT NULL DEFAULT 1,
        CreatedAt       DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_DeviceUsage_Device    FOREIGN KEY (DeviceId)   REFERENCES Device(DeviceId),
        CONSTRAINT FK_DeviceUsage_TimeSlot  FOREIGN KEY (TimeSlotId) REFERENCES TimeSlot(TimeSlotId),
        CONSTRAINT UQ_DeviceUsageSchedule   UNIQUE (DeviceId, TimeSlotId),
        CONSTRAINT CK_DeviceUsage_Hours     CHECK (DailyUsageHours >= 0 AND DailyUsageHours <= 24)
    );
END;
GO

-- Colonnes fines d'usage horaire (idempotent)
IF COL_LENGTH(N'dbo.DeviceUsageSchedule', N'UsageStartTime') IS NULL
    ALTER TABLE dbo.DeviceUsageSchedule ADD UsageStartTime TIME NULL;
GO

IF COL_LENGTH(N'dbo.DeviceUsageSchedule', N'UsageEndTime') IS NULL
    ALTER TABLE dbo.DeviceUsageSchedule ADD UsageEndTime TIME NULL;
GO

-- Validation de coherence UsageStartTime/UsageEndTime:
-- geree cote service pour couvrir les creneaux traversant minuit (ex: 22:00-02:00).


/* =========================
   TABLES CONSOMMATIONS & PRODUCTION
   ========================= */

-- Table : Historique détaillé de consommation énergétique
IF OBJECT_ID(N'dbo.EnergyConsumption', N'U') IS NULL
BEGIN
    CREATE TABLE EnergyConsumption (
        ConsumptionId    BIGINT        IDENTITY PRIMARY KEY,
        DeviceId         INT           NOT NULL,
        TimeSlotId       TINYINT       NOT NULL,
        ConsumptionDate  DATE          NOT NULL,
        EnergyConsumedWh DECIMAL(12,2) NOT NULL,
        DurationHours    DECIMAL(5,2)  NOT NULL,
        Notes            NVARCHAR(250) NULL,
        CreatedAt        DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_EnergyConsumption_Device    FOREIGN KEY (DeviceId)   REFERENCES Device(DeviceId),
        CONSTRAINT FK_EnergyConsumption_TimeSlot  FOREIGN KEY (TimeSlotId) REFERENCES TimeSlot(TimeSlotId),
        CONSTRAINT CK_EnergyConsumption_Energy    CHECK (EnergyConsumedWh >= 0),
        CONSTRAINT CK_EnergyConsumption_Duration  CHECK (DurationHours    >= 0)
    );
END;
GO

-- Table : Production d'énergie des panneaux solaires
IF OBJECT_ID(N'dbo.SolarPanelProduction', N'U') IS NULL
BEGIN
    CREATE TABLE SolarPanelProduction (
        SolarProductionId    BIGINT        IDENTITY PRIMARY KEY,
        ProductionDate       DATE          NOT NULL,
        TimeSlotId           TINYINT       NOT NULL,
        TotalPanelCapacityW  DECIMAL(12,2) NOT NULL,
        ProductionPercentage DECIMAL(5,2)  NOT NULL,
        EnergyProducedWh     AS (TotalPanelCapacityW * ProductionPercentage / 100.0) PERSISTED,
        Notes                NVARCHAR(250) NULL,
        CreatedAt            DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_SolarProduction_TimeSlot      FOREIGN KEY (TimeSlotId) REFERENCES TimeSlot(TimeSlotId),
        CONSTRAINT CK_SolarProduction_Capacity      CHECK (TotalPanelCapacityW   > 0),
        CONSTRAINT CK_SolarProduction_Percentage    CHECK (ProductionPercentage >= 0 AND ProductionPercentage <= 100)
    );
END;
GO

-- Table : Stockage et gestion de la batterie
IF OBJECT_ID(N'dbo.BatteryStorage', N'U') IS NULL
BEGIN
    CREATE TABLE BatteryStorage (
        BatteryId             INT            IDENTITY PRIMARY KEY,
        BatteryCode           NVARCHAR(50)   NOT NULL UNIQUE,
        TotalCapacityWh       DECIMAL(12,2)  NOT NULL,
        CurrentChargeWh       DECIMAL(12,2)  NOT NULL DEFAULT 0,
        MinChargeWh           DECIMAL(12,2)  NULL,
        MaxChargeWh           DECIMAL(12,2)  NULL,
        ChargingEfficiencyPct DECIMAL(5,2)   NOT NULL DEFAULT 95.0,
        Description           NVARCHAR(250)  NULL,
        Status                NVARCHAR(20)   NOT NULL DEFAULT N'ACTIF',
        LastUpdatedAt         DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
        CreatedAt             DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT CK_Battery_Capacity   CHECK (TotalCapacityWh > 0),
        CONSTRAINT CK_Battery_Charge     CHECK (CurrentChargeWh >= 0 AND CurrentChargeWh <= TotalCapacityWh),
        CONSTRAINT CK_Battery_Efficiency CHECK (ChargingEfficiencyPct > 0 AND ChargingEfficiencyPct <= 100),
        CONSTRAINT CK_Battery_Status     CHECK (Status IN (N'ACTIF', N'MAINTENANCE', N'DEFAUT'))
    );
END;
GO

-- Table : Historique des mouvements de batterie (charge/décharge)
IF OBJECT_ID(N'dbo.BatteryMovement', N'U') IS NULL
BEGIN
    CREATE TABLE BatteryMovement (
        BatteryMovementId BIGINT        IDENTITY PRIMARY KEY,
        BatteryId         INT           NOT NULL,
        MovementDate      DATE          NOT NULL,
        TimeSlotId        TINYINT       NULL,
        MovementType      NVARCHAR(20)  NOT NULL,
        EnergyMovedWh     DECIMAL(12,2) NOT NULL,
        ChargeBeforeWh    DECIMAL(12,2) NOT NULL,
        ChargeAfterWh     DECIMAL(12,2) NOT NULL,
        SolarProductionId BIGINT        NULL,
        Notes             NVARCHAR(250) NULL,
        CreatedAt         DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_BatteryMovement_Battery         FOREIGN KEY (BatteryId)         REFERENCES BatteryStorage(BatteryId),
        CONSTRAINT FK_BatteryMovement_TimeSlot        FOREIGN KEY (TimeSlotId)        REFERENCES TimeSlot(TimeSlotId),
        CONSTRAINT FK_BatteryMovement_SolarProduction FOREIGN KEY (SolarProductionId) REFERENCES SolarPanelProduction(SolarProductionId),
        CONSTRAINT CK_BatteryMovement_Type   CHECK (MovementType    IN (N'CHARGE', N'DECHARGE')),
        CONSTRAINT CK_BatteryMovement_Energy CHECK (EnergyMovedWh   >= 0),
        CONSTRAINT CK_BatteryMovement_Charge CHECK (ChargeBeforeWh  >= 0 AND ChargeAfterWh >= 0)
    );
END;
GO

-- Table : Types de panneaux (centralisee ici pour schema complet)
IF OBJECT_ID(N'dbo.PanelType', N'U') IS NULL
BEGIN
    CREATE TABLE PanelType (
        PanelTypeId      INT            IDENTITY PRIMARY KEY,
        TypeName         NVARCHAR(80)   NOT NULL UNIQUE,
        UnitEnergyW      DECIMAL(10,2)  NOT NULL,
        ExploitablePct   DECIMAL(5,2)   NOT NULL,
        UsableEnergyWh   AS (UnitEnergyW * ExploitablePct / 100.0) PERSISTED,
        UnitPriceAr      DECIMAL(12,2)  NOT NULL,
        PeakPowerWh      DECIMAL(10,2)  NULL,
        Description      NVARCHAR(250)  NULL,
        CreatedAt        DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),

        CONSTRAINT CK_PanelType_Exploit CHECK (ExploitablePct > 0 AND ExploitablePct <= 100),
        CONSTRAINT CK_PanelType_Energy  CHECK (UnitEnergyW > 0),
        CONSTRAINT CK_PanelType_Price   CHECK (UnitPriceAr >= 0)
    );
END;
GO

-- Compatibilite ascendante: garder la colonne historique UsableEnergyW si absente
IF COL_LENGTH(N'dbo.PanelType', N'UsableEnergyW') IS NULL
    ALTER TABLE dbo.PanelType ADD UsableEnergyW AS (UnitEnergyW * ExploitablePct / 100.0) PERSISTED;
GO

IF COL_LENGTH(N'dbo.PanelType', N'UnitEnergyW') IS NULL
    ALTER TABLE dbo.PanelType ADD UnitEnergyW DECIMAL(10,2) NOT NULL CONSTRAINT DF_PanelType_UnitEnergyW DEFAULT 1;
GO

IF COL_LENGTH(N'dbo.PanelType', N'ExploitablePct') IS NULL
    ALTER TABLE dbo.PanelType ADD ExploitablePct DECIMAL(5,2) NOT NULL CONSTRAINT DF_PanelType_ExploitablePct DEFAULT 1;
GO

IF COL_LENGTH(N'dbo.PanelType', N'UsableEnergyWh') IS NULL
    ALTER TABLE dbo.PanelType ADD UsableEnergyWh AS (UnitEnergyW * ExploitablePct / 100.0) PERSISTED;
GO

IF COL_LENGTH(N'dbo.PanelType', N'UnitPriceAr') IS NULL
    ALTER TABLE dbo.PanelType ADD UnitPriceAr DECIMAL(12,2) NOT NULL CONSTRAINT DF_PanelType_UnitPriceAr DEFAULT 0;
GO

IF COL_LENGTH(N'dbo.PanelType', N'PeakPowerWh') IS NULL
    ALTER TABLE dbo.PanelType ADD PeakPowerWh DECIMAL(10,2) NULL;
GO

-- Contraintes PanelType ajoutees avec guards
IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_PanelType_Exploit'
      AND parent_object_id = OBJECT_ID(N'dbo.PanelType')
)
    ALTER TABLE dbo.PanelType
    ADD CONSTRAINT CK_PanelType_Exploit CHECK (ExploitablePct > 0 AND ExploitablePct <= 100);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_PanelType_Energy'
      AND parent_object_id = OBJECT_ID(N'dbo.PanelType')
)
    ALTER TABLE dbo.PanelType
    ADD CONSTRAINT CK_PanelType_Energy CHECK (UnitEnergyW > 0);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_PanelType_Price'
      AND parent_object_id = OBJECT_ID(N'dbo.PanelType')
)
    ALTER TABLE dbo.PanelType
    ADD CONSTRAINT CK_PanelType_Price CHECK (UnitPriceAr >= 0);
GO

-- Nouveaux parametres de monetisation dans la configuration systeme
IF COL_LENGTH(N'dbo.SystemConfiguration', N'EnergySellingPriceArWh') IS NULL
    ALTER TABLE dbo.SystemConfiguration ADD EnergySellingPriceArWh DECIMAL(12,4) NOT NULL CONSTRAINT DF_SystemConfiguration_EnergySellingPriceArWh DEFAULT 0;
GO

IF COL_LENGTH(N'dbo.SystemConfiguration', N'SellingPriceStartDate') IS NULL
    ALTER TABLE dbo.SystemConfiguration ADD SellingPriceStartDate DATE NULL;
GO

IF COL_LENGTH(N'dbo.SystemConfiguration', N'SellingPriceEndDate') IS NULL
    ALTER TABLE dbo.SystemConfiguration ADD SellingPriceEndDate DATE NULL;
GO


/* =========================
   VUES
   ========================= */

-- Vue : Programmes d'utilisation avec consommation énergétique calculée
IF OBJECT_ID(N'dbo.vw_DeviceUsageSchedule', N'V') IS NOT NULL
    DROP VIEW dbo.vw_DeviceUsageSchedule;
GO

CREATE VIEW vw_DeviceUsageSchedule AS
SELECT
    dus.UsageScheduleId,
    dus.DeviceId,
    dus.TimeSlotId,
    d.DeviceName,
    d.PowerW,
    dus.DailyUsageHours,
    (d.PowerW * dus.DailyUsageHours) AS DailyEnergyConsumptionWh,
    ts.SlotName,
    dus.IsEnabled,
    dus.CreatedAt
FROM DeviceUsageSchedule dus
INNER JOIN Device   d  ON dus.DeviceId   = d.DeviceId
INNER JOIN TimeSlot ts ON dus.TimeSlotId = ts.TimeSlotId;
GO

-- Vue : Bilan énergétique quotidien agrégé depuis les tables sources
-- Source de vérité unique : pas de table intermédiaire
IF OBJECT_ID(N'dbo.vw_EnergyBalance', N'V') IS NOT NULL
    DROP VIEW dbo.vw_EnergyBalance;
GO

CREATE VIEW vw_EnergyBalance AS
SELECT
    ec.ConsumptionDate                                         AS BalanceDate,
    SUM(ec.EnergyConsumedWh)                                   AS TotalConsumptionWh,
    ISNULL(MAX(sp.TotalProductionWh), 0)                       AS TotalProductionWh,
    night.NightConsumptionWh,

    -- Panneaux solaires nécessaires
    CASE
        WHEN SUM(ec.EnergyConsumedWh) = 0 THEN 0
        ELSE SUM(ec.EnergyConsumedWh) * 100.0 / sc.SolarPanelEfficiencyPct
    END                                                        AS RequiredPanelCapacityW,

    -- Batterie nécessaire (basée sur conso nuit)
    CASE
        WHEN night.NightConsumptionWh IS NULL THEN NULL
        ELSE night.NightConsumptionWh * (1.0 + sc.BatteryOvercapacityPct / 100.0)
    END                                                        AS RequiredBatteryCapacityWh,

    -- Bilan net (positif = excédent, négatif = déficit)
    ISNULL(MAX(sp.TotalProductionWh), 0)
        - SUM(ec.EnergyConsumedWh)                             AS EnergyBalanceWh,

    sc.SolarPanelEfficiencyPct,
    sc.BatteryOvercapacityPct

FROM EnergyConsumption ec

LEFT JOIN (
    SELECT ProductionDate, SUM(EnergyProducedWh) AS TotalProductionWh
    FROM   SolarPanelProduction
    GROUP  BY ProductionDate
) sp ON sp.ProductionDate = ec.ConsumptionDate

LEFT JOIN (
    SELECT ec2.ConsumptionDate, SUM(ec2.EnergyConsumedWh) AS NightConsumptionWh
    FROM   EnergyConsumption ec2
    INNER JOIN TimeSlot ts ON ec2.TimeSlotId = ts.TimeSlotId
    WHERE  ts.SlotName = N'NUIT'
    GROUP  BY ec2.ConsumptionDate
) night ON night.ConsumptionDate = ec.ConsumptionDate

CROSS JOIN (
    SELECT TOP 1 SolarPanelEfficiencyPct, BatteryOvercapacityPct
    FROM   SystemConfiguration
    WHERE  IsActive = 1
    ORDER  BY ConfigId DESC
) sc

GROUP BY
    ec.ConsumptionDate,
    night.NightConsumptionWh,
    sc.SolarPanelEfficiencyPct,
    sc.BatteryOvercapacityPct;
GO


/* =========================
   INDEXES
   ========================= */

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.Device') AND name = N'IX_Device_Status')
    CREATE INDEX IX_Device_Status ON Device(Status);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.Device') AND name = N'IX_Device_Type')
    CREATE INDEX IX_Device_Type ON Device(DeviceTypeId);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.DeviceUsageSchedule') AND name = N'IX_DeviceUsage_Device')
    CREATE INDEX IX_DeviceUsage_Device ON DeviceUsageSchedule(DeviceId);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.DeviceUsageSchedule') AND name = N'IX_DeviceUsage_TimeSlot')
    CREATE INDEX IX_DeviceUsage_TimeSlot ON DeviceUsageSchedule(TimeSlotId);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.EnergyConsumption') AND name = N'IX_EnergyConsumption_Device')
    CREATE INDEX IX_EnergyConsumption_Device ON EnergyConsumption(DeviceId, ConsumptionDate);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.EnergyConsumption') AND name = N'IX_EnergyConsumption_TimeSlot')
    CREATE INDEX IX_EnergyConsumption_TimeSlot ON EnergyConsumption(TimeSlotId, ConsumptionDate);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.EnergyConsumption') AND name = N'IX_EnergyConsumption_Date')
    CREATE INDEX IX_EnergyConsumption_Date ON EnergyConsumption(ConsumptionDate);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.SolarPanelProduction') AND name = N'IX_SolarProduction_Date')
    CREATE INDEX IX_SolarProduction_Date ON SolarPanelProduction(ProductionDate, TimeSlotId);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.BatteryMovement') AND name = N'IX_BatteryMovement_Date')
    CREATE INDEX IX_BatteryMovement_Date ON BatteryMovement(BatteryId, MovementDate);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.BatteryMovement') AND name = N'IX_BatteryMovement_TimeSlot')
    CREATE INDEX IX_BatteryMovement_TimeSlot ON BatteryMovement(TimeSlotId, MovementDate);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.BatteryMovement') AND name = N'IX_BatteryMovement_SolarProduction')
    CREATE INDEX IX_BatteryMovement_SolarProduction ON BatteryMovement(SolarProductionId);
GO