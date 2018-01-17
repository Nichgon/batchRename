# batchRename
Bridge Batch Rename in Maya

### Features
* Generate new object names by using combination of the following generators
  * **Text**
  * **Current Object Name**
  * **Current Object Type**
  * **Parent Name**
  * **Sequence Number**
  * **Sequence Letter**
  * **String Substitution**
* Change object names by selection order
* Save preset for use later
* Preview new object names
* Export CSV file

### Compatibility
* 2015 - N/A
* 2016 - **OK**
* 2017 - N/A
* 2018 - **OK**

### Usage
1. Download and unzip file. Copy `batchRename.py`, `batchRename.ui`, `Qt.py` (If you already have [Qt.py](https://github.com/mottosso/Qt.py) then you can skip it) to your scripts folder (eg. C:\Users\'YOUR USER NAME'\Documents\maya\2016\scripts) 
1. Start Maya execute the command below in command line or Script Editor.
```python
import batchRename
batchRename.execute()
```
