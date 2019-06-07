# ArkPlanner

明日方舟最优刷图策略规划。基于开源的掉落统计数据、素材合成规则以及（非常简单的）线性规划算法。

ArkPlanner is a tiny python program for the mobile game Arknight. It helps you make the smartest strategies to obtain any given conbinations of required item based on open-sourced stats data and linear programming algorithms. 

### 安装说明 - Installation
----

***1. 环境配置 - Environment requirements***

需要安装Python 3.6以上版本。Windows系统可通过[此链接](https://www.anaconda.com/distribution/)安装Anaconda。强烈推荐使用Jupyter notebook，详情请百度。

Python >= 3.6 Required. For Windows users, I recommand to install [Anaconda](https://www.anaconda.com/distribution/). Jupyter notebook is highly recommanded. Google it for more details.

***2. 安装 - Installation***

在命令行中执行以下命令，或手动下载解压。Run the following commands in command lines.

```
git clone https://github.com/ycremar/ArkPlanner.git
cd ArkPlanner
python setup.py install
```

*Note: 如何打开命令行？Windows下可从Anaconda或Win+R开启运行对话框，输入cmd并回车。Mac下control+空格并搜索“终端”/“Terminal”。*

### 使用说明 - Usage
---

***1. 在命令行中使用***

* 找到 *required.txt* 以及 *owned.txt* 两个文件，在 *required.txt* 中列出你所需要的材料以及数量，材料和数量间空格隔开，多个材料用回车隔开，在 *owned.txt* 中列出你现有的材料及数目，格式同上。

	例如：
	
	```
	双极纳米片 4
	RMA70-24 5
	```

* 修改完成后保存并关闭，在命令行中运行

	```
	python main.py
	```
你将看到如下输出


	> Optimization terminated successfully, Computed in 0.0446 seconds,
	
	> Estimated total cost 1872 <span style="color:red"><-- 预计的总共体力消耗</span>
	
	> Looting at stages :  <span style="color:red"><-- 你要刷哪些副本以及刷多少次</span>
	
	>
	```
	3-1, 5 times, available items: 代糖 糖 异铁 双酮 酮凝集 酮凝集组
	4-10, 9 times, available items: 源岩 固源岩 装置 全新装置 赤金
	GT-5, 11 times, available items: 扭转醇
	GT-6, 7 times, available items: 研磨石
	1-7, 59 times, available items: 源岩 固源岩 基础作战记录
	2-10, 47 times, available items: 代糖 糖 双酮 酮凝集 RMA70-12 基础作战记录
	S3-1, 12 times, available items: 代糖 糖 异铁碎片 双酮 酮凝集 初级作战记录
	```
	
	> Synthesize items: <span style="color:red"><-- 你要合成哪些材料以及合成多少次</span>
	
	>
	```
	双极纳米片 for 3 times from: 改量装置 (3)  白马醇 (6) 
	RMA70-24 for 4 times from: RMA70-12 (4)  固源岩组 (8)  酮凝集组 (4) 
	白马醇 for 8 times from: 扭转醇 (8)  糖组 (8)  RMA70-12 (8) 
	改量装置 for 3 times from: 全新装置 (3)  固源岩组 (6)  研磨石 (3) 
	酮凝集组 for 2 times from: 酮凝集 (8) 
	糖组 for 7 times from: 糖 (28) 
	固源岩组 for 16 times from: 固源岩 (80) 
	酮凝集 for 4 times from: 双酮 (12) 
	糖 for 4 times from: 代糖 (12) 
	固源岩 for 3 times from: 源岩 (9) 
	```
	
***2. Jupyter Notebook 或在你自己的代码中调用***

参考*demo.ipynb*中的用法。



### 鸣谢 - Acknowledgement
---
数据来源：

- 明日方舟企鹅物流数据统计 [penguin-stats.io](https://penguin-stats.io/)

- 明日方舟工具箱 [ak.graueneko.xyz](https://ak.graueneko.xyz/)