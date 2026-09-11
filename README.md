# Light & Lens

Photography within Euler Letters AI’s multidisciplinary practice, alongside
[Math to Code](https://eulerlettersai.github.io/math-to-code/) and
[Letters & Verse](https://eulerlettersai.github.io/letters-and-verse/).

Site: https://eulerlettersai.github.io/light-and-lens/

## Add Hamza’s photographs

One-time local setup with uv (Python 3.11 or newer):

```sh
uv sync
```

Import a folder of JPEG, PNG, or WebP photographs:

```sh
uv run python scripts/gallery.py import "/path/to/photographs"
```

Or pass individual image paths. Hamza Elkababji is the default photographer.
The command copies originals into `photos/hamza-elkababji/` without modifying
them and adds entries to `data/photos.json`. Original files retain their metadata;
review any location or other embedded information before publishing.
Duplicate names are rejected without overwriting an existing photograph.
Use descriptive filenames such as `Sunset over Wadi Rum.jpg` for initial titles.
Review the generated titles and write meaningful `alt` descriptions in the catalogue;
optionally add a `description`. File order in the catalogue controls gallery order.

Then commit and push:

```sh
git add photos data
git commit -m "Add photographs by Hamza Elkababji"
git push origin main
```

GitHub Actions generates smaller WebP previews and publishes the gallery. No layout
edits or manually generated thumbnails are required. Images are shown without cropping.
Downloads use the untouched originals. The page and download links work without JavaScript;
JavaScript adds the copy-attribution button and mobile navigation.

## Preview locally

```sh
uv run python scripts/gallery.py build
uv run python -m http.server 8000 --directory _site
```

Open http://localhost:8000. `_site/` is disposable build output; do not store originals
there. Rebuilding removes it, including obsolete published photographs.
The root `index.html` is the template; serve `_site/` to see catalogue entries.

## Add another photographer

Add a record to `data/photographers.json`, using a unique ID:

```json
"photographer-id": {
  "name": "Photographer Name",
  "url": "https://example.com/profile",
  "terms": "Photographer-approved reuse terms. Attribution required."
}
```

Then import with:

```sh
uv run python scripts/gallery.py import "/path/to/photos" --photographer photographer-id
```

Every preview’s credit automatically links to that photographer’s profile.
Hamza’s profile is https://www.linkedin.com/in/hamzakababji/.

## Attribution and reuse

Every photo offers a linked credit, copyable attribution with a source link, and reuse
terms beside its download. Attribution remains visible if clipboard access fails.
The current wording requires attribution and directs visitors to the photographer for
permission covering their intended use. It does not assume permission for commercial
use or editing. Replace the photographer’s `terms` with their approved wording when
available; a photo’s optional `terms` field overrides that photographer’s default.

The repository’s Apache 2.0 license covers the website software, not the photographs.
Photographs remain the property of their respective photographers and are governed
by their stated reuse terms. Downloading cannot technically enforce subsequent credit.

## Storage

Start with originals in `photos/`; no database or backend is needed. Previews are generated
only into the published artifact. Keep the combined originals, previews, and site below
GitHub Pages’ 1 GB published-site limit. Do not commit individual files of 100 MiB or more.
Deleting an image from the catalogue removes it from future deployments, but previously
committed originals remain in Git history.

For a larger collection, host originals and previews on HTTPS object storage and use an
entry with `original` and `preview` URLs plus `width` and `height` in pixels. Local and
external entries can coexist. The build never downloads external images. Configure the
host’s Content-Disposition header for attachment downloads; otherwise the original opens
in another tab and visitors can save it there. No gallery layout changes are needed.

## Publishing and maintenance

In repository **Settings → Pages → Build and deployment**, select **GitHub Actions** once.
The workflow builds and tests pull requests, and publishes pushes to `main`.
Only `_site/` is deployed; scripts, data files, and the Python environment are excluded.

`styles.css` matches the parent site. `gallery.css` contains gallery-only additions using
the parent’s design variables. To adopt later parent design updates, copy its stylesheet
here and review the gallery. No changes are needed in sibling repositories.

Run checks with:

```sh
uv run python -m unittest discover -s tests
```

References: [GitHub Pages workflow setup](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages),
[Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
