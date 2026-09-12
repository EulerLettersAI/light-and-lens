import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

spec = importlib.util.spec_from_file_location('gallery', Path(__file__).resolve().parents[1] / 'scripts/gallery.py')
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)

class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['index.html', 'styles.css', 'gallery.css', 'gallery.js', '.nojekyll']:
            shutil.copy2(gallery.ROOT / name, self.root / name)
        for name in ['assets', 'data']:
            shutil.copytree(gallery.ROOT / name, self.root / name)
        (self.root / 'data/photos.json').write_text('[]')
        self.source = self.root / 'Desert sunset.jpg'
        image = Image.new('RGB', (1600, 900), '#dfb45a')
        exif = image.getexif()
        exif[274] = 6
        image.save(self.source, exif=exif)

    def test_import_build_preserves_original_and_links_credit(self):
        gallery.import_photos(self.root, [self.source], 'hamza-elkababji')
        catalogue = self.root / 'data/photos.json'
        photos = json.loads(catalogue.read_text())
        photos[0]['title'] = '<Sunset & light>'
        photos[0]['location'] = {'city': 'Amsterdam', 'country': 'Netherlands'}
        catalogue.write_text(json.dumps(photos))
        gallery.build(self.root)
        output = self.root / '_site'
        page = (output / 'index.html').read_text()
        self.assertIn('href="https://www.linkedin.com/in/hamzakababji/" target="_blank" rel="noopener noreferrer">Hamza Elkababji</a>', page)
        self.assertNotIn('Sunset &amp; light', page)
        self.assertIn('<h3>Amsterdam, Netherlands</h3>', page)
        self.assertIn('download aria-label=', page)
        self.assertEqual((output / photos[0]['original']).read_bytes(), self.source.read_bytes())
        with Image.open(next((output / 'previews').glob('*.webp'))) as preview:
            self.assertEqual(preview.size, (675, 1200))
        self.assertNotIn('coming soon', page)
        catalogue.write_text('[]')
        gallery.build(self.root)
        self.assertFalse((output / photos[0]['original']).exists())

    def test_duplicate_import_does_not_change_catalogue(self):
        gallery.import_photos(self.root, [self.source], 'hamza-elkababji')
        before = (self.root / 'data/photos.json').read_bytes()
        with self.assertRaises(ValueError):
            gallery.import_photos(self.root, [self.source], 'hamza-elkababji')
        self.assertEqual(before, (self.root / 'data/photos.json').read_bytes())

    def test_unsafe_path_is_rejected(self):
        with self.assertRaises(ValueError):
            gallery.local_photo(self.root, 'data/photos.json')

    def test_external_storage(self):
        photos = [{'id': 'external', 'photographer': 'hamza-elkababji',
                   'alt': 'A landscape',
                   'original': 'https://images.example.org/original.jpg',
                   'preview': 'https://images.example.org/preview.webp',
                   'width': 4000, 'height': 3000}]
        (self.root / 'data/photos.json').write_text(json.dumps(photos))
        gallery.build(self.root)
        page = (self.root / '_site/index.html').read_text()
        self.assertIn('https://images.example.org/original.jpg', page)
        self.assertNotIn('<h3>', page.split('<!-- GALLERY_START -->')[1].split('<!-- GALLERY_END -->')[0])
        self.assertIn('View preview: A landscape', page)
        self.assertIn('use Save Image to download', page)

if __name__ == '__main__':
    unittest.main()
