USE solar;
GO

SET XACT_ABORT ON;
GO

BEGIN TRANSACTION;

BEGIN TRY
    DECLARE @tvTypeId TINYINT;

    SELECT @tvTypeId = DeviceTypeId
    FROM DeviceType
    WHERE TypeName = N'ELECTRONIQUE';

    IF @tvTypeId IS NULL
    BEGIN
        INSERT INTO DeviceType (TypeName, Category, Description)
        VALUES (N'ELECTRONIQUE', N'Divertissement', N'Appareils electroniques');

        SET @tvTypeId = SCOPE_IDENTITY();
    END;

    -- Suppression des donnees liees a l'usage et aux materiels.
    DELETE FROM EnergyConsumption;
    DELETE FROM DeviceUsageSchedule;
    DELETE FROM Device;

    -- Reinitialisation des identites pour repartir de 1.
    DBCC CHECKIDENT ('EnergyConsumption', RESEED, 0);
    DBCC CHECKIDENT ('DeviceUsageSchedule', RESEED, 0);
    DBCC CHECKIDENT ('Device', RESEED, 0);

    -- Insertion de 3 televisions uniquement.
    INSERT INTO Device (DeviceCode, DeviceName, DeviceTypeId, PowerW, InstallationDate, Status)
    VALUES
    (N'TV001', N'Television 23W', @tvTypeId, 23, CAST(GETDATE() AS DATE), N'ACTIF'),
    (N'TV002', N'Television 20W', @tvTypeId, 20, CAST(GETDATE() AS DATE), N'ACTIF'),
    (N'TV003', N'Television 10W', @tvTypeId, 10, CAST(GETDATE() AS DATE), N'ACTIF');

    -- Planning d'usage attendu:
    -- TV001 -> NUIT 2h = 46 Wh
    -- TV002 -> SOIR 2h = 40 Wh
    -- TV003 -> JOUR 1h = 10 Wh
    INSERT INTO DeviceUsageSchedule (DeviceId, TimeSlotId, DailyUsageHours, IsEnabled)
    SELECT d.DeviceId,
           ts.TimeSlotId,
           v.DailyUsageHours,
           1
    FROM (VALUES
        (N'TV001', N'NUIT', CAST(2.0 AS DECIMAL(5,2))),
        (N'TV002', N'SOIR', CAST(2.0 AS DECIMAL(5,2))),
        (N'TV003', N'JOUR', CAST(1.0 AS DECIMAL(5,2)))
    ) AS v(DeviceCode, SlotName, DailyUsageHours)
    INNER JOIN Device d ON d.DeviceCode = v.DeviceCode
    INNER JOIN TimeSlot ts ON ts.SlotName = v.SlotName;

    COMMIT TRANSACTION;

    SELECT N'OK' AS Status,
           (SELECT COUNT(*) FROM Device) AS DeviceCount,
           (SELECT COUNT(*) FROM EnergyConsumption) AS EnergyConsumptionCount,
            (SELECT COUNT(*) FROM DeviceUsageSchedule) AS DeviceUsageScheduleCount;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO
