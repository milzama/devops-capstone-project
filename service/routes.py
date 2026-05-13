"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()

    # Mengaktifkan lokasi URL yang benar setelah get_accounts diimplementasikan
    location_url = url_for(
        "get_accounts",
        account_id=account.id,
        _external=True)

    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


######################################################################
# LIST ALL ACCOUNTS
######################################################################
@app.route("/accounts", methods=["GET"])
def list_accounts():
    """
    List all Accounts
    This endpoint will list all Accounts currently stored in the database
    """
    app.logger.info("Request to list Accounts")

    # 1. Ambil semua data akun dari database menggunakan metode .all() bawaan model
    accounts = Account.all()

    # 2. Ambil objek akun lalu serialize menjadi list of dictionaries
    account_list = [account.serialize() for account in accounts]

    # 3. Kembalikan list tersebut dalam format JSON bersama status 200 OK
    return jsonify(account_list), status.HTTP_200_OK


######################################################################
# READ AN ACCOUNT
######################################################################
@app.route("/accounts/<int:account_id>", methods=["GET"])
def get_accounts(account_id):
    """
    Reads an Account
    This endpoint will read an Account based on the account_id that is requested
    """
    app.logger.info("Request to read an Account with id: %s", account_id)

    # Mencari account berdasarkan id di database
    account = Account.find(account_id)
    if not account:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Account with id [{account_id}] could not be found."
        )

    # Mengembalikan data account yang ditemukan dengan status 200 OK
    return jsonify(account.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################
@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_accounts(account_id):
    """
    Updates an Existing Account
    This endpoint will update an Account based on the account_id and data posted
    """
    app.logger.info("Request to update an Account with id: %s", account_id)

    # 1. Cari akun berdasarkan id di database
    account = Account.find(account_id)
    if not account:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Account with id [{account_id}] could not be found."
        )

    # 2. Validasi format konten yang dikirim (harus application/json)
    check_content_type("application/json")

    # 3. Perbarui data model dengan data baru yang dikirim dari request body
    account.deserialize(request.get_json())

    # 4. Simpan perubahan tersebut ke database
    account.update()

    # 5. Kembalikan data yang diperbarui beserta kode 200 OK
    return jsonify(account.serialize()), status.HTTP_200_OK


######################################################################
# DELETE AN ACCOUNT
######################################################################
@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_accounts(account_id):
    """
    Delete an Account
    This endpoint will delete an Account based on the account_id that is requested
    """
    app.logger.info("Request to delete an Account with id: %s", account_id)

    # 1. Cari akun berdasarkan id di database
    account = Account.find(account_id)

    # 2. Jika akun ditemukan, lakukan penghapusan
    if account:
        account.delete()

    # 3. Kembalikan respons kosong (make_response) bersama kode status 204 NO CONTENT
    return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )


######################################################################
#  S E C U R I T Y   H E A D E R S
######################################################################
@app.after_request
def add_security_headers(response):
    """Menambahkan header keamanan ke setiap respons HTTP"""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; object-src 'none'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
