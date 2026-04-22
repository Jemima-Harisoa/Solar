/*
  Reset de la base Solar en conservant PanelType
  Vide les donnees metier et les donnees de reference utiles a l'import.
*/

USE solar;
GO

SET NOCOUNT ON;
GO
SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

/* =========================
   SUPPRESSION DES DONNEES DEPENDANTES
   ========================= */

DELETE FROM BatteryMovement;
GO
DELETE FROM EnergyConsumption;
GO
DELETE FROM DeviceUsageSchedule;
GO
DELETE FROM SolarPanelProduction;
GO
DELETE FROM Device;
GO
DELETE FROM BatteryStorage;
GO
DELETE FROM DeviceType;
GO
DELETE FROM TimeSlot;
GO

/* =========================
   DONNEES CONSERVEES
   ========================= */

-- PanelType est conserve.
-- SystemConfiguration est conserve.

PRINT 'Base reinitialisee. PanelType conserve.';
GO