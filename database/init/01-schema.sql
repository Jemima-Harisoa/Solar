/*
  Schéma SQL Server - Gestion d'Énergie Solaire Domestique (Solar)
  Version 1.0 - Avril 2026
*/

SET NOCOUNT ON;
GO;

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
CREATE TABLE TimeSlot (
    TimeSlotId TINYINT IDENTITY PRIMARY KEY,
    SlotName NVARCHAR(50) NOT NULL UNIQUE,
    StartHour TINYINT NOT NULL,
    EndHour TINYINT NOT NULL,
    Description NVARCHAR(200) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT CK_TimeSlot_Hours CHECK (StartHour >= 0 AND StartHour < 24 AND EndHour > 0 AND EndHour <= 24)
);
GO

-- Table : Configuration du système (tension secteur, paramètres globaux)
CREATE TABLE SystemConfiguration (
    ConfigId INT IDENTITY PRIMARY KEY,
    GridVoltageV DECIMAL(8,2) NOT NULL DEFAULT 230.0,
    SolarPanelEfficiencyPct DECIMAL(5,2) NOT NULL DEFAULT 40.0,
    BatteryOvercapacityPct DECIMAL(5,2) NOT NULL DEFAULT 50.0,
    Description NVARCHAR(300) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2(0) NULL,

    CONSTRAINT CK_SystemConfig_Voltage CHECK (GridVoltageV > 0),
    CONSTRAINT CK_SystemConfig_Efficiency CHECK (SolarPanelEfficiencyPct > 0 AND SolarPanelEfficiencyPct <= 100),
    CONSTRAINT CK_SystemConfig_Overcapacity CHECK (BatteryOvercapacityPct > 0)
);
GO

-- Contrainte unique filtrée : garantir une seule config active à la fois
CREATE UNIQUE INDEX UQ_SystemConfig_OneActive
ON SystemConfiguration(IsActive)
WHERE IsActive = 1;
GO


/* =========================
   TABLES MATÉRIELS
   ========================= */

