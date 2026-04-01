"""Prompt engineering templates pour l'agent d'analyse de tendances Reddit.

Techniques utilisées :
- Role assignment avec persona experte
- Structured output (JSON / Markdown imposé)
- Chain-of-thought reasoning
- Grounding constraints (pas de fabrication)
- Temperature tuning par tâche
- Langue française imposée
"""

# ── Prompt Système Principal ──────────────────────────────────────────
SYSTEM_PROMPT = """\
Tu es **TrendScope**, un analyste expert en culture internet et prévision de tendances.

## Mission
Analyser les données brutes de Reddit pour identifier, expliquer et prédire les tendances émergentes.

## Règles strictes
1. Ancre chaque affirmation dans les données fournies — ne fabrique JAMAIS de posts ou statistiques.
2. Quand tu manques d'information, dis-le clairement ; ne spécule pas.
3. Quantifie systématiquement (scores, nombre de commentaires, ratios).
4. Rédige en français clair et concis, adapté à un briefing professionnel.
5. Structure ta sortie exactement comme demandé dans chaque prompt utilisateur.
6. Utilise le raisonnement étape par étape (chain-of-thought) avant de conclure.
"""

# ── Identification des Tendances ──────────────────────────────────────
TREND_IDENTIFICATION_PROMPT = """\
Voici un tableau JSON des top posts Reddit collectés aujourd'hui sur plusieurs subreddits.

```json
{posts_json}
```

### Tâche
Identifie les **{n} principales tendances émergentes** de ces posts.

Raisonne étape par étape :
1. Regroupe les posts par thèmes similaires.
2. Évalue l'ampleur de chaque thème (scores cumulés, nombre de posts).
3. Identifie le sentiment dominant.

Pour chaque tendance, fournis :
1. **topic** — titre court et descriptif (≤ 8 mots).
2. **summary** — 2-3 phrases expliquant ce qui se passe.
3. **evidence** — liste des titres de posts et subreddits qui soutiennent cette tendance.
4. **sentiment** — sentiment global (Positif / Négatif / Mixte / Neutre).
5. **momentum** — Hausse 🔺, Stable ➡️, ou Baisse 🔻 selon les signaux d'engagement.
6. **score** — score d'importance de 1 à 10.

Retourne UNIQUEMENT un tableau JSON d'objets avec les clés : \
`topic`, `summary`, `evidence`, `sentiment`, `momentum`, `score`.
Si le format JSON n'est pas lisible, privilégie un format Markdown structuré avec titres, listes et paragraphes.
"""

# ── Analyse Approfondie (Deep Dive) ──────────────────────────────────
DEEP_DIVE_PROMPT = """\
Voici un post Reddit et ses meilleurs commentaires.

**Post**
- Titre : {title}
- Subreddit : r/{subreddit}
- Score : {score} | Commentaires : {num_comments}
- Texte : {selftext}

**Top Commentaires**
{comments}

### Tâche
Fournis une analyse approfondie en français :
1. **Arguments clés** — résume les 3 principaux points de vue de la discussion.
2. **Consensus vs. Controverse** — où la communauté est-elle d'accord / en désaccord ?
3. **Contexte élargi** — utilise tes connaissances pour expliquer pourquoi ce sujet compte maintenant.
4. **Prédiction** — que va-t-il probablement se passer ensuite ?

Rédige en Markdown structuré avec des titres.
"""

# ── Prévisions ────────────────────────────────────────────────────────
FORECAST_PROMPT = """\
Voici les tendances identifiées aujourd'hui :

{trends_summary}

### Tâche
Agis en tant que stratège prévisionniste. Pour chaque tendance :
1. **Perspective court terme (1-7 jours)** — va-t-elle croître, stagner ou s'estomper ?
2. **Potentiel long terme (1-3 mois)** — peut-elle devenir mainstream ?
3. **Signaux à surveiller** — qu'est-ce qui confirmerait ou invaliderait la prévision ?
4. **Insight actionnable** — une recommandation concrète pour un veilleur (journaliste, marketeur, investisseur, développeur).

Retourne une liste numérotée correspondant à l'ordre des tendances. Rédige en français.
"""

# ── Résumé Exécutif ──────────────────────────────────────────────────
EXECUTIVE_SUMMARY_PROMPT = """\
En utilisant toute l'analyse ci-dessous, rédige un **Briefing Exécutif** adapté à un public dirigeant.

{full_analysis}

### Format
- **Titre principal** (≤ 12 mots capturant l'histoire dominante du jour)
- **Top 3 Tendances** — un paragraphe chacune
- **Risques & Opportunités** — liste à puces
- **Actions recommandées** — 3 prochaines étapes concrètes

Limite le total à 500 mots. Rédige en français.
Rédige de manière accessible. Après chaque section, ajoute un encadré **Glossaire** qui définit en 1 phrase les termes techniques, acronymes et noms de projets mentionnés (ex: LLaMA, supply chain attack, CVE, RAG, MCP, etc.).
"""

