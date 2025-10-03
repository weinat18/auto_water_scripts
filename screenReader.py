import cv2
import numpy as np
import pyautogui
from PIL import Image
import os
from pynput import keyboard
import time


class KeyboardMonitor:
    def __init__(self):
        self.listener = None
        self.is_running = False


    def on_release(self, key):
        if key == keyboard.Key.esc:
            # ESC键停止监听
            return False

    def start(self):
        """启动键盘监听（非阻塞）"""
        self.is_running = True
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

def get_top_n_values(result, n=5):
    flat_result = result.flatten()  # 将二维数组展平为一维
    indices = np.argpartition(flat_result, -n)[-n:]  # 获取前 n 个最大值的索引
    top_values = flat_result[indices]  # 获取对应的值
    sorted_indices = indices[np.argsort(-top_values)]  # 按值降序排序索引
    sorted_values = top_values[np.argsort(-top_values)]  # 按值降序排序值

     # 将一维索引转换为二维坐标
    positions = [np.unravel_index(idx, result.shape) for idx in sorted_indices]
    return list(zip(sorted_values, positions))

def preprocess(src, gray_src):
    # 分离颜色通道
    bgr_images = cv2.split(src)

    # 获取各个通道
    r_src_img = bgr_images[2]  # 红色通道
    g_src_img = bgr_images[1]  # 绿色通道
    b_src_img = bgr_images[0]  # 蓝色通道

    # 计算 a_src_img = r_src_img + 10 - g_src_img
    a_src_img = cv2.add(r_src_img, 10)
    a_src_img = cv2.subtract(a_src_img, g_src_img)

    # 对 a_src_img 进行模糊处理
    blur_a_src = cv2.blur(a_src_img, (3, 3))

    # 以下是被注释掉的代码
    # threshold(a_src_img, gray_src, 90, 255, THRESH_BINARY)
    # dst2 = getStructuringElement(MORPH_RECT, Size(5, 5))
    # maodian = Point(-1, -1)
    # morphologyEx(gray_src, gray_src, MORPH_CLOSE, dst2)

    # 对蓝色通道进行阈值处理
    _, gray_src = cv2.threshold(b_src_img, 90, 255, cv2.THRESH_BINARY)

    # 创建结构元素并进行闭操作
    dst2 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    gray_src = cv2.morphologyEx(gray_src, cv2.MORPH_CLOSE, dst2)

    # 显示图像
    cv2.imshow("r_src_img", b_src_img)
    cv2.imshow("gray_src", gray_src)

    return gray_src

def find_contours(binary_src , min_area):
    contours, hierarchy = cv2.findContours(binary_src, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i , cnt in enumerate(contours):
        area = cv2.contourArea(cnt)  # 普通面积（正数）
        if area < min_area:
            continue

class ScreenPatternAutomation:
    def __init__(self, confidence_threshold):
        """
        初始化自动化脚本

        Args:
            confidence_threshold (float): 图案识别置信度阈值，0-1之间
        """
        self.confidence_threshold = confidence_threshold
        self.template_images = {}

    def load_template(self, template_name, template_path):
        """
        加载模板图像

        Args:
            template_name (str): 模板名称
            template_path (str): 模板图像文件路径
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")

        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            raise ValueError(f"无法加载模板图像: {template_path}")
        else :
            print('cv2好使辣')
        self.template_images[template_name] = template
        print(f"已加载模板: {template_name}")



    def find_pattern(self, template_name, region=None):
        """
        在屏幕上查找指定模板

        Args:
            template_name (str): 要查找的模板名称
            region (tuple): 搜索区域 (x, y, width, height)，None表示全屏

        Returns:
            dict: 包含位置和置信度的字典，未找到返回None
        """
        if template_name not in self.template_images:
            raise ValueError(f"未找到模板: {template_name}")

        # 截取屏幕
        screenshot = pyautogui.screenshot(region=region)
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        template = self.template_images[template_name]

        # 模板匹配
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if result is not None:
            top_five = get_top_n_values(result)
        else:
            print("未找到匹配的图案或 target_info 为空")
            return False
        print(top_five)
        if max_val >= self.confidence_threshold:
            # 计算中心点坐标
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2

            if region:
                center_x += region[0]
                center_y += region[1]

            return {
                'position': (center_x, center_y),
                'top_left': (max_loc[0], max_loc[1]),
                'bottom_right': (max_loc[0] + w, max_loc[1] + h),
                'size': (w, h),
                'confidence': max_val,
                'target_info': result
            }

        return None

    def wait_for_pattern(self, template_name, timeout=30000, interval=1, region=None):
        """
        等待图案出现

        Args:
            template_name (str): 要等待的模板名称
            timeout (int): 超时时间（秒）
            interval (float): 检查间隔（秒）
            region (tuple): 搜索区域

        Returns:
            dict: 找到的图案信息，超时返回None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.find_pattern(template_name, region)
            if result:
                return result


        return None

    def type_at_pattern(self, template_name, text, wait_timeout=30, region=None, offset_x=0, offset_y=0):
        """
        在图案位置输入文本，支持偏移

        Args:
            template_name (str): 模板名称
            text (str): 要输入的文本
            wait_timeout (int): 等待图案出现的超时时间
            region (tuple): 搜索区域
            offset_x (int): 相对于模板中心的X轴偏移量
            offset_y (int): 相对于模板中心的Y轴偏移量

        Returns:
            bool: 成功输入返回True，否则False
        """
        pattern_info = self.wait_for_pattern(template_name, wait_timeout, region=region)
        if pattern_info and 'target_info' in pattern_info and pattern_info['target_info'] is not None:
            top_five = get_top_n_values(pattern_info['target_info'])
        else:
            print("未找到匹配的图案或 target_info 为空")
            return False
        for value , position in top_five:
            x, y = position
            # 应用偏移
            target_x = x + offset_x
            target_y = y + offset_y
            pyautogui.write(text)

            pyautogui.click(target_x, target_y)  # 先点击定位
        return True



def main():
    # 创建自动化实例
    automation = ScreenPatternAutomation(confidence_threshold=0.99)

    try:
        automation.load_template('water', 'needWater.png')

        while monitor.is_alive():


            automation.type_at_pattern('water', '1', offset_y=0, offset_x=10, wait_timeout=10)

    except Exception as e:
        print(f"执行过程中出现错误: {e}")


if __name__ == "__main__":
    # 安全设置：鼠标移动到角落时停止程序
    pyautogui.FAILSAFE = False
    monitor = KeyboardMonitor()
    monitor.start()
    main()
