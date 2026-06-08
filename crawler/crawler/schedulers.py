"""
信息差发现平台 — 爬虫系统 APScheduler 调度器

基于 APScheduler BackgroundScheduler 实现定时调度。
支持：
- 定时任务（cron 表达式）
- 手动触发运行
- 运行状态查询
- 优雅启停
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)


class CrawlerScheduler:
    """基于 APScheduler 的定时调度器

    管理所有 spider 的定时调度、手动触发和状态查询。

    Usage:
        scheduler = CrawlerScheduler()
        scheduler.add_job(WechatChengduSpider, "0 8,18 * * *")
        scheduler.start()
        status = scheduler.get_status()
        scheduler.run_once("wechat_chengdu")
    """

    def __init__(self, settings_module: str = "config.settings"):
        """
        初始化调度器

        Args:
            settings_module: Scrapy 设置模块路径，默认 "config.settings"
        """
        self.settings_module = settings_module
        self.scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": True,          # 合并错过的任务
                "max_instances": 1,        # 同一时刻只运行一个实例
                "misfire_grace_time": 300, # 错过执行后 5 分钟内补跑
            }
        )
        # 内部状态
        self._jobs: dict[str, dict] = {}        # job_name -> {cron, enabled}
        self._spider_map: dict[str, type] = {}   # job_name -> spider_class

    # ── 生命周期管理 ──

    def start(self):
        """启动调度器（开始执行定时任务）"""
        logger.info("调度器启动中...")
        self.scheduler.start()
        enabled_count = sum(1 for j in self._jobs.values() if j["enabled"])
        logger.info(f"调度器已启动，共 {len(self._jobs)} 个任务（已启用: {enabled_count}）")

    def stop(self, force: bool = False):
        """停止调度器

        Args:
            force: 是否强制停止（不等待正在运行的任务）
        """
        if force:
            logger.warning("调度器强制停止中...")
            self.scheduler.shutdown(wait=False)
        else:
            logger.info("调度器优雅停止中...")
            self.scheduler.shutdown(wait=True)
        logger.info("调度器已停止")

    # ── 任务管理 ──

    def add_job(self, spider_cls: type, cron_expr: str):
        """
        注册一个定时任务

        Args:
            spider_cls: Spider 类（需有 name 属性）
            cron_expr:  5 段 cron 表达式，如 "0 8,18 * * *"
                       格式: 分 时 日 月 周

        Raises:
            ValueError: cron 表达式格式无效
        """
        # 校验 cron 表达式格式
        self._validate_cron(cron_expr)

        # 获取 spider 名称
        spider_name = getattr(spider_cls, "name", spider_cls.__name__)

        # 解析 cron 表达式为 APScheduler CronTrigger
        trigger = self._parse_cron(cron_expr)

        # 注册到 APScheduler
        self.scheduler.add_job(
            func=self._run_spider_job,
            trigger=trigger,
            args=[spider_cls],
            id=spider_name,
            name=spider_name,
            replace_existing=True,
        )

        # 保存内部状态
        self._jobs[spider_name] = {
            "cron": cron_expr,
            "enabled": True,
        }
        self._spider_map[spider_name] = spider_cls

        logger.info(f"[{spider_name}] 定时任务已注册: cron={cron_expr}")

    def run_once(self, spider_name: str):
        """
        手动触发运行某个 spider

        Args:
            spider_name: spider 的名称（对应注册时的 name）

        Raises:
            ValueError: spider 未注册
        """
        if spider_name not in self._spider_map:
            raise ValueError(f"Spider '{spider_name}' 未注册，无法手动触发")

        spider_cls = self._spider_map[spider_name]
        job_id = f"{spider_name}_manual_{int(datetime.now().timestamp())}"

        self.scheduler.add_job(
            func=self._run_spider_job,
            trigger=DateTrigger(run_date=datetime.now()),
            args=[spider_cls],
            id=job_id,
            name=f"{spider_name}_manual",
        )

        logger.info(f"[{spider_name}] 手动触发已提交")

    def remove_job(self, spider_name: str):
        """移除已注册的定时任务"""
        if spider_name in self._jobs:
            self.scheduler.remove_job(spider_name)
            del self._jobs[spider_name]
            del self._spider_map[spider_name]
            logger.info(f"[{spider_name}] 定时任务已移除")

    # ── 状态查询 ──

    def get_status(self) -> dict[str, dict]:
        """
        查看各 spider 运行状态

        Returns:
            {spider_name: {cron, enabled, next_run_time, pending}}
        """
        status: dict[str, dict] = {}
        for name, info in self._jobs.items():
            job = self.scheduler.get_job(name)
            status[name] = {
                "cron": info["cron"],
                "enabled": info["enabled"],
                "next_run_time": str(job.next_run_time) if job and job.next_run_time else None,
                "pending": False,
            }
        return status

    # ── 内部方法 ──

    def _run_spider_job(self, spider_cls: type):
        """执行 spider 爬取任务（由 APScheduler 回调）

        实际执行通过 Scrapy 的 CrawlerProcess 完成。
        这里封装了异常捕获和日志。

        Args:
            spider_cls: Spider 类
        """
        spider_name = getattr(spider_cls, "name", spider_cls.__name__)
        logger.info(f"[{spider_name}] 开始执行爬取任务")
        try:
            # 使用 Scrapy 的 CrawlerProcess 运行 spider
            self._execute_spider(spider_cls)
            logger.info(f"[{spider_name}] 爬取任务完成")
        except Exception as e:
            logger.error(f"[{spider_name}] 爬取任务失败: {e}", exc_info=True)

    def _execute_spider(self, spider_cls: type):
        """使用 Scrapy CrawlerProcess 执行 spider

        注意：CrawlerProcess 启动后不会自动返回，
        因此在 APScheduler 线程中调用时使用 CrawlerRunner。
        """
        from twisted.internet import reactor
        from scrapy.crawler import CrawlerRunner
        from scrapy.utils.project import get_project_settings

        settings = get_project_settings()
        runner = CrawlerRunner(settings)

        deferred = runner.crawl(spider_cls)
        # 使用阻塞方式等待爬取完成（在 APScheduler 线程中）
        deferred.addBoth(lambda _: reactor.stop() if reactor.running else None)
        reactor.run(installSignalHandlers=False)

    def _validate_cron(self, cron_expr: str) -> None:
        """校验 cron 表达式格式（必须为 5 段）"""
        if not cron_expr or not isinstance(cron_expr, str):
            raise ValueError(f"Invalid cron format: '{cron_expr}' — cron expression must be a non-empty string")
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron format: '{cron_expr}' — "
                f"expected 5 fields (minute hour day month day_of_week), got {len(parts)}"
            )

    def _parse_cron(self, cron_expr: str) -> CronTrigger:
        """将 5 段 cron 字符串解析为 APScheduler CronTrigger

        cron 格式: 分 时 日 月 周
        """
        parts = cron_expr.strip().split()
        return CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
