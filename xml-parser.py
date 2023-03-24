from lxml import etree
import pandas as pd
import datetime
import numpy as np
import glob
import os
import sys


class XmlParser:

    def __init__(self, inp="", out="out", verbose=True, subset_cases=False, subset_tasks=True, wide=False):
        """
        @:param inp: specified input path of xml-files
        @:param out: specified out path of data frames
        @:param verbose: specify whether action data should be stored

        """

        self.relevant_data_points = []
        self.subset_tasks = subset_tasks
        self.wide = wide
        self.subset_cases = subset_cases
        self.verbose = verbose
        self.out = out
        self.input = inp
        self.test_description = None

        # STEP 0a -> df for action stream
        self.actionDfColumns = ["ID", "Item", "Date", "Test",
                                "TimeAfterOnset", "Phase", "Round",
                                "Action", "SpecificAction"]

        self.df_actions = pd.DataFrame(columns=self.actionDfColumns)

        # STEP 0b -> df for aggregated data
        self.dfLongColumns = ["ID", "Item", "Date", "Test",
                              "Phase", "Rounds",
                              "ED", "NumDependencies", "NumInput", "NumOutput",
                              "Time_NoInstr",
                              "Correct",
                              "VOTATfreq", "HOTATfreq", "NOTATfreq", "CAfreq",
                              "VOTAT_x_vars", "fullVOTAT",
                              "StratSeq", "ActionSeq"]

        self.df_long = pd.DataFrame(columns=self.dfLongColumns)

        # STEP 1a -> get all files in path
        this_path = os.path.join("data", self.input, "*_scoring.xml")
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

        if len(self.allFiles) == 0:
            print("""
            Based on your definitions in both ID.csv and/or tasks.csv no datapoints could be selected.
            Please redefine your specifications in these files or set "subset_clases" and/or "subset_tasks" to "False".
            """)

            print("# finished at", datetime.datetime.now().time())
            sys.exit(1)

        else:
            for self.thisFile in self.allFiles:
                self.parse_this_file()

    # save data frame
    def save_data_frames(self):
        """
        Saves all data frames and also call function long_to_wide to convert long df in wide df.
        """
        # check directory and create if not existing
        if not os.path.exists(self.out):
            os.makedirs(self.out)

        # save all data frames
        self.df_long.to_csv(self.out + os.sep + self.test_description + "_aggregated_long.csv", index=False)

        if self.wide:
            self.long_to_wide()
            self.df_wide.to_csv(self.out + os.sep + self.test_description + "_aggregated_wide.csv", index=False)

        if self.verbose:
            self.df_actions["TimeAfterOnset"] = pd.to_numeric(self.df_actions["TimeAfterOnset"])
            self.df_actions.sort_values(by=["ID", "Item", "TimeAfterOnset"], inplace=True)
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

        # create list in which included files are stored
        use_these_files = []

        # loop through all files and filter according to subset specifications
        for thisFile in self.allFiles:

            # select tasks
            if self.subset_tasks and not self.subset_cases:
                for task in tasks:
                    if task in thisFile:
                        use_these_files.append(thisFile)

            # select cases
            elif self.subset_cases and not self.subset_tasks:
                for case in cases:  # todo problem when codes are similar!
                    if case in thisFile:
                        use_these_files.append(thisFile)

            # select both tasks and cases
            elif self.subset_cases and self.subset_tasks:
                for task in tasks:
                    for case in cases:
                        if task in thisFile and case in thisFile:
                            use_these_files.append(thisFile)

            # over-write "allFiles" with subset of selected files (i.e., "use_these_files")
            self.allFiles = use_these_files

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

        start_time_path = tree.xpath("tracesOverview/logEntry")[2]
        start_time = convert_time(start_time_path.attrib['timeStamp'])

        # add start time to actions
        start_row = dict()
        start_row["ID"] = user
        start_row["Item"] = task
        start_row["SpecificAction"] = "START"
        start_row["Test"] = test
        start_row["TimeAfterOnset"] = 0
        start_row["Date"] = start_time
        start_row["Phase"] = "Start Test"
        start_row["Action"] = "Start"
        start_row["Round"] = 0
        start_row["strategy"] = np.NaN

        start_row_df = pd.DataFrame.from_dict(start_row, orient="index").T
        self.df_actions = pd.concat([self.df_actions, start_row_df], ignore_index=True)

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
            "RemoveDependency": "cbaloggingmodel:MicroDynRemoveDependencyLogEntry",
            "PressButton": "cbaloggingmodel:ButtonLogEntry"
        }

        buttons_to_ignore = ["Start",
                             "End",
                             "Reset",
                             "$284335466347500",  # start button Handball
                             "$335515708423800",  # start button Gardening
                             "$284335424819300",  # end item Handball
                             "$335515641725400"  # end item Gardening
                             ]

        votat_array = []
        this_strategy = None
        time_delta = None
        max_len = None

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


                # get performed actions
                else:

                    # check for all pre-defined actions
                    for action in actions:

                        # check whether action is in log entry
                        if actions[action] in entry.values():

                            # try to get phase and buttons
                            get_phase = entry.attrib.get("phase")

                            get_button = entry.attrib.get("button") \
                                if entry.attrib.get("button") is not None \
                                else entry.attrib.get("id")

                            # avoid that 'start' and 'end' buttons are counted as actions
                            if get_button not in buttons_to_ignore:

                                # IF press apply
                                if actions[action] == actions["PressApply"]:

                                    for thisPhase in phases:
                                        if thisPhase == get_phase and get_button == "Execute":
                                            rounds[get_phase] += 1

                                            # store values for exo + endo variables
                                            for variable in entry.iter("variable"):
                                                this_row[variable.attrib["userDefinedId"]] = int(
                                                    variable.attrib["value"])

                                            # code STRATEGIES
                                            this_exo_values = [this_row[exo] for exo in exo_variables]
                                            num_zeros = this_exo_values.count(0)
                                            max_len = len(this_exo_values)

                                            if num_zeros == max_len:
                                                this_strategy = "NOTAT"
                                            elif num_zeros == max_len - 1:
                                                this_strategy = "VOTAT"
                                                if thisPhase == "exploration":  # fullVOTAT is relevant for exploration
                                                    votat_array.append(this_exo_values)
                                            elif num_zeros == 0:
                                                this_strategy = "CA"
                                            elif max_len > 2 and num_zeros == 1:
                                                this_strategy = "HOTAT"
                                            else:
                                                this_strategy = np.NaN

                                # IF add or remove dependency
                                if actions[action] == actions["AddDependency"] or actions[action] == actions[
                                    "RemoveDependency"]:

                                    this_strategy = np.NaN

                                    if get_phase == "exploration":
                                        source = entry.attrib["sourceId"]
                                        destination = entry.attrib["destinationId"]
                                        this_row["ChangeDependency"] = source + "->" + destination

                                # Store actions
                                this_row["SpecificAction"] = get_button
                                this_row["TimeAfterOnset"] = time_delta
                                this_row["Date"] = this_time
                                this_row["Phase"] = get_phase
                                this_row["Action"] = action
                                this_row["Round"] = rounds[get_phase] if get_phase is not None else np.NaN
                                this_row["strategy"] = this_strategy

                                this_row_df = pd.DataFrame.from_dict(this_row, orient="index").T
                                self.df_actions = pd.concat([self.df_actions, this_row_df], ignore_index=True)

        # -------------------------------------------------------------------
        # check fullVOTAT
        # -------------------------------------------------------------------
        votat_array = np.array(votat_array)
        votat_array = np.absolute(votat_array)
        votat_by_vars = np.count_nonzero(votat_array.sum(axis=0))

        if votat_by_vars == max_len:
            full_votat = True
        else:
            full_votat = False

        # print(votat_array, votat_by_vars, full_votat)
        # -------------------------------------------------------------------
        # check if response was correct in EXPLORATION phase + ED + num relations
        # -------------------------------------------------------------------

        # correct dependencies
        given_model_results = []

        for dependency in model.iter("dependency"):

            this_source = dependency.attrib["sourceId"]
            this_destination = dependency.attrib["targetId"]

            if float(dependency.attrib["factor"]) != 1:  # ensured that only "real" dependencies are considere
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
            this_var = self.df_actions.get(variable)
            # print(this_var)

            # get last valid value (last valid log for each ENDO value)
            last_valid_index = this_var.last_valid_index()
            given_control_response[variable] = this_var.loc[last_valid_index]

        correct_control_partial_list = []
        correct_control_partial = np.NaN

        # compare given answer with pre-defined thresholds
        for given, thres1, thres2 in zip(given_control_response, threshold1, threshold2):

            if threshold1[thres1] < threshold2[thres2]:
                if threshold1[thres1] <= given_control_response[given] <= threshold2[thres2]:
                    correct_control_partial = 1
            elif threshold2[thres2] < threshold1[thres1]:
                if threshold2[thres2] <= given_control_response[given] <= threshold1[thres1]:
                    correct_control_partial = 1
            else:
                correct_control_partial = 0

            # store this partial solution of control phase for scoring in the next step
            correct_control_partial_list.append(correct_control_partial)

        # calculate full scoring
        if all(elem == 1 for elem in correct_control_partial_list):
            correct_control = 1
        else:
            correct_control = 0

        correct = {"exploration": correct_exploration,
                   "control": correct_control}


        # --- print output for control  ----------------------------------
        all_keys = list(set(given_control_response.keys()) | set(threshold1.keys()) | set(threshold2.keys()))

        given_list = [given_control_response.get(key, None) for key in all_keys]
        threshold_target_list = [threshold1.get(key, None) for key in all_keys]
        threshold_limit_list = [threshold2.get(key, None) for key in all_keys]

        print_out_control = pd.DataFrame({
            'given_respsonse': given_list,
            'threshold_target': threshold_target_list,
            'threshold_limit': threshold_limit_list
        }, index=all_keys).reindex(['EndoA', 'EndoB', 'EndoC'])

        print(print_out_control)
        print(f"Correct: {correct_control}")
        # ------------------------------------------------------------------

        # -------------------------------------------------------------------
        # get time on task
        # -------------------------------------------------------------------

        """
        End time is taken from microdyn overview. The Execution environment is caluclating the time on task
        correctly (double-checked) but this is only indicated in the overview. I.e., there is not log-entry
        when the "finish" button was pressed and the item was terminated. Hence, we use the entry from overview 
        and we also calculate the specific time stamp by date(end) = start time + time on task. 
        """

        # time excl. instruction
        end_data = tree.xpath("microdynOverview")[0]
        exploration_time_no_instr = end_data.attrib["explorationTime"]
        control_time_no_instr = end_data.attrib["controlTime"]

        times_no_instr = {"exploration": exploration_time_no_instr,
                          "control": control_time_no_instr}

        # add end time to actions
        end_row = dict()
        end_row["ID"] = user
        end_row["Item"] = task
        end_row["Test"] = test
        end_row["SpecificAction"] = "END"
        end_row["TimeAfterOnset"] = exploration_time_no_instr
        end_row["Date"] = start_time + datetime.timedelta(seconds=int(exploration_time_no_instr))
        end_row["Phase"] = "exploration"
        end_row["Action"] = "EndExploration"
        end_row["Round"] = np.NaN
        end_row["strategy"] = np.NaN

        end_row_df = pd.DataFrame.from_dict(end_row, orient="index").T
        self.df_actions = pd.concat([self.df_actions, end_row_df], ignore_index=True)

        # -------------------------------------------------------------------
        # task characteristics (relations, ED)
        # -------------------------------------------------------------------

        # check eigendynamic (ED)
        if len(ed_list) > 0:  # check whether some addend of variable is not 0
            ed = True
        else:
            ed = False

        # check number of dependencies (relations)
        num_dependencies = len(given_model_results)

        # ------------------------------------------------------------------
        # build df for aggregated data (long format)
        # ------------------------------------------------------------------

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

            if not this_action_df.empty:
                agg["Rounds"] = this_action_df["Round"].max()
                agg["Time_NoInstr"] = times_no_instr[phase]
                agg["Correct"] = correct[phase]
                agg["VOTATfreq"] = (this_action_df["strategy"] == "VOTAT").sum()
                agg["HOTATfreq"] = (this_action_df["strategy"] == "HOTAT").sum()
                agg["NOTATfreq"] = (this_action_df["strategy"] == "NOTAT").sum()
                agg["CAfreq"] = (this_action_df["strategy"] == "CA").sum()
                agg["VOTAT_x_vars"] = votat_by_vars
                agg["fullVOTAT"] = full_votat
                agg["StratSeq"] = "-".join(list(this_action_df["strategy"].replace("nan", np.NaN).dropna().values))
                agg["ActionSeq"] = "-".join(list(this_action_df["Action"].replace("nan", np.NaN).dropna().values))

            agg_df = pd.DataFrame.from_dict(agg, orient="index").T
            self.df_long = pd.concat([self.df_long, agg_df], ignore_index=True)

        # print task, user
        print("    -> finished -", user, "with", task)


if __name__ == '__main__':
    print("# start at", datetime.datetime.now().time())
    XmlParser(inp="AlexGT/data", subset_cases=False, subset_tasks=True, verbose=True, wide=False)
    print("# finished at", datetime.datetime.now().time())
