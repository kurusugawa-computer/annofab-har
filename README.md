# annofab-har
AnnofabのHAR(Http Archive)ファイルを扱うCLIです。

[![PyPI version](https://badge.fury.io/py/annofab-har.svg)](https://badge.fury.io/py/annofab-har)
[![Python Versions](https://img.shields.io/pypi/pyversions/annofab-har.svg)](https://pypi.org/project/annofab-har/)

# Requirements
* Python 3.10 以上


# `annofab_har sanitize`
AnnofabのHARファイルから機密情報をマスクします。

## マスク対象
HARファイルに含まれる以下の情報をマスクします。

* `response`
    * `content.text`（レスポンスボディ）
    * `cookies`
* `request`
    * `postData.text`（リクエストボディ）
    * `cookies`
    * `headers`
        * `name`が`Authorization`である`value`
    * `url`
        * AWS署名付きURLに含まれるマスク対象のクエリパラメータ（後述参照）
* `_initiator`
    * `url`に含まれるAWS署名付きURLに含まれるマスク対象のクエリパラメータ（後述参照）。再帰的に処理する。


### AWS署名付きURLに含まれるマスク対象のクエリパラメータ
* `X-Amz-Credential`
* `X-Amz-Signature`
* `X-Amz-Security-Token`



## Usage

```
$ uv run annofab_har sanitize input.har --output output.har
```


# `annofab_har to_timing_csv`

HARファイルからtimingに関する情報をCSVとして出力します。

## CSVの列名

 * startedDateTime
 * request.method
 * request.url
 * response.status
 * response.content.size
 * response.content.mimeType
 * response.headers.contentLength
 * time
 * timings.blocked
 * timings.dns
 * timings.connect
 * timings.send
 * timings.wait
 * timings.receive
 * timings.ssl


## Usage

```
$ uv run annofab_har to_timing_csv input.har --output output.csv
```
