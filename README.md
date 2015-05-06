# ustcbbs-archiver
- Scripts to archive ustcbbs posts.

## 工具

*  python3
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
