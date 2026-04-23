import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from shopapp.models import Product


TEST_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00"
    b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class ProductImageCleanupTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp_media_root = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._temp_media_root)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._temp_media_root, ignore_errors=True)

    def _uploaded_image(self, name: str) -> SimpleUploadedFile:
        return SimpleUploadedFile(name, TEST_GIF, content_type="image/gif")

    def test_old_product_image_deleted_on_replace(self):
        product = Product.objects.create(
            name="Товар с изображением",
            description="Проверка замены файла",
            price=Decimal("100.00"),
            image=self._uploaded_image("old.gif"),
        )
        old_path = Path(product.image.path)
        self.assertTrue(old_path.exists())

        product.image = self._uploaded_image("new.gif")
        product.save()
        product.refresh_from_db()

        self.assertFalse(old_path.exists())
        self.assertTrue(Path(product.image.path).exists())

    def test_product_image_deleted_on_product_delete(self):
        product = Product.objects.create(
            name="Товар на удаление",
            description="Проверка удаления файла",
            price=Decimal("100.00"),
            image=self._uploaded_image("delete.gif"),
        )
        image_path = Path(product.image.path)
        self.assertTrue(image_path.exists())

        product.delete()

        self.assertFalse(image_path.exists())