# ── Corrélations Cross-Subreddit ─────────────────────────────────────
CORRELATION_PROMPT = """\
Voici les posts tendance de plusieurs subreddits :

{posts_json}

### Tâche
Identifie les **corrélations cross-subreddit** : sujets ou thèmes qui apparaissent dans 2+ subreddits simultanément.

Pour chaque corrélation :
1. **theme** — le thème partagé
2. **subreddits** — les subreddits concernés
3. **significance** — pourquoi cette convergence est importante

Retourne un tableau JSON avec les clés : `theme`, `subreddits`, `significance`.
Si le format JSON n'est pas lisible, privilégie un format Markdown structuré avec titres, listes et paragraphes.
"""

# ── Analyse de Sentiment Avancée ─────────────────────────────────────
SENTIMENT_ANALYSIS_PROMPT = """\
Voici les posts et commentaires d'un subreddit :

**Subreddit** : r/{subreddit}

**Posts et commentaires** :
{posts_data}

### Tâche
Analyse le sentiment de cette communauté. Raisonne étape par étape :

1. Lis chaque post et ses commentaires.
2. Évalue le ton (positif, négatif, neutre) de chacun.
3. Calcule le sentiment global pondéré par l'engagement.

Retourne un objet JSON avec :
- `subreddit` : nom du subreddit
- `score` : score de sentiment entre -1.0 (très négatif) et +1.0 (très positif)
- `label` : "Très positif" / "Positif" / "Neutre" / "Négatif" / "Très négatif"
- `dominant_emotions` : liste des 3 émotions dominantes
- `key_drivers` : les 3 sujets qui influencent le plus le sentiment
- `sample_size` : nombre de posts analysés
Si le format JSON n'est pas lisible, privilégie un format Markdown structuré avec titres, listes et paragraphes.
"""

# ── Analyse des Signaux Faibles ──────────────────────────────────────
WEAK_SIGNALS_PROMPT = """\
Voici des posts Reddit détectés comme **signaux faibles** : peu d'upvotes mais un taux de commentaires anormalement élevé, ce qui indique un sujet en émergence.

```json
{weak_signals_json}
```

### Tâche
Pour chaque signal faible :
1. **Pourquoi ce sujet génère-t-il autant de discussion ?**
2. **A-t-il le potentiel de devenir viral ?** (Oui / Peut-être / Non) avec justification.
3. **Catégorisation** : Controverse / Innovation / Crise / Curiosité / Autre.

Retourne un tableau JSON avec les clés : \
`title`, `subreddit`, `analysis`, `viral_potential`, `category`.
Si le format JSON n'est pas lisible, privilégie un format Markdown structuré avec titres, listes et paragraphes.

Rédige les analyses en français.
"""

# ── Recherche Web Enrichie ────────────────────────────────────────────
WEB_ENRICHMENT_PROMPT = """\
Voici une tendance détectée sur Reddit :

**Tendance** : {topic}
**Résumé** : {summary}
**Evidence Reddit** : {evidence}

### Tâche
En utilisant tes capacités de recherche web :
1. Trouve des **articles de presse récents** qui confirment ou nuancent cette tendance.
2. Identifie des **données chiffrées** (statistiques, cours boursiers, études) pertinentes.
3. Mentionne les **acteurs clés** impliqués (entreprises, personnalités, institutions).
4. Évalue la **fiabilité** de la tendance : est-ce un vrai mouvement ou un buzz éphémère ?

Retourne en JSON :
- `topic` : le sujet
- `web_sources` : liste d'articles/sources trouvés (titre + résumé en 1 phrase)
- `key_data` : données chiffrées clés
- `key_actors` : acteurs impliqués
- `reliability` : "Confirmée" / "Probable" / "Incertaine" / "Buzz éphémère"
- `enriched_summary` : résumé enrichi en 3-4 phrases
Si le format JSON n'est pas lisible, privilégie un format Markdown structuré avec titres, listes et paragraphes.

**FORMAT IMPORTANT** : Rédige en texte fluide et structuré, PAS en JSON brut.
Utilise des paragraphes, des listes à puces et des titres Markdown.
Chaque source doit être sur sa propre ligne avec un tiret.
Évite les structures imbriquées complexes.

Rédige en français.
"""

# ── Comparaison Historique ────────────────────────────────────────────
HISTORY_COMPARISON_PROMPT = """\
Voici les tendances d'aujourd'hui et celles de la dernière analyse :

**Tendances actuelles** :
{current_trends}

**Tendances précédentes** ({previous_date}) :
{previous_trends}

**Nouvelles tendances** : {new_trends}
**Tendances disparues** : {disappeared_trends}
**Tendances persistantes** : {persistent_trends}

### Tâche
Rédige une **analyse comparative** en français :
1. **Évolution** — comment le paysage a-t-il changé ?
2. **Tendances montantes** — lesquelles gagnent en puissance ?
3. **Tendances déclinantes** — lesquelles perdent de l'intérêt ?
4. **Surprise du jour** — le fait le plus inattendu.

Rédige en Markdown avec titres. Sois concis (< 300 mots).
"""
