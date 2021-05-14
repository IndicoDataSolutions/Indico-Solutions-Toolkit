import os
import pytest
from indico_toolkit import create_client

HOST_URL = os.environ.get("HOST_URL")
API_TOKEN_PATH = os.environ.get("API_TOKEN_PATH")
API_TOKEN = os.environ.get("API_TOKEN")

def test_client_creation():
    create_client(HOST_URL, API_TOKEN_PATH, API_TOKEN)
