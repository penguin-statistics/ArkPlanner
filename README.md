# ArkPlanner

明日方舟最优刷图策略规划工具，基于开源的掉落统计数据、素材合成规则以及（原理很简单的）线性规划算法。由于混合掉落、额外掉落副本的存在且各种材料掉落概率不同，在材料需求较复杂时，要刷哪些副本并不直观，大多情况下需要通过比较复杂的计算得到最优解。同时，了解刷所需材料预计消耗多少体力也会帮助你更好的规划体力。原理：将素材合成也看作一种掉落在约束中加以考虑（目标材料掉落1，消耗的材料掉落为-1），其cost为0或合成所需代币的等价体力消耗。

ArkPlanner is a tiny python tool for the mobile game Arknight. It helps you make the smartest strategies for any given conbinations of required item based on open-sourced stats data, items synthesise rules. It consider both items dropping rate and synthesise rules as coefficients of restrictions and minimize the total cost using Linear Programming.

### 安装说明 - Installation
----

***1. 环境配置 - Environment requirements***

需要安装Python 3.5以上版本。Windows系统可通过[此链接](https://www.anaconda.com/distribution/)安装Anaconda。强烈推荐使用Jupyter notebook，详情请百度。

Python >= 3.5 Required. For Windows users, I recommand to install [Anaconda](https://www.anaconda.com/distribution/). Jupyter notebook is highly recommanded. Google it for more details.

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
	
	```
	Optimization terminated successfully, Computed in 0.0324 seconds,
	Estimated total cost 1598 <----（预计消耗的总体力）
	Loot at following stages: <----（以下是你要刷哪些副本以及次数）
	Stage 3-1 (5 times) ===> 双酮(1), 酮凝集组(2)
	Stage 4-10 (9 times) ===> 源岩(2), 固源岩(3), 全新装置(2), 赤金(1)
	Stage 1-7 (59 times) ===> 源岩(7), 固源岩(75), 破损装置(2), 酯原料(4), 代糖(4), 异铁碎片(2), 双酮(3), 赤金(5), 基础作战记录(65)
	Stage 2-10 (47 times) ===> 代糖(7), 糖(6), 异铁碎片(4), 异铁(4), 双酮(6), 酮凝集(4), RMA70-12(13), 基础作战记录(5), 初级作战记录(4)
	Stage S3-1 (12 times) ===> 代糖(1), 糖(19), 异铁碎片(1), 异铁(1), 双酮(1), 酮凝集(2), 初级作战记录(2)
	Synthesize following items: <----（以下是你要合成哪些材料以及次数）
	双极纳米片(4) <=== 改量装置(4) , 白马醇(8) 
	RMA70-24(5) <=== RMA70-12(5) , 固源岩组(10) , 酮凝集组(5) 
	白马醇(8) <=== 扭转醇(8) , 糖组(8) , RMA70-12(8) 
	改量装置(3) <=== 全新装置(3) , 固源岩组(6) , 研磨石(3) 
	酮凝集组(2) <=== 酮凝集(8) 
	糖组(7) <=== 糖(28) 
	固源岩组(16) <=== 固源岩(80) 
	酮凝集(4) <=== 双酮(12) 
	糖(4) <=== 代糖(12) 
	固源岩(3) <=== 源岩(9)
	```
	
* 由于数据中记录较少的副本掉落偏差较大，因此代码中默认过滤掉统计频次低于20的记录，如需修改，可在 *main.py* 中将第6行改为

	```
	    mp = MaterialPlanning(filter_freq=n)
	```
	
	n为你想自定义的频次下限，0则为不过滤。

	
***2. Jupyter Notebook 或在你自己的代码中调用***

参考*demo.ipynb*中的用法。


***3. 更新数据***

如果发生官方暗改掉率或更新新的材料等情况，可直接删除文件夹data，并重新运行
	```
	python main.py
	```



### 鸣谢 - Acknowledgement
---
数据来源：

- 明日方舟企鹅物流数据统计 [penguin-stats.io](https://penguin-stats.io/)

- 明日方舟工具箱 [ak.graueneko.xyz](https://ak.graueneko.xyz/)
