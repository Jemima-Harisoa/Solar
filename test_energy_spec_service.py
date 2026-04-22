"""
Étape 5: Tests unitaires pour EnergySpecService - Monétisation du surplus solaire.

7 cas de test pour calculer_surplus_monetisable():
1. Pas d'usage => tout le surplus est monétisable
2. Usage complet fenêtre => pas de surplus
3. Usage partiel (lacunes matin/après-midi)
4. Appareils chevauchants (consumption overlap)
5. Usage hors fenêtre (ignoré, pas de revenu)
6. Usage traversant la fenêtre (partiel comptabilisé)
7. Prix de vente zéro (pas de revenu)
"""

import pytest
from app.services.energy_spec_service import EnergySpecService


class TestCalculSurplusMonetisable:
    """Tests pour EnergySpecService.calculer_surplus_monetisable()"""

    @pytest.fixture
    def service(self):
        """Instance de service pour tous les tests."""
        return EnergySpecService()

    def test_case_1_no_usage_all_surplus(self, service):
        """
        Cas 1: Pas d'usage => tout le surplus est monétisable.
        
        Fenêtre solaire: 8h-17h
        Production: JOUR=100 Wh, SOIR=50 Wh, NUIT=0 Wh
        Usages: (vide)
        Prix: 10 Ar/Wh
        
        Résultat attendu:
        - JOUR (6-17h): production=100, conso=0, surplus=100, revenu=1000 Ar (chevauche fenêtre)
        - SOIR (17-19h): production=50, conso=0, surplus=50, revenu=0 Ar (hors fenêtre)
        - NUIT (19-6h): production=0, conso=0, surplus=0, revenu=0 Ar (hors fenêtre)
        - Total: surplus=150, revenu=1000 Ar
        """
        fenetre_solaire = (8.0, 17.0)
        production = {"JOUR": 100.0, "SOIR": 50.0, "NUIT": 0.0}
        usages = []
        prix = 10.0
        
        resultat = service.calculer_surplus_monetisable(fenetre_solaire, production, usages, prix)
        
        assert resultat["JOUR"]["production_wh"] == 100.0
        assert resultat["JOUR"]["consommation_wh"] == 0.0
        assert resultat["JOUR"]["surplus_wh"] == 100.0
        assert resultat["JOUR"]["revenu_ar"] == 1000.0
        
        assert resultat["SOIR"]["production_wh"] == 50.0
        assert resultat["SOIR"]["consommation_wh"] == 0.0
        assert resultat["SOIR"]["surplus_wh"] == 50.0
        assert resultat["SOIR"]["revenu_ar"] == 0.0
        
        assert resultat["NUIT"]["surplus_wh"] == 0.0
        assert resultat["NUIT"]["revenu_ar"] == 0.0
        
        assert resultat["total"]["surplus_wh"] == 150.0
        assert resultat["total"]["revenu_ar"] == 1000.0

    def test_case_2_full_usage_no_surplus(self, service):
        """
        Cas 2: Usage complet fenêtre => pas de surplus.
        
        Production: JOUR=200 Wh, SOIR=100 Wh, NUIT=50 Wh
        Usages: JOUR=200, SOIR=100, NUIT=50 (égale production)
        Prix: 10 Ar/Wh
        
        Résultat attendu:
        - Surplus=0 Wh, Revenu=0 Ar pour tous les crénaux
        """
        fenetre_solaire = (8.0, 17.0)
        production = {"JOUR": 200.0, "SOIR": 100.0, "NUIT": 50.0}
        usages = [
            {"creneau": "JOUR", "energie_wh": 200.0},
            {"creneau": "SOIR", "energie_wh": 100.0},
            {"creneau": "NUIT", "energie_wh": 50.0},
        ]
        prix = 10.0
        
        resultat = service.calculer_surplus_monetisable(fenetre_solaire, production, usages, prix)
        
        assert resultat["JOUR"]["surplus_wh"] == 0.0
        assert resultat["JOUR"]["revenu_ar"] == 0.0
        assert resultat["SOIR"]["surplus_wh"] == 0.0
        assert resultat["SOIR"]["revenu_ar"] == 0.0
        assert resultat["NUIT"]["surplus_wh"] == 0.0
        assert resultat["NUIT"]["revenu_ar"] == 0.0
        assert resultat["total"]["surplus_wh"] == 0.0
        assert resultat["total"]["revenu_ar"] == 0.0

    def test_case_3_partial_usage_morning_afternoon_gap(self, service):
        """
        Cas 3: Usage partiel avec lacunes (matin libre, usage soir).
        
        Production: JOUR=300 Wh
        Usages: JOUR=100 (sur 300) => 200 Wh surplus
        Prix: 5 Ar/Wh
        
        Résultat attendu:
        - JOUR: surplus=200, revenu=1000 Ar
        """
        fenetre_solaire = (8.0, 17.0)
        production = {"JOUR": 300.0, "SOIR": 0.0, "NUIT": 0.0}
        usages = [
            {"creneau": "JOUR", "energie_wh": 100.0},
        ]
        prix = 5.0
        
        resultat = service.calculer_surplus_monetisable(fenetre_solaire, production, usages, prix)
        
        assert resultat["JOUR"]["production_wh"] == 300.0
        assert resultat["JOUR"]["consommation_wh"] == 100.0
        assert resultat["JOUR"]["surplus_wh"] == 200.0
        assert resultat["JOUR"]["revenu_ar"] == 1000.0

    def test_case_4_overlapping_devices(self, service):
        """
        Cas 4: Appareils chevauchants dans même créneau.
        
        Production: JOUR=500 Wh
        Usages: JOUR=[150 Wh, 150 Wh] => consommation=300 Wh
        Prix: 2 Ar/Wh
        
        Résultat attendu:
        - JOUR: surplus=200, revenu=400 Ar
        """
        fenetre_solaire = (8.0, 17.0)
        production = {"JOUR": 500.0, "SOIR": 0.0, "NUIT": 0.0}
        usages = [
            {"creneau": "JOUR", "energie_wh": 150.0},
            {"creneau": "JOUR", "energie_wh": 150.0},
        ]
        prix = 2.0
        
        resultat = service.calculer_surplus_monetisable(fenetre_solaire, production, usages, prix)
        
        assert resultat["JOUR"]["consommation_wh"] == 300.0
        assert resultat["JOUR"]["surplus_wh"] == 200.0
        assert resultat["JOUR"]["revenu_ar"] == 400.0

    def test_case_5_usage_outside_window_ignored(self, service):
        """
        Cas 5: Usage hors fenêtre => ignoré, pas de revenu.
        
        Fenêtre: 8h-17h
        Production: JOUR=100, SOIR=50, NUIT=0
        Usages: NUIT=30 Wh (hors fenêtre => pas de revenu)
        Prix: 10 Ar/Wh
        
        Résultat attendu:
        - NUIT: revenu=0 (hors fenêtre) car 19h-6h n'intersecte pas 8h-17h
        - Total: revenu=1000 Ar (JOUR seulement)
        """
        fenetre_solaire = (8.0, 17.0)
        production = {"JOUR": 100.0, "SOIR": 50.0, "NUIT": 0.0}
        usages = [
            {"creneau": "NUIT", "energie_wh": 30.0},
        ]
        prix = 10.0
        
        resultat = service.calculer_surplus_monetisable(fenetre_solaire, production, usages, prix)
        
        assert resultat["NUIT"]["revenu_ar"] == 0.0
        assert resultat["JOUR"]["revenu_ar"] == 1000.0

    def test_case_6_usage_crossing_window_partial_count(self, service):
        """
        Cas 6: Usage traversant la fenêtre => partiel comptabilisé.
        
        Fenêtre: 8h-17h
        Production: JOUR=200, SOIR=100
        Usages: JOUR=200 (6h-17h, intersecte fenêtre)
        Prix: 5 Ar/Wh
        
        Résultat attendu:
        - JOUR: surplus=0 (production entière consommée)
        - SOIR: surplus=100, revenu=0 Ar (hors fenêtre 8-17h)
        """
        fenetre_solaire = (8.0, 17.0)
        production = {"JOUR": 200.0, "SOIR": 100.0, "NUIT": 0.0}
        usages = [
            {"creneau": "JOUR", "energie_wh": 200.0, "heure_debut": 6.0, "heure_fin": 17.0},
        ]
        prix = 5.0
        
        resultat = service.calculer_surplus_monetisable(fenetre_solaire, production, usages, prix)
        
        assert resultat["JOUR"]["consommation_wh"] == 200.0
        assert resultat["JOUR"]["surplus_wh"] == 0.0
        assert resultat["SOIR"]["surplus_wh"] == 100.0
        assert resultat["SOIR"]["revenu_ar"] == 0.0

    def test_case_7_zero_selling_price_no_revenue(self, service):
        """
        Cas 7: Prix de vente zéro => pas de revenu.
        
        Production: JOUR=150 Wh
        Usages: (vide)
        Prix: 0 Ar/Wh
        
        Résultat attendu:
        - Surplus=150, Revenu=0 Ar (prix=0)
        """
        fenetre_solaire = (8.0, 17.0)
        production = {"JOUR": 150.0, "SOIR": 0.0, "NUIT": 0.0}
        usages = []
        prix = 0.0
        
        resultat = service.calculer_surplus_monetisable(fenetre_solaire, production, usages, prix)
        
        assert resultat["JOUR"]["surplus_wh"] == 150.0
        assert resultat["JOUR"]["revenu_ar"] == 0.0
        assert resultat["total"]["surplus_wh"] == 150.0
        assert resultat["total"]["revenu_ar"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
