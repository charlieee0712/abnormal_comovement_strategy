# e6i_vendor —— 第三方实现的固定版本副本（brief §0.1 EDGE 条）

## bidask（Ardia, Guidotti & Kroencke 2024, JFE 161, 103916 的作者实现）
- 来源: https://github.com/eguidotti/bidask （作者仓库；MIT License，原文见 bidask/LICENSE）
- 固定 commit: 1caba55d63ebab6c855536be51c43bdfc48d2dec （2025-10-13 "Fix CRAN"）
- 取得方式: 47 上 raw.githubusercontent 与 https git clone 均因 SSL EOF 失败（api.github.com 与
  git ls-remote 可达），故在本地工作站 `git clone` 该 commit 后逐行审阅，原样复制 `python/bidask/`
  四个文件 + LICENSE；测试数据 `pseudocode/ohlc.csv`、`ohlc-miss.csv` 同 commit 原样复制。
  **未 pip install、未运行任何安装脚本。**
- 审阅结论: edge.py / edge_rolling.py / edge_expanding.py 只依赖 numpy / pandas，无 I/O、无网络、
  无全局副作用；逐行对照论文式 (GMM 两矩加权、tau / po / pc 指示量、去均值收益)。未改一个字。
- 本轮用法: 主实现 = edge_rolling(window=w, min_periods=max(3, ceil(0.7w)))，逐股、复权 OHLC；
  解释性核对 = edge() 在抽样窗口上重算（plan §4.2 第 4 条：缺失数据下两者可不逐位一致，
  不作为错误锚）。signed (sign=True) 与作者默认非负值分别保存。
- 自检: e6i_vendor_check.py 用本地测试数据复现作者 tests/test_edge.py 的已知值
  （0.0101849034905478 / 前 10 行 signed -0.016889917516422 / 缺失版 0.01013284969780197 /
  全平价格 NaN）以及 edge_rolling 与 edge 的窗口一致性。
9aa76dcc8deabe57d3a8de57434279927a4109021876ab0977b73a37a430a042 *bidask/__init__.py
6b74c3ddab92d800b8b47f80bde3d1187120bc68c7c29e22fd2dac33c5e03c85 *bidask/edge.py
b02c4274c53ac4755c047c0c16590d38b26b05d7d8292a8eaf1f6c45a92c3e2c *bidask/edge_expanding.py
306da02bb4388be1aca5417b7ba609535074dcf73dabecb9473e707cffcfecf8 *bidask/edge_rolling.py
9e611dfbf3dd9bed2beb0f7b8865c7a89f888cfc9614683ba0d74a7228660c30 *bidask/LICENSE
6d3067f952fa96314efc1d9b8c9043ff7e8945a9be22e68585604527a11fcd89 *bidask_testdata/ohlc-miss.csv
d6e598e0cba5617462d616b7ecbb99c07eac2a56188f2312accfbdc64e9e57f4 *bidask_testdata/ohlc.csv
(以上 sha256 追加于复制完成时)
