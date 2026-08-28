# Un moteur d'allocation sous politique de placement, aux modules vérifiés contre les papiers

Les quatre briques d'un gestionnaire de portefeuille institutionnel, en Python testé : Black-Litterman
(validé chiffre à chiffre contre He-Litterman 1999 et Idzorek 2005), parité de risque hiérarchique (López
de Prado 2016), attribution de Brinson-Fachler avec chaînage de Cariño, et bandes de rééquilibrage avec
coûts pour appliquer une politique de placement.

[![ci](https://github.com/Guilou001/portfolio-ops-ca/actions/workflows/ci.yml/badge.svg)](https://github.com/Guilou001/portfolio-ops-ca/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.12-blue)
![licence](https://img.shields.io/badge/code-MIT-green)

**Résultat en une phrase.** Le module Black-Litterman reproduit l'exemple complet d'Idzorek (2005) contre
les tables imprimées du papier : **rendements a posteriori exacts aux deux décimales, poids à 0,02 point
près, confiances implicites à 0,2 point près**, et l'équilibre de He-Litterman (1999) à 0,05 point ;
19 tests couvrent les quatre modules, dont les identités algébriques que chacun doit respecter.

*English summary.* The four building blocks of institutional portfolio operations, in tested Python:
Black-Litterman verified cell-by-cell against the printed tables of He-Litterman (1999) and Idzorek (2005)
(posterior returns exact to the printed 2 decimals, weights within 0.02 pt, implied confidence levels
within 0.2 pt); hierarchical risk parity (López de Prado, 2016); Brinson-Fachler performance attribution
with Cariño geometric linking (effects provably sum to the active return); and investment-policy
rebalancing bands with transaction costs. Next step: the Canadian monthly report engine on ETF data.

## 1. La question posée

Comment un gestionnaire passe-t-il d'une politique de placement, le document qui fixe les cibles par classe
d'actifs et les bandes de tolérance autour, à des décisions mensuelles justifiables ? Il lui faut quatre
mécanismes : incliner l'allocation vers ses vues sans casser le portefeuille (Black-Litterman), construire
des poids robustes quand la covariance est bruitée (HRP), expliquer chaque écart de rendement à la politique
(attribution de Brinson), et rééquilibrer au bon moment sans brûler la performance en coûts (bandes avec
hystérésis). Ce dépôt implémente les quatre, et surtout les vérifie.

## 2. D'où vient le projet, et ce qu'il apporte

Black-Litterman est partout dans l'industrie et presque toujours implémenté de travers, parce que trois
conventions cohabitent sans être imprimées dans les papiers : le rôle de tau, la construction d'Omega, et le
fait que les poids non contraints ne somment pas à 1 (He-Litterman, note 5 : le portefeuille sans vue
détient exactement w_eq/(1+tau)). Ce que ce dépôt apporte :

- **La vérification contre les sources.** Les tables des deux papiers fondateurs ont été extraites en CSV
  (`refs/oracles/`, artefacts d'impression documentés) et servent de tests : chaque convention est tranchée
  par un chiffre imprimé, pas par une opinion de forum.
- **Les quatre modules dans un seul paquet cohérent**, avec les identités algébriques testées (les trois
  effets de Brinson somment exactement à l'écart actif ; le chaînage de Cariño retombe sur l'écart
  géométrique composé ; les poids HRP sont positifs et somment à 1 ; une vue certaine est imposée
  exactement, une confiance nulle ne bouge rien).
- **La méthode d'Idzorek en fonction utilisable** : donner une confiance en pourcent à chaque vue, et le
  module calibre Omega numériquement pour que l'inclinaison des poids soit exactement cette fraction de
  l'inclinaison à confiance totale (testé : 50 % de confiance produit 50 % de l'inclinaison, à 2 % près).

## 3. Les données de vérification

| Source | Contenu | Usage |
|---|---|---|
| He et Litterman (1999), PDF UPenn | 7 pays : volatilités, poids d'équilibre, rendements d'équilibre, corrélations ; delta = 2,5 | oracle d'équilibre ; convention Omega/tau (seul le rapport omega/tau compte) |
| Idzorek (2005), PDF Duke | 8 classes d'actifs : les 8 tables du papier (équilibre, covariance, vues, a posteriori, poids, confiances) ; lambda = 3,07, tau = 0,025 | oracle de la chaîne complète |

Deux honnêtetés d'extraction, documentées dans `refs/oracles/` : la version UPenn du papier de He-Litterman
n'imprime des poids que pour un seul graphique (les autres sont purement graphiques, rien n'a été inventé) ;
et trois cellules d'Idzorek portent des artefacts d'arrondi du papier lui-même (par exemple sa Table 6
soustrait des valeurs non arrondies), conservés tels quels avec leur explication.

## 4. Les quatre modules, et ce que chacun garantit

1. **`black_litterman.py`.** L'optimisation inverse (les rendements qui justifient les poids de marché),
   la moyenne a posteriori entre équilibre et vues, la covariance d'estimation, les poids non contraints,
   l'Omega proportionnel de He-Litterman et l'Omega calibré par confiance d'Idzorek. Garanti par : les
   8 tests oracles ci-dessous.
2. **`hrp.py`.** La parité de risque hiérarchique en trois étapes du papier de 2016 : arbre de corrélations,
   réordonnancement, bissection récursive à l'inverse de la variance. Aucune inversion de matrice. Garanti
   par : poids positifs sommant à 1, préférence aux actifs peu volatils.
3. **`brinson.py`.** L'attribution Brinson-Fachler (allocation, sélection, interaction) et le chaînage
   géométrique de Cariño. Garanti par : la somme des effets égale l'écart actif à 10⁻¹² près sur une
   période, et l'écart géométrique composé en multi-périodes.
4. **`policy.py`.** La politique de placement mécanisée : dérive des poids, bandes de tolérance avec
   hystérésis (on ne touche à rien tant qu'on est dans la bande), rééquilibrage au bord de bande (moins
   coûteux que le retour à la cible), coûts en points de base. Garanti par : un scénario testé où seul un
   choc de 25 % déclenche l'unique rééquilibrage attendu.

## 5. Les résultats de vérification (mesurés)

| Ce qui est comparé | Tolérance | Verdict |
|---|---:|---|
| Équilibre He-Litterman, 7 pays (delta = 2,5) | 0,05 pt | reproduit |
| Lambda d'Idzorek (prime de 3 % sur le marché) | 0,01 | 3,07, reproduit |
| Omega de l'équation 8 d'Idzorek | 5 × 10⁻⁷ | reproduit |
| Rendements a posteriori, 8 classes (Table 6) | 0,01 pt | exacts aux 2 décimales imprimées |
| Nouveaux poids (Table 6) | 0,02 pt | reproduits (l'écart vient des arrondis d'impression) |
| Poids à confiance totale (Table 7) | 0,02 pt | reproduits |
| Confiances implicites (Table 7) | 0,2 pt | reproduites |

Comment lire ce tableau, en deux constats : d'abord, la chaîne Black-Litterman complète colle aux deux
papiers dans leurs conventions respectives, y compris la différence de convention entre eux (Idzorek
optimise avec Sigma seule, He-Litterman avec Sigma plus la covariance d'estimation, les deux sont dans le
module et testées) ; ensuite, les tolérances non nulles viennent des arrondis d'impression des papiers,
documentés cellule par cellule dans `refs/oracles/idzorek_parametres.md`, pas de l'implémentation.

## 6. Reproduire

```bash
uv sync --locked --all-extras     # environnement verrouillé (Python 3.12, pandas 3)
uv run pytest                     # 19 tests : 8 oracles papier + 11 propriétés algébriques, sans réseau
```

Durée mesurée : la suite complète tourne en 3 secondes ; les oracles sont commités (petits CSV de valeurs
publiées), la CI les rejoue à chaque commit.

## 7. Limites, avec leur statut

| Limite | Statut |
|---|---|
| Le moteur canadien de bout en bout (FNB, vues systématiques momentum/valorisation, rapport mensuel régénérable, backtest 1996-2026 net de coûts) | à venir ; c'est la moitié applicative de la fiche, les modules vérifiés ici en sont les fondations |
| La version UPenn de He-Litterman n'imprime pas les tables 4 à 7 des autres éditions | non trouvé ; l'oracle se limite à ce que ce PDF imprime |
| Entropy pooling (vues non linéaires) et poids contraints (long-only) dans Black-Litterman | à venir ; le module expose déjà la covariance a posteriori nécessaire |
| Le chaînage de Cariño est un choix parmi d'autres (Menchero, GRAP) | reconnu ; choisi pour sa propriété de somme exacte, testée |

## 8. Crédits, licence, citation

He, G. et Litterman, R. (1999), « The Intuition Behind Black-Litterman Model Portfolios », Goldman Sachs
Investment Management Research ; Idzorek, T. (2005), « A Step-by-Step Guide to the Black-Litterman Model » ;
López de Prado, M. (2016), « Building Diversified Portfolios that Outperform Out of Sample », Journal of
Portfolio Management ; Brinson, G. et Fachler, N. (1985) ; Cariño, D. (1999). Code : Guillaume Vaudescal,
2026, licence MIT ; les valeurs des oracles restent celles des papiers cités.
