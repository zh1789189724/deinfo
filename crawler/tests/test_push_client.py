"""测试 PushClient HTTP 推送逻辑"""

import json
import os
from unittest import mock

import pytest
import requests

from crawler.items import CrawlerItem, PushResult, BulkPushResult
from crawler.push_client import PushClient


@pytest.fixture(autouse=True)
def clear_env():
    """确保测试环境干净"""
    # 保存原环境变量
    old_url = os.environ.pop("BACKEND_URL", None)
    yield
    # 恢复
    if old_url is not None:
        os.environ["BACKEND_URL"] = old_url


@pytest.fixture
def domestic_item():
    return CrawlerItem(
        source_type="domestic",
        source_name="wechat_chengdu",
        lang="zh",
        title="成都消费券来了",
        content="成都市发放新一轮消费券",
        original_url="https://example.com/coupon/1",
        summary="消费券摘要",
        author="成都发布",
        created_at="2026-06-08T10:00:00Z",
        location="成都",
        price=50.0,
        validity_end="2026-07-08T23:59:59Z",
        tags=["消费券"],
    )


@pytest.fixture
def overseas_item():
    return CrawlerItem(
        source_type="overseas",
        source_name="producthunt",
        lang="en",
        title="Awesome Product",
        content="A new AI-powered tool",
        original_url="https://producthunt.com/posts/1",
        author="John Doe",
        created_at="2026-06-08T07:00:00Z",
        tags=["ai", "tools"],
    )


class TestPushClientInit:
    """PushClient 初始化测试"""

    def test_default_base_url(self):
        """默认 base_url 应为 localhost:8080"""
        client = PushClient()
        assert "localhost:8080" in client.base_url

    def test_base_url_from_env(self, monkeypatch):
        """环境变量 BACKEND_URL 应覆盖默认值"""
        monkeypatch.setenv("BACKEND_URL", "https://api.example.com/crawler")
        client = PushClient()
        assert client.base_url == "https://api.example.com/crawler"

    def test_base_url_parameter_overrides_env(self):
        """显式传入的 base_url 应优先于环境变量"""
        os.environ["BACKEND_URL"] = "https://env.example.com"
        client = PushClient(base_url="https://param.example.com")
        assert client.base_url == "https://param.example.com"


class TestPushOne:
    """单条推送测试"""

    def test_push_one_success(self, domestic_item):
        """推送成功应返回 PushResult(success=True, status_code=200)"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {
                "type": "domestic",
                "deal": {"id": 1},
            }
            mock_post.return_value = mock_response

            result = client.push_one(domestic_item)

            assert isinstance(result, PushResult)
            assert result.success is True
            assert result.status_code == 200

            # 验证请求体格式
            call_args = mock_post.call_args
            url = call_args[0][0]
            assert url.endswith("/push")
            body = call_args[1]["json"]
            assert body["sourceType"] == "domestic"
            assert body["lang"] == "zh"
            assert body["sourceName"] == "wechat_chengdu"
            assert body["content"]["title"] == "成都消费券来了"
            assert body["content"]["content"] == "成都市发放新一轮消费券"
            assert body["content"]["originalUrl"] == "https://example.com/coupon/1"
            assert body["content"]["location"] == "成都"
            assert body["content"]["price"] == 50.0
            assert body["content"]["tags"] == ["消费券"]

    def test_push_overseas_format(self, overseas_item):
        """海外源推送格式验证"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {
                "type": "overseas",
                "content": {"id": 1},
            }
            mock_post.return_value = mock_response

            result = client.push_one(overseas_item)
            assert result.success is True

            call_body = mock_post.call_args[1]["json"]
            assert call_body["sourceType"] == "overseas"
            assert call_body["lang"] == "en"
            assert call_body["content"]["tags"] == ["ai", "tools"]

    def test_push_one_400_error(self, domestic_item):
        """后端返回 400 应标记失败"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 400
            mock_response.ok = False
            mock_response.raise_for_status.side_effect = (
                requests.exceptions.HTTPError("400 Client Error")
            )
            mock_post.return_value = mock_response

            result = client.push_one(domestic_item)
            assert result.success is False
            assert result.status_code == 400

    def test_push_one_500_error(self, domestic_item):
        """后端返回 500 应触发重试"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 500
            mock_response.ok = False
            mock_response.raise_for_status.side_effect = (
                requests.exceptions.HTTPError("500 Server Error")
            )
            mock_post.return_value = mock_response

            result = client.push_one(domestic_item)
            assert result.success is False
            # 应重试多次（默认最多 5 次）
            assert mock_post.call_count == 5

    def test_push_one_retry_then_success(self, domestic_item):
        """重试后成功的情况"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            # 前 2 次失败，第 3 次成功
            failures = [mock.MagicMock() for _ in range(2)]
            for f in failures:
                f.status_code = 502
                f.ok = False
                f.raise_for_status.side_effect = (
                    requests.exceptions.HTTPError("502 Bad Gateway")
                )
            success = mock.MagicMock()
            success.status_code = 200
            success.ok = True
            success.json.return_value = {"type": "domestic", "deal": {"id": 1}}

            mock_post.side_effect = failures + [success]

            result = client.push_one(domestic_item)
            assert result.success is True
            assert result.status_code == 200
            assert mock_post.call_count == 3

    def test_push_one_network_error(self, domestic_item):
        """网络错误应触发重试"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError(
                "Connection refused"
            )

            result = client.push_one(domestic_item)
            assert result.success is False
            assert mock_post.call_count == 5

    def test_push_one_retry_delay_increasing(self, domestic_item):
        """重试间隔应递增（1s, 2s, 4s, 8s）"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 500
            mock_response.ok = False
            mock_response.raise_for_status.side_effect = (
                requests.exceptions.HTTPError("500 Error")
            )
            mock_post.return_value = mock_response

            with mock.patch.object(client, "_sleep") as mock_sleep:
                client.push_one(domestic_item)
                # 检查退避时间
                assert mock_sleep.call_args_list[0][0][0] == 1
                assert mock_sleep.call_args_list[1][0][0] == 2
                assert mock_sleep.call_args_list[2][0][0] == 4
                assert mock_sleep.call_args_list[3][0][0] == 8


class TestPushBulk:
    """批量推送测试"""

    def test_push_bulk_success(self, domestic_item, overseas_item):
        """批量推送全部成功"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        items = [domestic_item, overseas_item]
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {
                "total": 2,
                "success": 2,
                "failed": 0,
            }
            mock_post.return_value = mock_response

            result = client.push_bulk(items)
            assert isinstance(result, BulkPushResult)
            assert result.total == 2
            assert result.success == 2
            assert result.failed == 0
            # 验证请求 URL
            call_url = mock_post.call_args[0][0]
            assert call_url.endswith("/push-bulk")

    def test_push_bulk_empty_list(self):
        """空列表应返回全零结果"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        result = client.push_bulk([])
        assert result.total == 0
        assert result.success == 0
        assert result.failed == 0

    def test_push_bulk_partial_failure(self, domestic_item, overseas_item):
        """批量推送部分失败"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        items = [domestic_item, overseas_item]
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {
                "total": 2,
                "success": 1,
                "failed": 1,
            }
            mock_post.return_value = mock_response

            result = client.push_bulk(items)
            assert result.total == 2
            assert result.success == 1
            assert result.failed == 1


