# Comparatif DeepSeek vs Claude — tokens et coût

**Projet :** MaintiDoc  
**Date :** 2026-11-27  
**Objet :** comparer la consommation réelle observée sous DeepSeek Flash avec une
facturation équivalente sur Claude Fable 5.2.

---

## 1. Périmètre

Deux périmètres sont distingués :

| Périmètre | Définition |
|---|---|
| **MaintiDoc** | à partir de la demande de réalisation du projet jusqu’à aujourd’hui |
| **Session complète** | depuis la restructuration initiale du cours jusqu’à aujourd’hui |

Les tokens proviennent du journal de session DSH, qui enregistre les champs
`inputTokens`, `outputTokens` et `cacheReadTokens` pour chaque appel.

---

## 2. Tokens mesurés

### 2.1. MaintiDoc

| Métrique | Valeur |
|---|---:|
| Appels modèle | 342 |
| Entrée non cachée | 757 544 |
| Sortie | 203 482 |
| Cache read | 214 795 520 |
| **Total contexte** | **215 756 546** |
| **Nouveaux tokens** | **961 026** |

### 2.2. Session complète

| Métrique | Valeur |
|---|---:|
| Appels modèle | 664 |
| Entrée non cachée | 1 287 001 |
| Sortie | 459 519 |
| Cache read | 297 898 624 |
| **Total contexte** | **299 645 144** |
| **Nouveaux tokens** | **1 746 520** |

> « Nouveaux tokens » = entrée non cachée + sortie.  
> Le total de contexte inclut les relectures de cache, facturées séparément.

---

## 3. Tarifs utilisés

### 3.1. DeepSeek Flash

Modèle : `deepseek-flash` — DeepSeek-V4.1-Flash-1017.

| Poste | Heures creuses | Heures pleines |
|---|---:|---:|
| Entrée, cache miss | 0,15 $ / M | 0,30 $ / M |
| Entrée, cache hit | 0,003 $ / M | 0,006 $ / M |
| Sortie | 0,60 $ / M | 1,20 $ / M |

