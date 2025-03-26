# WuYan's code for cracking MT19937

不仅仅能实现Python官方库的randcrack，还打破了每次泄露数据必须是32位的限制，适配**隔任意位**泄露任意位随机数，只要泄露数据超过19968比特就可以构建矩阵。

破解过程仅需五分钟左右~~（比我刚入门时用的要跑一个多小时的脚本不知道快了多少）~~

并且整了一个好看的log来分析~

## Dependency

Sage!S4ge!5493!Without sage we can't do anything!

## Specific

具体使用方法详见我的博客 <http://www.wuy4n.com/2025/03/26/PYRandCrack/>