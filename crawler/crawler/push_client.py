"""PushClient — HTTP POST 推送到后端

参考接口契约第 6 章推送接口契约。
支持单条推送、批量推送、指数退避重试、失败降级写入本地队列。

用法:
    client = PushClient()
    result = client.push_one(item)           # 单条推送
    result = client.push_bulk([item1, item2])  # 批量推送
    client.retry_failed_queue()              # 启动时重试失败队列
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import requests

from crawler.items import CrawlerItem, BulkPushResult, PushResult

logger = logging.getLogger("push_client")


class PushClient:
    """推送到后端的 HTTP 客户端

    负责将清洗后的 CrawlerItem 通过 HTTP POST 发送到后端服务。
    内置指数退避重试和失败降级机制。
    """

    # 最大重试次数
    MAX_RETRIES = 5
    # 退避基数（秒），第 N 次重试等待 base_delay * 2^(N-1)
    BASE_DELAY = 1
    # 请求超时（秒）
    REQUEST_TIMEOUT = 30

    def __init__(
        self,
        base_url: Optional[str] = None,
        failed_queue_path: Optional[str] = None,
    ):
        """初始化 PushClient

        Args:
            base_url: 后端 API 基础地址。默认从环境变量 BACKEND_URL 读取，
                      兜底为 http://localhost:8080/api/crawler
            failed_queue_path: 失败队列文件路径。默认当前目录下的 failed_queue.json
        """
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            self.base_url = os.environ.get(
                "BACKEND_URL",
                "http://localhost:8080/api/crawler",
            ).rstrip("/")

        self.failed_queue_path = failed_queue_path or os.path.join(
            os.getcwd(), "failed_queue.json"
        )
        logger.info("PushClient 初始化: base_url=%s, failed_queue=%s",
                     self.base_url, self.failed_queue_path)

    # ──────────────────────────────────────────────
    # 公开方法
    # ──────────────────────────────────────────────

    def push_one(self, item: CrawlerItem) -> PushResult:
        """推送单条内容到后端。

        使用指数退避重试策略：
            第 1 次失败后等待 1s，然后 2s，4s，8s，16s。
            最多重试 MAX_RETRIES 次。
            全部耗尽后写入失败队列文件。

        Args:
            item: CrawlerItem 实例

        Returns:
            PushResult: 推送结果
        """
        url = f"{self.base_url}/push"
        payload = self._build_payload(item)

        last_error = ""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.REQUEST_TIMEOUT,
                )
                if response.ok:
                    logger.info("推送成功: %s (%s)", item.title, response.status_code)
                    return PushResult(
                        success=True,
                        status_code=response.status_code,
                    )
                else:
                    # 429 限流 — 应重试（使用退避）
                    if response.status_code == 429:
                        last_error = f"被限流(429)"
                        logger.warning("推送被限流(第%d次): %s", attempt, item.title)
                    # 其他 4xx 错误不重试（客户端错误，重试也无法解决）
                    elif 400 <= response.status_code < 500:
                        logger.warning("推送失败(客户端错误): %s, status=%s, 不重试",
                                       item.title, response.status_code)
                        return PushResult(
                            success=False,
                            status_code=response.status_code,
                            message=f"客户端错误: {response.status_code}",
                        )
                    # 5xx 错误需要重试
                    last_error = f"服务端错误: {response.status_code}"
                    logger.warning("推送失败(第%d次): %s, status=%s",
                                   attempt, item.title, response.status_code)

            except requests.exceptions.Timeout:
                last_error = "请求超时"
                logger.warning("推送超时(第%d次): %s", attempt, item.title)
            except requests.exceptions.ConnectionError:
                last_error = "连接失败"
                logger.warning("推送连接失败(第%d次): %s", attempt, item.title)
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning("推送异常(第%d次): %s, %s", attempt, item.title, e)

            # 最后一次重试后不再等待
            if attempt < self.MAX_RETRIES:
                delay = self.BASE_DELAY * (2 ** (attempt - 1))
                logger.info("等待 %d 秒后重试...", delay)
                self._sleep(delay)

        # 所有重试耗尽，写入失败队列
        logger.error("推送彻底失败: %s, 写入失败队列: %s", item.title, last_error)
        self._save_to_failed_queue(item)
        return PushResult(
            success=False,
            status_code=0,
            message=f"重试耗尽: {last_error}",
        )

    def push_bulk(self, items: list[CrawlerItem]) -> BulkPushResult:
        """批量推送多条内容到后端。

        Args:
            items: CrawlerItem 列表

        Returns:
            BulkPushResult: 批量推送结果
        """
        if not items:
            return BulkPushResult(total=0, success=0, failed=0)

        url = f"{self.base_url}/push-bulk"
        payloads = [self._build_payload(item) for item in items]

        try:
            response = requests.post(
                url,
                json=payloads,
                timeout=self.REQUEST_TIMEOUT * 2,  # 批量请求给更长超时
            )
            if response.ok:
                data = response.json()
                logger.info("批量推送完成: total=%s, success=%s, failed=%s",
                            data.get("total", 0), data.get("success", 0),
                            data.get("failed", 0))
                return BulkPushResult(
                    total=data.get("total", len(items)),
                    success=data.get("success", 0),
                    failed=data.get("failed", 0),
                )
            else:
                logger.error("批量推送失败: status=%s", response.status_code)
                return BulkPushResult(
                    total=len(items),
                    success=0,
                    failed=len(items),
                )
        except requests.exceptions.RequestException as e:
            logger.error("批量推送异常: %s", e)
            return BulkPushResult(
                total=len(items),
                success=0,
                failed=len(items),
            )

    def retry_failed_queue(self) -> tuple[int, int]:
        """重试失败队列中的所有条目。

        在调度器启动时调用，尝试重新推送之前失败的内容。
        推送成功的条目会从队列文件中移除。

        Returns:
            (total, success): 队列总数和成功数
        """
        if not os.path.exists(self.failed_queue_path):
            return (0, 0)

        try:
            with open(self.failed_queue_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("读取失败队列出错: %s", e)
            return (0, 0)

        if not records:
            return (0, 0)

        logger.info("开始重试失败队列: %d 条", len(records))
        success_count = 0
        remaining = []

        for record in records:
            # 从 dict 重建 CrawlerItem
            item = CrawlerItem(
                source_type=record.get("source_type", ""),
                source_name=record.get("source_name", ""),
                lang=record.get("lang", ""),
                title=record.get("title", ""),
                content=record.get("content", ""),
                original_url=record.get("original_url", ""),
                summary=record.get("summary", ""),
                author=record.get("author", ""),
                created_at=record.get("created_at", ""),
                location=record.get("location", ""),
                price=record.get("price", 0.0),
                validity_end=record.get("validity_end", ""),
                tags=record.get("tags", []),
                images=record.get("images", []),
            )
            result = self.push_one(item)
            if result.success:
                success_count += 1
            else:
                remaining.append(record)

        # 更新失败队列（移除已成功的）
        if remaining:
            with open(self.failed_queue_path, "w", encoding="utf-8") as f:
                json.dump(remaining, f, ensure_ascii=False, indent=2)
        else:
            # 全部成功，删除队列文件
            os.remove(self.failed_queue_path)
            logger.info("失败队列已全部推送成功，文件已删除")

        logger.info("重试完成: total=%d, success=%d", len(records), success_count)
        return (len(records), success_count)

    # ──────────────────────────────────────────────
    # 内部方法
    # ──────────────────────────────────────────────

    def _build_payload(self, item: CrawlerItem) -> dict:
        """根据接口契约第 6.2 节构建推送请求体。

        Args:
            item: CrawlerItem 实例

        Returns:
            dict: 符合后端 /push 接口格式的请求体
        """
        content = {
            "title": item.title,
            "content": item.content,
            "originalUrl": item.original_url,
            "summary": item.summary,
            "author": item.author,
            "createdAt": item.created_at,
        }

        # 国内源附加 location、price、validityEnd
        if item.source_type == "domestic":
            if item.location:
                content["location"] = item.location
            if item.price > 0:
                content["price"] = item.price
            if item.validity_end:
                content["validityEnd"] = item.validity_end

        # 通用可选字段：tags、images
        if item.tags:
            content["tags"] = item.tags
        if item.images:
            content["images"] = item.images

        return {
            "sourceType": item.source_type,
            "lang": item.lang,
            "sourceName": item.source_name,
            "content": content,
        }

    def _save_to_failed_queue(self, item: CrawlerItem) -> None:
        """将推送失败的 item 存储到本地失败队列。

        Args:
            item: 推送失败的 CrawlerItem
        """
        record = {
            "source_type": item.source_type,
            "source_name": item.source_name,
            "lang": item.lang,
            "title": item.title,
            "content": item.content,
            "original_url": item.original_url,
            "summary": item.summary,
            "author": item.author,
            "created_at": item.created_at,
            "location": item.location,
            "price": item.price,
            "validity_end": item.validity_end,
            "tags": item.tags,
            "images": item.images,
        }

        try:
            records = []
            if os.path.exists(self.failed_queue_path):
                with open(self.failed_queue_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
            records.append(record)
            with open(self.failed_queue_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            logger.info("已写入失败队列: %s", item.original_url)
        except (IOError, json.JSONDecodeError) as e:
            logger.error("写入失败队列出错: %s", e)

    @staticmethod
    def _sleep(seconds: float) -> None:
        """等待指定秒数。（抽离为静态方法以便测试中 mock）
        """
        time.sleep(seconds)