Source : [DeepSeek API Pricing](https://api-docs.deepseek.com/quick_start/pricing)

### 3.2. Claude Fable 5.2

| Poste | Prix |
|---|---:|
| Entrée | 8,00 $ / M |
| Sortie | 40,00 $ / M |
| Cache read | 0,20 $ / M |
| Cache write 5 min | 10,00 $ / M |
| Cache write 1 h | 16,00 $ / M |

Source : [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing)

---

## 4. Coût pour MaintiDoc

### 4.1. DeepSeek Flash

#### Heures creuses

| Poste | Calcul | Coût |
|---|---|---:|
| Entrée | 757 544 × 0,15 / 1 M | 0,11 $ |
| Cache read | 214 795 520 × 0,003 / 1 M | 0,64 $ |
| Sortie | 203 482 × 0,60 / 1 M | 0,12 $ |
| **Total** |  | **0,88 $** |

#### Heures pleines

| Poste | Coût |
|---|---:|
| Entrée | 0,23 $ |
| Cache read | 1,29 $ |
| Sortie | 0,24 $ |
| **Total** | **1,76 $** |

**Fourchette DeepSeek : 0,88 $ – 1,76 $.**

### 4.2. Claude Fable 5.2

| Poste | Calcul | Coût |
|---|---|---:|
| Entrée | 757 544 × 8 / 1 M | 6,06 $ |
| Cache read | 214 795 520 × 0,20 / 1 M | 42,96 $ |
| Sortie | 203 482 × 40 / 1 M | 8,14 $ |
| **Total** |  | **57,16 $** |

**Claude : 57,16 $.**

### 4.3. Rapport

| Modèle | Coût MaintiDoc |
|---|---:|
| DeepSeek Flash, creux | **0,88 $** |
| DeepSeek Flash, pleines | **1,76 $** |
| Claude Fable 5.2 | **57,16 $** |

**Claude coûte environ 32× à 65× plus cher que DeepSeek Flash sur ce projet.**

---

## 5. Coût pour la session complète

### 5.1. DeepSeek Flash

| Poste | Creux | Pleines |
|---|---:|---:|
| Entrée | 0,19 $ | 0,39 $ |
| Cache read | 0,89 $ | 1,79 $ |
| Sortie | 0,28 $ | 0,55 $ |
| **Total** | **1,36 $** | **2,72 $** |

### 5.2. Claude Fable 5.2

| Poste | Calcul | Coût |
|---|---|---:|
| Entrée | 1 287 001 × 8 / 1 M | 10,30 $ |
| Cache read | 297 898 624 × 0,20 / 1 M | 59,58 $ |
| Sortie | 459 519 × 40 / 1 M | 18,38 $ |
| **Total** |  | **88,26 $** |

### 5.3. Rapport

| Modèle | Coût session |
|---|---:|
| DeepSeek Flash, creux | **1,36 $** |
| DeepSeek Flash, pleines | **2,72 $** |
| Claude Fable 5.2 | **88,26 $** |

**Claude coûte environ 32× à 65× plus cher que DeepSeek Flash sur la session.**

---

## 6. Effet du tokenizer Claude

Claude 4.7+ utilise un tokenizer qui produit environ **30 % de tokens en plus**
pour le même texte. Fable 5.2 est concerné.

Si on applique ce facteur aux tokens mesurés :

| Périmètre | DeepSeek creux | DeepSeek pleines | Claude +30 % |
|---|---:|---:|---:|
| MaintiDoc | 0,88 $ | 1,76 $ | **74,31 $** |
| Session | 1,36 $ | 2,72 $ | **114,73 $** |

Le rapport passe alors à environ **42× – 84×**.

---

## 7. Cache writes

Le coût Claude ci-dessus ne comprend **pas** les écritures de cache.

Dans un vrai usage Claude, il faudrait ajouter :

- 10 $ / M pour un cache de 5 minutes ;
- 16 $ / M pour un cache d’une heure.

Les tokens mesurés ne permettent pas de distinguer les cache writes des cache
reads. Le coût réel Claude est donc **supérieur** à 57 $ / 88 $ si le cache est
créé à chaque session.

---

## 8. Ce qui n’est pas inclus

- frais de recherche web ;
- outils serveur ;
- fast mode Claude ;
- taxes ;
- éventuel abonnement ou forfait.

Si l’usage DeepSeek est couvert par un forfait, son **coût marginal** est proche
de zéro ; les montants ci-dessus sont les coûts API théoriques.

---

## 9. Lecture des résultats

### Pourquoi Claude est beaucoup plus cher

1. **Prix d’entrée** : 8 $/M contre 0,15–0,30 $/M.
2. **Prix de sortie** : 40 $/M contre 0,60–1,20 $/M.
3. **Cache read** : 0,20 $/M contre 0,003–0,006 $/M.

Le cache read représente **75 % du coût Claude** pour MaintiDoc :

```text
42,96 $ / 57,16 $ = 75,2 %
```

### Pourquoi le cache est central

Le cache contient 214,8 M de tokens pour MaintiDoc, contre 757 544 tokens
d’entrée non cachée.

C’est ce qui rend Claude très coûteux malgré un cache à 0,20 $/M : le volume est
énorme.

---

## 10. Conclusion

| Question | Réponse |
|---|---|
| Coût DeepSeek Flash pour MaintiDoc | **0,88 $ – 1,76 $** |
| Coût Claude Fable 5.2 pour MaintiDoc | **57,16 $** |
| Coût Claude avec tokenizer +30 % | **74,31 $** |
| Coût DeepSeek session | **1,36 $ – 2,72 $** |
| Coût Claude session | **88,26 $** |
| Coût Claude session +30 % | **114,73 $** |
| Rapport | **≈ 32× à 65×** |

**Conclusion :** pour ce projet, DeepSeek Flash est environ **32 à 65 fois moins
cher** que Claude Fable 5.2 à volume de tokens identique, et l’écart monte à
**42–84×** si on tient compte du tokenizer Claude.

---

## 11. Sources

- [DeepSeek API Pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Journal de session DSH : champs `usage` des 664 appels.
