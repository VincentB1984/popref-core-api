# Popref Local pour Windows

**Popref Local** est une version autonome de l’outil de génération de dossiers de population de référence. Elle traite les fichiers Excel sur le poste de l’utilisateur : aucun fichier de données, aucune carte et aucun dossier HTML n’est envoyé vers un serveur tiers.

## Installation et lancement

Après avoir téléchargé l’archive `Popref-Windows.zip` depuis l’onglet **Actions** du dépôt GitHub, extrayez **tout** son contenu dans un dossier local, par exemple `C:\Outils\Popref`. Double-cliquez ensuite sur `Popref.exe`.

L’application ouvre automatiquement votre navigateur sur une adresse locale de la forme `http://127.0.0.1:xxxxx`. Il ne s’agit pas d’un site web public : cette adresse ne fonctionne que sur votre poste.

> Windows peut afficher un avertissement SmartScreen tant que l’exécutable n’est pas signé numériquement. Vérifiez que l’archive provient bien du dépôt officiel `VincentB1984/popref-core-api`, puis choisissez **Informations complémentaires** et **Exécuter quand même** si nécessaire.

## Utilisation

Sélectionnez le classeur Popref fourni par l’INSEE, recherchez une commune par son nom ou son code INSEE, puis cliquez sur **Générer le dossier HTML**. Les codes à cinq chiffres, les communes corses (`2A…`, `2B…`) et les communes d’outre-mer figurant dans l’onglet `COM` sont pris en charge.

L’option **« Enrichir avec les données publiques INSEE »** est activée par défaut. Elle permet d’ajouter les blocs de logements, de pyramide des âges et de naissances-décès lorsque les pages INSEE sont accessibles. Une connexion internet est requise uniquement pour cet enrichissement ; le reste de la génération fonctionne à partir du classeur local.

Les cartes lissées PNG peuvent être ajoutées avant la génération. Le moteur reconnaît leurs noms portables déjà définis dans `popref_core` et signale les cartes facultatives non trouvées sans empêcher la production du dossier.

| Élément | Emplacement local sous Windows |
|---|---|
| Fichiers Excel importés | `%LOCALAPPDATA%\Popref\imports` |
| Cartes PNG importées | `%LOCALAPPDATA%\Popref\assets` |
| Dossiers HTML et payloads JSON | `%LOCALAPPDATA%\Popref\dossiers` |
| Journal de diagnostic | `%LOCALAPPDATA%\Popref\logs\popref-local.log` |

## Construire l’exécutable Windows depuis GitHub

Le dépôt contient le workflow prêt à l’emploi dans `docs/build-windows.workflow.yml`. Une seule étape manuelle est nécessaire, car le jeton GitHub de développement ne possède pas l’autorisation de créer un workflow au nom de l’utilisateur.

Dans GitHub, créez le fichier `.github/workflows/build-windows.yml`, copiez-y exactement le contenu de `docs/build-windows.workflow.yml`, puis validez le commit sur la branche `master`. Ouvrez ensuite **Actions** → **Construire Popref pour Windows** → **Run workflow**. À la fin du traitement, téléchargez l’artefact **Popref-Windows**.

Ce build est réalisé sur `windows-latest` avec Python 3.11 et PyInstaller. Il produit une distribution de type `onedir` : gardez les fichiers extraits ensemble, car `Popref.exe` s’appuie sur les bibliothèques incluses à ses côtés.
