# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test source serializer."""
import pytest

from api import messages
from api.models import Credential, Source
from api.source.serializer import SourceSerializer


@pytest.fixture
def openshift_cred_type():
    """Return openshift credential."""
    openshift_credential = Credential.objects.create(
        name="openshift_cred",
        cred_type=Credential.OPENSHIFT_CRED_TYPE,
        auth_token="openshift_token",
    )
    return openshift_credential.id


@pytest.fixture
def satellite_cred_type():
    """Return satellite credential."""
    satellite_credential = Credential.objects.create(
        name="sat_cred",
        cred_type=Credential.SATELLITE_CRED_TYPE,
        username="satellite_user",
        password="satellite_password",
        become_password=None,
        ssh_keyfile=None,
    )
    return satellite_credential.id


@pytest.mark.django_db
def test_unknown_source_type(openshift_cred_type):
    """Test if serializer is invalid when passing unknown source type."""
    data = {
        "name": "source1",
        "source_type": "test_source_type",
        "credentials": [openshift_cred_type],
    }
    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert serializer.errors["source_type"]


@pytest.mark.django_db
def test_wrong_cred_type(satellite_cred_type):
    """Test if serializer is invalid when passing inappropriate cred type."""
    error_message = messages.SOURCE_CRED_WRONG_TYPE
    data = {
        "name": "source2",
        "source_type": Source.OPENSHIFT_SOURCE_TYPE,
        "hosts": ["1.2.3.4"],
        "credentials": [satellite_cred_type],
    }
    serializer = SourceSerializer(data=data)
    assert not serializer.is_valid(), serializer.errors
    assert error_message in serializer.errors["source_type"]


@pytest.mark.django_db
def test_openshift_source_green_path(openshift_cred_type):
    """Test if serializer is valid when passing mandatory fields."""
    data = {
        "name": "source3",
        "source_type": Source.OPENSHIFT_SOURCE_TYPE,
        "port": 222,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_type],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["port"] == 222


@pytest.mark.django_db
def test_openshift_source_default_port(openshift_cred_type):
    """Test if serializer is valid when not passing port field."""
    data = {
        "name": "source3",
        "source_type": Source.OPENSHIFT_SOURCE_TYPE,
        "hosts": ["1.2.3.4"],
        "credentials": [openshift_cred_type],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["port"] == 6443


@pytest.mark.django_db
def test_openshift_source_update(openshift_cred_type):
    """Test if serializer updates fields correctly."""
    data = {
        "name": "source3",
        "source_type": Source.OPENSHIFT_SOURCE_TYPE,
        "credentials": [openshift_cred_type],
        "hosts": ["1.2.3.4"],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid()

    source_object = serializer.save()
    assert source_object.name == "source3"
    updated_data = {
        "name": "source4",
        "hosts": ["5.4.3.2.1"],
    }
    serializer.update(source_object, updated_data)
    assert serializer.is_valid()
    assert source_object.name == "source4"
    assert source_object.source_type == Source.OPENSHIFT_SOURCE_TYPE


@pytest.mark.django_db
def test_openshift_source_update_options(openshift_cred_type):
    """Test if serializer updates fields correctly when options are present."""
    data = {
        "name": "source3",
        "source_type": Source.OPENSHIFT_SOURCE_TYPE,
        "credentials": [openshift_cred_type],
        "hosts": ["1.2.3.4"],
    }
    serializer = SourceSerializer(data=data)
    assert serializer.is_valid()

    source_object = serializer.save()
    assert source_object.name == "source3"
    assert source_object.options.ssl_cert_verify is True
    updated_data = {
        "name": "source4",
        "hosts": ["5.4.3.2.1"],
        "options": {"ssl_cert_verify": False},
    }
    serializer.update(source_object, updated_data)
    assert serializer.is_valid()
    assert source_object.name == "source4"
    assert source_object.source_type == Source.OPENSHIFT_SOURCE_TYPE
    assert source_object.options.ssl_cert_verify is False
