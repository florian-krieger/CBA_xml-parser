from lxml import etree
import pandas as pd
import datetime
import numpy as np
import glob
import os
import sys


class XmlParser:

    def __init__(self, inp="data", out="out", verbose=True, subset_cases=False, subset_tasks=False):
        """
        @:param inp: specified input path of xml-files
        @:param out: specified out path of data frames
        @:param verbose: specify whether action data should be stored

        """

        self.relevant_data_points = []
        self.subset_tasks = subset_tasks
        self.subset_cases = subset_cases
        self.verbose = verbose
        self.out = out
        self.input = inp
        self.test_description = None

        # STEP 0a -> df for action stream
        self.actionDfColumns = ["ID", "Item", "Date", "Test",
                                "TimeAfterOnset", "Phase", "Round",
                                "Action", "DeltaDependency"]

        self.df_actions = pd.DataFrame(columns=self.actionDfColumns)

        # STEP 0b -> df for aggregated data
        self.dfLongColumns = ["ID", "Item", "Date", "Test",
                              "Phase", "Rounds",
                              "ED", "NumDependencies", "NumInput", "NumOutput",
                              "Time_Instr", "Time_NoInstr",
                              "Correct",
                              "VOTATfreq", "HOTATfreq", "NOTATfreq", "CAfreq",
                              "StratSeq", "ActionSeq"]

        self.df_long = pd.DataFrame(columns=self.dfLongColumns)

        # STEP 1a -> get all files in path
        this_path = os.path.join(self.input, "*_scoring.xml")
        self.allFiles = glob.glob(this_path)

        # STEP 1b -> if subset of cases/tasks for analyses is desired, only include them
        if self.subset_cases or self.subset_tasks:
            self.include_these_files()

        # STEP 2 -> parse all files
        self.parse_all_files()

        # STEP 3 -> save files
        self.save_data_frames()

    # -- helper functions for steps 1 to 3 -- #

    # Parse all files
    def parse_all_files(self):
        """
        Loops through all files defined in self.allFiles in __init__.
        Calls the function self.parse_this_file for each file in the list
        """

        try:
            for self.thisFile in self.allFiles:
                self.parse_this_file()
        except:

            print("""
            Based on your definitions in both ID.csv and/or tasks.csv no datapoints could be selected.
            Please redefine your specifications in these files or set "subset_clases" and/or "subset_tasks" to "False".
            """)

            print("# finished at", datetime.datetime.now().time())
            sys.exit(1)

    # save data frame
    def save_data_frames(self):
        """
        Saves all data frames and also call function long_to_wide to convert long df in wide df.
        """
        # check directory and create if not existing
        if not os.path.exists(self.out):
            os.makedirs(self.out)

        # convert long to wide
        self.long_to_wide()

        # save all data frames
        self.df_long.to_csv(self.out + os.sep + self.test_description + "_aggregated_long.csv", index=False)
        self.df_wide.to_csv(self.out + os.sep + self.test_description + "_aggregated_wide.csv", index=False)

        if self.verbose:
            self.df_actions.to_csv(self.out + os.sep + self.test_description + "_actions.csv", index=False)

    # convert dfLong to dfWide
    def long_to_wide(self):

        # get defined values
        values = self.df_long.columns.tolist()
        idx = "ID"
        values.remove(idx)
        values.remove("Date")

        # convert to wide df
        self.df_wide = self.df_long.pivot_table(index=idx, columns=['Item', 'Phase'],
                                                values=values)

        # rename columns with format 'item_value_phase'
        self.df_wide.columns = [item + "_" + value + "_" + phase for (value, item, phase) in
                                list(self.df_wide.columns)]
        self.df_wide["ID"] = self.df_wide.index

    # Select relevant IDs
    def include_these_files(self):
        """
        Loads a *.csv file in which all IDs (cases) are listed (one row = one case) and only parses xml-Files
        from these cases.
        """

        # get infos
        self.df_cases = pd.read_csv("info/IDs.csv")
        self.df_tasks = pd.read_csv("info/tasks.csv")
        cases = list(self.df_cases["ID"].values)
        cases = [str(i) for i in cases]
        tasks = list(self.df_tasks["tasks"].values)

        # convert file names to pandas data frames preparing filter process
        s = pd.Series(self.allFiles)
        df_all_files = s.str.split(pat="_", expand=True)
        df_all_files.replace(r"data\\", "", regex=True, inplace=True)
        df_all_files_columns = [
            "ID", "IB_Test", "Test", "Num_Item",
            "Item_Name_GER", "IB_Version", "Item_Name_EN",
            "Day", "Month", "Year", "Hour",
            "Minute", "Second", "dtype"
        ]

        # rename columns
        df_all_files.columns = df_all_files_columns

        # apply filter
        if self.subset_cases and not self.subset_tasks:
            df_select_cases = df_all_files[df_all_files["ID"].isin(cases)]
        elif self.subset_tasks and not self.subset_cases:
            df_select_cases = df_all_files[df_all_files["Item_Name_EN"].isin(tasks)]
        elif self.subset_cases and self.subset_tasks:
            df_select_cases = df_all_files[(df_all_files["ID"].isin(cases)) &
                                           (df_all_files["Item_Name_EN"].isin(tasks))]

        # convert filtered / selected dataframe to file list
        x = df_select_cases.to_string(header=False, index=False, index_names=False).split("\n")
        self.allFiles = ['_'.join(element.split()) for element in x]
        self.allFiles = [os.path.join(self.input, element) for element in self.allFiles]

    # -- MAIN FUNCTION -- #

    def parse_this_file(self):
        """
        Parses one xml-file. File name is defined in __init__ with thisFile.
        Checks each actions and returns dataframes for both actions and aggregated data
        """

        # helper functions
        def convert_time(time_stamp):
            time_stamp = time_stamp.replace("T", " ")
            time_stamp = time_stamp[:-5]
            time_stamp = datetime.datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S.%f")
            return time_stamp

        # -------------------------------------------------------------------
        # load and parse xml-file(s)
        # -------------------------------------------------------------------

        # get XML tree of the file
        tree = etree.parse(self.thisFile)

        # -------------------------------------------------------------------
        # get properties of user and task + model info
        # -------------------------------------------------------------------

        # properties
        properties_path = tree.xpath("tracesOverview/logEntry/logEntry")[0]
        task = properties_path.attrib['entryPoint']
        user = properties_path.attrib['user']
        test = properties_path.attrib['test']

        self.test_description = test

        start_time_path = tree.xpath("tracesOverview/logEntry")[0]
        start_time = convert_time(start_time_path.attrib['timeStamp'])

        # model
        model = tree.xpath("tracesOverview/logEntry/logEntry/designMicrodynModel")[0]

        # variables and eigendynamic
        variables = []
        ed_list = []
        for variable in model.iter("variable"):
            variables.append(variable.attrib["userDefinedId"])

            if variable.attrib["addend"] != "0":
                ed_list.append(variable.attrib["id"])

        exo_variables = [i for i in variables if "Exo" in i]
        endo_variables = [i for i in variables if "Endo" in i]

        # -------------------------------------------------------------------
        # Create 'help variables'
        # -------------------------------------------------------------------

        phases = ["exploration", "control"]
        rounds = {"exploration": 0,
                  "control": 0}

        actions = {
            "PressApply": "cbaloggingmodel:MicroDynButtonPressLogEntry",
            "AddDependency": "cbaloggingmodel:MicroDynAddDependencyLogEntry",
            "RemoveDependency": "cbaloggingmodel:MicroDynRemoveDependencyLogEntry"
        }

        buttons_to_ignore = ["Start", "End"]

        # -------------------------------------------------------------------
        # iterate through log entries
        # -------------------------------------------------------------------

        logEntries = tree.xpath("tracesOverview/logEntry")

        # loop through each log entry in tree
        for logEntry in logEntries:

            # iterate through each log entry
            for entry in logEntry.iter():

                # define dict for output
                this_row = dict()
                this_row["ID"] = user
                this_row["Item"] = task
                this_row["Test"] = test

                # get timeStamp
                if 'cbaloggingmodel:LogEntryTimeStamp' in entry.values():
                    this_time = convert_time(entry.attrib["timeStamp"])
                    time_delta = (this_time - start_time).total_seconds()

                # get start of control phase
                elif "StartControl" in entry.values():
                    start_time_control = this_time

                # get performed actions
                else:

                    # check for all pre-defined actions
                    for action in actions:

                        # check whether action is in log entry
                        if actions[action] in entry.values():

                            # try to get phase and buttons
                            get_phase = entry.attrib.get("phase")
                            get_button = entry.attrib.get("button")

                            # avoid that 'start' and 'end' buttons are counted as actions
                            if get_button not in buttons_to_ignore:

                                # IF press apply
                                if actions[action] == actions["PressApply"]:

                                    for thisPhase in phases:
                                        if thisPhase == get_phase and get_button == "Execute":
                                            rounds[get_phase] += 1

                                            # store STRATEGIES
                                            for variable in entry.iter("variable"):
                                                this_row[variable.attrib["userDefinedId"]] = int(
                                                    variable.attrib["value"])

                                # IF add or remove dependency
                                if actions[action] == actions["AddDependency"] or actions[action] == actions[
                                    "RemoveDependency"]:
                                    if get_phase == "exploration":
                                        source = entry.attrib["sourceId"]
                                        destination = entry.attrib["destinationId"]
                                        this_row["DeltaDependency"] = source + "->" + destination

                                # Store actions
                                this_row["TimeAfterOnset"] = time_delta
                                this_row["Date"] = this_time
                                this_row["Phase"] = get_phase
                                this_row["Action"] = action
                                this_row["Round"] = rounds[get_phase]

                                self.df_actions = self.df_actions.append(this_row, ignore_index=True)

        # -------------------------------------------------------------------
        # Calcuate strategy scores
        # -------------------------------------------------------------------
        max_len = len(exo_variables)  # checks how many exo variables (i.e., sliders) do we have
        sum0 = (self.df_actions[exo_variables] == 0).sum(axis=1)  # check how many slider were not changed in this round
        sum_na_n = self.df_actions[exo_variables].isna().sum(axis=1)  # ensure that we have valid date for each slider

        conditions = [
            (sum0 == max_len) & (sum_na_n == 0),  # NOTAT
            (sum0 == max_len - 1) & (sum_na_n == 0),  # VOTAT
            (sum0 == 0) & (sum_na_n == 0),  # CA
            (sum0 == 1) & (max_len > 2)  # HOTAT
        ]

        choices = ['NOTAT', 'VOTAT', 'CA', 'HOTAT']
        self.df_actions['strategy'] = np.select(conditions, choices, default=np.NaN)

        # todo der dataframe muss jedes mal neu geladen werden, ansonsten wird die strategy für jede Zeile bei jedem
        # neuem item neu berechnet und die alten dann ggf. überschrieben, wenn neue exo variablen dazukommen.
        # es muss dieses Item und auch diese Versuchsperson ausgewählt werden mit:
        """
        self.df_actions[(self.df_actions["Phase"] == phase) &
                (self.df_actions["ID"] == user) &
                (self.df_actions["Item"] == task)
        """

        # -------------------------------------------------------------------
        # check if response was correct in EXPLORATION phase + ED + num relations
        # -------------------------------------------------------------------

        # correct dependencies
        given_model_results = []

        for dependency in model.iter("dependency"):

            this_source = dependency.attrib["sourceId"]
            this_destination = dependency.attrib["targetId"]

            if float(dependency.attrib["factor"]) != 1:  # ensure that only "real" dependencies are considered
                given_model_results.append(this_source + "->" + this_destination)

        # get also dependencies for eigendynamic
        for dependency_ed in ed_list:
            given_model_results.append(dependency_ed + "->" + dependency_ed)

        # given dependencies + thresholds
        end_model = tree.xpath("tracesOverview/logEntry/logEntry/runtimeMicrodynModel")[0]
        end_model_response = []

        for dependency in end_model.iter("dependency"):
            end_model_response.append(dependency.attrib["sourceId"] + "->" + dependency.attrib["targetId"])

        # check EXPLORATION
        if set(end_model_response) == set(given_model_results):
            correct_exploration = 1
        else:
            correct_exploration = 0

        # -------------------------------------------------------------------
        # check if response was correct in CONTROL phase
        # -------------------------------------------------------------------

        # get thresholds
        threshold1 = dict()
        threshold2 = dict()

        for variable in model.iter("variable"):
            name = variable.attrib["userDefinedId"]
            if "Endo" in name:
                threshold1[name] = int(variable.attrib["targetValue"])
                threshold2[name] = int(variable.attrib["targetLimit"])

        # get given response
        given_control_response = dict()
        for variable in endo_variables:
            given_control_response[variable] = self.df_actions[variable].iloc[-1]

        # compare given answer with pre-defined thresholds
        for given, thres1, thres2 in zip(given_control_response, threshold1, threshold2):

            if threshold1[thres1] <= given_control_response[given] <= threshold2[thres2] \
                    or threshold2[thres2] <= given_control_response[given] <= threshold2[thres2]:
                correct_control = 1
            else:
                correct_control = 0

        correct = {"exploration": correct_exploration,
                   "control": correct_control}

        # -------------------------------------------------------------------
        # get time on task
        # -------------------------------------------------------------------

        # We already go "start time" and "start control time". We take last assignment to "this_time" as TimeMax of the task.

        # time incl. instruction
        end_time = this_time
        exploration_time = (start_time_control - start_time).total_seconds()
        control_time = (end_time - start_time_control).total_seconds()

        times = {"exploration": exploration_time,
                 "control": control_time}

        # time excl. instruction
        time_data = tree.xpath("microdynOverview/executedPhases")

        for td in time_data:
            for entry in td.iter():
                if "EXPLORATION" in entry.values():
                    exploration_time_no_instr = entry.attrib["time"]

                elif "CONTROL" in entry.values():
                    control_time_no_instr = entry.attrib["time"]

        times_noInstr = {"exploration": exploration_time_no_instr,
                         "control": control_time_no_instr}

        # -------------------------------------------------------------------
        # task characteristics (relations, ED)
        # -------------------------------------------------------------------

        # check eigendynamic (ED)
        if len(ed_list) > 0:  # check whether some addend of variable is not 0
            ed = True
        else:
            ed = False

        # check number of dependencies (relations)
        num_dependencies = len(given_model_results) + len(ed_list)

        # -------------------------------------------------------------------
        # build df for aggregated data (long format)
        # -------------------------------------------------------------------

        # get Data
        for phase in phases:
            this_action_df = self.df_actions[(self.df_actions["Phase"] == phase) &
                                             (self.df_actions["ID"] == user) &
                                             (self.df_actions["Item"] == task)]

            agg = dict()
            agg["ID"] = user
            agg["Item"] = task
            agg["Date"] = start_time
            agg["Test"] = test
            agg["Phase"] = phase
            agg["ED"] = ed
            agg["NumDependencies"] = num_dependencies
            agg["NumInput"] = len(exo_variables)
            agg["NumOutput"] = len(endo_variables)
            agg["Rounds"] = this_action_df["Round"].max()
            agg["Time_Instr"] = times[phase]
            agg["Time_NoInstr"] = times_noInstr[phase]
            agg["Correct"] = correct[phase]
            agg["VOTATfreq"] = (this_action_df["strategy"] == "VOTAT").sum()
            agg["HOTATfreq"] = (this_action_df["strategy"] == "HOTAT").sum()
            agg["NOTATfreq"] = (this_action_df["strategy"] == "NOTAT").sum()
            agg["CAfreq"] = (this_action_df["strategy"] == "CA").sum()
            agg["StratSeq"] = "-".join(list(this_action_df["strategy"].replace("nan", np.NaN).dropna().values))
            agg["ActionSeq"] = "-".join(list(this_action_df["Action"].replace("nan", np.NaN).dropna().values))

            self.df_long = self.df_long.append(agg, ignore_index=True)

        # print task, user
        print("    -> finished -", user, "with", task)


if __name__ == '__main__':
    print("# start at", datetime.datetime.now().time())
    XmlParser(subset_cases=True, subset_tasks=True, verbose=True)

    print("# finished at", datetime.datetime.now().time())

# todo add fullVOTAT
# todo startTime neu definieren? (etwas später?)
# todo generell Zeiten checken
# todo check whether rounds is calculated correctly
# todo ignore instruction/instructionED/FinnAngst?
# todo check whether item with ED (even better: get structure of item)
