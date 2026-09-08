#set document(title: "Gérer un portefeuille en suivant des règles fixées à l'avance", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [portfolio-ops-ca], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Gérer un portefeuille en suivant des règles fixées à l'avance]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-08 · #link("https://github.com/Guilou001/03-gestion-portefeuille")[Guilou001/03-gestion-portefeuille]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Un plan de placement précise quelle part de l'argent va aux actions, aux obligations et à l'immobilier. Mais les prix changent. Une part prévue à 25 % peut devenir trop grande après une hausse.

Le gestionnaire doit décider quand revenir vers son plan. Il peut aussi modifier les montants parce qu'il prévoit qu'un marché fera mieux qu'un autre. Ce projet compare ces deux décisions sur six fonds cotés à Toronto.

*Le plan suivi sans prévisions rapporte davantage sur la période étudiée.* Les prévisions ajoutées n'améliorent pas le résultat après les frais.

== Attendre une limite avant d'acheter ou de vendre

Une bande de tolérance est l'écart autorisé autour de la part prévue. Pour les actions canadiennes, la cible est 25 % et la zone autorisée va de 20 % à 30 %.

#figure(image("../results/figures/presentation.png", width: 100%), caption: [Croissance annuelle des trois règles après coûts])

Les barres comparent la croissance annuelle après coûts. La règle qui attend le franchissement des limites finit devant celle qui ajoute des prévisions. Le tableau suivant donne aussi leur plus forte baisse.

== Ce que donnent les deux choix

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Règle*],
    [*Rendement annuel composé*],
    [*Plus forte baisse depuis un sommet*],
    [Suivre les bandes sans prévisions],
    [6,63 %],
    [−28,1 %],
    [Modifier les parts avec des prévisions],
    [6,25 %],
    [−29,2 %],
    [Mettre la même somme dans chaque fonds],
    [5,91 %],
    [−31,5 %],
)

Ces résultats couvrent *novembre 2007 à août 2026*, soit 226 mois. Les frais sont de 0,10 % par montant échangé. L'achat initial n'est facturé à aucune des règles. #link("results/tables/backtest_resume.csv")[Table complète].

== Comment les décisions sont prises

Les prévisions reposent sur les hausses récentes et sur les baisses des cinq dernières années. Le modèle de Black-Litterman les combine avec le plan initial, en tenant compte de la confiance accordée à chacune.

Le programme utilise seulement les mois antérieurs à la décision. Les montants restent dans les bandes autorisées. Il produit ensuite un #link("reports/monthly/2026-08.md")[rapport mensuel] qui indique les positions et explique leurs écarts au plan.

== Les limites du résultat

Le test porte sur un seul profil, avec 65 % d'actifs de croissance et 35 % d'obligations. Les prévisions et leur degré de confiance sont des choix déclarés. Le résultat ne condamne donc pas toutes les prévisions possibles. La fiscalité et l'effet des gros ordres sur les prix ne sont pas modélisés.

== Refaire les calculs

#raw("uv sync --locked --all-extras\nuv run pops fetch\nuv run pops backtest\nuv run pops report\nuv run pytest", block: true, lang: "bash")

Les commandes de téléchargement accèdent aux sources externes. Les résultats publiés restent consultables sans lancer les calculs. Le graphique de présentation se régénère hors réseau avec #raw("uv run python scripts/figure_presentation.py"), depuis les tableaux publiés.

== Pour aller plus loin

#link("docs/ETUDE_DETAILLEE.md")[Méthodes, résultats complets et références] · #link("rapport/rapport.pdf")[Présentation en PDF] · #link("CITATION.cff")[Citer le projet] · #link("LICENSE")[Licence].

== English summary

A Canadian portfolio following fixed allocation bands outperforms the tested forecast-driven allocation after costs over November 2007 to August 2026. The result concerns one policy and two specified forecast rules.
