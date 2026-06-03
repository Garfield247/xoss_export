import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict

from requests import Session
from tqdm import tqdm


def convert_sport_to_number(sport: str) -> str:
    """将运动类型转换为数字字符串"""
    sport_mapping = {
        "徒步": "1",
        "跑步": "2",
        "骑行": "3",
        "游泳": "4",
        "滑雪": "5",
        "训练": "6",
        "室内骑行": "7",
        "虚拟骑行": "8",
        "其他": "0",
    }

    # 如果已经是数字字符串，直接返回
    if sport.isdigit():
        return sport

    # 如果是中文，转换为数字
    return sport_mapping.get(sport, "")


class XossExport:
    def __init__(self, cookies, export_dir: str = "export_file") -> None:
        self.session = Session()
        self.cookies = cookies
        # 使用 pathlib 管理导出目录
        self.export_path = Path(os.path.abspath(export_dir))
        # 自动创建导出目录
        self.export_path.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.total_downloaded = 0
        self.total_failed = 0
        self.start_time = None

    def _print_status(self, message: str, status: str = "INFO"):
        """打印带状态标识的消息"""
        status_colors = {
            "INFO": "\033[94m",  # 蓝色
            "SUCCESS": "\033[92m",  # 绿色
            "WARNING": "\033[93m",  # 黄色
            "ERROR": "\033[91m",  # 红色
            "RESET": "\033[0m",  # 重置
        }

        status_symbols = {"INFO": "ℹ", "SUCCESS": "✓", "WARNING": "⚠", "ERROR": "✗"}

        color = status_colors.get(status, status_colors["INFO"])
        symbol = status_symbols.get(status, "ℹ")
        reset = status_colors["RESET"]

        print(f"{color}[{symbol}] {message}{reset}")

    @property
    def headers(self):

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://www.imxingzhe.com/workouts/list",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Cookie": self.cookies,
        }
        return headers

    def get_pgworkout(self, offset=0, limit=10, sport="", year="", month="") -> Dict:
        url = f"https://www.imxingzhe.com/api/v1/pgworkout/?offset={offset}&limit={limit}&sport={sport}&year={year}&month={month}"

        self._print_status(f"正在获取数据 (偏移: {offset}, 长度: {limit})", "INFO")

        payload = {}
        response = self.session.request("GET", url, headers=self.headers, data=payload)

        if response.status_code == 200:
            data = response.json()
            sport_list = data.get("data", {}).get("data", [])
            self._print_status(f"成功获取 {len(sport_list)} 条运动记录", "SUCCESS")
            return data
        else:
            self._print_status(f"请求失败，状态码: {response.status_code}", "ERROR")
            return None

    def download_workout_file(
        self, title: str, sport_id: int, file_format: str = "gpx"
    ):
        """下载运动文件 (gpx 或 fit)"""
        url = f"https://www.imxingzhe.com/api/v1/workout/{sport_id}/{file_format}/"

        # 使用 pathlib 构建文件路径
        safe_title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = self.export_path / f"{safe_title}_{sport_id}.{file_format}"

        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()  # 检查请求是否成功

            # 使用 pathlib 写入文件
            with open(filename, "wb") as file:
                file.write(response.content)

            self.total_downloaded += 1
            return True

        except Exception as e:
            self.total_failed += 1
            self._print_status(
                f"下载失败: {title} (ID: {sport_id}, 格式: {file_format}) - {str(e)}",
                "ERROR",
            )
            return False

    def run(self, limit=100, sport="", year="", month="", file_format="gpx"):
        self.start_time = time.time()
        self._print_status(f"开始导出行者数据 ({file_format})...", "INFO")
        self._print_status(f"导出目录: {self.export_path.absolute()}", "INFO")

        # 显示筛选条件
        if sport:
            sport_display = (
                sport
                if sport.isdigit()
                else f"{sport}({convert_sport_to_number(sport)})"
            )
            self._print_status(f"运动类型筛选: {sport_display}", "INFO")
        if year:
            self._print_status(f"年份筛选: {year}", "INFO")
        if month:
            self._print_status(f"月份筛选: {month}", "INFO")

        offset = 0
        total_items = 0
        processed_items = 0

        while True:
            data = self.get_pgworkout(offset, limit, sport, year, month)
            if not data:
                break

            sport_list = data.get("data", {}).get("data", [])
            if not sport_list:
                break

            # 如果是第一批数据，显示总数
            if offset == 0:
                total_count = data.get("data", {}).get("total", 0)
                if total_count > 0:
                    total_items = total_count
                    self._print_status(f"发现 {total_items} 条运动记录", "INFO")

            # 显示当前页面信息
            page_num = (offset // limit) + 1
            self._print_status(
                f"正在处理第 {page_num} 页，共 {len(sport_list)} 个文件", "INFO"
            )

            # 使用 tqdm 创建进度条
            with tqdm(
                sport_list,
                desc=f"第{page_num}页",
                unit="文件",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            ) as pbar:

                for s in pbar:
                    processed_items += 1
                    title = s.get("title", "未知标题")
                    sport_id = s.get("id")

                    # 更新进度条描述
                    pbar.set_postfix_str(f"正在下载: {title[:20]}...")

                    success = self.download_workout_file(title, sport_id, file_format)
                    if not success:
                        self._print_status(f"下载失败: {title}", "WARNING")

                    time.sleep(1)  # 避免请求过于频繁

            # 页面下载完成，显示总体进度
            if total_items > 0:
                self._print_status(
                    f"第 {page_num} 页完成，总体进度: {processed_items}/{total_items}",
                    "SUCCESS",
                )
            else:
                self._print_status(
                    f"第 {page_num} 页完成，已处理 {processed_items} 个文件", "SUCCESS"
                )

            offset += limit

        # 显示最终统计
        self._print_final_stats()

    def _print_final_stats(self):
        """打印最终统计信息"""
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)

            print("\n" + "=" * 50)
            self._print_status("导出完成！", "SUCCESS")
            print(f"总耗时: {minutes}分{seconds}秒")
            print(f"成功下载: {self.total_downloaded} 个文件")
            if self.total_failed > 0:
                print(f"下载失败: {self.total_failed} 个文件")
            print(f"导出目录: {self.export_path.absolute()}")
            print("=" * 50)


