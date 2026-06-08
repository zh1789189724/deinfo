"""测试 CrawlerScheduler 调度器"""

import pytest
from unittest.mock import MagicMock
from crawler.schedulers import CrawlerScheduler


class FakeSpider:
    """用于调度器测试的假 spider"""
    name = "test_spider"


@pytest.fixture
def scheduler():
    """创建一个调度器实例，并 mock 内部的 APScheduler BackgroundScheduler"""
    sched = CrawlerScheduler()
    # 用 MagicMock 替换真实调度器，避免线程干扰
    sched.scheduler = MagicMock()
    # mock get_job 返回值
    mock_job = MagicMock()
    mock_job.next_run_time = None
    sched.scheduler.get_job.return_value = mock_job
    return sched


class TestInit:
    """初始化测试"""

    def test_default_settings_module(self):
        """默认 settings_module 应为 config.settings"""
        sched = CrawlerScheduler()
        assert sched.settings_module == "config.settings"
        assert hasattr(sched, "_jobs")
        assert hasattr(sched, "_spider_map")

    def test_custom_settings_module(self):
        """可自定义 settings_module"""
        sched = CrawlerScheduler(settings_module="custom.settings")
        assert sched.settings_module == "custom.settings"

    def test_internal_scheduler_created(self):
        """未 mock 时应创建 BackgroundScheduler 实例"""
        from apscheduler.schedulers.background import BackgroundScheduler
        sched = CrawlerScheduler()
        try:
            assert isinstance(sched.scheduler, BackgroundScheduler)
        finally:
            # 未 start() 的 scheduler 不能直接 shutdown
            if sched.scheduler.state == 0:  # STATE_STOPPED
                pass
            else:
                sched.scheduler.shutdown(wait=False)


class TestAddJob:
    """add_job 方法测试"""

    def test_adds_job_with_valid_cron(self, scheduler):
        """有效的 cron 表达式应成功注册"""
        scheduler.add_job(FakeSpider, "0 8 * * *")
        # 应调用 APScheduler 的 add_job
        scheduler.scheduler.add_job.assert_called_once()
        args, kwargs = scheduler.scheduler.add_job.call_args
        assert "id" in kwargs
        assert kwargs["id"] == "test_spider"
        assert kwargs["replace_existing"] is True

    def test_stores_job_info(self, scheduler):
        """注册后应在 _jobs 和 _spider_map 中存储信息"""
        scheduler.add_job(FakeSpider, "0 8 * * *")
        assert "test_spider" in scheduler._jobs
        assert scheduler._jobs["test_spider"]["cron"] == "0 8 * * *"
        assert scheduler._jobs["test_spider"]["enabled"] is True
        assert scheduler._spider_map["test_spider"] is FakeSpider

    def test_replaces_existing_job(self, scheduler):
        """相同名称的 spider 重复注册应替换旧任务"""
        scheduler.add_job(FakeSpider, "0 8 * * *")
        scheduler.add_job(FakeSpider, "0 9 * * *")
        assert scheduler._jobs["test_spider"]["cron"] == "0 9 * * *"
        # APScheduler add_job 应被调用两次，第二次 replace_existing=True
        assert scheduler.scheduler.add_job.call_count == 2

    def test_raises_on_invalid_cron_format(self, scheduler):
        """无效的 cron 表达式（非 5 段）应抛出 ValueError"""
        with pytest.raises(ValueError, match="cron.*5.*段|cron.*格式|Invalid cron"):
            scheduler.add_job(FakeSpider, "invalid")

    def test_raises_on_empty_cron(self, scheduler):
        """空的 cron 表达式应抛出 ValueError"""
        with pytest.raises(ValueError):
            scheduler.add_job(FakeSpider, "")

    def test_raises_on_too_many_parts(self, scheduler):
        """超过 5 段的 cron 表达式应抛出 ValueError"""
        with pytest.raises(ValueError):
            scheduler.add_job(FakeSpider, "0 8 * * * *")

    def test_uses_spider_name_as_job_id(self, scheduler):
        """job id 应使用 spider 的 name 属性"""
        scheduler.add_job(FakeSpider, "0 */4 * * *")
        scheduler.scheduler.add_job.assert_called_once()
        _, kwargs = scheduler.scheduler.add_job.call_args
        assert kwargs["id"] == "test_spider"
        assert kwargs["name"] == "test_spider"


