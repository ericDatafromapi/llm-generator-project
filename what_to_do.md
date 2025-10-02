
# MVP “LLM-Ready avec Mdream” — Phase 1 (Minimal)

> **Objectif :** un **unique script Python** qui lance **Mdream** sur un site, puis génère un dossier `md/` + `llms.txt` (et `llms-full.txt`) dans un répertoire `output/`.
> **Pas d’API, pas de CI** pour l’instant — juste un outil local/CLI, simple et fiable.

## Stack & contraintes

* **Python 3.11** (standard library uniquement : `argparse`, `subprocess`, `json`, `pathlib`, `zipfile`, `datetime`).
* Mdream est appelé via **Docker** (prioritaire) ou fallback **npx** si Docker indisponible.
* Code clair, commenté, **zéro dépendance externe**.

## À livrer (fichiers)

```
llmready_min.py       # CLI
README.md             # guide d'utilisation
.output.example/      # (optionnel) structure d’exemple
```

## Fonctionnalités (strict minimum)

1. **CLI** `llmready_min.py` avec options :

   * `--origin` (obligatoire) : URL racine du site à crawler.
   * `--out` (défaut: `./output`) : dossier de sortie.
   * `--include` (optionnel, CSV) : ex. `"docs,faq,pricing"`.
   * `--exclude` (optionnel, CSV) : ex. `"login,cart"`.
   * `--use-playwright` (bool) : `false` par défaut.
   * `--max-pages` (int, défaut raisonnable: 500).
   * `--timeout` (int secondes, défaut: 300).
   * `--zip` (bool) : si présent, zippe les artefacts en fin de run.
2. **Détection d’environnement** :

   * Si `docker` dispo → utiliser `docker run --rm harlanzw/mdream …`.
   * Sinon, tenter `npx @mdream/crawl …` (vérifier que `node`/`npx` existent).
   * Message d’erreur clair si aucun des deux n’est dispo.
3. **Exécution Mdream** :

   * Lance le crawl/conversion avec les flags transmis.
   * Doit produire **`<out>/md/`**, **`<out>/llms.txt`**, **`<out>/llms-full.txt`**.
4. **Manifest minimal** :

   * Créer `<out>/manifest.json` avec :

     ```json
     {
       "origin": "...",
       "started_at": "ISO8601",
       "ended_at": "ISO8601",
       "duration_sec": 0.0,
       "total_files": 0
     }
     ```
   * `total_files` = nb de fichiers dans `<out>/md/` + 2 txt (si présents).
5. **Validation & code retour** :

   * Si `llms.txt` **ou** le dossier `md/` manquent → exit code ≠ 0 + message explicite.
6. **Option ZIP** :

   * Si `--zip` : créer `<out>.zip` contenant `md/`, `llms.txt`, `llms-full.txt`, `manifest.json`.

## UX en ligne de commande (exemples)

```bash
python llmready_min.py --origin https://example.com

python llmready_min.py \
  --origin https://example.com \
  --out ./output \
  --include "docs,faq,pricing" \
  --exclude "login,cart" \
  --max-pages 300 \
  --timeout 240 \
  --zip
```

## Détails d’implémentation attendus

* **Construction de commande Mdream (Docker prioritaire)** :

  * Docker :

    ```
    docker run --rm -v <abs_out>:/out harlanzw/mdream crawl \
      --origin <origin> --out /out \
      [--include "..."] [--exclude "..."] \
      [--playwright] --timeout <timeout> --max-pages <max_pages>
    ```
  * Fallback npx :

    ```
    npx @mdream/crawl --origin <origin> --out <abs_out> \
      [--include "..."] [--exclude "..."] \
      [--playwright] --timeout <timeout> --max-pages <max_pages>
    ```
* **Logs** : imprimer la commande exécutée et un résumé (durée, nb fichiers).
* **Robustesse** : capturer `stdout/stderr`, afficher une erreur claire si Mdream retourne un code ≠ 0.

## README.md (contenu)

* **What/Why (2 lignes)** : Génère `md/` + `llms.txt` via **Mdream** pour rendre un site “LLM-ready”.
* **Prereqs** : Docker **ou** Node+npx.
* **Install** : rien (Python stdlib).
* **Usage** : exemples de commandes ci-dessus.
* **Sorties** : structure du dossier `output/` + `manifest.json`.
* **Astuce POC (30 min)** :

  1. Choisir 10–20 pages clés.
  2. Lancer `llmready_min.py …`.
  3. Vérifier `llms.txt` + `md/`.
  4. Poser 5 questions “avant/après” à une IA en lui donnant ces URLs Markdown.

## Critères d’acceptation

* En lançant :

  ```
  python llmready_min.py --origin https://example.com --out ./output
  ```

  on obtient **`./output/md/`**, **`./output/llms.txt`**, **`./output/llms-full.txt`**, **`./output/manifest.json`**.
* Le script **échoue proprement** (exit code ≠ 0) si Mdream n’a pas pu générer les fichiers.
* L’option `--zip` produit `./output.zip`.

> **Note :** Mdream est l’outil cœur (crawler + HTML→Markdown + `llms.txt`). Cette Phase 1 te donne un **outil local prêt à l’emploi** pour faire des POC rapides chez des prospects.
