# PTA (Packet Traffic Arbitration) python scripts

PTA is used to manage radio coexistence of Wi-Fi with other standards

Common use cases are:
* Wi-Fi + Bluetooth
* Wi-Fi + Zigbee

(Watch https://www.youtube.com/watch?v=BiEe_EbhpGg to discover the benefits of PTA and
visit https://www.silabs.com/products/wireless/learning-center/wi-fi-coexistence for more details)

## Usage

To manage PTA, sending configuration data is required to
* Provide the PTA settings to the WFX firmware
* Control the PTA priority
* Turn PTA ON/OFF

## Source repository
https://github.com/SiliconLabs/wfx-common-tools

## Python version
The scripts have been written for and tested for Python3 

## Installation
These scripts are used to format PTA bytes according to the user's preferences and send them to the WFX firmware.

They can be used either directly on the target or on a remote tester, via the **WXF connection layer**

### Prerequisites
First install the  **WXF connection layer**
The connection layer is the same as the one used for WFX RF testing, allowing connection in the following modes:
* Local
* SSH
* UART

The connection layer is available in 
https://github.com/SiliconLabs/wfx-common-tools/tree/master/connection
(a subfolder of `wfx-common-tools`, so from the PTA scripts perspective they are under `../connection`)

Refer to 
https://github.com/SiliconLabs/wfx-common-tools/blob/master/connection/README.md
 for details on the connection layer and its installation.

----------------

### PTA scripts installation
Once you have installed the **WXF connection layer** you will also have installed the Python scripts for PTA, since
these are in the same repository, in the `pta` folder.
```
cd siliconlabs/wfx-common-tools/pta
```

----------------

### PTA help
Help can be obtained using the `pta_help()` function, and will also be displayed in case a function parameter
 is missing or invalid.
```
python3
>>> from wfx_pta import *
>>> dut = WfxPtaTarget('local')
>>> dut.pta_help()
```
#### PTA help content
```
usage:  <settings/priority/state> [options]...

        Prepare and send PTA parameters depending on the selected pta_cmd


positional arguments:
  {settings,priority,state}
                        pta_cmd <settings/priority/state>

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

settings options:
  --Config {3W_NOT_COMBINED_BLE,3W_COMBINED_BLE,3W_NOT_COMBINED_ZIGBEE,3W_COMBINED_ZIGBEE}
                        Preset configurations for common use cases (presets
                        required non-default 'settings' options, these can
                        then be overwritten using options listed below)
  --PtaMode {1W_WLAN_MASTER,1W_COEX_MASTER,2W,3W,4W}
                        PTA mode selection (default 0)
  --RequestSignalActiveLevel {LOW,HIGH}
                        Active level on REQUEST signal, provided by Coex to
                        request the RF (default 1)
  --PrioritySignalActiveLevel {LOW,HIGH}
                        Active level on PRIORITY signal, provided by Coex to
                        set the priority of the request (default 1)
  --FreqSignalActiveLevel {LOW,HIGH}
                        Active level on FREQ signal, provided by Coex in
                        4-wire mode when Coex and Wlan share the same band
                        (default 1)
  --GrantSignalActiveLevel {LOW,HIGH}
                        Active level on GRANT signal, generated by PTA to
                        grant the RF to Coex (default 0)
  --CoexType {GENERIC,BLE}
                        Coex type (default 0)
  --DefaultGrantState {NO_GRANT,GRANT}
                        State of the GRANT signal before arbitration at
                        GrantValidTime (default 1)
  --SimultaneousRxAccesses {0,1}
                        (uint8), Boolean to allow both Coex and Wlan to
                        receive concurrently, also named combined mode
                        (default 0)
  --PrioritySamplingTime PRIORITYSAMPLINGTIME
                        (uint8), Time in microseconds from the Coex request to
                        the sampling of the priority on PRIORITY signal (1 to
                        31), (default 9)
  --TxRxSamplingTime TXRXSAMPLINGTIME
                        (uint8), Time in microseconds from the Coex request to
                        the sampling of the directionality on PRIORITY signal
                        (PrioritySamplingTime to 63) (default 50)
  --FreqSamplingTime FREQSAMPLINGTIME
                        (uint8), Time in microseconds from the Coex request to
                        the sampling of the freq-match information on FREQ
                        signal (1 to 127) (default 70)
  --GrantValidTime GRANTVALIDTIME
                        (uint8), Time in microseconds from Coex request to the
                        GRANT signal assertion (max(TxRxSamplingTime,
                        FreqSamplingTime), to 0xFF), (default 72)
  --FemControlTime FEMCONTROLTIME
                        (uint8), Time in microseconds from Coex request to the
                        control of FEM (GrantValidTime to 0xFF), (default 140)
  --FirstSlotTime FIRSTSLOTTIME
                        (uint8), Time in microseconds from the Coex request to
                        the beginning of reception or transmission
                        (GrantValidTime to 0xFF), (default 150)
  --PeriodicTxRxSamplingTime PERIODICTXRXSAMPLINGTIME
                        (uint16), Period in microseconds from FirstSlotTime of
                        following samplings of the directionality on PRIORITY
                        signal (1 to 1023), (default 1)
  --CoexQuota COEXQUOTA
                        (uint16), Duration in microseconds for which RF is
                        granted to Coex before it is moved to Wlan (default 0)
  --WlanQuota WLANQUOTA
                        (uint16), Duration in microseconds for which RF is
                        granted to Wlan before it is moved to Coex (default 0)

priority options:
  --PriorityMode {COEX_MAXIMIZED,COEX_HIGH,BALANCED,WLAN_HIGH,WLAN_MAXIMIZED}
                        COEX_MAXIMIZED = 0x0562 : Maximizes priority to COEX,
                        WLAN connection is not ensured. COEX_HIGH = 0x0462 :
                        High priority to COEX, targets low-latency to COEX.
                        BALANCED = 0x1461 : Balanced PTA arbitration, WLAN
                        acknowledge receptions are protected. WLAN_HIGH =
                        0x1851 : High priority to WLAN, protects WLAN
                        transmissions. WLAN_MAXIMIZED = 0x1A51 : Maximizes
                        priority to WLAN

state options:
  --State {ON,OFF}      PTA state on/off

        Examples:
        python wfx_pta.py settings --Config 3W_COMBINED_BLE
        python wfx_pta.py settings --Config 3W_NOT_COMBINED_BLE --FirstSlotTime 123
        python wfx_pta.py settings --Config 3W_NOT_COMBINED_BLE --FirstSlotTime 123 --PrioritySamplingTime 12
        python wfx_pta.py priority --PriorityMode BALANCED
        python wfx_pta.py state --State ON
        python wfx_pta.py state --State OFF

```
## PTA API
### settings(options)

PTA settings are filled based on the `options` string as a structure with the following parameters

| parameter                | Possible values                      | default       |
|--------------------------|--------------------------------------|---------------|
| PtaMode                  |1W_WLAN_MASTER,1W_COEX_MASTER,2W,3W,4W| 1W_WLAN_MASTER|
| RequestSignalActiveLevel |LOW,HIGH                              | LOW           |
| PrioritySignalActiveLevel|LOW,HIGH                              | HIGH          |
| FreqSignalActiveLevel    |LOW,HIGH                              | HIGH          |
| GrantSignalActiveLevel   |LOW,HIGH                              | LOW           |
| CoexType                 |GENERIC,BLE                           | GENERIC       |
| DefaultGrantState        |NO_GRANT,GRANT                        | GRANT         |
| SimultaneousRxAccesses   |FALSE,TRUE                            | FALSE         |
| PrioritySamplingTime     |TBD                                   |   9           |
| TxRxSamplingTime         |TBD                                   |  50           |
| FreqSamplingTime         |1 to 127                              |  70           |
| GrantValidTime           |TBD                                   |  72           |
| FemControlTime           |TBD                                   | 140           |
| FirstSlotTime            |TBD                                   | 150           |
| PeriodicTxRxSamplingTime |1 to 1023                             |   1           |
| CoexQuota                |TBD                                   |   0           |
| WlanQuota                |TBD                                   |   0           |

* Each parameter can be set using the `--<parameter>=<value>` syntax
* No specific order for parameters provided in the `options` string
* All parameters are optional

#### PTA setting pre-filled configurations

Typical pre-filled configurations (matching common use cases) can be selected using an additional `Config` parameter.
There are 4 such configurations:

| '--Config=<pre_filled_config>'| pre-filled options         |
|-------------------------------|----------------------------|
| 3W_COMBINED_ZIGBEE            |PtaMode=3W <br>CoexType=GENERIC <br>SimultaneousRxAccesses=TRUE  <br>PrioritySamplingTime=10 <br>TxRxSamplingTime=30 <br>GrantValidTime=40 <br>FemControlTime=40 <br>FirstSlotTime=40|
| 3W_NOT_COMBINED_ZIGBEE        |PtaMode=3W <br>CoexType=GENERIC <br>SimultaneousRxAccesses=FALSE <br>PrioritySamplingTime=10 <br>GrantValidTime=20 <br>FemControlTime=20
| 3W_COMBINED_BLE               |PtaMode=3W <br>CoexType=BLE     <br>SimultaneousRxAccesses=TRUE  <br>PrioritySamplingTime=10
| 3W_NOT_COMBINED_BLE           |PtaMode=3W <br>CoexType=BLE     <br>SimultaneousRxAccesses=FALSE <br>PrioritySamplingTime=10

#### PTA settings defaults vs pre-filled configurations vs user options
**PTA settings** are applied in the following order:

* All defaults
* Pre-filled configuration options values
* User options

NB: Using the PTA data filling tracing (described below) can be a good way to become familiar with this process

## Use case examples
```
python3
>>> from wfx_pta import *
```
### Connection
Select one of (with your own parameters for the SSH or UART cases)
```
>>> dut = WfxPtaTarget('Pi203', host='pi203', user='pi', port=22, password='default_password')
>>> dut = WfxPtaTarget('Serial', port='COM8')
>>> dut = WfxPtaTarget('Local')
```

### PTA settings 
**All defaults + PtaMode & TxRxSamplingTime**
```
>>> dut.settings('--PtaMode=3W TxRxSamplingTime=30')
```
**Pre-filled configuration 'as is'**
```
>>> dut.settings('--Config 3W_NOT_COMBINED_BLE')
```
**Pre-filled configuration + user-selected values**
```
>>> dut.settings('--Config 3W_NOT_COMBINED_BLE --FirstSlotTime 123')
```
### PTA priority
```
>>> dut.priority('--PriorityMode BALANCED')
```
### PAT state
```
>>> dut.state('--State OFF')
```

## Tracing
### Tracing PTA data filling
Adding `mode='verbose'` to a PTA function call will enable tracing of the PTA data filling process

**without traces**
```
>>> dut.settings('--Config 3W_NOT_COMBINED_BLE')
'HI_STATUS_SUCCESS'
```
**with traces**
```
>>> dut.settings('--Config 3W_NOT_COMBINED_BLE --FemControlTime 135', mode='verbose')
['settings', '--Config', '3W_NOT_COMBINED_BLE', '--FemControlTime', '135']
Configuring for 3W_NOT_COMBINED_BLE
CoexType                              0 =>        1 (x1)
PtaMode                               0 =>        3 (x3)
PrioritySamplingTime                  9 =>       10 (xa)
FemControlTime                      140 ->      135 (x135)
PtaMode                        3          \x03
RequestSignalActiveLevel       1          \x01
PrioritySignalActiveLevel      1          \x01
FreqSignalActiveLevel          1          \x01
GrantSignalActiveLevel         0          \x00
CoexType                       1          \x01
DefaultGrantState              1          \x01
SimultaneousRxAccesses         0          \x00
PrioritySamplingTime           10         \x0a
TxRxSamplingTime               50         \x32
FreqSamplingTime               70         \x46
GrantValidTime                 72         \x48
FemControlTime                 135        \x87
FirstSlotTime                  150        \x96
PeriodicTxRxSamplingTime       1          \x01\x00
CoexQuota                      0          \x00\x00
WlanQuota                      0          \x00\x00
'HI_STATUS_SUCCESS'
>>>
```
NB: Above we can see
 * Indicated with `=>`: the changes done on the defaults when applying '3W_NOT_COMBINED_BLE'
 * Indicated with `->`: the changes done on the current settings when applying '--FemControlTime 135'
 * When there is a change from the default: the default values on the left side, the final value on the right
 
### Tracing PTA data transmission
It is also possible to track the connection layer communication with the DUT, using
```
>>> dut.link.trace = True
```
**without connection traces**
```
>>> dut.settings('--Config 3W_NOT_COMBINED_BLE')
'HI_STATUS_SUCCESS'
```
**with connection traces**
```
>>> dut.settings('--Config 3W_NOT_COMBINED_BLE')
pi       D>>|  wfx_exec wfx_hif_send_msg "\x18\x00\x2b\x00\x03\x01\x01\x01\x00\x01\x01\x00\x0a\x32\x46\x48\x8c\x96\x01\x00\x00\x00\x00\x00"
<<D       pi|  0
'HI_STATUS_SUCCESS'
```

# Self test
A specific `selftest` function has been added to allow testing proper installation of the tools.
`selftest` calls the 3 PTA functions will valid example values to check that PAT data formatting and transmission
 is working as expected. To achieve this, internal tracing features are used.

## Running the self test
```
python3
>>> from wfx_pta import *
```
Select one of (with your own parameters for the SSH or UART cases)
```
>>> dut = WfxPtaTarget('Pi203', host='pi203', user='pi', port=22, password='default_password')
>>> dut = WfxPtaTarget('Serial', port='COM8')
>>> dut = WfxPtaTarget('Local')
```
Call selftest()
```
>>> dut.selftest()
```
## Expected result of dut.selftest():
```
['settings', '--Config', '3W_NOT_COMBINED_BLE']
Configuring for 3W_NOT_COMBINED_BLE
PtaMode                               0 =>        3 (x3)
CoexType                              0 =>        1 (x1)
PrioritySamplingTime                  9 =>       10 (xa)
PtaMode                        3          \x03
RequestSignalActiveLevel       1          \x01
PrioritySignalActiveLevel      1          \x01
FreqSignalActiveLevel          1          \x01
GrantSignalActiveLevel         0          \x00
CoexType                       1          \x01
DefaultGrantState              1          \x01
SimultaneousRxAccesses         0          \x00
PrioritySamplingTime           10         \x0a
TxRxSamplingTime               50         \x32
FreqSamplingTime               70         \x46
GrantValidTime                 72         \x48
FemControlTime                 140        \x8c
FirstSlotTime                  150        \x96
PeriodicTxRxSamplingTime       1          \x01\x00
CoexQuota                      0          \x00\x00
WlanQuota                      0          \x00\x00
pi       D>>|  set -ex; wfx_exec wfx_hif_send_msg "\x18\x00\x2b\x00\x03\x01\x01\x01\x00\x01\x01\x00\x0a\x32\x46\x48\x8c\x96\x01\x00\x00\x00\x00\x00"
<<D       pi|  0
settings result: HI_STATUS_SUCCESS
['priority', '--PriorityMode', 'BALANCED']
PriorityMode                   5217       \x61\x14\x00\x00
pi       D>>|  set -ex; wfx_exec wfx_hif_send_msg "\x08\x00\x2c\x00\x61\x14\x00\x00"
<<D       pi|  0
priority result: HI_STATUS_SUCCESS
['state', '--State', 'OFF']
State                          0          \x00\x00\x00\x00
pi       D>>|  set -ex; wfx_exec wfx_hif_send_msg "\x08\x00\x2d\x00\x00\x00\x00\x00"
+ wfx_exec wfx_hif_send_msg \x08\x00\x2d\x00\x00\x00\x00\x00
<<D       pi|  0
state    result: HI_STATUS_SUCCESS
```