def main():
    """主函数，处理命令行参数并运行导出程序"""
    parser = argparse.ArgumentParser(
        description="行者数据导出工具 - 从行者网站导出GPX运动数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python xoss_export.py --cookies "your_cookies_here"
  python xoss_export.py --cookies "your_cookies_here" --output-dir "my_exports"
  python xoss_export.py -c "your_cookies_here" -o "my_exports" -l 50
  python xoss_export.py -c "your_cookies_here" -s "跑步" -y "2024" -m "1"
  python xoss_export.py -c "your_cookies_here" -s "2" -l 20
        """,
    )

    parser.add_argument(
        "--cookies", "-c", required=True, help="浏览器中的Cookie字符串（必需）"
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        default="export_file",
        help="导出文件的保存目录（默认: export_file）",
    )

    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="每次请求的记录数量（默认: 10）"
    )

    parser.add_argument(
        "--sport",
        "-s",
        choices=[
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "徒步",
            "跑步",
            "骑行",
            "游泳",
            "滑雪",
            "训练",
            "室内骑行",
            "虚拟骑行",
            "其他",
        ],
        default="",
        help="运动类型筛选（默认: 全部）\n"
        "数字格式: 0=其他, 1=徒步, 2=跑步, 3=骑行, 4=游泳, 5=滑雪, 6=训练, 7=室内骑行, 8=虚拟骑行\n"
        "中文格式: 徒步, 跑步, 骑行, 游泳, 滑雪, 训练, 室内骑行, 虚拟骑行, 其他",
    )

    parser.add_argument("--year", "-y", default="", help="年份筛选（默认: 全部）")

    parser.add_argument("--month", "-m", default="", help="月份筛选（默认: 全部）")

    parser.add_argument(
        "--format",
        "-f",
        choices=["gpx", "fit"],
        default="gpx",
        help="导出文件格式 (默认: gpx)",
    )

    args = parser.parse_args()

    # 验证参数
    if not args.cookies.strip():
        print("\033[91m[✗] 错误: Cookie不能为空\033[0m")
        return

    # 验证Cookie中是否包含sessionid
    if "sessionid=" not in args.cookies:
        print("\033[91m[✗] 错误: Cookie中必须包含sessionid\033[0m")
        print("\033[93m[ℹ] 请确保从浏览器复制的Cookie包含完整的sessionid字段\033[0m")
        return

    # 转换运动类型参数
    sport_param = convert_sport_to_number(args.sport) if args.sport else ""

    # 显示启动信息
    print("\n" + "=" * 60)
    print("🚴 行者数据导出工具")
    print("=" * 60)
    print(f"📁 导出目录: {args.output_dir}")
    print(f"📊 每次请求数量: {args.limit}")
    if args.sport:
        sport_display = (
            args.sport if args.sport.isdigit() else f"{args.sport}({sport_param})"
        )
        print(f"🏃 运动类型: {sport_display}")
    if args.year:
        print(f"📅 年份: {args.year}")
    if args.month:
        print(f"📅 月份: {args.month}")
    print("=" * 60 + "\n")

    try:
        xe = XossExport(args.cookies, args.output_dir)
        xe.run(
            limit=args.limit,
            sport=sport_param,
            year=args.year,
            month=args.month,
            file_format=args.format,
        )
    except KeyboardInterrupt:
        print("\n\033[93m[⚠] 用户中断了程序\033[0m")
        sys.exit(1)
    except Exception as e:
        print(f"\n\033[91m[✗] 导出过程中发生错误: {e}\033[0m")
        sys.exit(1)


def run_export(
    cookies,
    output_dir="export_file",
    limit=10,
    sport="",
    year="",
    month="",
    file_format="gpx",
):
    """导出函数，供GUI调用"""
    try:
        xe = XossExport(cookies, output_dir)
        xe.run(
            limit=limit, sport=sport, year=year, month=month, file_format=file_format
        )
        return True, "导出完成"
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    main()
