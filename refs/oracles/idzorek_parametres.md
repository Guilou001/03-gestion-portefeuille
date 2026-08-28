# Paramètres de l'exemple à 8 actifs d'Idzorek (2005)

Source : Idzorek, T. M. (2005, brouillon du 2004-07-20), « A step-by-step guide to the
Black-Litterman model », Zephyr Associates. Fichiers : `refs/Idzorek_2005_onBL.pdf` (34 pages)
et `refs/Idzorek_2005_onBL.txt`. La pagination du papier va de 1 à 32 ; la page N du papier
correspond à la page N+2 du PDF (page de titre et résumé non paginés). Toutes les valeurs
ci-dessous sont copiées du papier (statut : rapporté), sauf mention « recalculé » (statut :
mesuré, recalcul du 2026-08-28 à partir de la Table 5 et des poids de marché de la Table 2).

Ordre des 8 actifs, constant dans tout le papier et dans les CSV :
US Bonds, Int'l Bonds, US Large Growth, US Large Value, US Small Growth, US Small Value,
Int'l Dev. Equity, Int'l Emerg. Equity.

## Les trois vues (page 7 du papier, page 9 du PDF)

| Vue | Énoncé | Type | Q | Confiance |
|---|---|---|---|---|
| 1 | Int'l Dev. Equity aura un rendement excédentaire absolu de 5,25 % | absolue | 5,25 % | 25 % |
| 2 | Int'l Bonds surperformera US Bonds de 25 points de base | relative | 0,25 % | 50 % |
| 3 | US Large Growth et US Small Growth surperformeront US Large Value et US Small Value de 2 % | relative | 2,00 % | 65 % |

Vecteur Q (équation 4, page 10) : Q = [5,25 ; 0,25 ; 2,00] en pourcents.

## Matrice P

Deux variantes sont imprimées. Les calculs du papier utilisent la seconde.

Pondération égale, à la Satchell et Scowcroft (équation 6, page 11) :

```
P_egal = [  0    0    0    0    0    0    1    0
           -1    1    0    0    0    0    0    0
            0    0    0.5 -0.5  0.5 -0.5  0    0 ]
```

Pondération par capitalisation, méthode retenue par Idzorek (équation 7, page 13),
dérivée des Tables 3a et 3b (page 9) :

```
P = [  0    0    0    0    0    0    1    0
      -1    1    0    0    0    0    0    0
       0    0    0.9 -0.9  0.1 -0.1  0    0 ]
```

## Aversion au risque (lambda, le papier n'emploie pas la lettre delta)

lambda ≈ 3,07 (note sous la Table 1, page 4). La note dit : prime de risque de « 3 »
divisée par la variance des rendements excédentaires du marché. Le signe % manque dans le
PDF lui-même ; la valeur 3 % est cohérente avec l'Excess Return de 3,000 % du portefeuille
de marché (Table 8, page 19). Recalculé : w'.Sigma.w = 0,0097854579, d'où
lambda = 0,03 / 0,0097854579 = 3,065774.

## Tau (page 15 du papier, page 17 du PDF)

tau = 0,025, choisi par hypothèse pour calibrer Omega à la He et Litterman (1999),
soit omega_k / tau = p_k.Sigma.p_k'. Le papier note que la valeur de tau devient alors
indifférente, seul le ratio omega/tau entre dans le modèle.

## Omega (équation 8, page 15)

Diagonale : Omega = diag(0,000709 ; 0,000141 ; 0,000866), soit tau fois les variances des
portefeuilles de vues de la Table 4 (page 13) : 2,836 %, 0,563 %, 3,462 %.
Recalculé depuis la Table 5 avec la matrice P par capitalisation :
0,000708875 ; 0,000140650 ; 0,000865628.

## Où trouver chaque table

