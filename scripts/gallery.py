"""Import originals and build a static photography gallery."""
import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote, urlsplit

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = 'https://eulerlettersai.github.io/light-and-lens/'
FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}


def read_data(root):
    return (json.loads((root / 'data/photographers.json').read_text()),
            json.loads((root / 'data/photos.json').read_text()))


def slug(value):
    result = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    if not result:
        raise ValueError('Use a filename containing letters or numbers.')
    return result


def https_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.netloc:
        raise ValueError(f'Expected an HTTPS URL: {value}')
    return value


def local_photo(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to((root / 'photos').resolve()) or not path.is_file():
        raise ValueError(f'Photo must be an existing file inside photos/: {value}')
    return path


def import_photos(root, sources, photographer):
    root = root.resolve()
    people, photos = read_data(root)
    if photographer not in people or slug(photographer) != photographer:
        raise ValueError('Add this photographer to data/photographers.json first.')
    files = []
    for source in sources:
        source = Path(source)
        if source.is_dir():
            files.extend(sorted(p for p in source.iterdir() if p.suffix.lower() in FORMATS))
        elif source.is_file() and source.suffix.lower() in FORMATS:
            files.append(source)
        else:
            raise ValueError(f'Expected a JPEG, PNG, WebP, or folder: {source}')
    if not files:
        raise ValueError('No supported images found.')
    pending = []
    known = {p['id'] for p in photos}
    for source in files:
        identity = f'{photographer}-{slug(source.stem)}'
        if identity in known:
            raise ValueError(f'Duplicate photo {identity}; rename the new file or edit the existing entry.')
        known.add(identity)
        destination = root / 'photos' / photographer / (slug(source.stem) + source.suffix.lower())
        if source.resolve().parent == (root / 'photos' / photographer).resolve():
            destination = source.resolve()
        if destination.exists() and destination.resolve() != source.resolve():
            raise ValueError(f'Refusing to overwrite {destination}')
        if source.stat().st_size >= 100 * 1024 * 1024:
            raise ValueError(f'{source.name} exceeds the repository file limit; use external storage.')
        with Image.open(source) as image:
            image.verify()
        title = re.sub(r'[-_]+', ' ', source.stem).strip()
        pending.append((source, destination, {
            'id': identity, 'photographer': photographer, 'title': title,
            'alt': title, 'description': '', 'original': destination.relative_to(root).as_posix()
        }))
    for source, destination, entry in pending:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
        photos.append(entry)
    (root / 'data/photos.json').write_text(json.dumps(photos, indent=2, ensure_ascii=False) + '\n')
    print(f'Imported {len(pending)} photo(s). Review titles and alt descriptions in data/photos.json.')


def build(root):
    root = root.resolve()
    people, photos = read_data(root)
    out = root / '_site'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    for name in ['styles.css', 'gallery.css', 'gallery.js', '.nojekyll']:
        shutil.copy2(root / name, out / name)
    shutil.copytree(root / 'assets', out / 'assets')
    cards, seen = [], set()
    e = html.escape
    for photo in photos:
        identity = photo['id']
        if slug(identity) != identity or identity in seen:
            raise ValueError(f'Invalid or duplicate photo ID: {identity}')
        seen.add(identity)
        person = people[photo['photographer']]
        profile = https_url(person['url'])
        title, alt = photo['title'].strip(), photo['alt'].strip()
        location = photo.get('location', {})
        place = ', '.join(location.get(key, '').strip() for key in ('city', 'country') if location.get(key, '').strip())
        display_title = f'{title} — {place}' if place else title
        terms = photo.get('terms', person.get('terms', '')).strip()
        if not title or not alt or not terms:
            raise ValueError(f'{identity} needs a title, alt description, and reuse terms.')
        original = photo['original']
        remote = original.startswith('https://')
        if remote:
            original = https_url(original)
            preview = https_url(photo['preview'])
            width, height = int(photo['width']), int(photo['height'])
            if width <= 0 or height <= 0:
                raise ValueError(f'Invalid dimensions for {identity}')
            meta = f'{width:,} × {height:,} pixels · Original file'
        else:
            source = local_photo(root, original)
            original = source.relative_to(root).as_posix()
            target = out / original
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            preview = f'previews/{identity}.webp'
            (out / 'previews').mkdir(exist_ok=True)
            with Image.open(source) as image:
                upright = ImageOps.exif_transpose(image)
                width, height = upright.size
                upright.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                upright.convert('RGB').save(out / preview, 'WEBP', quality=85, method=6)
            meta = f'{width:,} × {height:,} pixels · {source.stat().st_size / 1024 / 1024:.1f} MB'
            original = quote(original, safe='/')
        attribution = f'“{display_title}” — Photograph by {person["name"]} ({profile}). Source: {SITE_URL}#{identity}. {terms}'
        download = 'target="_blank" rel="noopener noreferrer"' if remote else 'download'
        remote_note = '<p class="photo-meta">Opens the original on the image host; use Save Image to download.</p>' if remote else ''
        cards.append(f'''<article class="card photo-card" id="{e(identity)}">
  <figure>
    <a class="photo-preview" href="{e(preview)}" target="_blank" rel="noopener noreferrer" aria-label="View preview: {e(title)}">
      <img src="{e(preview)}" alt="{e(alt)}" width="{width}" height="{height}" loading="lazy" decoding="async">
    </a>
    <figcaption class="photo-caption">
      <h3>{e(display_title)}</h3>
      <p class="photo-credit">Photograph by <a href="{e(profile)}" target="_blank" rel="noopener noreferrer">{e(person['name'])}</a></p>
      <p>{e(photo.get('description', ''))}</p>
      <p class="photo-meta">{e(meta)}</p>
      <p class="photo-terms">{e(terms)}</p>
      <div class="photo-actions">
        <a class="button primary" href="{e(original)}" {download} aria-label="Download full resolution: {e(title)}">Download full resolution</a>
        <button class="button ghost" type="button" data-copy-attribution>Copy attribution</button>
      </div>
      {remote_note}
      <details class="attribution"><summary>Attribution text</summary><p>{e(attribution)}</p></details>
      <p class="copy-status" role="status" aria-live="polite"></p>
    </figcaption>
  </figure>
</article>''')
    page = (root / 'index.html').read_text()
    if cards:
        start, end = '<!-- GALLERY_START -->', '<!-- GALLERY_END -->'
        before, rest = page.split(start)
        _, after = rest.split(end)
        page = before + start + '\n<div class="gallery-grid">\n' + '\n'.join(cards) + '\n</div>\n' + end + after
    (out / 'index.html').write_text(page)
    print(f'Built {len(cards)} photograph(s) in {out}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('build', help='Generate the site and previews in _site/')
    importer = commands.add_parser('import', help='Copy photos and add catalogue entries')
    importer.add_argument('sources', nargs='+', help='Image files or folders')
    importer.add_argument('--photographer', default='hamza-elkababji')
    args = parser.parse_args()
    try:
        if args.command == 'build':
            build(ROOT)
        else:
            import_photos(ROOT, args.sources, args.photographer)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'Gallery error: {error}\n')
