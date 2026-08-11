POLIS Vector 3D Demo

场景：Chicago selected New ERA Trail corridor
场地几何：OpenStreetMap way 624189839 和研究使用的 40 m 分析包络

启动：
1. 解压整个 ZIP，不要单独移动其中某个文件。
2. 双击 Start_POLIS_Demo.command。
3. 浏览器会通过本机 localhost 打开 Demo。
4. 完成后可双击 Stop_POLIS_Demo.command 关闭本机服务。

如果双击时 macOS 提示"无法打开"或"来自身份不明的开发者"：
- 方法一：右键点击 Start_POLIS_Demo.command → 选"打开" → 在弹窗中再点"打开"。只需这样做一次，之后可以直接双击。
- 方法二：打开"终端"，输入 xattr -dr com.apple.quarantine ，后面拖入整个解压出来的文件夹，回车，然后再双击启动器。
- 如果提示需要安装"命令行开发者工具"，点"安装"（启动器依赖系统自带的 python3）。

录制：
1. 点击页面右上角 Record demo。
2. 倒计时结束后，系统自动执行 60 秒、10 镜头流程。
3. 使用 QuickTime 或 OBS 进行屏幕录制；按 Esc 可取消自动流程。

技术说明：
- 这是多文件版本，不要直接双击 index.html（file:// 下浏览器会拦截模块脚本）。
- 需要网络连接以读取 CARTO/OSM 矢量瓦片、字体和图标。
- 建筑使用 CARTO building 图层的 render_height 和 render_min_height 挤出。
- 缺失高度使用 6 m 演示回退值，不代表实测建筑高度。
- 底图基于 CARTO Dark Matter，本包内置的样式对地面配色做了轻微调亮处理。
- 界面记录和实时指标为工作流演示数据，不是已完成的实验或居民研究结果。