-- Table : Type d'appareils électriques (catégories)
CREATE TABLE DeviceType (
    DeviceTypeId TINYINT IDENTITY PRIMARY KEY,
    TypeName NVARCHAR(50) NOT NULL UNIQUE,
    Category NVARCHAR(100) NOT NULL,
    Description NVARCHAR(250) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- Table : Appareils électriques présents dans la maison
CREATE TABLE Device (
    DeviceId INT IDENTITY PRIMARY KEY,
    DeviceCode NVARCHAR(50) NOT NULL UNIQUE,
    DeviceName NVARCHAR(120) NOT NULL,
    DeviceTypeId TINYINT NOT NULL,
    PowerW DECIMAL(10,2) NOT NULL,
    Description NVARCHAR(250) NULL,
    InstallationDate DATE NOT NULL,
    Status NVARCHAR(20) NOT NULL DEFAULT N'ACTIF',
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT FK_Device_DeviceType FOREIGN KEY (DeviceTypeId)
        REFERENCES DeviceType(DeviceTypeId),

    CONSTRAINT CK_Device_Power CHECK (PowerW > 0),
    CONSTRAINT CK_Device_Status CHECK (Status IN (N'ACTIF', N'INACTIF', N'MAINTEN'))
);
GO

-- Table : Programme d'utilisation des appareils par créneau horaire
CREATE TABLE DeviceUsageSchedule (
    UsageScheduleId BIGINT IDENTITY PRIMARY KEY,
    DeviceId INT NOT NULL,
    TimeSlotId TINYINT NOT NULL,
    DailyUsageHours DECIMAL(5,2) NOT NULL,
    IsEnabled BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT FK_DeviceUsage_Device FOREIGN KEY (DeviceId)
        REFERENCES Device(DeviceId),

    CONSTRAINT FK_DeviceUsage_TimeSlot FOREIGN KEY (TimeSlotId)
        REFERENCES TimeSlot(TimeSlotId),

    CONSTRAINT UQ_DeviceUsageSchedule UNIQUE (DeviceId, TimeSlotId),
    CONSTRAINT CK_DeviceUsage_Hours CHECK (DailyUsageHours >= 0 AND DailyUsageHours <= 24)
);
GO


/* =========================
   TABLES CONSOMMATIONS & PRODUCTION
   ========================= */

-- Table : Historique détaillé de consommation énergétique
CREATE TABLE EnergyConsumption (
    ConsumptionId BIGINT IDENTITY PRIMARY KEY,
    DeviceId INT NOT NULL,
    TimeSlotId TINYINT NOT NULL,
    ConsumptionDate DATE NOT NULL,
    EnergyConsumedWh DECIMAL(12,2) NOT NULL,
    DurationHours DECIMAL(5,2) NOT NULL,
    Notes NVARCHAR(250) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT FK_EnergyConsumption_Device FOREIGN KEY (DeviceId)
        REFERENCES Device(DeviceId),

    CONSTRAINT FK_EnergyConsumption_TimeSlot FOREIGN KEY (TimeSlotId)
        REFERENCES TimeSlot(TimeSlotId),

    CONSTRAINT CK_EnergyConsumption_Energy CHECK (EnergyConsumedWh >= 0),
    CONSTRAINT CK_EnergyConsumption_Duration CHECK (DurationHours >= 0)
);
GO

-- Table : Production d'énergie des panneaux solaires
CREATE TABLE SolarPanelProduction (
    SolarProductionId BIGINT IDENTITY PRIMARY KEY,
    ProductionDate DATE NOT NULL,
    TimeSlotId TINYINT NOT NULL,
    TotalPanelCapacityW DECIMAL(12,2) NOT NULL,
    ProductionPercentage DECIMAL(5,2) NOT NULL,
    EnergyProducedWh AS (
        TotalPanelCapacityW * ProductionPercentage / 100.0
    ) PERSISTED,
    Notes NVARCHAR(250) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT FK_SolarProduction_TimeSlot FOREIGN KEY (TimeSlotId)
        REFERENCES TimeSlot(TimeSlotId),

    CONSTRAINT CK_SolarProduction_Capacity CHECK (TotalPanelCapacityW > 0),
    CONSTRAINT CK_SolarProduction_Percentage CHECK (ProductionPercentage >= 0 AND ProductionPercentage <= 100)
);
GO

-- Table : Stockage et gestion de la batterie
CREATE TABLE BatteryStorage (
    BatteryId INT IDENTITY PRIMARY KEY,
    BatteryCode NVARCHAR(50) NOT NULL UNIQUE,
    TotalCapacityWh DECIMAL(12,2) NOT NULL,
    CurrentChargeWh DECIMAL(12,2) NOT NULL DEFAULT 0,
    MinChargeWh DECIMAL(12,2) NULL,
    MaxChargeWh DECIMAL(12,2) NULL,
    ChargingEfficiencyPct DECIMAL(5,2) NOT NULL DEFAULT 95.0,
    Description NVARCHAR(250) NULL,
    Status NVARCHAR(20) NOT NULL DEFAULT N'ACTIF',
    LastUpdatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT CK_Battery_Capacity CHECK (TotalCapacityWh > 0),
    CONSTRAINT CK_Battery_Charge CHECK (CurrentChargeWh >= 0 AND CurrentChargeWh <= TotalCapacityWh),
    CONSTRAINT CK_Battery_Efficiency CHECK (ChargingEfficiencyPct > 0 AND ChargingEfficiencyPct <= 100),
    CONSTRAINT CK_Battery_Status CHECK (Status IN (N'ACTIF', N'MAINTENANCE', N'DEFAUT'))
);
GO

-- Table : Historique des mouvements de batterie (charge/décharge)
CREATE TABLE BatteryMovement (
    BatteryMovementId BIGINT IDENTITY PRIMARY KEY,
    BatteryId INT NOT NULL,
    MovementDate DATE NOT NULL,
    TimeSlotId TINYINT NULL,
    MovementType NVARCHAR(20) NOT NULL,
    EnergyMovedWh DECIMAL(12,2) NOT NULL,
    ChargeBeforeWh DECIMAL(12,2) NOT NULL,
    ChargeAfterWh DECIMAL(12,2) NOT NULL,
    SolarProductionId BIGINT NULL,
    Notes NVARCHAR(250) NULL,
    CreatedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT FK_BatteryMovement_Battery FOREIGN KEY (BatteryId)
        REFERENCES BatteryStorage(BatteryId),

    CONSTRAINT FK_BatteryMovement_TimeSlot FOREIGN KEY (TimeSlotId)
        REFERENCES TimeSlot(TimeSlotId),

    CONSTRAINT FK_BatteryMovement_SolarProduction FOREIGN KEY (SolarProductionId)
        REFERENCES SolarPanelProduction(SolarProductionId),

    CONSTRAINT CK_BatteryMovement_Type CHECK (MovementType IN (N'CHARGE', N'DECHARGE')),
    CONSTRAINT CK_BatteryMovement_Energy CHECK (EnergyMovedWh >= 0),
    CONSTRAINT CK_BatteryMovement_Charge CHECK (ChargeBeforeWh >= 0 AND ChargeAfterWh >= 0)
);
GO


/* =========================
   VUES MATERIALISÉES (CALCULS DYNAMIQUES)
   ========================= */

-- Vue : Programmes d'utilisation avec consommation énergétique calculée
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
INNER JOIN Device d ON dus.DeviceId = d.DeviceId
INNER JOIN TimeSlot ts ON dus.TimeSlotId = ts.TimeSlotId;
GO

-- Vue : Bilan énergétique quotidien agrégé depuis les tables sources
-- Source de vérité unique : pas de table intermédiaire
CREATE VIEW vw_EnergyBalance AS
SELECT
    ec.ConsumptionDate AS BalanceDate,
    SUM(ec.EnergyConsumedWh) AS TotalConsumptionWh,
    ISNULL(MAX(sp.TotalProductionWh), 0) AS TotalProductionWh,
    night.NightConsumptionWh,

    -- Panneaux solaires nécessaires
    CASE
        WHEN SUM(ec.EnergyConsumedWh) = 0 THEN 0
        ELSE SUM(ec.EnergyConsumedWh) * 100.0 / sc.SolarPanelEfficiencyPct
    END AS RequiredPanelCapacityW,

    -- Batterie nécessaire (basée sur conso nuit)
    CASE
        WHEN night.NightConsumptionWh IS NULL THEN NULL
        ELSE night.NightConsumptionWh * (1.0 + sc.BatteryOvercapacityPct / 100.0)
    END AS RequiredBatteryCapacityWh,

    -- Déficit
    ISNULL(MAX(sp.TotalProductionWh), 0) - SUM(ec.EnergyConsumedWh) AS EnergyBalanceWh,

    sc.SolarPanelEfficiencyPct,
    sc.BatteryOvercapacityPct

FROM EnergyConsumption ec

LEFT JOIN (
    SELECT ProductionDate, SUM(EnergyProducedWh) AS TotalProductionWh
    FROM SolarPanelProduction
    GROUP BY ProductionDate
) sp ON sp.ProductionDate = ec.ConsumptionDate

LEFT JOIN (
    SELECT ec2.ConsumptionDate, SUM(ec2.EnergyConsumedWh) AS NightConsumptionWh
    FROM EnergyConsumption ec2
    INNER JOIN TimeSlot ts ON ec2.TimeSlotId = ts.TimeSlotId
    WHERE ts.SlotName = N'NUIT'
    GROUP BY ec2.ConsumptionDate
) night ON night.ConsumptionDate = ec.ConsumptionDate

CROSS JOIN (
    SELECT TOP 1 SolarPanelEfficiencyPct, BatteryOvercapacityPct
    FROM SystemConfiguration
    WHERE IsActive = 1
    ORDER BY ConfigId DESC
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

CREATE INDEX IX_Device_Status ON Device(Status);
GO

CREATE INDEX IX_Device_Type ON Device(DeviceTypeId);
GO

CREATE INDEX IX_DeviceUsage_Device ON DeviceUsageSchedule(DeviceId);
GO

CREATE INDEX IX_DeviceUsage_TimeSlot ON DeviceUsageSchedule(TimeSlotId);
GO

CREATE INDEX IX_EnergyConsumption_Device ON EnergyConsumption(DeviceId, ConsumptionDate);
GO

CREATE INDEX IX_EnergyConsumption_TimeSlot ON EnergyConsumption(TimeSlotId, ConsumptionDate);
GO

CREATE INDEX IX_EnergyConsumption_Date ON EnergyConsumption(ConsumptionDate);
GO

CREATE INDEX IX_SolarProduction_Date ON SolarPanelProduction(ProductionDate, TimeSlotId);
GO

CREATE INDEX IX_BatteryMovement_Date ON BatteryMovement(BatteryId, MovementDate);
GO

CREATE INDEX IX_BatteryMovement_TimeSlot ON BatteryMovement(TimeSlotId, MovementDate);
GO

CREATE INDEX IX_BatteryMovement_SolarProduction ON BatteryMovement(SolarProductionId);
GO 
