# Purpose
The CBA xml-parser was developed in order to extract log-files in xml-format from tasks run in CBA Itembuilder. Currently it supports the extraction of log-files from one variant of the **MicroDYN** approach, which runs within the CBA Itembuilder environment. It parses through each xml-file and calculates relevant scores, needed for both summative and formative assessment.

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

If Python was installed successfully, just download the whole repository from GitHub and open the script with an IDE (e.g., `Spyder`, which comes with a full anaconda installation)

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

     when calling the main function at the end of the script. **Caution**: If you choose this option, please make sure that only "normal" MicroDYN items are included. Thus, delete all items with `instruction`or `eigendynamic`in their name.

5. Run the script :-). 

# Description extracted data

After running the script `xml-parser.py`, you receive three output files, which are stored in `.\out`, summarizing the extracted information. The files are:

*  Actions data file: `[Studyname]_actions.csv`
*  Aggregated file in long format: `[Studyname]_aggregated_long.csv`
* Aggregated file in wide format: `[Studyname]_aggregated_wide.csv` (not fully implemented yet...)

To understand the data a little bit of theoretical background might be useful.

## Background

### CPS process

The CPS process consists of two phases: knowledge acquisition phase and knowledge application phase. In the first phase, participants explore the system and try to infer the relationships between input and output variables, which are presented in the system. For instance, how are variables In1 and In2 related to Out1 and Out2. In the second phase, participants need to use the knowledge from first phase to reach predefined goals in the system. To reach these goals a range is given in the output variables, with both an upper and a lower threshold.

### Rounds

Participants can change values of input variables and can then click on "apply". This process is coded as one round. 

### Strategies

In the both phases, there are many ways to manipulate the system. Some are more efficient than others, and these ways can be "translated" to strategies. We code the following strategies:

| Name                          | Abbreviation | Description                                                  |
| ----------------------------- | ------------ | ------------------------------------------------------------ |
| Vary one thing at a time      | VOTAT        | All variables were kept constant, except one variable        |
| Full Vary one thing at a time | Full VOTAT   | Over all rounds, VOTAT was applied to all input variables separately in the system (considered only in knowledge acquisition phase) |
| Ho-one-thing-at-time          | HOTAT        | Only one variable was kept constant, all other variables were varied |
| No-thing-at-a-time            | NOTAT        | No variable was varied                                       |
| Change all                    | CA           | All variables were varied                                    |

## Actions data file

This file contains each **action** (labeled as `Action`) from each **participant** (labeled as `ID`) in each **item** (labeled as `Item`) in your (MicroDYN) test in separate rows. This means there are *a(actions) x n(participants) x i(items)* rows in this data file.

The following actions will be coded:


* `PressApply`: Button was pressed on apply to apply changes from sliders to the system. This is coded for both phases knowledge acquisition (labeled `exploration`) and knowledge application (labeled as `control`).

  * It is also coded, which values output (i.e., `Endo` variables) variables in the system have *after* clicking on apply.
  * According to the changes made on the input variables (i.e., `Exo` variables), strategies are coded (see table above).
* `AddDepedency` : Action coded when a dependency in knowledge acquisition phase (exploration) was added. Added dependency is indicated in `DeltaDepdendency`.
* `RemoveDependency`: Same as `AddDependency` but coded when a dependency was removed.

Additional variables in this data file are:

* `Date` : date when the test was taken (timestamp is start time of each item)
* `TimerAfterOnset`: Time when each action was performed relative to start time of respective item. 

## Aggregated file in long format

All date are stored in long format with *n(participants) x i(items) x p(phases)* as rows.

The following variables are stored

| Column name               | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `ID`                      | Participants' ID                                             |
| `Item`                    | Item name in German                                          |
| `Date`                    | Start date of each item                                      |
| `Test`                    | Name of test given by researcher                             |
| `Phase`                   | Phase of CPS process, either `exploration` (knowledge acquisition) or `control` (knowledge application) |
| `Rounds`                  | Number of rounds in the respective phase. Max for exploration is 180. Max for control is 4. |
| `ED`                      | Does the system has so-called "eigendynamics"?               |
| `NumDepdendencies`        | How many dependencies does the system have?                  |
| `NumInput`                | How many input variables does the system have?               |
| `NumOutput`               | How many output variables does the system have?              |
| `Time_noInstr`            | Response time for respective phase without time for reading the instructions |
| `Correct`                 | Score whether item was solved correctly (for each phase)     |
| `VOTATfreg` and following | In how many rounds was VOTAT (or another strategy, see following columns) applied? |
| `VOTAT_x_vars` | On how many (distinct) variables was VOTAT applied? |
| `fullVOTAT` | Full VOTAT, see table above |
| `StratSeq` | Strategy sequence in both phases |
| `ActionSeq` | Action sequence in both phases |

## General remarks on data files

* **Missing values**: If you encounter missing values (indicated as empty cells), these are the result of no interaction between participant and system at all in this item (or this phase). This is because in some item versions it is possible to skip a phase. Hence, in this case, a missing would be coded.