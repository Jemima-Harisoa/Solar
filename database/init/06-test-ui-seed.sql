USE solar;
GO

SET NOCOUNT ON;
GO

/* =========================
   CONFIG ACTIVE + PRIX VENTE
   ========================= */
IF NOT EXISTS (
    SELECT 1
    FROM SystemConfiguration
    WHERE Description = N'Config test UI surplus'
)
BEGIN
    INSERT INTO SystemConfiguration (
        GridVoltageV,
        SolarPanelEfficiencyPct,
        BatteryOvercapacityPct,
        Description,
        IsActive,
        EnergySellingPriceArWh,
        SellingPriceStartDate,
        SellingPriceEndDate
    )
    VALUES (230, 40, 50, N'Config test UI surplus', 0, 12.5000, NULL, NULL);
END;
GO

UPDATE SystemConfiguration SET IsActive = 0 WHERE IsActive = 1;
UPDATE SystemConfiguration
SET IsActive = 1, UpdatedAt = SYSUTCDATETIME()
WHERE Description = N'Config test UI surplus';
GO

/* =========================
   TIME SLOTS
   ========================= */
IF NOT EXISTS (SELECT 1 FROM TimeSlot WHERE SlotName = N'JOUR')
    INSERT INTO TimeSlot (SlotName, StartHour, EndHour, Description)
    VALUES (N'JOUR', 6, 17, N'Jour 6h-17h');

IF NOT EXISTS (SELECT 1 FROM TimeSlot WHERE SlotName = N'SOIR')
    INSERT INTO TimeSlot (SlotName, StartHour, EndHour, Description)
    VALUES (N'SOIR', 17, 19, N'Soir 17h-19h');

IF NOT EXISTS (SELECT 1 FROM TimeSlot WHERE SlotName = N'NUIT')
    INSERT INTO TimeSlot (SlotName, StartHour, EndHour, Description)
    VALUES (N'NUIT', 19, 6, N'Nuit 19h-6h');
GO

/* =========================
   DEVICE TYPES
   ========================= */
IF NOT EXISTS (SELECT 1 FROM DeviceType WHERE TypeName = N'ELECTRONIQUE')
    INSERT INTO DeviceType (TypeName, Category, Description)
    VALUES (N'ELECTRONIQUE', N'Divertissement', N'Appareils electroniques');

IF NOT EXISTS (SELECT 1 FROM DeviceType WHERE TypeName = N'ELECTROMENAGER')
    INSERT INTO DeviceType (TypeName, Category, Description)
    VALUES (N'ELECTROMENAGER', N'Maison', N'Appareils domestiques');

IF NOT EXISTS (SELECT 1 FROM DeviceType WHERE TypeName = N'LUMIERE')
    INSERT INTO DeviceType (TypeName, Category, Description)
    VALUES (N'LUMIERE', N'Eclairage', N'Appareils eclairage');
GO

/* =========================
   DEVICES
   ========================= */
IF NOT EXISTS (SELECT 1 FROM Device WHERE DeviceCode = N'TV-TEST-01')
BEGIN
    INSERT INTO Device (DeviceCode, DeviceName, DeviceTypeId, PowerW, Description, InstallationDate, Status)
    SELECT N'TV-TEST-01', N'Television Test', dt.DeviceTypeId, 100, N'TV scenario UI', CAST(GETDATE() AS DATE), N'ACTIF'
    FROM DeviceType dt
    WHERE dt.TypeName = N'ELECTRONIQUE';
END;

IF NOT EXISTS (SELECT 1 FROM Device WHERE DeviceCode = N'FOUR-TEST-01')
BEGIN
    INSERT INTO Device (DeviceCode, DeviceName, DeviceTypeId, PowerW, Description, InstallationDate, Status)
    SELECT N'FOUR-TEST-01', N'Four Test', dt.DeviceTypeId, 1200, N'Four scenario UI', CAST(GETDATE() AS DATE), N'ACTIF'
    FROM DeviceType dt
    WHERE dt.TypeName = N'ELECTROMENAGER';
END;

IF NOT EXISTS (SELECT 1 FROM Device WHERE DeviceCode = N'LAMP-TEST-01')
BEGIN
    INSERT INTO Device (DeviceCode, DeviceName, DeviceTypeId, PowerW, Description, InstallationDate, Status)
    SELECT N'LAMP-TEST-01', N'Lampe Test', dt.DeviceTypeId, 20, N'Lampe scenario UI', CAST(GETDATE() AS DATE), N'ACTIF'
    FROM DeviceType dt
    WHERE dt.TypeName = N'LUMIERE';
END;
GO

/* =========================
   DEVICE USAGE SCHEDULE
   ========================= */