| Table | Contenu | Page papier | Page PDF | CSV |
|---|---|---|---|---|
| 1 | Quatre vecteurs de rendements excédentaires attendus | 4 | 6 | idzorek_table1.csv |
| 2 | Poids recommandés et poids de marché | 5 | 7 | idzorek_table2.csv |
| 3a | Vue 3, mini-portefeuille « surperformant » | 9 | 11 | idzorek_table3a.csv |
| 3b | Vue 3, mini-portefeuille « sous-performant » | 9 | 11 | idzorek_table3b.csv |
| 4 | Variances des portefeuilles de vues | 13 | 15 | idzorek_table4.csv |
| 5 | Matrice de covariance des rendements excédentaires | 17 | 19 | idzorek_table5.csv |
| 6 | E[R], nouveaux poids et écarts | 17 | 19 | idzorek_table6.csv |
| 7 | Niveaux de confiance implicites | 23 | 25 | idzorek_table7.csv |
| 8 | Statistiques de portefeuille | 19 | 21 | idzorek_table8.csv |

Le papier n'imprime aucune matrice de corrélation ni annexe de données : la Table 5 est la
seule matrice imprimée. Il n'existe pas de « Table 3 » unique, la table 3 est scindée en 3a
et 3b dans le papier. Les colonnes suffixées `_pct` sont en pourcents tels qu'imprimés
(3.15 pour 3,15 %) ; la Table 5 est en décimales. Les cellules imprimées « -- » dans les
Tables 7 et 8 sont laissées vides dans les CSV.

## Vérifications faites (recalcul du 2026-08-28, numpy, script non conservé)

1. La Table 5 est symétrique et définie positive (valeur propre minimale 0,000632).
2. Pi = lambda.Sigma.w_mkt avec lambda = 3,065774 redonne la colonne Pi de la Table 1 à
   0,01 point près sur les 8 actifs.
3. Les variances des vues recalculées : 2,8355 %, 0,5626 %, 3,46251 %. La vue 3 s'imprime
   3,462 % dans la Table 4 alors que l'arrondi standard de 3,46251 donne 3,463 : écart d'une
   demi-unité sur la dernière décimale, voir « cellules douteuses ».
4. E[R] recalculé (formule 3) reproduit la colonne 2 de la Table 6 exactement aux 2
   décimales ; les poids recalculés reproduisent les Tables 6 et 7 à 0,01 point près
   (29,89 contre 29,88 ; 15,58 contre 15,59 ; 43,83 contre 43,82 ; 1,64 contre 1,65 ;
   confiance implicite 32,93 contre 32,94). Ces écarts viennent de l'arrondi à 2 décimales
   des entrées imprimées, pas d'une erreur du papier.
5. Table 8 recalculée : Excess Return 3,000 / 3,101, Variance 0,00979 / 0,01011 (le papier
   imprime 0,01012), écart-type 9,892 / 10,057 (le papier imprime 9,893 / 10,058). Écarts
   d'une unité sur la dernière décimale, imputables aux arrondis intermédiaires.

## Cellules douteuses ou artefacts d'extraction

1. Note de la Table 1 (page 4) : « a risk premium of 3 » sans signe %. Le % manque dans le
   PDF d'origine. Lire 3 %.
2. Table 4, vue 3 : 3,462 % imprimé contre 3,46251 % recalculé. Pour un test, tolérance
   d'une unité sur la troisième décimale ou recalcul direct depuis Table 5 et P.
3. Équation 8 : la diagonale d'Omega sort illisible de l'extraction texte
   (« 000007090. » etc.). Valeurs reconstruites 0,000709 / 0,000141 / 0,000866, confirmées
   par tau fois les variances de la Table 4.
4. Table 5 : l'extraction texte insère des espaces parasites (« 0. 023036 »,
   « -0 .002237 »). Valeurs restituées sans ambiguïté, symétrie vérifiée sur les 28 paires.
5. Table 6, colonne Différence : US Bonds affiche -0,02 % alors que 0,07 - 0,08 = -0,01 ;
   US Large Growth affiche 0,08 % alors que 6,50 - 6,41 = 0,09. Le papier a soustrait les
   valeurs non arrondies. Les CSV gardent les valeurs imprimées.
6. L'équation 4 (page 10) sort de l'extraction avec les chiffres de Q inversés
   (« 2 / 25.0 / 25.5 ») : lire Q = [5,25 ; 0,25 ; 2], cohérent avec les vues de la page 7.
