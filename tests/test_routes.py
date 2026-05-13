"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

# Konfigurasi lingkungan untuk mensimulasikan request HTTPS aman
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""
        pass

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_account(self):
        """It should Read a single Account"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)

    def test_get_account_not_found(self):
        """It should not Read an Account that is not found"""
        # Melakukan GET request ke /accounts/0 (ID 0 diasumsikan tidak pernah ada)
        resp = self.client.get(f"{BASE_URL}/0")
        
        # Memastikan sistem merespons dengan status 404 NOT FOUND
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account(self):
        """It should Update an existing Account"""
        # 1. Buat akun dummy terlebih dahulu menggunakan helper
        test_account = self._create_accounts(1)[0]
        new_account_data = test_account.serialize()
        
        # 2. Ubah data nama pada objek dummy tersebut
        new_account_data["name"] = "Nama Baru Terupdate"
        
        # 3. Kirim PUT request ke endpoint /accounts/<id>
        resp = self.client.put(
            f"{BASE_URL}/{test_account.id}",
            json=new_account_data,
            content_type="application/json"
        )
        
        # 4. Pastikan status responsnya adalah 200 OK
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        # 5. Pastikan data yang dikembalikan sudah berubah sesuai update
        updated_account = resp.get_json()
        self.assertEqual(updated_account["name"], "Nama Baru Terupdate")

    def test_update_account_not_found(self):
        """It should not Update an Account that is not found"""
        # 1. Siapkan data update dummy
        account = AccountFactory()
        data = account.serialize()
        
        # 2. Kirim PUT request ke ID 0 yang tidak ada di database
        resp = self.client.put(f"{BASE_URL}/0", json=data, content_type="application/json")
        
        # 3. Pastikan sistem menolak dengan status 404 NOT FOUND
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should Delete an Account"""
        # 1. Buat akun dummy menggunakan helper method
        account = self._create_accounts(1)[0]
        
        # 2. Kirim DELETE request ke endpoint /accounts/<id>
        resp = self.client.delete(f"{BASE_URL}/{account.id}")
        
        # 3. Pastikan status responsnya adalah 204 NO CONTENT
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        
        # 4. Pastikan data benar-benar terhapus dengan melakukan GET kembali ke ID yang sama
        get_resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(get_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_account_list(self):
        """It should Get a list of Accounts"""
        # 1. Buat 3 akun dummy menggunakan helper method
        self._create_accounts(3)
        
        # 2. Kirim GET request ke endpoint /accounts
        resp = self.client.get(BASE_URL)
        
        # 3. Pastikan status responsnya adalah 200 OK
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        # 4. Ambil data JSON dan pastikan jumlahnya ada 3 sesuai data yang dibuat
        data = resp.get_json()
        self.assertEqual(len(data), 3)

    def test_security_headers(self):
        """Seharusnya mengembalikan header keamanan"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'; object-src 'none'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    def test_cors_security(self):
        """Seharusnya mengembalikan header CORS"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Periksa header CORS
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')