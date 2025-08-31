import time
import numpy as np
import requests
import bs4
import re
import os
import pandas as pd
import matplotlib.pyplot as plt
import platform

# 根据操作系统设置 matplotlib 的字体
system = platform.system()

if system == 'Windows':
    # Windows系统使用黑体
    plt.rcParams['font.family'] = 'SimHei'
elif system == 'Darwin':
    # Mac系统使用苹方
    plt.rcParams['font.family'] = 'Heiti TC'
else:
    # 其他系统使用默认字体
    plt.rcParams['font.family'] = 'sans-serif'

# 全局标记，保存信息用
SELECT = None  # 选择的查询模式
PAGE = None  # 查询的页数
WARNING = "过大的页数将降低性能和分析图表的可读性"  # 警告信息


# 1) 【数据爬取】 采用 Requests 抓取网页数据
def GetHtmlFromUrl(path, file, url, user_input_final, page=1):
    """
    从指定URL获取HTML内容

    参数:
        path: 保存路径
        file: 文件名
        url: 基础URL
        user_input_final: 用户输入的查询参数
        page: 要爬取的页数

    返回:
        text: 获取的HTML内容
    """
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
    }
    text = ""
    for i in range(page):
        final_url = url + user_input_final + f"{i + 1}"  # 构建完整URL
        response = requests.get(final_url, headers=headers)
        print(f"正在爬取第{i + 1}个地址：{response.url}")
        response.encoding = "GBK"  # 设置编码为GBK
        text += response.text
        # delay避免被反爬
        time.sleep(1)
    SaveHtml(path, file, text)  # 保存HTML到文件
    return text


# 2) 【网页存储】 将爬到的结果需要写进 html 文件中
def SaveHtml(path, file, data):
    """
    保存HTML内容到文件

    参数:
        path: 保存路径
        file: 文件名
        data: 要保存的HTML内容
    """
    if not os.path.exists(path):
        os.makedirs(path)  # 如果路径不存在则创建
    with open(path + "/" + file, 'w+', encoding="GBK") as f:
        f.writelines(data)
    print(f"原始HTML网页文件已保存至./data/dangdang-{SELECT}-{PAGE}.html中")
    time.sleep(1)


def SelectMode_andInit(path, file, url):
    """
    选择查询模式并初始化爬虫

    参数:
        path: 保存路径
        file: 文件名
        url: 基础URL

    返回:
        爬取的HTML内容
    """
    global SELECT
    global PAGE
    user_input_final = None
    page = None
    file_all = ""

    print(f"{'当当网图书数据爬虫1.1':=^64}")
    print(f"{'请输入选择当当热销图书查询模式':=^60}")
    print("1.查询往年（2021-2024）全年排行")
    print("2.查询2025年各月排行")
    print("3.查询最近30天排行")
    print("4.查询最近7天排行")
    print("5.查询最近24小时排行")
    print("其他任意键.退出程序")
    user_input = input("请输入序号：")

    # 根据用户选择设置查询参数
    if user_input == "1":
        user_input_final = input("请输入要搜索的年份（2021-2024）：")
        if 2021 <= eval(user_input_final) <= 2024:
            SELECT = f"{user_input_final}年"
            user_input_final = f"year-{user_input_final}-0-1-"
            page = int(input(f"请输入要搜索的页数（1-25）ps:{WARNING}："))
            if 1 <= page <= 25:
                PAGE = f"{page}页"
            else:
                Input_Error()
        else:
            Input_Error()
    elif user_input == "2":
        user_input_final = input("请输入要搜索的月份（1-5）：")
        if 1 <= int(user_input_final) <= 5:
            SELECT = f"{user_input_final}月"
            user_input_final = f"month-2025-{user_input_final}-1-"
            page = int(input(f"请输入要搜索的页数（1-25）ps:{WARNING}："))
            if 1 <= page <= 25:
                PAGE = f"{page}页"
            else:
                Input_Error()
        else:
            Input_Error()
    elif user_input == "3":
        page = int(input(f"请输入要搜索的页数（1-25）ps:{WARNING}："))
        if 1 <= page <= 25:
            PAGE = f"{page}页"
            SELECT = f"最近30天"
            user_input_final = f"recent30-0-0-1-"
        else:
            Input_Error()
    elif user_input == "4":
        page = int(input(f"请输入要搜索的页数（1-25）ps:{WARNING}："))
        if 1 <= page <= 25:
            PAGE = f"{page}页"
            SELECT = f"最近7天"
            user_input_final = f"recent7-0-0-1-"
        else:
            Input_Error()
    elif user_input == "5":
        page = int(input(f"请输入要搜索的页数（1-25）ps:{WARNING}："))
        if 1 <= page <= 25:
            PAGE = f"{page}页"
            SELECT = f"最近24小时"
            user_input_final = f"24hours-0-0-1-"
        else:
            Input_Error()
    else:
        exit()  # 用户选择退出

    if page is None or user_input_final is None:
        exit()
    file_all += file.split(".")[0] + "-" + SELECT + "-" + PAGE + "." + file.split(".")[1]
    return GetHtmlFromUrl(path, file_all, url, user_input_final, page)


