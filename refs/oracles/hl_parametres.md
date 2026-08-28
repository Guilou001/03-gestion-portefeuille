# Paramètres imprimés dans He et Litterman (1999), « The Intuition Behind Black-Litterman Model Portfolios »

Source : `refs/HeLitterman_1999_intuition.pdf` (Goldman Sachs Investment Management Research,
décembre 1999). Les pages citées sont les numéros imprimés en pied de page ; dans le fichier PDF,
la page imprimée n correspond à la page n+1 du fichier (page imprimée 3 = page 4 du PDF).
Chaque valeur ci-dessous a été relue sur le rendu image du PDF, pas seulement sur l'extraction
texte. Statut : mesuré (copié du PDF) sauf mention « dérivé ».

## Delta (aversion au risque)

- δ = 2.5, note de bas de page 3, page imprimée 4 : « Throughout our examples, we use δ = 2.5 as
  the risk aversion parameter representing the world average risk tolerance. »
- Attention : l'extraction texte (`HeLitterman_1999_intuition.txt`, ligne 378) rend « δ = 25. »,
  artefact d'extraction ; le PDF imprime bien 2.5.
- Les rendements d'équilibre s'obtiennent par Π = δ Σ w_eq (Appendix B, point 2, page imprimée 17).

## Tau

- Aucune valeur numérique de τ n'est imprimée dans ce papier. Note de bas de page 6, page
  imprimée 6 : « There is no need to separately specify the value of τ since only the ratio ω/τ
  enters the Black-Litterman expected returns formula. »
