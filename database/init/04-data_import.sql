/*
  Script d'insertion de donnees de test - Gestion d Energie Solaire
  Reinitialise les donnees existantes et insere les equipements et leurs usages
  Idempotent : peut etre re-execute sans probleme
*/

USE solar;
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO


/* =========================
   STEP 1 : REINITIALISER LES DONNEES EXISTANTES
   ========================= */

-- Supprimer les historiques de consommation
DELETE FROM EnergyConsumption WHERE 1=1;
GO

-- Supprimer les historiques de batterie
DELETE FROM BatteryMovement WHERE 1=1;
GO

-- Supprimer les historiques de production solaire
DELETE FROM SolarPanelProduction WHERE 1=1;
GO

-- Supprimer les programmes d utilisation
DELETE FROM DeviceUsageSchedule WHERE 1=1;
GO

-- Supprimer les appareils
DELETE FROM Device WHERE 1=1;
GO

/* =========================
   STEP 2 : INSERER LES CRENEAUX HORAIRES (JOUR, SOIR, NUIT)
   ========================= */

MERGE INTO TimeSlot AS target
USING (
    VALUES
        (N'JOUR', 6, 17, N'Periode jour'),
        (N'SOIR', 17, 19, N'Periode soir'),
        (N'NUIT', 19, 6, N'Periode nuit')
) AS source(SlotName, StartHour, EndHour, Description)
ON target.SlotName = source.SlotName
WHEN NOT MATCHED THEN
    INSERT (SlotName, StartHour, EndHour, Description)
    VALUES (source.SlotName, source.StartHour, source.EndHour, source.Description);
GO

PRINT 'Creneaux horaires inseres ou verifies';
GO


/* =========================
   STEP 3 : INSERER LES TYPES D APPAREILS
   ========================= */

DECLARE @DeviceTypes TABLE (
    TypeName NVARCHAR(50),
    Category NVARCHAR(100),
    Description NVARCHAR(250)
);

INSERT INTO @DeviceTypes VALUES
    (N'TV', N'Electronique', N'Televiseur'),
    (N'Ventilateur', N'Climatisation', N'Ventilateur air'),
    (N'Refrigerateur', N'Cuisine', N'Appareil froid'),
    (N'Lampe', N'Eclairage', N'Lampe LED'),
    (N'Routeur WiFi', N'Reseau', N'Routeur WiFi');

MERGE INTO DeviceType AS target
USING @DeviceTypes AS source
ON target.TypeName = source.TypeName
WHEN NOT MATCHED THEN
    INSERT (TypeName, Category, Description)
    VALUES (source.TypeName, source.Category, source.Description);
GO

PRINT 'Types d appareils inseres ou verifies';
GO


/* =========================
   STEP 4 : INSERER LES APPAREILS
   ========================= */

DECLARE @DeviceData TABLE (
    RowNum INT IDENTITY(1,1),
    TypeName NVARCHAR(50),
    PowerW INT
);

INSERT INTO @DeviceData (TypeName, PowerW) VALUES
    (N'TV', 55),
    (N'Ventilateur', 75),
    (N'Refrigerateur', 120),
    (N'Lampe', 10),
    (N'TV', 55),
    (N'Routeur WiFi', 10),
    (N'Refrigerateur', 120),
    (N'Lampe', 10);

INSERT INTO Device (DeviceCode, DeviceName, DeviceTypeId, PowerW, Description, InstallationDate, Status)
SELECT
    CONCAT(dd.TypeName, '-', dd.RowNum) AS DeviceCode,
    CONCAT(dd.TypeName, ' (', dd.PowerW, 'W)') AS DeviceName,
    dt.DeviceTypeId,
    dd.PowerW,
    CONCAT(dd.PowerW, 'W') AS Description,
    CAST(GETDATE() AS DATE) AS InstallationDate,
    N'ACTIF' AS Status
FROM @DeviceData dd
INNER JOIN DeviceType dt ON dt.TypeName = dd.TypeName;
GO

PRINT 'Appareils inseres';
GO


