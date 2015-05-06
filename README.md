# ustcbbs-archiver
--- Scripts to archive ustcbbs posts.

使用 Python 作为爬虫，获取 ustcbbs 的信息存入本地。

仍然处在开发中。

## 当前成果

可以将指定板块的所有文章的标题、链接存入数据库。(libbbsarchiver.py)

为了防止流量过大，限制了每页暂停1秒。

## 工具

*  python3+requests+bs4
*  sqlite3

## 思路

*  建议在网络环境良好的地方进行下载

### 正文区

- 由 `http://bbs.ustc.edu.cn/cgi/bbsdoc?board=Linux` 的文章数获取当前版面最大文章值
- 由 `http://bbs.ustc.edu.cn/cgi/bbsdoc?board=Linux&start=12345` 的方式获取链接对应的 **时间**，写入数据库
- 遍历文章数添加数据库
- 进行下载，将网页正文添加至数据库

进阶：

- 对网页正文进行分析得到原文与发文相关信息，存入新数据库
- 实现增量更新（根据时间）
- 对附件进行下载

## 授权

MIT License

## 作者

Boyuan Yang (073plan@gmail.com)
