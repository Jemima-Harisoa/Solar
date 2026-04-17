USE solar;
GO

SET ANSI_NULLS ON;
GO

SET QUOTED_IDENTIFIER ON;
GO

/* =========================
   TABLE PANNEAUX SOLAIRES
   ========================= */

-- Table : Types de panneaux solaires
-- Permet de parametrer le rendement exploitable, la puissance unitaire et le prix unitaire.
IF OBJECT_ID(N'dbo.PanelType', N'U') IS NULL
BEGIN
	CREATE TABLE PanelType (
		PanelTypeId       INT            IDENTITY PRIMARY KEY,
		TypeName          NVARCHAR(80)   NOT NULL UNIQUE,
		ExploitablePct    DECIMAL(5,2)   NOT NULL,
		UnitEnergyW       DECIMAL(12,2)  NOT NULL,
		UnitPriceAr       DECIMAL(18,2)  NOT NULL,
		Description       NVARCHAR(250)  NULL,
		CreatedAt         DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),

		UsableEnergyW AS (UnitEnergyW * ExploitablePct / 100.0) PERSISTED,

		CONSTRAINT CK_PanelType_Exploit CHECK (ExploitablePct > 0 AND ExploitablePct <= 100),
		CONSTRAINT CK_PanelType_Energy  CHECK (UnitEnergyW > 0),
		CONSTRAINT CK_PanelType_Price   CHECK (UnitPriceAr >= 0)
	);
END;
GO
