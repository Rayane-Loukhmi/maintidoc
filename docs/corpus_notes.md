# Notes sur le corpus

## Document

- **ID** : `SAN-MAN-001`
- **Titre** : Manuel de maintenance SAN — SAN-LAB 2000
- **Révision** : 1.1
- **Pages** : 9
- **Tableaux** : 9
- **Images** : 6 (couverture + 5 schémas)
- **Nature** : corpus pédagogique fictif

## Structure des pages

| Page | Contenu | Images | Tableaux |
|---:|---|---:|---:|
| 1 | couverture | 1 | 0 |
| 2 | présentation et périmètre | 1 (FIG-01) | 1 |
| 3 | Fibre Channel et MPIO | 1 (FIG-02) | 1 |
| 4 | contrôleurs, disques, capacité | 1 (FIG-03) | 1 |
| 5 | voyants et alarmes | 1 (FIG-04) | 1 |
| 6 | workflow et sécurité | 1 (FIG-05) | 1 |
| 7 | historique fictif + questions | 0 | 3 |
| 8 | page de séparation | 0 | 0 |
| 9 | annexes et index | 0 | 1 |

## Schémas

| ID | Page | Contenu |
|---|---:|---|
| FIG-01 | 2 | architecture logique |
| FIG-02 | 3 | Fibre Channel et MPIO |
| FIG-03 | 4 | contrôleurs et disques |
| FIG-04 | 5 | voyants du simulateur |
| FIG-05 | 6 | workflow de maintenance |

## Tableaux notables

- **ALARM-TAB-01** : codes AL-00 à AL-04.
- **PROC-SAN-01** : procédure documentaire standard.
- **Ticket exemple** : champs `Equipment ID`, `Titre`, `Description`, `Preuves`.
- **Jeu de questions** : Q01 à Q12.

## Questions de référence

Le fichier `eval/questions.jsonl` contient 14 questions :

- 12 questions issues du manuel ;
- 2 questions volontairement sans réponse (prix, niveau RAID exact).

Chaque question porte :

- `expected_pages` ;
- `expected_figures` ;
- `expected_status` ;
- `visual_query` pour CLIP.

## Problèmes d'extraction rencontrés

1. `table.extract()` perd les espaces : `Valeurpedagogique`, `AetB`.
   → corrigé avec `page.get_textbox(Rect(cell))`.
2. La page 8 ne contient que l'en-tête : ce n'est pas une erreur.
3. Les identifiants documentaires (`ALARM-TAB-01`) ne sont pas des identifiants
   de preuve (`P05-TAB01`) : le modèle peut les confondre.
   → les citations inconnues sont filtrées et signalées.

## Règles de citation

- Une preuve est identifiée par `element_id` + `page`.
- Les identifiants sont stables (`P05-TEXT`, `P05-TAB01`, `P05-IMG01`).
- La couverture (`COVER`) n'est pas indexée.
