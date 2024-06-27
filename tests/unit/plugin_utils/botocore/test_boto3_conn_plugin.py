# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.plugin_utils.botocore as utils_botocore


class FailException(Exception):
    pass


@pytest.fixture
def aws_plugin(monkeypatch):
    aws_plugin = MagicMock()
    aws_plugin.fail_aws.side_effect = FailException()
    monkeypatch.setattr(aws_plugin, "ansible_name", sentinel.PLUGIN_NAME)
    return aws_plugin


@pytest.fixture
def botocore_utils(monkeypatch):
    return utils_botocore


###############################################################
# module_utils.botocore.boto3_conn
###############################################################
def test_boto3_conn_success_plugin(monkeypatch, aws_plugin, botocore_utils):
    connection_method = MagicMock(name="_boto3_conn")
    monkeypatch.setattr(botocore_utils, "_boto3_conn", connection_method)
    connection_method.return_value = sentinel.RETURNED_CONNECTION

    assert botocore_utils.boto3_conn(aws_plugin) is sentinel.RETURNED_CONNECTION
    passed_args = connection_method.call_args
    assert passed_args == call(conn_type=None, resource=None, region=None, endpoint=None)

    result = botocore_utils.boto3_conn(
        aws_plugin,
        conn_type=sentinel.PARAM_CONNTYPE,
        resource=sentinel.PARAM_RESOURCE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.PARAM_ENDPOINT,
        extra_arg=sentinel.PARAM_EXTRA,
    )
    assert result is sentinel.RETURNED_CONNECTION
    passed_args = connection_method.call_args
    assert passed_args == call(
        conn_type=sentinel.PARAM_CONNTYPE,
        resource=sentinel.PARAM_RESOURCE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.PARAM_ENDPOINT,
        extra_arg=sentinel.PARAM_EXTRA,
    )


@pytest.mark.parametrize(
    "failure, custom_error",
    [
        (ValueError(sentinel.VALUE_ERROR), "Couldn't connect to AWS: sentinel.VALUE_ERROR"),
        (botocore.exceptions.ProfileNotFound(profile=sentinel.PROFILE_ERROR), None),
        (
            botocore.exceptions.PartialCredentialsError(
                provider=sentinel.CRED_ERROR_PROV, cred_var=sentinel.CRED_ERROR_VAR
            ),
            None,
        ),
        (botocore.exceptions.NoCredentialsError(), None),
        (botocore.exceptions.ConfigParseError(path=sentinel.PARSE_ERROR), None),
        (botocore.exceptions.NoRegionError(), "The sentinel.PLUGIN_NAME plugin requires a region"),
        (
            botocore.exceptions.UnknownServiceError(
                service_name=sentinel.SERVICE_ERROR_NAME, known_service_names=sentinel.SERVICE_ERROR_KNOWN
            ),
            None,
        ),
        (botocore.exceptions.BotoCoreError(), None),
    ],
)
def test_boto3_conn_exception_plugin(monkeypatch, aws_plugin, botocore_utils, failure, custom_error):
    connection_method = MagicMock(name="_boto3_conn")
    monkeypatch.setattr(botocore_utils, "_boto3_conn", connection_method)
    connection_method.side_effect = failure

    if custom_error is None:
        custom_error = str(failure)

    with pytest.raises(FailException):
        botocore_utils.boto3_conn(aws_plugin)

    fail_args = aws_plugin.fail_aws.call_args
    assert custom_error in fail_args[0][0]


@pytest.mark.parametrize(
    "failure, custom_error",
    [
        (ValueError(sentinel.VALUE_ERROR), "Couldn't connect to AWS: sentinel.VALUE_ERROR"),
        (botocore.exceptions.ProfileNotFound(profile=sentinel.PROFILE_ERROR), None),
        (
            botocore.exceptions.PartialCredentialsError(
                provider=sentinel.CRED_ERROR_PROV, cred_var=sentinel.CRED_ERROR_VAR
            ),
            None,
        ),
        (botocore.exceptions.NoCredentialsError(), None),
        (botocore.exceptions.ConfigParseError(path=sentinel.PARSE_ERROR), None),
        (
            botocore.exceptions.NoRegionError(),
            "A region is required and none was found",
        ),
        (
            botocore.exceptions.UnknownServiceError(
                service_name=sentinel.SERVICE_ERROR_NAME, known_service_names=sentinel.SERVICE_ERROR_KNOWN
            ),
            None,
        ),
        (botocore.exceptions.BotoCoreError(), None),
    ],
)
def test_boto3_conn_exception_no_plugin_name(monkeypatch, aws_plugin, botocore_utils, failure, custom_error):
    connection_method = MagicMock(name="_boto3_conn")
    monkeypatch.setattr(botocore_utils, "_boto3_conn", connection_method)
    connection_method.side_effect = failure
    del aws_plugin.ansible_name

    if custom_error is None:
        custom_error = str(failure)

    with pytest.raises(FailException):
        botocore_utils.boto3_conn(aws_plugin)

    fail_args = aws_plugin.fail_aws.call_args
    assert custom_error in fail_args[0][0]