class TestRunOnce:
    """run_once 方法测试"""

    def test_registered_spider_adds_date_job(self, scheduler):
        """已注册的 spider 应添加一个一次性任务"""
        from apscheduler.triggers.date import DateTrigger
        scheduler.add_job(FakeSpider, "0 8 * * *")
        scheduler.run_once("test_spider")
        # 应再调用一次 add_job（带 date trigger）
        assert scheduler.scheduler.add_job.call_count == 2
        args, kwargs = scheduler.scheduler.add_job.call_args
        assert isinstance(kwargs.get("trigger"), DateTrigger)

    @pytest.mark.parametrize("spider_name", ["non_existent", "unknown", ""])
    def test_not_registered_spider_raises_error(self, scheduler, spider_name):
        """未注册的 spider 应抛出 ValueError"""
        with pytest.raises(ValueError, match="未注册|not registered|not found"):
            scheduler.run_once(spider_name)


class TestGetStatus:
    """get_status 方法测试"""

    def test_returns_dict(self, scheduler):
        """应返回 dict 类型"""
        status = scheduler.get_status()
        assert isinstance(status, dict)

    def test_returns_status_for_all_jobs(self, scheduler):
        """应返回所有已注册任务的状态"""
        scheduler.add_job(FakeSpider, "0 8 * * *")
        status = scheduler.get_status()
        assert "test_spider" in status
        assert status["test_spider"]["cron"] == "0 8 * * *"
        assert status["test_spider"]["enabled"] is True

    def test_status_contains_next_run_time(self, scheduler):
        """状态应包含 next_run_time 字段"""
        scheduler.add_job(FakeSpider, "0 8 * * *")
        status = scheduler.get_status()
        assert "next_run_time" in status["test_spider"]

    def test_empty_when_no_jobs(self, scheduler):
        """无注册任务时应返回空 dict"""
        status = scheduler.get_status()
        assert status == {}

    def test_handles_multiple_spiders(self, scheduler):
        """多个 spider 的状态应分别返回"""
        class Spider2:
            name = "spider2"
        scheduler.add_job(FakeSpider, "0 8 * * *")
        scheduler.add_job(Spider2, "0 */2 * * *")
        status = scheduler.get_status()
        assert len(status) == 2
        assert "test_spider" in status
        assert "spider2" in status


class TestStartStop:
    """start / stop 生命周期测试"""

    def test_start_calls_apscheduler_start(self, scheduler):
        """start() 应调用 APScheduler 的 start()"""
        scheduler.start()
        scheduler.scheduler.start.assert_called_once()

    def test_stop_calls_apscheduler_shutdown(self, scheduler):
        """stop() 应调用 APScheduler 的 shutdown()"""
        scheduler.stop()
        scheduler.scheduler.shutdown.assert_called_once()

    def test_stop_with_force(self, scheduler):
        """stop(force=True) 应传递 wait=False"""
        scheduler.stop(force=True)
        scheduler.scheduler.shutdown.assert_called_once_with(wait=False)

    def test_start_idempotent(self, scheduler):
        """多次调用 start() 应不会导致错误"""
        scheduler.start()
        scheduler.start()  # 第二次调用不应抛异常
        assert scheduler.scheduler.start.call_count == 2


class TestEdgeCases:
    """边界情况测试"""

    def test_cron_with_slash(self, scheduler):
        """cron 表达式包含 / 时应正常工作（如 */4）"""
        scheduler.add_job(FakeSpider, "0 */4 * * *")
        scheduler.scheduler.add_job.assert_called_once()
        _, kwargs = scheduler.scheduler.add_job.call_args
        assert kwargs["id"] == "test_spider"

    def test_cron_with_comma(self, scheduler):
        """cron 表达式包含逗号时应正常工作（如 8,18）"""
        scheduler.add_job(FakeSpider, "0 8,18 * * *")
        scheduler.scheduler.add_job.assert_called_once()

    def test_cron_with_hyphen(self, scheduler):
        """cron 表达式包含连字符时应正常工作（如 1-5）"""
        scheduler.add_job(FakeSpider, "0 10 * * 1-5")
        scheduler.scheduler.add_job.assert_called_once()

    def test_spider_without_name_attribute(self, scheduler):
        """spider 类没有 name 属性时，应使用类名作为 fallback"""
        class NoNameSpider:
            pass
        scheduler.add_job(NoNameSpider, "0 8 * * *")
        # 应使用类名
        assert "NoNameSpider" in scheduler._jobs
