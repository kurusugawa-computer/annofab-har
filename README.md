# annofab-har-sanitizer
Annofabに関するHAR(Http Archive)ファイルから機密情報をマスクします。

# マスク対象
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
    * `url`
        * AWS署名付きURLに含まれるマスク対象のクエリパラメータ（後述参照）

### AWS署名付きURLに含まれるマスク対象のクエリパラメータ
* `X-Amz-Credential`
* `X-Amz-Signature`
* `X-Amz-Security-Token`


    