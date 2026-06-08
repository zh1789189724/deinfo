"""
信息差发现平台 — 爬虫系统 入口文件

用法：
    python run.py                  # 启动调度器（所有已启用的 spider 按 cron 定时运行）
    python run.py --once wechat    # 手动触发某个 spider 运行一次
    python run.py --status         # 查看运行状态
"""
import argparse
import importlib
import logging
import os
import sys

from dotenv import load_dotenv

# 将项目根目录加入 sys.path
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def setup_logging():
    """配置日志格式"""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="[%(asctime)s] [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_spider_class(source_name: str, source_type: str) -> type | None:
    """
    动态导入 spider 类

    Args:
        source_name: 数据源名称（如 wechat_chengdu）
        source_type: 数据源类型（domestic / overseas）

    Returns:
        Spider 类，如果未找到则返回 None
    """
    module_path = f"crawler.spiders.{source_type}.{source_name}"
    class_name = _to_camel_case(source_name) + "Spider"
    try:
        module = importlib.import_module(module_path)
        spider_cls = getattr(module, class_name, None)
        if spider_cls is None:
            logging.warning(f"[{source_name}] 未找到 spider 类 {class_name}，跳过")
            return None
        return spider_cls
    except (ImportError, ModuleNotFoundError) as e:
        logging.warning(f"[{source_name}] 导入失败: {e}，跳过")
        return None


def _to_camel_case(snake_str: str) -> str:
    """snake_case 转 CamelCase"""
    return "".join(word.capitalize() for word in snake_str.split("_"))


def start_scheduler():
    """启动调度器，注册所有已启用的数据源 spider"""
    from config.sources import SOURCES
    from crawler.schedulers import CrawlerScheduler
    from crawler.spiders.base import BaseSpider

    scheduler = CrawlerScheduler()

    registered_count = 0
    for name, cfg in SOURCES.items():
        if not cfg.get("enabled", True):
            logging.info(f"[{name}] 已禁用，跳过注册")
            continue

        spider_cls = load_spider_class(name, cfg["type"])
        if spider_cls is None:
            continue

        # 验证 spider 类继承 BaseSpider
        if not issubclass(spider_cls, BaseSpider):
            logging.warning(f"[{name}] {spider_cls.__name__} 未继承 BaseSpider，跳过")
            continue

        scheduler.add_job(spider_cls, cfg["cron"])
        registered_count += 1

    if registered_count == 0:
        logging.warning("未注册任何 spider 任务，请先实现 spider 类")
        logging.warning("Spider 类应位于 crawler/spiders/domestic/ 或 overseas/ 目录下")
    else:
        logging.info(f"共注册 {registered_count} 个 spider 任务")

    try:
        scheduler.start()
        # 保持主线程运行
        from twisted.internet import reactor
        reactor.run(installSignalHandlers=True)
    except (KeyboardInterrupt, SystemExit):
        logging.info("收到停止信号，正在关闭...")
        scheduler.stop()
        logging.info("爬虫系统已停止")


def show_status():
    """查看调度器运行状态"""
    from crawler.schedulers import CrawlerScheduler

    scheduler = CrawlerScheduler()
    status = scheduler.get_status()
    if not status:
        print("当前没有注册任何任务。")
        return

    print(f"{'Spider':<25} {'Cron':<20} {'启用':<8} {'下次执行':<30}")
    print("-" * 83)
    for name, info in status.items():
        print(
            f"{name:<25} {info['cron']:<20} "
            f"{'是' if info['enabled'] else '否':<8} "
            f"{info['next_run_time'] or '无':<30}"
        )


def run_once(source_name: str):
    """手动触发指定 spider 运行一次"""
    from config.sources import SOURCES
    from crawler.schedulers import CrawlerScheduler

    # 查找数据源配置
    cfg = SOURCES.get(source_name)
    if not cfg:
        logging.error(f"未找到数据源: {source_name}")
        sys.exit(1)

    # 加载 spider 类
    spider_cls = load_spider_class(source_name, cfg["type"])
    if spider_cls is None:
        logging.error(f"无法加载 spider 类: {source_name}")
        sys.exit(1)

    # 注册并运行
    scheduler = CrawlerScheduler()
    scheduler.add_job(spider_cls, cfg["cron"])
    scheduler.run_once(source_name)
    scheduler.start()

    from twisted.internet import reactor
    reactor.run(installSignalHandlers=True)


def main():
    """主入口"""
    load_dotenv()
    setup_logging()

    parser = argparse.ArgumentParser(description="信息差发现平台 — 爬虫系统")
    parser.add_argument("--once", type=str, help="手动触发某个 spider 运行一次（如 wechat_chengdu）")
    parser.add_argument("--status", action="store_true", help="查看运行状态")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.once:
        run_once(args.once)
    else:
        start_scheduler()


if __name__ == "__main__":
    main()
