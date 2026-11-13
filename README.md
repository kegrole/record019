# extract — 配置驱动的商品字段抽取器

只用 Python 标准库。同一个商品在不同模板页面（列表页 / 详情页）上呈现不同，
抽取器按一份 JSON 配置把字段取出来；取不到的字段如实标成 `"missing"`，
绝不拿别的字段顶替，也不填默认值。

## 运行

```bash
python -m extract.cli --config demo/schema.json --pages demo/pages --out out/records.jsonl
# stdout 打印一行摘要，例如：
# pages=6 records=6 missing_fields=2
```

测试：

```bash
cd tests && python -m unittest test_extract -v
# 或在仓库根目录：python -m unittest discover -s tests -v
```

## 配置格式（demo/schema.json）

```json
{
  "fields": {
    "<字段名>": {
      "normalize": "text | spec | price | url | none",
      "rules": [ "<规则>", "..." ]
    }
  }
}
```

每条规则支持的键：

| 键 | 含义 |
| --- | --- |
| `source` | 规则适用的页面来源：`list` / `detail` / `any`（缺省 `any`） |
| `method` | 取值方式：`tag_text` / `attr` / `regex` |
| `tag` / `class` / `id` | 元素定位条件（`tag_text`、`attr` 用，均可选） |
| `attr` | 属性名（`attr` 方式必填） |
| `pattern` | 正则（`regex` 方式必填），有捕获组取第 1 组，否则取整个匹配 |
| `index` | 多个候选值时取下标，缺省 0；下标越界视为该规则未命中 |
| `match` | 候选值过滤正则，不匹配的候选被丢弃（用于剔除懒加载占位图等） |

一个字段可声明多条规则，按顺序尝试，**第一个产出非空候选的规则胜出**；
全部规则都未命中 → 字段记为 `missing`。

## 页面类型识别

- 页面里 class 含 `product-item` / `product-card` / `goods-item` / `item` 的商品块
  ≥ 2 个 → 判为**列表页**，抽取上下文为第一个商品块；
- 否则若存在 id 为 `product-title` / `product-detail` / `detail-main` 或 class 含
  `product-detail` / `product-main` / `detail-main` 的元素 → 判为**详情页**，
  抽取上下文为整个文档；
- 都不满足时按详情页处理。

## source_url 的确定

依次尝试：`<link rel="canonical" href="...">` → `<base href="...">` 拼上文件名 →
本地文件的 `file://` URI。`record_id` 为 `"rec-" + sha1(source_url)[:12]`，
同一批页面重复运行结果逐字节一致。

## 归一化规则

- `text`：NFKC（全角→半角）+ 连续空白折叠为单个空格 + 去首尾空白。
- `spec`：NFKC + 删除所有空白字符（规格串紧凑化）。
- `price`：去掉货币符号、单位与千分位逗号后按十进制解析，统一成**整数分**
  （四舍五入到分）。`"1,299.00 元"` 与 `"1299元"` 都得到 `129900`。
- `url`：用 `urllib.parse.urljoin` 以 `source_url` 为基准补成绝对地址，
  如 `../img/a.png` → `https://example.com/img/a.png`。
- `none`：原样保留。

## missing 语义

- 字段取不到时，输出里该字段的值**正好是字符串 `"missing"`**，不是空串、
  不是 `null`，也不会用其他字段的值顶替；
- 记录的 `missing` 数组列出缺失字段名；
- `status`：全部字段取到为 `"ok"`，有缺失为 `"partial"`。

## 输出格式（JSONL）

每行一个 JSON 对象，字段顺序固定：

```json
{"record_id": "rec-...", "source_url": "https://example.com/pages/detail_a.html",
 "page_type": "detail", "status": "ok", "missing": [],
 "fields": {"name": "...", "price": 129900, "sku": "...", "image_url": "..."}}
```

## demo 夹具的构造规则（验收按此重新生成页面）

6 个页面都是同一商品：`name=无线蓝牙耳机 X1`、`sku=A100`、价格 `1299.00 元`、
图片相对路径 `../img/a.png`（相对 `https://example.com/pages/<文件名>`，
绝对地址为 `https://example.com/img/a.png`）。每页 `<head>` 里带
`<link rel="canonical" href="https://example.com/pages/<文件名>">`。

| 文件 | 类型 | 模板特征 | 价格写法 | 期望 |
| --- | --- | --- | --- | --- |
| `list_a.html` | 列表页 | 3 个 `div.product-item`，目标为第 1 个；sku 在它的 `data-sku` 属性上 | `1,299.00 元` | 4 字段齐全 |
| `list_b.html` | 列表页 | 3 个 `div.item`；sku 在文本 `编号：A100` 里 | `1299元` | 4 字段齐全 |
| `detail_a.html` | 详情页 | `h1#product-title`、`span#price`、文本 `SKU: A100`、`img#main-image` | `1,299.00 元` | 4 字段齐全 |
| `detail_b.html` | 详情页 | `div.product-main`；sku 是第 2 个 `span.spec`（下标 1） | `1299元` | 4 字段齐全 |
| `lazy_image.html` | 详情页 | 图片懒加载：`src="placeholder.gif"`，真图在 `data-src` | `1,299.00 元` | `image_url` = `missing` |
| `no_sku.html` | 详情页 | 页面里没有任何 sku 信息 | `1,299.00 元` | `sku` = `missing` |

期望：6 条记录；4 条完整记录的 `name/price/sku/image_url` 逐字等于
`无线蓝牙耳机 X1` / `129900` / `A100` / `https://example.com/img/a.png`；
缺字段的记录对应字段正好是字符串 `"missing"`。