- Calibration par défaut (même note 6) : ω/τ = p'Σp pour chaque vue, c'est-à-dire
  Ω/τ = diag(p_k' Σ p_k). Sauf mention contraire, toutes les vues du papier utilisent cette
  calibration.
- La valeur τ = 0.05 souvent associée à He-Litterman vient d'Idzorek (2005), pas de ce papier.

## Sigma (matrice de covariance)

- Non imprimée directement : se reconstruit par Σ_ij = ρ_ij σ_i σ_j depuis Table 1 (volatilités)
  et Table 2 (corrélations), Appendix A, page imprimée 16. Table 2 imprime le triangle inférieur
  sans diagonale ; `hl_table2_correlations.csv` complète par symétrie et diagonale 1.000 (dérivé
  trivialement, pas imprimé).

## Vues, P, Q et Omega par exemple

### Exemple 0, approche moyenne-variance traditionnelle (Charts 1A, 1B, 1C, pages imprimées 3 à 5)

- Chart 1A : rendements espérés égaux à 7 % pour tous les pays, puis décalage Allemagne +2.5 %,
  France et UK −2.5 % (page imprimée 3). Pas de P/Ω : ce n'est pas encore le modèle BL.
- Chart 1B : départ des rendements d'équilibre ; Allemagne fixée 5 % au-dessus de la moyenne
  pondérée par capitalisation de France et UK, somme européenne pondérée inchangée, écart
  France-UK inchangé (page imprimée 4). Décalages imprimés sur le graphique : Allemagne 1.7 %,
  France 0.6 %, UK 0.4 % (flèches ; l'Allemagne monte, France et UK baissent ; le signe n'est pas
  imprimé, il se lit sur les barres).

### Exemple 1, une vue (Charts 2A, 2B, 2C, pages imprimées 6 à 8)

- Vue : « German equity will outperform the rest of Europe by 5% per year », exprimée comme
  rendement espéré de 5 % sur le portefeuille long Allemagne, short France et UK en poids de
  capitalisation (page imprimée 6). Q = 5 %.
- P (1×7, ordre AUL, CAN, FRA, GER, JAP, UKG, USA) : décrit verbalement, jamais imprimé en
  chiffres. Dérivé depuis Table 1 : GER = +1, FRA = −5.2/(5.2+12.4) = −0.2955,
  UKG = −12.4/(5.2+12.4) = −0.7045, autres = 0. Statut : dérivé.
- Ω : ω/τ = p'Σp (note 6, page imprimée 6).

### Exemple 2, deux vues (Charts 3A, 3B, page imprimée 9)

- Vue 1 : identique à l'exemple 1 (Q1 = 5 %).
- Vue 2 : « the Canadian equity market will outperform the US equity market by 3% per annum »
  (page imprimée 9). Q2 = 3 %. P2 : CAN = +1, USA = −1, autres = 0 (dérivé de l'énoncé verbal).
- Ω : ω_k/τ = p_k'Σp_k pour les deux vues ; vues indépendantes, Ω diagonale (Appendix B, point 3,
  page imprimée 17).

### Exemple 3 et variantes (Chart 4, page imprimée 10)

Trois scénarios comparés, poids Λ des portefeuilles de vues en ordonnée (axe 0 à 0.6, aucune
valeur numérique imprimée sur les barres) :

1. « Example 3 » : les deux vues de l'exemple 2 (Q = 5 % et 3 %, ω_k/τ = p_k'Σp_k).
2. « More Bullish on Canada/USA » : Q2 passe de 3 % à 4 %, tout le reste inchangé.
3. « Less Confident on Germany/Europe » : confiance sur la vue Allemagne réduite de moitié
   (« only half as confident as in the previous example », donc ω1 doublé : ω1/τ = 2 p1'Σp1,
   dérivé de l'énoncé) ; vue Canada/USA maintenue à Q2 = 4 %.

### Contraintes (Charts 5, 6, 7, pages imprimées 11 à 13)

Deux vues de l'exemple 2 (avec Q2 = 3 %) dans les trois cas :

- Chart 5 : contrainte de risque, volatilité cible 20 % par an (page imprimée 11).
- Chart 6 : contraintes de risque et de budget (somme des poids = 1), page imprimée 12.
- Chart 7 : contraintes de risque, budget et bêta (bêta = 1 vs portefeuille de marché), page
  imprimée 13. Formules des solutions : Appendix C, page imprimée 18.

## Exhibits sans valeurs numériques imprimées

Vérifié sur le rendu image de chaque page : les graphiques suivants sont purement graphiques
(axes gradués et légendes, aucune étiquette de donnée sur les barres). Aucun poids n'en a été
extrait ; toute valeur utilisée en test doit venir du recalcul, pas de ces charts.

| Exhibit | Contenu | Page imprimée |
|---|---|---|
| Chart 1C | poids optimaux MV traditionnel, équilibre vs décalé | 5 |
| Chart 2A | rendements espérés BL, une vue | 7 |
| Chart 2B | poids optimaux BL, une vue | 8 |
| Chart 2C | déviations optimales, une vue | 8 |
| Chart 3A | portefeuilles des vues et déviations optimales, deux vues | 9 |
| Chart 3B | poids du portefeuille BL, deux vues | 9 |
| Chart 4 | poids Λ des vues, trois scénarios | 10 |
| Chart 5 | deux vues, contrainte de risque | 11 |
| Chart 6 | deux vues, risque et budget | 12 |
| Chart 7 | deux vues, risque, budget et bêta | 13 |

Seuls Chart 1A (trois poids : 71.4 % AUL, −33.5 % GER, −94.8 % FRA, repris dans
`hl_charts.csv`) et Chart 1B (trois décalages de rendements espérés : 1.7 % GER, 0.6 % FRA,
0.4 % UKG, ci-dessus) impriment des valeurs.

## Note sur ce papier vs les valeurs « He-Litterman » usuelles

Les tables numériques complètes de poids et de rendements souvent citées pour He-Litterman
(Tables 4 à 7 dans d'autres versions du même papier, reprises par les répliques comme
Walters 2014) n'apparaissent pas dans cette version du PDF : non trouvé dans ce document. Les
tests qui veulent des poids cibles complets doivent les recalculer depuis Table 1, Table 2 et les
paramètres ci-dessus, ou citer une autre édition du papier en la datant.