DECLARE @tv_id INT = (SELECT DeviceId FROM Device WHERE DeviceCode = N'TV-TEST-01');
DECLARE @four_id INT = (SELECT DeviceId FROM Device WHERE DeviceCode = N'FOUR-TEST-01');
DECLARE @lamp_id INT = (SELECT DeviceId FROM Device WHERE DeviceCode = N'LAMP-TEST-01');

DECLARE @jour_id TINYINT = (SELECT TimeSlotId FROM TimeSlot WHERE SlotName = N'JOUR');
DECLARE @soir_id TINYINT = (SELECT TimeSlotId FROM TimeSlot WHERE SlotName = N'SOIR');
DECLARE @nuit_id TINYINT = (SELECT TimeSlotId FROM TimeSlot WHERE SlotName = N'NUIT');

IF @tv_id IS NOT NULL AND @jour_id IS NOT NULL
BEGIN
    IF EXISTS (SELECT 1 FROM DeviceUsageSchedule WHERE DeviceId = @tv_id AND TimeSlotId = @jour_id)
        UPDATE DeviceUsageSchedule
        SET DailyUsageHours = 1.00, UsageStartTime = '08:00', UsageEndTime = '09:00', IsEnabled = 1
        WHERE DeviceId = @tv_id AND TimeSlotId = @jour_id;
    ELSE
        INSERT INTO DeviceUsageSchedule (DeviceId, TimeSlotId, DailyUsageHours, UsageStartTime, UsageEndTime, IsEnabled)
        VALUES (@tv_id, @jour_id, 1.00, '08:00', '09:00', 1);
END;

IF @four_id IS NOT NULL AND @jour_id IS NOT NULL
BEGIN
    IF EXISTS (SELECT 1 FROM DeviceUsageSchedule WHERE DeviceId = @four_id AND TimeSlotId = @jour_id)
        UPDATE DeviceUsageSchedule
        SET DailyUsageHours = 1.00, UsageStartTime = '11:00', UsageEndTime = '12:00', IsEnabled = 1
        WHERE DeviceId = @four_id AND TimeSlotId = @jour_id;
    ELSE
        INSERT INTO DeviceUsageSchedule (DeviceId, TimeSlotId, DailyUsageHours, UsageStartTime, UsageEndTime, IsEnabled)
        VALUES (@four_id, @jour_id, 1.00, '11:00', '12:00', 1);
END;

IF @lamp_id IS NOT NULL AND @soir_id IS NOT NULL
BEGIN
    IF EXISTS (SELECT 1 FROM DeviceUsageSchedule WHERE DeviceId = @lamp_id AND TimeSlotId = @soir_id)
        UPDATE DeviceUsageSchedule
        SET DailyUsageHours = 1.00, UsageStartTime = '17:30', UsageEndTime = '18:30', IsEnabled = 1
        WHERE DeviceId = @lamp_id AND TimeSlotId = @soir_id;
    ELSE
        INSERT INTO DeviceUsageSchedule (DeviceId, TimeSlotId, DailyUsageHours, UsageStartTime, UsageEndTime, IsEnabled)
        VALUES (@lamp_id, @soir_id, 1.00, '17:30', '18:30', 1);
END;
GO

/* =========================
   PANEL TYPES
   ========================= */
IF NOT EXISTS (SELECT 1 FROM PanelType WHERE TypeName = N'Mono 550W Test')
BEGIN
    INSERT INTO PanelType (TypeName, UnitEnergyW, ExploitablePct, UnitPriceAr, PeakPowerWh, Description)
    VALUES (N'Mono 550W Test', 550, 85, 780000, 550, N'Panneau test UI 550W');
END;

IF NOT EXISTS (SELECT 1 FROM PanelType WHERE TypeName = N'Poly 420W Test')
BEGIN
    INSERT INTO PanelType (TypeName, UnitEnergyW, ExploitablePct, UnitPriceAr, PeakPowerWh, Description)
    VALUES (N'Poly 420W Test', 420, 80, 560000, 420, N'Panneau test UI 420W');
END;
GO

/* =========================
   VERIFICATION RAPIDE
   ========================= */
SELECT 'SystemConfiguration active' AS [Section], COUNT(*) AS [Rows] FROM SystemConfiguration WHERE IsActive = 1
UNION ALL
SELECT 'TimeSlot', COUNT(*) FROM TimeSlot
UNION ALL
SELECT 'DeviceType', COUNT(*) FROM DeviceType
UNION ALL
SELECT 'Device', COUNT(*) FROM Device
UNION ALL
SELECT 'DeviceUsageSchedule', COUNT(*) FROM DeviceUsageSchedule
UNION ALL
SELECT 'PanelType', COUNT(*) FROM PanelType;
GO
