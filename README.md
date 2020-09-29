# Purpose
The CBA xml-parser was developed in order to extract log-files in xml-format from tasks run in CBA Itembuilder. Currently it support the extraction of log-files from one variant of the **MicroDYN** approach, which runs within the CBA Itembuilder environment. It parses through each xml-file and calculates relevant scores, needed for both summative and formative assessment.

# Installation

The main script was programmed in `Python3.7`. Hence, Python 3.x must be installed. Additionally, the following packages (including dependencies) need to be installed:

* `lxml`
* `pandas`
* `numpy`
* `datetime`
* `glob`
* `os`
* `sys`

The easiest way to install both Python 3.x and all dependencies is to use [anaconda](https://www.anaconda.com/products/individual). Packages can then be installed with `anaconda prompt`. For instance, open anaconda prompt and type

```python
conda install -c anaconda lxml
```

If Python was installed successfully, just download the whole repository from github and open the script with an IDE (e.g., `Spyder`)

# Run

Please stick to the following guide in order to perform the log-file extraction:

1. Open the python script `xml-paser.py` in an IDE

2. Put all the xml-files you want to extract in the `.\data`folder. If there is not folder called `data`in your repository, please create one.

3. Check, whether you want to include *all* cases. By default, the script will include all cases located in `data`-folder. 
   - If you want to include all cases, proceed with 4.
   
   - If you want to included only a subset of cases, please create a file named `IDs.csv` in `.\info`. Include all cases, which should be processed. See also instructions on that in `read_me.md` in `.\info`. Then, set 
   
     ```python
     subset_cases=True
     ```
   
     when calling the main function at the end of the script.

4. Check, which items you want to include. Per default only items are included, which are defined in `tasks.csv`in `.\info`. If you use the script for the first time, no such file is stored there, thus no xml-file will be processed. See the `read_me.md` in `.\info` on how to create this file. 

   - If you have defined, which item should be processed, please proceed with 5.

   - If you want to have all files processed, you can set

     ```python
     subset_tasks=False
     ```

     when calling the main function at the end of the script. Caution: If you choose this option, please make sure that only "normal" MicroDYN items are included. Thus, delete all items with `instruction`or `eigendynamic`in their name.

5. Run the script :-). 

# Extracted data

tbd...