def Input_Error():
    """处理输入错误"""
    print("输入有误，请重新运行程序")
    exit()


# 3) 【数据解析】 采用 BeautifulSoup 解析抓取到的数据，解析后的原始数据保存为csv文件
def CatchInfoFromHtml(string):
    """
    从HTML中提取图书信息

    参数:
        string: HTML内容

    返回:
        dataf: 包含图书信息的DataFrame
    """
    book_name = []  # 书名列表
    author = []  # 作者列表
    publishing_house = []  # 出版社列表
    book_date = []  # 出版日期列表
    price_n = []  # 当前价格列表
    price_r = []  # 原价列表
    price_s = []  # 折扣列表
    comments_num = []  # 评论数列表
    book_link = []  # 图书链接列表
    comments_link = []  # 评论链接列表

    soup = bs4.BeautifulSoup(string, "html.parser")  # 创建BeautifulSoup对象

    # 提取书名和链接
    for div in soup.find_all("div", class_="name"):
        for a in div.find_all("a"):
            title = a.get("title")
            book_name.append(Title_Clean(title))  # 清洗书名
            book_link.append(a.get("href"))

    catch_count = 0
    # 提取作者、出版社和出版日期
    for div in soup.find_all("div", class_="publisher_info"):
        date = div.find("span", string=re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
        if catch_count % 2:
            if date:
                book_date.append(date.string)
            else:
                # 如果没有日期 增加假值
                book_date.append("2000-01-01")
        a_tag = div.find("a")
        # 有的div->publisher_info中没有<a></a>
        if a_tag:
            # 增加对 a_tag.string 是否为 None 的检查
            if a_tag.string:
                if catch_count % 2 == 0:
                    author.append(a_tag.string.strip())
                else:
                    publishing_house.append(a_tag.string.strip())
            else:
                # 当 a_tag 存在但没有文本时
                if catch_count % 2 == 0:
                    author.append("未知作者")
                else:
                    publishing_house.append("未知出版社")
        else:
            if catch_count % 2 == 0:
                author.append("未知作者")
            else:
                publishing_house.append("未知出版社")
        catch_count = catch_count + 1

    # 提取价格信息
    for div in soup.find_all("div", class_="price"):
        price_n_tag = div.find("span", class_="price_n")
        price_r_tag = div.find("span", class_="price_r")
        price_s_tag = div.find("span", class_="price_s")

        # 添加检查防止 NoneType 错误
        if price_n_tag and price_n_tag.string:
            price_n.append(eval(price_n_tag.string[1:]))  # 去掉价格前的符号并转换为数字
        else:
            price_n.append(0.0)

        if price_r_tag and price_r_tag.string:
            price_r.append(eval(price_r_tag.string[1:]))
        else:
            price_r.append(0.0)

        if price_s_tag and price_s_tag.string:
            price_s.append(price_s_tag.string)
        else:
            price_s.append("0折")

    # 提取评论信息
    for a in soup.find_all("a", string=re.compile(r"条评论")):
        # 网页bug，无评论值
        if a.string == "条评论" or a.string is None:
            comments_num.append(0)
        else:
            comments_num.append(eval(a.string[:-3]))  # 去掉"条评论"并转换为数字
        comments_link.append(a.get("href"))

    # 创建DataFrame
    dataf = pd.DataFrame({
        "书名": book_name,
        "作者": author,
        "出版社": publishing_house,
        "出版时间": book_date,
        "价格": price_n,
        "原价": price_r,
        "折扣": price_s,
        "评论数": comments_num,
        "商品链接": book_link
    })
    dataf.to_csv(f"./data/{SELECT}-{PAGE}.csv", index=False)  # 保存为CSV文件
    time.sleep(1)
    print(f"CSV原始网页数据表格文件已保存至./data/{SELECT}-{PAGE}中")
    return dataf


# 4) 【数据分析】 采用 numpy 和 pandas， 对上述数据进行分析
def CatchInfoFromDF(dataframe):
    """
    对图书数据进行统计分析

    参数:
        dataframe: 包含图书信息的DataFrame
    """
    # 检查路径是否正常
    if not os.path.exists("./analysis"):
        os.makedirs("./analysis")

    # csv1最受欢迎作者排行
    author_counter = dataframe["作者"].value_counts()  # 统计作者出现次数
    author_counter.to_csv(f"./analysis/{SELECT}最受欢迎作者排行.csv")

    # csv2出版图书最多出版社排行
    publishing_house_counter = dataframe["出版社"].value_counts()  # 统计出版社出现次数
    publishing_house_counter.to_csv(f"./analysis/{SELECT}出版图书最多出版社排行.csv")

    # csv3讨论最多图书排行，增加评论数比例
    # ascending=False 降序 True升序
    most_hot_comments = dataframe[["书名", "作者", "评论数"]].sort_values(by=["评论数"], ascending=False)
    if len(most_hot_comments) > 0 and max(most_hot_comments['评论数']) > 0:
        most_hot_comments["评论数比例"] = [f"{i / max(most_hot_comments['评论数']):.4f}"
                                           for i in most_hot_comments["评论数"]]
        most_hot_comments["评论数比例"] = [f"{float(i) * 100:.2f}%" for i in most_hot_comments["评论数比例"]]
    else:
        most_hot_comments["评论数比例"] = ["0.00%" for _ in most_hot_comments["评论数"]]
    most_hot_comments.to_csv(f"./analysis/{SELECT}讨论最多图书排行.csv", index=False)

    # csv4最便宜图书价格排行与平均价差价，增加相对图书平均价差价
    cheap_price = dataframe[["书名", "作者", "价格"]].sort_values(by=["价格"], ascending=True)
    if len(cheap_price) > 0:
        cheap_price["相对图书平均价差价"] = [
            f"-{np.mean(cheap_price['价格'] - i):.2f}" if i < np.mean(cheap_price["价格"])
            else f"+{i - np.mean(cheap_price['价格']):.2f}"
            for i in cheap_price["价格"]
        ]
    else:
        cheap_price["相对图书平均价差价"] = []
    cheap_price.to_csv(f"./analysis/{SELECT}最便宜图书价格排行与平均价差价.csv", index=False)

    # csv5图书折扣力度排行榜，增加降价幅度
    try:
        dataframe["折扣"] = [float(i[:-1]) if i and i != '' else 0.0 for i in dataframe["折扣"]]  # 转换折扣格式
        bigger_discount = dataframe[["书名", "作者", "价格", "原价", "折扣"]].sort_values(by=["折扣"], ascending=True)
        bigger_discount["降价幅度"] = [
            f"-{j - i:.2f}" for i, j in zip(bigger_discount["价格"], bigger_discount["原价"])
        ]
        bigger_discount.to_csv(f"./analysis/{SELECT}图书折扣力度排行榜.csv", index=False)
    except Exception as e:
        print(f"处理折扣数据时出错: {e}")
        # 创建一个空的折扣排行榜文件
        empty_df = pd.DataFrame(columns=["书名", "作者", "价格", "原价", "折扣", "降价幅度"])
        empty_df.to_csv(f"./analysis/{SELECT}图书折扣力度排行榜.csv", index=False)

    time.sleep(1)
    print(f"CSV表格分析文件已保存至./analysis/{SELECT}XX中")


# 5) 【数据可视化】 分析得到的结果选择合适的图表进行可视化
def DrawPlotFromData(dataframe):
    """
    根据数据绘制可视化图表

    参数:
        dataframe: 包含图书信息的DataFrame
    """
    # 检查路径是否正常
    if not os.path.exists("./matplot"):
        os.makedirs("./matplot")

    # 统计作者出现次数，最多取前十，一页没有十个作者的话就有几个取几个
    author_counter = dataframe["作者"].value_counts()
    name_list = []
    name_count_list = []
    temp_counter = 10 if len(author_counter) > 10 else len(author_counter)
    for name, count in zip(author_counter.index, author_counter):
        if temp_counter:
            name_list.append(name)
            name_count_list.append(count)
            temp_counter = temp_counter - 1
        else:
            break

    # 统计全部出版社出现次数，如果出版图书小于平均值，归为其他
    publishing_house_counter = dataframe["出版社"].value_counts()
    if len(publishing_house_counter) > 0:
        avg_publishing_house_counter = publishing_house_counter.mean()
        publishing_list = []
        publishing_count_list = []
        for publishing_house, count in zip(publishing_house_counter.index, publishing_house_counter):
            publishing_list.append(publishing_house)
            publishing_count_list.append(count)
            # 如果接下来小于平均值，归为其他
            if count < avg_publishing_house_counter:
                break
        # 绘制饼图需要把数据总值归为1
        # 每个值➗总值即为该值对应的百分比
        if sum(publishing_house_counter) > 0:
            publishing_count_list = [i / sum(publishing_house_counter) for i in publishing_count_list]
            publishing_count_list.append(1 - sum(publishing_count_list))
            publishing_list.append('其他')
        else:
            publishing_count_list = []
            publishing_list = []
    else:
        publishing_list = []
        publishing_count_list = []

    # 切换时间为datetime格式，进行时间排序
    dataframe["出版时间"] = pd.to_datetime(dataframe["出版时间"], errors='coerce')
    dataframe = dataframe.sort_values(by=["出版时间"], ascending=True)
    dataframe = dataframe.dropna(subset=["出版时间"])  # 删除无效日期
    temp_counter = 10 if len(dataframe) > 10 else len(dataframe)

    if temp_counter > 0:
        # 处理重名图书，将第2本重名的书改为书名(2)
        book_name_count = {}
        book_name_twice = []
        for i in dataframe["书名"][:temp_counter]:
            book_name_count[i] = book_name_count.get(i, 0) + 1
            if book_name_count[i] > 1:
                book_name_twice.append(f"{i}({book_name_count[i]})")
            else:
                book_name_twice.append(i)
        publishing_date = [str(i) + ":" + j[1:11] for i, j in
                           zip(dataframe["出版时间"].dt.year[:temp_counter], book_name_twice)]
        comments = [i for i in dataframe["评论数"][:temp_counter]]

        # 前十折扣与评论数对比
        dataframe["折扣"] = [i if not np.isnan(i) else 0 for i in dataframe["折扣"]]
        dataframe = dataframe.sort_values(by=["折扣"], ascending=True)
        discount_top10 = [f"{i}折:{j[1:11]}" for i, j in zip(dataframe["折扣"][:10], dataframe["书名"][:10])]
        comments_top10 = [i for i in dataframe["评论数"][:10]]
    else:
        publishing_date = []
        comments = []
        discount_top10 = []
        comments_top10 = []

    # 绘制最受欢迎作者条形图
    if name_list and name_count_list:
        plt.figure(1, figsize=(10, 5))
        plt.bar(name_list, name_count_list, color=["blue", "green"])
        plt.title("最受欢迎作者")
        plt.ylabel("图书数量")
        plt.xlabel("作者")
        plt.xticks(rotation=45)
        plt.yticks(name_count_list)
        plt.tight_layout()
        plt.savefig(f"./matplot/{SELECT}最受欢迎作者.png")

    # 绘制出版社市场占用率饼图
    if publishing_list and publishing_count_list:
        plt.figure(2, figsize=(10, 5))
        plt.pie(publishing_count_list,
                labels=publishing_list,
                autopct='%.2f%%',
                colors=["#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#b2df8a", "#1f78b4"]
                )
        plt.title("热门图书出版社市场占用率")
        plt.savefig(f"./matplot/{SELECT}热门图书出版社市场占用率.png")

    # 绘制价格与原价对比折线图
    double_plot_df = dataframe.sort_values(by=["评论数"], ascending=False)
    if len(double_plot_df) > 0:
        temp_bookname = [i for i in double_plot_df["书名"][:10 if len(double_plot_df) > 10 else len(double_plot_df)]]
        temp_price_n = [i for i in double_plot_df["价格"][:10 if len(double_plot_df) > 10 else len(double_plot_df)]]
        temp_price_r = [i for i in double_plot_df["原价"][:10 if len(double_plot_df) > 10 else len(double_plot_df)]]
        # 处理重复标签
        title_count = {}
        temp_bookname_2 = []
        for title in temp_bookname:
            title_count[title] = title_count.get(title, 0) + 1
            # 如果出现过一次了，加标签
            if title_count[title] > 1:
                # [:10]防止有些书名实在是太长了，严重影响图表可读性
                temp_bookname_2.append(f"{title[:10]}({title_count[title]})")
            else:
                temp_bookname_2.append(title[:10])

        plt.figure(3, figsize=(10, 5))
        plt.plot(temp_bookname_2, temp_price_n, 'b', temp_bookname_2, temp_price_r, 'c-.')
        plt.title("图书价格与原价对比（左侧评论数最多）")
        plt.xlabel("书名")
        plt.ylabel("价格（元）")
        plt.xticks(rotation=45)
        plt.legend(labels=["价格", "原价"])
        plt.tight_layout()
        plt.savefig(f"./matplot/{SELECT}图书价格与原价对比.png")

    # 绘制出版时间与评论数对比条形图
    if publishing_date and comments:
        plt.figure(4, figsize=(10, 5))
        plt.bar(publishing_date, comments, color=["red", "green"])
        plt.ylabel("评论数")
        plt.xticks(publishing_date, rotation=45)
        plt.ticklabel_format(axis='y', style='plain')  # 关闭科学计数法
        plt.title("图书出版时间与评论数对比")
        plt.tight_layout()
        plt.savefig(f"./matplot/{SELECT}图书出版时间与评论数对比.png")

    # 绘制折扣力度与评论数对比条形图
    if discount_top10 and comments_top10:
        plt.figure(5, figsize=(10, 5))
        plt.bar(discount_top10, comments_top10)
        plt.ticklabel_format(axis='y', style='plain')  # 关闭科学计数法
        plt.title("折扣力度与评论数对比")
        plt.xticks(rotation=45)
        plt.ylabel("评论数")
        plt.tight_layout()
        plt.savefig(f"./matplot/{SELECT}折扣力度与评论数对比.png")

    # 询问用户是否显示图表
    while True:
        yes_or_no = input("图表绘制成功，是否立即展示？[Y/N]:")
        if yes_or_no == "Y" or yes_or_no == "y":
            plt.show()
            break
        elif yes_or_no == "N" or yes_or_no == "n":
            break
        else:
            print("输入有误，请再次确定您的操作")
            continue

    print(f"matplotlib图表图片已保存至./analysis/{SELECT}XX中")


# 正则表达式 清洗书名
def Title_Clean(title):
    """
    清洗图书标题

    参数:
        title: 原始标题

    返回:
        清洗后的标题
    """
    # 1. 去除【】中的内容
    title = re.sub(r"【[^】]*】", "", title)
    # 2. 去除中英文括号及其后所有内容
    title = re.sub(r"[（(][^）)]*[）)].*", "", title)
    # 3. 去除破折号（- 或 --）及其后所有内容
    title = re.sub(r"-{1,2}.*", "", title)
    # 4. 去除第一个空格后的所有内容
    title = re.split(r'\s+', title, maxsplit=1)[0]
    # 5. 去除首尾空白字符
    title = title.strip()
    # 6. 加上中文书名号
    return f"《{title}》" if title else ""


# 主程序
URL = "https://bang.dangdang.com/books/bestsellers/01.00.00.00.00.00-"

# 爬虫获取html
html = SelectMode_andInit("./data", "dangdang.html", URL)

# 文件读取获取html
# html = ""
# print("正在从本地HTML读取信息...")
# with open("./data/dangdang.html", 'r', encoding="GBK") as f:
#     for i in f.readlines():
#         html += i.strip()

# 解析HTML获取数据
df = CatchInfoFromHtml(html)

# pandas数据分析提取到csv
CatchInfoFromDF(df)

# 画matplotlib
DrawPlotFromData(df)