class TestFailedQueue:
    """失败降级队列测试"""

    def test_failed_queue_created_on_failure(self, domestic_item, tmp_path):
        """推送失败时应写入 failed_queue.json"""
        client = PushClient(
            base_url="http://test-backend:8080/api/crawler",
            failed_queue_path=str(tmp_path / "failed_queue.json"),
        )
        with mock.patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("fail")

            client.push_one(domestic_item)

            queue_file = tmp_path / "failed_queue.json"
            assert queue_file.exists()
            with open(queue_file, "r", encoding="utf-8") as f:
                records = json.load(f)
            assert len(records) >= 1
            assert records[0]["original_url"] == domestic_item.original_url

    def test_failed_queue_appends(self, domestic_item, tmp_path):
        """多次失败时 failed_queue 应追加"""
        client = PushClient(
            base_url="http://test-backend:8080/api/crawler",
            failed_queue_path=str(tmp_path / "failed_queue.json"),
        )
        with mock.patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("fail")

            client.push_one(domestic_item)
            client.push_one(domestic_item)

            queue_file = tmp_path / "failed_queue.json"
            with open(queue_file, "r", encoding="utf-8") as f:
                records = json.load(f)
            assert len(records) == 2

    def test_retry_failed_queue(self, domestic_item, tmp_path):
        """重试失败队列中的条目"""
        queue_path = tmp_path / "failed_queue.json"
        # 先写入一条到失败队列
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump([{
                "source_type": domestic_item.source_type,
                "source_name": domestic_item.source_name,
                "lang": domestic_item.lang,
                "title": domestic_item.title,
                "content": domestic_item.content,
                "original_url": domestic_item.original_url,
            }], f)

        client = PushClient(
            base_url="http://test-backend:8080/api/crawler",
            failed_queue_path=str(queue_path),
        )
        with mock.patch("requests.post") as mock_post:
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {
                "type": "domestic",
                "deal": {"id": 1},
            }
            mock_post.return_value = mock_response

            client.retry_failed_queue()
            # 验证队列已清空
            assert not queue_path.exists() or json.load(open(queue_path)) == []


class TestRequestTimeout:
    """请求超时测试"""

    def test_push_one_timeout(self, domestic_item):
        """推送应设置超时时间"""
        client = PushClient(base_url="http://test-backend:8080/api/crawler")
        with mock.patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("timeout")

            result = client.push_one(domestic_item)
            assert result.success is False
            # 确保设置了 timeout 参数
            if mock_post.call_count > 0:
                _, kwargs = mock_post.call_args
                assert "timeout" in kwargs


class TestPushResultDataclass:
    """PushResult 数据结构测试"""

    def test_push_result_defaults(self):
        """PushResult 默认值"""
        r = PushResult(success=True, status_code=200)
        assert r.message == ""
        assert r.item_id == ""

    def test_bulk_push_result_defaults(self):
        """BulkPushResult 默认值"""
        r = BulkPushResult(total=0, success=0, failed=0)
        assert r.results == []
