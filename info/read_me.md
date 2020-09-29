Put your specification files here. These options are available:

* `IDs.csv`: define, which cases should be included. Use `ID`as column header and add the cases row-wise. For instance:

  | ID           |
  | ------------ |
  | Mickey Mouse |
  | Donald Duck  |
  | Goofy        |

* `tasks.csv`: define, which tasks should be included. Use `tasks`as column header and add the tasks row-wise. Please stick to the original English (!) names from the respective MicroDYN items. You can find them in the file name of the respective xml-File. For instance:

  | tasks    |
  | -------- |
  | Lemonade |
  | Cat      |
  | Moped    |

* you can filter by ID, tasks or both with the attributes `subset_cases` or `subset_tasks` in the `main`  function.

