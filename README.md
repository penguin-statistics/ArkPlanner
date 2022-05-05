<img src="https://penguin.upyun.galvincdn.com/logos/penguin_stats_logo.png"
     alt="Penguin Statistics - Logo"
     width="96px" />

# Penguin Statistics - ArkPlanner

> :heart: ArkPlanner is not possible without any of the initial founders, [@ycremar](https://github.com/ycremar) and [@SQRPI](https://github.com/SQRPI). They both contributed a whole lot to this project to make ArkPlanner eventually possible.
>
> This repository previously was a fork of the original ycremar/ArkPlanner repository, but later @ycremar decided to transfer the ownership to Penguin Statistics.

[Web App](https://penguin-stats.io/planner) is now available at Penguin Statistics.

> The previous web app have been replaced with the integrated [Planner](https://penguin-stats.io/planner) in Penguin Statistics to further integrate the experience. The previous frontend app is built from [ycremar/ArkPlanner-FrontEnd](https://github.com/ycremar/ArkPlanner-FrontEnd) and is based on the initial [vanilla version](https://ak.inva.land/) implemented by [@invisiblearts](https://github.com/invisiblearts).

明日方舟最优刷图策略规划工具，基于开源的掉落统计数据、素材合成规则以及线性规划实现。由于混合掉落、额外掉落副本的存在且各种材料掉落概率不同，在材料需求较复杂时，要刷哪些副本并不直观，大多情况下需要通过比较复杂的计算得到最优解。同时，了解刷所需材料预计消耗多少体力也会帮助你更好的规划体力。原理：将素材合成也看作一种掉落在约束中加以考虑（目标材料掉落 1，消耗的材料掉落为 -1），其 cost 为 0 或合成所需代币的等价体力消耗。

ArkPlanner is a tiny python tool for the mobile game Arknights. The variety of items dropping at different stages and the complicate synthesize system make it difficult to make the most efficient plan to obtain items. ArkPlanner helps you to make the optimal plan for any given combinations of the required item based on open-sourced stats data and items synthesize rules, and linear programming algorithms.

_Note: the linear programming is based on the items dropping expectations estimated by the existing samples. Due to the randomness, divergence may occur especially when you require a small number of items._

## Use ArkPlanner via HTTP API - 通过 HTTP API 调用 ArkPlanner

[API ReadMe](https://github.com/penguin-statistics/ArkPlanner/blob/master/API.md)

## Use ArkPlanner via Command Line - 通过命令行调用 ArkPlanner

### 安装说明 - Installation

**_1. 环境配置 - Environment requirements_**

需要安装 Python 3.5 以上版本。Web 服务器则需要 3.6 以上。Windows 系统可通过[此链接](https://www.anaconda.com/distribution/)安装 Anaconda。强烈推荐使用 Jupyter notebook，详情请百度。

Python >= 3.5 (3.6 for web server) Required. For Windows users, I recommend installing [Anaconda](https://www.anaconda.com/distribution/). Jupyter notebook is highly recommended. Google it for more details.

**_2. 安装 - Installation_**

在命令行中执行以下命令，或手动下载解压。Run the following commands in command lines.

```
git clone https://github.com/ycremar/ArkPlanner.git
cd ArkPlanner
python setup.py install
```

_Note: 如何打开命令行？Windows 下可从 Anaconda 或 Win+R 开启运行对话框，输入 cmd 并回车。Mac 下 control+空格并搜索“终端”/“Terminal”。_

### 使用说明 - Usage

---

**_1. 在命令行中使用_**

- 找到 _required.txt_ 以及 _owned.txt_ 两个文件，在 _required.txt_ 中列出你所需要的材料以及数量，材料和数量间空格隔开，多个材料用回车隔开，在 _owned.txt_ 中列出你现有的材料及数目，格式同上。

  Find and edit the files _required.txt_ and _owned.txt_. List the items you need and you already have. Seperate item name and quatity by space and two items by return. For example:

  例如：

  ```
  双极纳米片 4
  RMA70-24 5
  ```

- 修改完成后保存并关闭，在命令行中运行

  Then save the files and run the following command in your command line:

  ```
  python main.py
  ```

  你将看到如下输出

  You shall find some outputs like this:

  ```
  Optimization terminated successfully, Computed in 0.0324 seconds,
  Estimated total sanity cost <----（预计消耗的总体力）
  Farm at following stages: <----（以下是你要刷哪些副本以及次数）
  Stage 3-1 (5 times) ===> 双酮(1), 酮凝集组(2)
  Stage 4-10 (9 times) ===> 源岩(2), 固源岩(3), 全新装置(2), 赤金(1)
  Stage 1-7 (59 times) ===> 源岩(7), 固源岩(75), 破损装置(2), 酯原料(4), 代糖(4), 异铁碎片(2), 双酮(3)
  Stage 2-10 (47 times) ===> 代糖(7), 糖(6), 异铁碎片(4), 异铁(4), 双酮(6), 酮凝集(4), RMA70-12(13)
  Stage S3-1 (12 times) ===> 代糖(1), 糖(19), 异铁碎片(1), 异铁(1), 双酮(1), 酮凝集(2)
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

- 由于数据中记录较少的副本掉落偏差较大，因此代码中默认过滤掉统计频次低于 200 的记录，如需修改，可在 _main.py_ 中将第 6 行改为

  My code filters the records by their frequency from Penguin-Stats since records with low frequency may cause bias. To customize your filter, replace line 6 in _main.py_ with

  ```
      mp = MaterialPlanning(filter_freq=n)
  ```

  n 为你想自定义的频次下限，0 则为不过滤。

  where n is the lower bound of acceptable frequence. If n=0, no filter will be applied.

**_2. Jupyter Notebook 或在你自己的代码中调用_**

参考*demo.ipynb*中的用法。

Please refer to _demo.ipynb_.

**_3. 运行 Web 服务器_**
`python server.py` 将在 127.0.0.1 监听 8000 端口，可供调试。

然而，对于生产环境，建议使用`python -m sanic server.app --host=<your_host> --port=<your_port> --workers=<workers_num>`，以获得更好的性能和灵活性。

For debugging, simply run `python server.py`, which spins up a server listening at `http://127.0.0.1:8000`.

For deployment, however, `python -m sanic server.app --host=<your_host> --port=<your_port> --workers=<workers_num>` is recommended for better performance and flexibility.

**_4. 更新数据_**

如果发生官方暗改掉率或材料、地图更新等情况，可直接删除文件夹 data，并重新运行。

If new items or stages are updated, delete the data folder and run the following command as usual.

    ```
    python main.py
    ```

## 鸣谢 - Acknowledgement

数据来源：

- 明日方舟企鹅物流数据统计 [penguin-stats.io](https://penguin-stats.io/)

- 明日方舟工具箱 [ak.graueneko.xyz](https://ak.graueneko.xyz/)
