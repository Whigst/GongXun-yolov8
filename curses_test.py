import curses
import psutil
import time


def get_cpu_usage():
    # 使用 psutil 库获取 CPU 使用率
    cpu_usage = psutil.cpu_percent(interval=1)
    return cpu_usage


def draw_progress_bar(stdscr, y, x, width, percent):
    # 绘制进度条
    filled_length = int(width * percent // 100)
    # bar = '█' * filled_length + '-' * (width - filled_length)
    bar = '|' * filled_length + ' ' * (width - filled_length)
    stdscr.addstr(y, x, f"CPU: [{bar}] {percent:.2f}%")


def main(stdscr):
    try:
        # 初始化 curses 屏幕，将光标设置为不可见
        curses.curs_set(0)
        # 设置 stdscr 为非阻塞模式，以便程序可以继续执行而不等待用户输入
        stdscr.nodelay(1)
        # 清除屏幕内容
        stdscr.clear()
        # 启动颜色模式
        curses.start_color()
        # 初始化颜色对，前景色为绿色，背景色为黑色
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        while True:
            # 获取 CPU 使用率
            cpu_usage = get_cpu_usage()
            # 清除屏幕，为更新显示做准备
            stdscr.clear()
            # 获取屏幕的高度和宽度
            height, width = stdscr.getmaxyx()
            # 计算进度条的宽度
            bar_width = 50
            # 计算进度条的水平起始位置，使其居中显示
            bar_x = (width - bar_width) // 2
            # 计算进度条的垂直位置，使其居中显示
            bar_y = height // 2
            # 开启之前初始化的颜色对，使进度条显示为绿色
            stdscr.attron(curses.color_pair(1))
            # 调用 draw_progress_bar 函数绘制进度条
            draw_progress_bar(stdscr, bar_y, bar_x, bar_width, cpu_usage)
            # 关闭颜色对
            stdscr.attroff(curses.color_pair(1))
            # 刷新屏幕，显示更新后的内容
            stdscr.refresh()
            # 等待 1 秒，控制更新频率
            time.sleep(1)
    except Exception as e:
        # 打印异常信息
        print(f"Error occurred: {e}")



if __name__ == "__main__":
    curses.wrapper(main)
