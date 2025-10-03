import cv2
import numpy as np

def find_contours(binary_src , min_area):
    contours, hierarchy = cv2.findContours(binary_src, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i , cnt in enumerate(contours):
        if cnt is None:
            print("cnt is None")
            continue
        area = cv2.contourArea(cnt)  # 普通面积（正数）
        if area < min_area:
            continue
    cv2.drawContours(binary_src, [cnt], -1, (0, 0, 255), 2)
    return
def preprocess(src):
    # 分离颜色通道
    bgr_images = cv2.split(src)

    # 获取各个通道
    r_src_img = bgr_images[2]  # 红色通道
    g_src_img = bgr_images[1]  # 绿色通道（注意：原C++代码中这里索引为0）
    b_src_img = bgr_images[0]  # 蓝色通道

    # 计算 a_src_img = r_src_img + 10 - g_src_img
    a_src_img = cv2.add(b_src_img, 10)
    a_src_img = cv2.subtract(a_src_img, r_src_img)
    a_src_img = cv2.subtract(a_src_img, g_src_img)

    # 对 a_src_img 进行模糊处理
    blur_a_src = cv2.blur(a_src_img, (3, 3))

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
    cv2.imshow("r_src_img", r_src_img)
    cv2.imshow("gray_src", gray_src)

    return gray_src


# 使用示例
if __name__ == "__main__":
    # 读取图像
    src = cv2.imread("test.png")
    if src is None:
        print("无法加载图像")
        exit()
    # 调用预处理函数
    result = preprocess(src)
    # 等待按键并关闭窗口
    cv2.waitKey(0)
    cv2.destroyAllWindows()