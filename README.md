# \# Transaction Reconciliation App

# 

# \## Description

# 

# Cette application permet de réaliser une \*\*réconciliation de transactions financières\*\* entre deux sources de données :

# 

# \- les transactions provenant de la \*\*plateforme de paiement\*\*

# \- les transactions provenant du \*\*système marchand\*\*

# 

# L'application compare les deux jeux de données afin de détecter :

# 

# \- les différences de montants

# \- les différences de frais

# \- les transactions dont le statut n'est pas valide

# \- les écarts dans les totaux

# 

# Un \*\*rapport Excel\*\* est ensuite généré pour faciliter l'analyse.

# 

# \---

# 

# \## Fonctionnalités

# 

# \- Import de \*\*plusieurs fichiers CSV\*\* pour chaque source

# \- Concaténation automatique des fichiers importés

# \- Comparaison des transactions entre les deux systèmes

# \- Détection des anomalies :

# &#x20; - montants différents

# &#x20; - frais différents

# &#x20; - statut incorrect

# \- Calcul des écarts globaux :

# &#x20; - dépôts

# &#x20; - retraits

# &#x20; - frais

# \- Génération d'un \*\*rapport Excel téléchargeable\*\*

# \- Interface simple via Streamlit

# 

# \---

# 

# \## Structure du projet

# 

# 

