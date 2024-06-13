# iChart

iChart is a Python implementation of the Standard Celeration Chart (SCC). The SCC is a versatile data visualization tool used in the field of Precision Teaching and other areas for analysis of frequencies. The project is currently in alpha. The goal is a free and easy to use app for charting on desktop.

Contact: ichart.wopak@simplelogin.com<br>

## Instructions
- [Installation](#installation)
- [Import Formatting](#import-formatting)

## Features
- Data import and export
- Direct data entry
- Phase lines
- Aim lines
- Trend analysis
- Selective viewing
- Credit lines
- Changeable start date
- Supports multiple chart types

## Installation

Extract content in your preferred directory. Launch by running iChart executable.

On Windows, right click and select "Run as administrator". Windows Defender will then raise a warning. To proceed, click on "More info" and then click "Run anyway". In the unlikely event that this does not work, you may need to manually add an [exception](https://support.microsoft.com/en-us/windows/add-an-exclusion-to-windows-security-811816c0-4dfd-af4a-47e4-c301afe13b26).


## Import Formatting

You can data import from csv, xls, xlsx, and ods, files. iChart will only look at sheet 1 if you have multiple sheets, and only the first 6 columns. All subsequent columns will be ignored. You can use these extra columns for notes and other stuff. iChart will also only look at the first letter and ignore case when determining the data type. Subsequent letters can be added for human readabiliy. Column order does not matter.

1) *Date column*. Any column name starting with "d" will be interpreted as the date column. This column must contain full dates – day, month, and year. iChart should be quite flexible with exactly how the date is formatted in the column, provided they are complete dates. If you still get import errors or strange date behaviors, try this format: yyyy-mm-dd (for instance, 2024-04-19). Values for duplicate dates will be averaged together.
2) *Dot column*. Any column name starting with "c" (corrects) are interpreted as the dot column. These are expected to be raw counts. This column will automatically be padded with zero values if omitted.
3) *X column*. Any column name starting with "i" (incorrects) are interpreted as the x column. These are expected to be raw counts. This column will automatically be padded with zero values if omitted.
4) *Time column*. Any column starting with "s", "m" or "h" (seconds, minutes, hours) will be interpreted as part of the timing floor. They will be added up in the background as the total amount of minutes, and automatically used for obtaing frequency counts. You can omit all these columns if you are not using the minute charts. For minute charts, you can use them in any combination. For example, only use the "m" and "s" column and iChart will automatically convert this to the total amount of minutes.

Here is an [example.](https://github.com/SJV-S/iChart/blob/main/example_data.csv)


![Default Chart](images/default_chart.png)

![Example Chart](images/example_chart.png)

