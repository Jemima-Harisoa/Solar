/*
  Script d insertion de types de panneaux solaires
  Reinitialise et insere les donnees de panneaux personnalises
*/

USE solar;
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

/* =========================
   REINITIALISER LES TYPES DE PANNEAUX
   ========================= */

DELETE FROM PanelType WHERE 1=1;

GO

PRINT 'Types de panneaux existants supprimes';
GO


/* =========================
   INSERER LES NOUVEAUX TYPES DE PANNEAUX
   ========================= */

INSERT INTO PanelType (TypeName, ExploitablePct, UnitEnergyW, UnitPriceAr, Description)
VALUES
    (N'PANNEAU TYPE 1', 40, 110, 215000, N'Panneau Type 1 : 110W brut, 40% exploitable, soit 44W utiles - Prix: 215000 Ar'),
    (N'PANNEAU TYPE 2', 30, 130, 200000, N'Panneau Type 2 : 130W brut, 30% exploitable, soit 39W utiles - Prix: 200000 Ar');

GO

PRINT 'Types de panneaux inseres';
GO


/* =========================
   AFFICHER LE RESUME
   ========================= */

PRINT '';
PRINT '========== TYPES DE PANNEAUX INSEREES ==========';
PRINT '';

SELECT 
    PanelTypeId AS ID,
    TypeName AS TypePanneau,
    ExploitablePct AS ExploitablePct,
    UnitEnergyW AS EnergieBruteW,
    UsableEnergyW AS EnergieUtileW,
    UnitPriceAr AS PrixUnitaireAr,
    Description
FROM PanelType
ORDER BY PanelTypeId;

PRINT '';
PRINT '========== INSERTION COMPLETEE AVEC SUCCES ==========';
