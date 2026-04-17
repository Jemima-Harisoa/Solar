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

/* =========================
   DONNEES D'EXEMPLE PANNEAUX
   ========================= */

IF NOT EXISTS (SELECT 1 FROM PanelType WHERE TypeName = N'PANNEAU 100W 25%')
BEGIN
	INSERT INTO PanelType (TypeName, ExploitablePct, UnitEnergyW, UnitPriceAr, Description)
	VALUES (N'PANNEAU 100W 25%', 25, 100, 180000, N'Exemple : 100W brut, 25% exploitable, soit 25W utiles');
END;
GO

IF NOT EXISTS (SELECT 1 FROM PanelType WHERE TypeName = N'PANNEAU 200W 35%')
BEGIN
	INSERT INTO PanelType (TypeName, ExploitablePct, UnitEnergyW, UnitPriceAr, Description)
	VALUES (N'PANNEAU 200W 35%', 35, 200, 320000, N'Panneau plus puissant pour besoins moyens');
END;
GO

IF NOT EXISTS (SELECT 1 FROM PanelType WHERE TypeName = N'PANNEAU 400W 40%')
BEGIN
	INSERT INTO PanelType (TypeName, ExploitablePct, UnitEnergyW, UnitPriceAr, Description)
	VALUES (N'PANNEAU 400W 40%', 40, 400, 580000, N'Panneau haut rendement pour besoins plus importants');
END;
GO