/* =========================
   STEP 5 : INSERER LES PROGRAMMES D UTILISATION PAR CRENEAU
   ========================= */

DECLARE @UsageData TABLE (
    RowNum INT IDENTITY(1,1),
    EquipementNom NVARCHAR(50),
    Puissance INT,
    TrancheName NVARCHAR(10),
    HeureDebut TIME,
    HeureFin TIME,
    DureeUtilisation DECIMAL(5,2)
);

INSERT INTO @UsageData (EquipementNom, Puissance, TrancheName, HeureDebut, HeureFin, DureeUtilisation) VALUES
    (N'TV', 55, N'JOUR', '08:00:00', '12:00:00', 4),
    (N'Ventilateur', 75, N'JOUR', '10:00:00', '14:00:00', 4),
    (N'Refrigerateur', 120, N'JOUR', '06:00:00', '17:00:00', 11),
    (N'Lampe', 10, N'SOIR', '17:00:00', '19:00:00', 2),
    (N'TV', 55, N'SOIR', '17:00:00', '19:00:00', 2),
    (N'Routeur WiFi', 10, N'NUIT', '19:00:00', '06:00:00', 11),
    (N'Refrigerateur', 120, N'NUIT', '19:00:00', '06:00:00', 11),
    (N'Lampe', 10, N'NUIT', '19:00:00', '23:00:00', 4);

INSERT INTO DeviceUsageSchedule (DeviceId, TimeSlotId, DailyUsageHours, IsEnabled)
SELECT
    d.DeviceId,
    ts.TimeSlotId,
    usage.DureeUtilisation AS DailyUsageHours,
    1 AS IsEnabled
FROM @UsageData usage
INNER JOIN Device d ON d.DeviceCode = CONCAT(usage.EquipementNom, '-', usage.RowNum)
INNER JOIN TimeSlot ts ON ts.SlotName = usage.TrancheName;
GO

PRINT 'Programmes d utilisation inseres';
GO


/* =========================
   STEP 6 : AFFICHER UN RESUME DES DONNEES INSEREES
   ========================= */

PRINT '';
PRINT '========== RESUME DES DONNEES INSEREES ==========';
PRINT '';

PRINT 'CRENEAUX HORAIRES :';
SELECT SlotName AS Creneau, 
       CONCAT(StartHour, 'h') AS Debut, 
       CONCAT(EndHour, 'h') AS Fin,
       Description
FROM TimeSlot
WHERE SlotName IN (N'JOUR', N'SOIR', N'NUIT')
ORDER BY StartHour;

PRINT '';
PRINT 'TYPES D APPAREILS :';
SELECT TypeName, Category, Description
FROM DeviceType
WHERE TypeName IN (N'TV', N'Ventilateur', N'Refrigerateur', N'Lampe', N'Routeur WiFi')
ORDER BY TypeName;

PRINT '';
PRINT 'APPAREILS DECLARES :';
SELECT DeviceId, DeviceCode, DeviceName, PowerW, dt.TypeName, Status
FROM Device d
INNER JOIN DeviceType dt ON d.DeviceTypeId = dt.DeviceTypeId
WHERE DeviceCode LIKE 'TV-%'
   OR DeviceCode LIKE 'Ventilateur-%'
   OR DeviceCode LIKE 'Refrigerateur-%'
   OR DeviceCode LIKE 'Lampe-%'
   OR DeviceCode LIKE 'Routeur%'
ORDER BY DeviceName;

PRINT '';
PRINT 'PROGRAMMES D UTILISATION PAR CRENEAU :';
SELECT d.DeviceName, ts.SlotName, dus.DailyUsageHours, dus.IsEnabled
FROM DeviceUsageSchedule dus
INNER JOIN Device d ON dus.DeviceId = d.DeviceId
INNER JOIN TimeSlot ts ON dus.TimeSlotId = ts.TimeSlotId
ORDER BY d.DeviceName, ts.SlotName;

PRINT '';
PRINT '========== INSERTION COMPLETEE AVEC SUCCES ==========';
