USE solar;
GO

/* =========================
   CONFIGURATION
   ========================= */

INSERT INTO SystemConfiguration (
    GridVoltageV,
    SolarPanelEfficiencyPct,
    BatteryOvercapacityPct,
    Description,
    IsActive
)
VALUES (230, 40, 50, N'Configuration par défaut', 1);
GO


/* =========================
   TIME SLOTS
   ========================= */

INSERT INTO TimeSlot (SlotName, StartHour, EndHour, Description)
VALUES 
(N'JOUR', 6, 17, N'Journée (6h à 17h)'),
(N'SOIR', 17, 19, N'Soirée (17h à 19h) - transition'),
(N'NUIT', 19, 6, N'Nuit (19h à 6h)');
GO


/* =========================
   DEVICE TYPES
   ========================= */

INSERT INTO DeviceType (TypeName, Category, Description)
VALUES
(N'LUMIERE', N'Eclairage', N'Appareils d’éclairage'),
(N'ELECTROMENAGER', N'Maison', N'Appareils domestiques'),
(N'ELECTRONIQUE', N'Divertissement', N'Appareils électroniques');
GO


/* =========================
   DEVICES
   ========================= */

INSERT INTO Device (DeviceCode, DeviceName, DeviceTypeId, PowerW, InstallationDate, Status)
VALUES
(N'LAMP001', N'Ampoule Salon', 1, 10, '2025-01-01', N'ACTIF'),
(N'FRIGO01', N'Réfrigérateur', 2, 150, '2024-06-15', N'ACTIF'),
(N'TV001', N'Télévision', 3, 100, '2025-02-10', N'ACTIF'),
(N'MICRO01', N'Micro-ondes', 2, 1200, '2025-03-01', N'ACTIF');
GO


/* =========================
   DEVICE USAGE SCHEDULE
   ========================= */

INSERT INTO DeviceUsageSchedule (DeviceId, TimeSlotId, DailyUsageHours)
VALUES
(1, 1, 4), -- lampe jour
(1, 2, 2), -- lampe soir
(1, 3, 4), -- lampe nuit
(2, 1, 11), -- frigo jour
(2, 2, 2), -- frigo soir
(2, 3, 7), -- frigo nuit
(3, 2, 2), -- tv soir
(3, 3, 1), -- tv nuit
(4, 1, 0.5); -- micro-ondes jour
GO


/* =========================
   ENERGY CONSUMPTION
   ========================= */

INSERT INTO EnergyConsumption (
    DeviceId,
    TimeSlotId,
    ConsumptionDate,
    EnergyConsumedWh,
    DurationHours
)
VALUES
-- Jour (6h-17h, 11h)
(1, 1, '2026-04-10', 40, 4),      -- lampe jour
(2, 1, '2026-04-10', 1650, 11),   -- frigo jour
(4, 1, '2026-04-10', 600, 0.5),   -- micro-ondes jour

-- Soir (17h-19h, 2h)
(1, 2, '2026-04-10', 20, 2),      -- lampe soir
(2, 2, '2026-04-10', 300, 2),     -- frigo soir
(3, 2, '2026-04-10', 200, 2),     -- tv soir

-- Nuit (19h-6h, 11h)
(1, 3, '2026-04-10', 40, 4),      -- lampe nuit après 19h
(2, 3, '2026-04-10', 1050, 7),    -- frigo nuit
(3, 3, '2026-04-10', 100, 1);     -- tv nuit
GO


/* =========================
   SOLAR PRODUCTION
   ========================= */

INSERT INTO SolarPanelProduction (
    ProductionDate,
    TimeSlotId,
    TotalPanelCapacityW,
    ProductionPercentage
)
VALUES
('2026-04-10', 1, 2500, 100),  -- JOUR : production maximale
('2026-04-10', 2, 2500, 50),   -- SOIR : 50% (soleil se couche)
('2026-04-10', 3, 2500, 0);    -- NUIT : 0% (pas de soleil)
GO


/* =========================
   BATTERY STORAGE
   ========================= */

INSERT INTO BatteryStorage (
    BatteryCode,
    TotalCapacityWh,
    CurrentChargeWh,
    MinChargeWh,
    MaxChargeWh,
    ChargingEfficiencyPct,
    Status
)
VALUES
(N'BAT001', 10000, 5000, 1000, 9000, 95, N'ACTIF');
GO


/* =========================
   BATTERY MOVEMENTS
   ========================= */

INSERT INTO BatteryMovement (
    BatteryId,
    MovementDate,
    TimeSlotId,
    MovementType,
    EnergyMovedWh,
    ChargeBeforeWh,
    ChargeAfterWh,
    SolarProductionId
)
VALUES
(1, '2026-04-10', 1, N'CHARGE', 1250, 5000, 6250, 1),    -- charge JOUR
(1, '2026-04-10', 2, N'CHARGE', 625, 6250, 6875, 2),     -- charge SOIR
(1, '2026-04-10', 3, N'DECHARGE', 1420, 6875, 5455, NULL); -- décharge NUIT
GO