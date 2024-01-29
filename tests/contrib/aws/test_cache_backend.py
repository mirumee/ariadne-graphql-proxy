import os
import time

import boto3
import pytest
from freezegun import freeze_time
from moto import mock_aws

from ariadne_graphql_proxy.contrib.aws import DynamoDBCacheBackend, DynamoDBCacheError


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def test_table(aws_credentials):
    with mock_aws():
        table = boto3.resource("dynamodb").create_table(
            TableName="test_table",
            KeySchema=[{"AttributeName": "key", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "key", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        table.wait_until_exists()
        yield table


def test_object_can_be_created_with_existing_table_name(test_table):
    DynamoDBCacheBackend(table_name="test_table")


@mock_aws
def test_init_raises_dynamodb_cache_error_for_unavailable_table(aws_credentials):
    with pytest.raises(DynamoDBCacheError):
        DynamoDBCacheBackend(table_name="not_exisitng_table_name")


@pytest.mark.asyncio
async def test_set_creates_correct_item_in_table(test_table):
    cache = DynamoDBCacheBackend(table_name="test_table")

    await cache.set(key="test_key", value="test_value")

    response = test_table.get_item(Key={"key": "test_key"})
    assert response["Item"] == {"key": "test_key", "value": "test_value"}


@pytest.mark.asyncio
@freeze_time("2023-01-01 12:00:00")
async def test_set_creates_item_with_ttl(test_table):
    cache = DynamoDBCacheBackend(table_name="test_table")

    await cache.set(key="test_key", value="test_value", ttl=300)

    response = test_table.get_item(Key={"key": "test_key"})
    assert response["Item"] == {
        "key": "test_key",
        "value": "test_value",
        "ttl": int(time.time()) + 300,
    }


@pytest.mark.asyncio
async def test_get_returns_value_from_table(test_table):
    test_table.put_item(Item={"key": "test_key", "value": "test_value"})
    cache = DynamoDBCacheBackend(table_name="test_table")

    assert await cache.get(key="test_key") == "test_value"


@pytest.mark.asyncio
async def test_get_returns_default_for_not_exisitng_key(test_table):
    cache = DynamoDBCacheBackend(table_name="test_table")

    assert await cache.get(key="not_existing_key", default="default") == "default"


@pytest.mark.asyncio
@freeze_time("2023-01-01 12:00:00")
async def test_get_returns_not_expired_item(test_table):
    test_table.put_item(
        Item={"key": "test_key", "value": "test_value", "ttl": int(time.time()) + 900}
    )
    cache = DynamoDBCacheBackend(table_name="test_table")

    assert await cache.get(key="test_key") == "test_value"


@pytest.mark.asyncio
@freeze_time("2023-01-01 12:00:00")
async def test_get_returns_default_for_expired_item(test_table):
    test_table.put_item(
        Item={"key": "test_key", "value": "test_value", "ttl": int(time.time()) - 900}
    )
    cache = DynamoDBCacheBackend(table_name="test_table")

    assert await cache.get(key="test_key", default="default") == "default"
