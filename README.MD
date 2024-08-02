# pyads を使った構造体変数のNotificationアクセス

Pythonで、TwinCAT PLC上の変数の変化に基づいてデータを収集するには、[pyads](https://pyads.readthedocs.io/)のNotificationを使うのが便利です。

これを使うと、単一の変数を指定するだけで、PLCのサイクル毎に値の変化が生じた場合のみADSによるメッセージ通知が行われます。

Python側では、コールバック関数を用意しておくことで、通知を受けた際に関数実行が可能です。

また、pyadsではタプルにて定義した構造体データにより、構造体データの値変化による通知も可能です。

本サンプルコードは

## 事前準備

### TwinCAT側

以下の通りWindows側と共有したいデータの構造体を作成します。先頭には`{attribute 'pack_mode' := '1'}`を付加する事で、1byte アライメントでメモリ配置することを宣言します。

``` 
{attribute 'pack_mode' := '1'}
TYPE ST_sample :
STRUCT
    title :STRING;
    name: STRING;
    age: UINT;
    sex: UINT;
    mail_address : STRING;
    event_date : ULINT;
    description : STRING;
END_STRUCT
END_TYPE
```

PLCプログラム上では、この構造体型をインスタンス化した変数に対して、任意のタイミングで値をセットしてください。

### Python側

#### pyads のインストール

``` bash
$ pip install pyads
```

#### 構造体変数モデルの定義

model.pyを編集します。先ほど定義したTwinCATの構造体のデータモデルを示すタプル変数を定義します。

``` python
structure_def = (
        ("title", pyads.PLCTYPE_STRING, 1),
        ("name", pyads.PLCTYPE_STRING, 1),
        ("age", pyads.PLCTYPE_UINT, 1),
        ("sex", pyads.PLCTYPE_UINT, 1),
        ("mail_address", pyads.PLCTYPE_STRING, 1),
        ("event_datetime", pyads.PLCTYPE_ULINT, 1),
        ("description", pyads.PLCTYPE_STRING, 1)
)
```

`EventReporter`クラスの`__post_init__` 最下行に、TwinCATの構造体変数名、データモデルのタプル変数、および、そのイベントハンドラを定義します。

``` python
    def __post_init__(self):
        self.plc: AdsCommunication = AdsCommunication(
            ams_net_id=self.ams_net_id,
            ams_port=self.ads_port
        )
        # 監視したい変数とデータ構造を定義したtupleを登録
        self.plc.reg_notification('MAIN.ads_watch_variable', structure_def,  self.job_event_handler)
```


#### ターゲットIPC設定

main.pyを開いて、ターゲットIPCのルータのAMS Net IDを設定してください。デフォルトで、ローカルIPCを示しています。

``` python
if __name__ == '__main__':
    reporter = EventReporter(ams_net_id='127.0.0.1.1.1') # ターゲットのNetIDをセット
    asyncio.run(event_listener(reporter))
```

## 実行方法

1. TwinCAT側をRUNモードでPLCスタートしてください。
2. Pythonを次の通り実行します。

    ``` bash
    $ python ./main.py
    ```

3. ターミナル上に構造体データの変化があるたびにそのデータが出力されます。

### 解説

model.pyの `EventReporter` クラスで定義したイベントハンドラでは、 asyncio.Queue を使って非同期FIFOキューでデータをキューインしています。

main.pyの`event_listener`タスクで、キューを順次取り出して、print() で標準出力しているだけです。このデータはOrderdTuple型になっていますので、model.pyの`structure_def`で定義した最初の要素キーでアクセスできます。例えば、TwinCATのPLCで`F_GetSystemTime()`を使って書き込んだFILETIMEの値は、`data['event_datetime']`でアクセスできます。

このFILETIMEの値は、前回収集したデータとの差分を計算して出力しています。これでPLC側のサイクルタイムごとのデータが全て収集できているかチェックすることができます。

FILETIMEの精度は100nsですので、250usのサイクルタイムの場合、差分時間としては2500となります。

``` python
async def event_listener(reporter: EventReporter):
    last_time = 0
    while True:
        data = await reporter.queue.get()
        print(data)
        time_diff = data['event_datetime'] - last_time
        print(f"Diff : {time_diff} (x100ns)")
        last_time = data['event_datetime']
        await asyncio.sleep(0.001)
```
