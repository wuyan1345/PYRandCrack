# WuYan's code for cracking MT19937 (2.0 Version)

不仅仅能实现Python官方库的randcrack，还打破了每次泄露数据必须是32位的限制，适配**隔任意位**泄露**任意位**随机数，只要泄露数据就可以构建矩阵并找到能生成此类随机数的**种子**(泄露数据足够多可保证求解存在**唯一解**)。

破解过程仅需五分钟左右 ~~（比我刚入门时用的要跑一个多小时的脚本不知道快了多少）~~

并且整了一个好看的log来分析~

## Dependency

Sage!S4ge!5493!Without sage we can't do anything!

## Specific

具体使用方法详见我的博客 <http://www.wuy4n.com/2025/09/17/PYRandCrack2/>

## Others

2.0版本新增
+ 支持根据随机数生成器状态直接求解种子
+ 更新多个check函数，便于测试与用户理解