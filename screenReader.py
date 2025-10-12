import cv2
import numpy as np
import pyautogui
from PIL import Image
import os
from pynput import keyboard
import time
class KeyboardMonitor:
    def __init__(self):
        self.status = 'pause'  # 初始状态为暂停
        self.tool = '1'  # 初始工具为浇水
        self.listener = None
        self.is_running = False


    def on_release(self, key):
        if key == keyboard.Key.f1:
            # ESC键停止监听
            self.tool = '1'
            print('浇水模式')
            return self.tool

        if key == keyboard.Key.f2:
            # ESC键停止监听
            self.tool = '2'
            print('喂食模式')
            return self.tool

        if key == keyboard.Key.f3:
            # ESC键停止监听
            self.tool = '3'
            print('除虫模式')
            return self.tool

        if key == keyboard.Key.f4:
            # ESC键停止监听
            self.tool = '4'
            print('音乐模式')
            return self.tool

        if key == keyboard.Key.esc:
            # ESC键停止监听
            self.status = 'shutdown'
            print('Shutdown')
            return self.status

        if key == keyboard.Key.caps_lock:
            self.status = 'start'
            print('Start')
            return self.status

        if key == keyboard.Key.shift:
            self.status = 'pause'
            print('Pause')
            return self.status
    def start(self):
        """启动键盘监听（非阻塞）"""
        self.is_running = True
        if self.on_release == 'shutdown':
            self.stop()
        if self.on_release == 'start':
            self.is_running = True
        if self.on_release == 'pause':
            self.is_running = False
        self.listener = keyboard.Listener(
            on_release=self.on_release)
        self.listener.start()
        print("键盘监听已启动")

    def stop(self):
        """停止键盘监听"""
        if self.listener:
            self.listener.stop()
        self.is_running = False
        print("键盘监听已停止")

    def is_alive(self):
        """检查监听器是否在运行"""
        return self.listener and self.listener.is_alive()


def preprocess(srcs):
    # 分离颜色通道
    bgr_images = cv2.split(srcs)

    # 获取各个通道
    r_src_img = bgr_images[0]  # 红色通道(注意：因为screenshot读入的图像通道顺序是rgb)
    g_src_img = bgr_images[1]  # 绿色通道(注意：因为screenshot读入的图像通道顺序是rgb)
    b_src_img = bgr_images[2]  # 蓝色通道(注意：因为screenshot读入的图像通道顺序是rgb)

    # 计算 a_src_img = r_src_img + 10 - g_src_img
    a_src_img = cv2.add(b_src_img, 10)
    a_src_img = cv2.subtract(a_src_img, r_src_img)
    a_src_img = cv2.subtract(a_src_img, g_src_img)

    # 对 a_src_img 进行模糊处理
    blur_a_src = cv2.blur(a_src_img, (4, 2))

    # 以下是被注释掉的代码
    # threshold(a_src_img, gray_src, 90, 255, THRESH_BINARY)
    # dst2 = getStructuringElement(MORPH_RECT, Size(5, 5))
    # maodian = Point(-1, -1)
    # morphologyEx(gray_src, gray_src, MORPH_CLOSE, dst2)

    # 对蓝色通道进行阈值处理
    _, gray_src = cv2.threshold(b_src_img, 254, 255, cv2.THRESH_BINARY)

    # 创建结构元素并进行闭操作
    dst2 = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 2))
    gray_src = cv2.morphologyEx(gray_src, cv2.MORPH_OPEN, dst2)

    # 显示图像

    return gray_src

def find_contours(binary_src , min_area):
    contours, hierarchy = cv2.findContours(binary_src, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours is None or len(contours) == 0:
        return None
    filtered_contours = []
    for i , cnt in enumerate(contours):

        area = cv2.contourArea(cnt)  # 普通面积（正数）
        if area < min_area:
            continue
        filtered_contours.append(cnt)
    return filtered_contours


    # def load_template(self, template_name, template_path):
    #     """
    #     加载模板图像
    #
    #     Args:
    #         template_name (str): 模板名称
    #         template_path (str): 模板图像文件路径
    #     """
    #     if not os.path.exists(template_path):
    #         raise FileNotFoundError(f"模板文件不存在: {template_path}")
    #
    #     template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    #     if template is None:
    #         raise ValueError(f"无法加载模板图像: {template_path}")
    #     else :
    #         print('cv2好使辣')
    #     self.template_images[template_name] = template
    #     print(f"已加载模板: {template_name}")


def find_pattern(region=None):
    """
    在屏幕上查找指定模板

    Args:
        region (tuple): 搜索区域 (x, y, width, height)，None表示全屏

    Returns:
        rotated_rect: 轮廓的最小外接矩形列表，未找到返回None
    """

    # 截取屏幕
    screenshot = pyautogui.screenshot(region=region)
    cv2.imwrite('screenshot.png', np.array(screenshot))
    screenshot = preprocess(np.array(screenshot))
    cv2.imwrite('preprocessed.png', np.array(screenshot))

    # 查找符合条件的轮廓，并返回最小外接矩形
    result = find_contours(screenshot, 120)
    rotated_rect=[]
    for cnt in result:
        rotated_rect.append(cv2.minAreaRect(cnt))

    return rotated_rect

def type_at_pattern(text, region=None, offset_x=0, offset_y=0):
    """
    在图案位置输入文本，支持偏移

    Args:
        text (str): 要输入的文本
        region (tuple): 搜索区域
        offset_x (int): 相对于模板中心的X轴偏移量
        offset_y (int): 相对于模板中心的Y轴偏移量

    Returns:
        bool: 成功输入返回True，否则False
    """
    pattern_info = find_pattern(region=region)
    if pattern_info is None:

        return False
    print('长度为',len(pattern_info))
    for rect in pattern_info:
        center_x, center_y = map(int, rect[0])  # 应用偏移
        target_x = center_x + offset_x
        target_y = center_y + offset_y

        pyautogui.write(text)
        pyautogui.click(target_x, target_y)  # 点击定位
    return True



def main():
    # 创建自动化实例
    monitor = KeyboardMonitor()
    monitor.start()
    try:

        while True :
            status = monitor.status
            tool = monitor.tool
            if status == 'shutdown':
                print('我结束辣')
                break
            elif status == 'start':
                print('我开始辣')
                type_at_pattern(text=tool, offset_y=58, offset_x=-79)
            elif status == 'pause':
                print('我休眠辣')
                while monitor.status == 'pause':
                    time.sleep(1)
        exit()

    except Exception as e:
        print(f"执行过程中出现错误: {e}")


if __name__ == "__main__":
    # 安全设置：鼠标移动到角落时停止程序
    pyautogui.FAILSAFE = False
    monitor = KeyboardMonitor()
    monitor.start()
    main()
