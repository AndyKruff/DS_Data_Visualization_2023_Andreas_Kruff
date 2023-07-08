import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def preprocess_data(filepath, delimiter, differentiating, observation_window=(6, 22)):
    """
    Preprocesses the data to allow the opportunity to calculate monthly average considering complete days or differentiating
    between day- and nighttime

    Parameters
    ----------
    filepath (String): Path to the noise data dataset
    delimiter (String): Delimiter used within the CSV file
    differentiating (Boolean): Gives the option to either calculate the average for the complete day or if it differentiates
                             betweeen day- and nighttime
    observation_window (Tupel): Contains the the starting and end point of the daytime definition (Default: 6 - 22)
    Returns
    -------
    df (DataFrame): Dataframe containing the newly created columns and aggregated data
    """

    # Reading dataset containing noise measurements in Basel
    df = pd.read_csv(filepath, delimiter=delimiter)
    df["date"] = df["Zeitstempel"].apply(lambda x: x[:7])

    if differentiating:
        # Extracting time of accident from column "Zeitstempel"

        df["Uhrzeit"] = df["Zeitstempel"].apply(lambda x: int(x[-13:-12]))

        # Creating new column for differentiating day- and nighttime
        df["time_of_day"] = df["Uhrzeit"].apply(
            set_time_of_day, observation_window=observation_window
        )

        # Using groupby to calculate the monthly average noise pollution during day- and nighttime
        df = df.groupby(["Station", "date", "time_of_day"])["Wert"].mean().reset_index()

        # Replaces outliers found in the dataset (e.g. 24.1 ± 5) by NaN values
        df["Wert"] = df["Wert"].apply(replace_missing_values, default=24.1, treshhold=5)

    else:
        # Using the groupby function to calculated the average noise per month, without differentiation of the time
        df = df.groupby(["Station", "date"])["Wert"].mean().reset_index()

        # Replaces outliers found in the dataset (e.g. 24.1 ± 5) by NaN values
        df["Wert"] = df["Wert"].apply(replace_missing_values, default=24.1, treshhold=5)

    return df


def visualize_noise_pollution_development(
    filepath, delimiter, differentiating=True, observation_window=(6, 22)
):
    """
    Creates a matplotlib lineplot regarding the noise pollution at the different monitoring stations in Basel

    Parameters
    ----------
    df (DataFrame): Preprocessed dataframe containing the noise data
    differentiating (Boolean): Should the entire day be used for the monthly averages or should it be differentiated
                               to compare day- and nighttime (Default: True)
    observation_window (Tupel): Contains the the starting and end point of the daytime definition (Default: 6 - 22)

    Returns
    -------

    """

    # Preprocesses the data to allow differentiating between the monthly averages for complete day and between day- and nighttime

    df = preprocess_data(
        filepath,
        delimiter,
        differentiating=differentiating,
        observation_window=observation_window,
    )
    # If clause for deciding if the average noise is plotted for the complete day or plotted separatly for day and
    # night time
    if differentiating:
        # Create sub Dataframes filtered by time of day
        nighttime_data = df[df["time_of_day"] == "nighttime"]
        daytime_data = df[df["time_of_day"] == "daytime"]

        # Swapping row values for Station names to column names for plotting
        nighttime_data = nighttime_data.pivot(
            index="date", columns="Station", values="Wert"
        )
        daytime_data = daytime_data.pivot(
            index="date", columns="Station", values="Wert"
        )

        # Converting the index in a datetime format
        nighttime_data.index = pd.to_datetime(nighttime_data.index)
        daytime_data.index = pd.to_datetime(daytime_data.index)

        # Choosing a color pallete from Seaborn ("colorblind")
        color_palette = sns.color_palette("colorblind")

        # Defining the figure regarding size, amount of plots ...
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6), sharey=True)
        ax1 = axes[0]

        # Defining the aesthetics for the different lines in the plot regarding color and linestyle
        ax1.plot(
            daytime_data.index.values,
            daytime_data["Feldbergstrasse"].values,
            label="Feldbergstrasse",
            drawstyle="steps-pre",
            color=color_palette[0],
        )
        ax1.plot(
            daytime_data.index.values,
            daytime_data["Grenzacherstrasse"].values,
            label="Grenzacherstrasse",
            drawstyle="steps-pre",
            color=color_palette[1],
        )
        ax1.plot(
            daytime_data.index.values,
            daytime_data["Hochbergerstrasse_162"].values,
            label="Hochbergerstrasse_162",
            drawstyle="steps-pre",
            color=color_palette[2],
        )
        ax1.plot(
            daytime_data.index.values,
            daytime_data["St.Jakobs-Strasse"].values,
            label="St.Jakobs-Strasse",
            drawstyle="steps-pre",
            color=color_palette[3],
        )
        ax1.plot(
            daytime_data.index.values,
            daytime_data["Zuercherstrasse148"].values,
            label="Zuercherstrasse148",
            drawstyle="steps-pre",
            color=color_palette[4],
        )

        # Adding title for plot 1 and labels for the axis
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
        ax1.set_title(
            f"Average decibel measurements for the different monitoring stations \n in Basel-City (Daytime - ({observation_window[0]} - {observation_window[1]} o'clock))"
        )
        ax1.set_xlabel("Dates [in months]")
        ax1.set_ylabel("Measured noise [in dB]")

        # Adding grid layout for better readability
        ax1.grid(True)

        # Similar to ax1
        ax2 = axes[1]
        ax2.plot(
            nighttime_data.index.values,
            nighttime_data["Feldbergstrasse"].values,
            label="Feldbergstrasse",
            drawstyle="steps-pre",
            color=color_palette[0],
        )
        ax2.plot(
            nighttime_data.index.values,
            nighttime_data["Grenzacherstrasse"].values,
            label="Grenzacherstrasse",
            drawstyle="steps-pre",
            color=color_palette[1],
        )
        ax2.plot(
            nighttime_data.index.values,
            nighttime_data["Hochbergerstrasse_162"].values,
            label="Hochbergerstrasse_162",
            drawstyle="steps-pre",
            color=color_palette[2],
        )
        ax2.plot(
            nighttime_data.index.values,
            nighttime_data["St.Jakobs-Strasse"].values,
            label="St.Jakobs-Strasse",
            drawstyle="steps-pre",
            color=color_palette[3],
        )
        ax2.plot(
            nighttime_data.index.values,
            nighttime_data["Zuercherstrasse148"].values,
            label="Zuercherstrasse148",
            drawstyle="steps-pre",
            color=color_palette[4],
        )
        ax2.set_title("Average decibel measurements during daytime")

        every_third_month_ticks = daytime_data.index[::3]
        ax1.set_xticks(every_third_month_ticks)
        ax1.set_xticklabels(every_third_month_ticks.strftime("%Y-%m"), rotation=45)

        ax2.set_xticks(every_third_month_ticks)
        ax2.set_xticklabels(every_third_month_ticks.strftime("%Y-%m"), rotation=45)
        ax2.set_title(
            f"Average decibel measurements for the different monitoring stations \n in Basel-City (Nighttime - ({observation_window[1]} - {observation_window[0]} o'clock))"
        )
        ax2.set_xlabel("Dates [in months]")
        ax2.set_ylabel("Measured noise [in dB]")
        ax2.grid(True)

        ax1.set_yticklabels(ax1.get_yticks())
        ax2.set_yticklabels(ax2.get_yticks())
        handles, labels = ax1.get_legend_handles_labels()

        # Automatically adjusting the spacing and positioning of elements in a plot to prevent overlapping
        # and optimize space utilization
        plt.tight_layout()

        # Setting one legend for both plots below the two plots
        fig.legend(handles, labels, loc="lower center", ncol=len(labels))

        plt.show()

    else:
        # Swapping row values for Station names to column names for plotting

        dataframe = df.pivot(index="date", columns="Station", values="Wert")

        # Converting the index in a datetime format
        dataframe.index = pd.to_datetime(dataframe.index)

        # Similar as above
        color_palette = sns.color_palette("colorblind")

        fig, ax = plt.subplots()
        ax.plot(
            dataframe.index.values,
            dataframe["Feldbergstrasse"].values,
            label="Feldbergstrasse",
            drawstyle="steps-pre",
            color=color_palette[0],
        )
        ax.plot(
            dataframe.index.values,
            dataframe["Grenzacherstrasse"].values,
            label="Grenzacherstrasse",
            drawstyle="steps-pre",
            color=color_palette[1],
        )
        ax.plot(
            dataframe.index.values,
            dataframe["Hochbergerstrasse_162"].values,
            label="Hochbergerstrasse_162",
            drawstyle="steps-pre",
            color=color_palette[2],
        )
        ax.plot(
            dataframe.index.values,
            dataframe["St.Jakobs-Strasse"].values,
            label="St.Jakobs-Strasse",
            drawstyle="steps-pre",
            color=color_palette[3],
        )
        ax.plot(
            dataframe.index.values,
            dataframe["Zuercherstrasse148"].values,
            label="Zuercherstrasse148",
            drawstyle="steps-pre",
            color=color_palette[4],
        )

        # Settings for the x-tick labels (displaying only every third xtick)
        every_third_month_ticks = dataframe.index[::3]
        ax.set_xticks(every_third_month_ticks)
        ax.set_xticklabels(every_third_month_ticks.strftime("%Y-%m"), rotation=45)

        ax.set_title(
            "Average decibel measurements for the different monitoring stations in Basel-City"
        )
        ax.set_xlabel("Dates [in months]")
        ax.set_ylabel("Measured noise [in dB]")
        ax.grid(True)
        ax.legend()

        plt.show()


def replace_missing_values(value, default, treshhold):
    """
    Function to replace the outliers by NaN

    Parameters
    ----------
    value (Float): Potential outlier from the dataset
    default (Float): Default value that was found to be an outlier within the dataset
    treshhold (Float): Treshhold to set a range of potential outliers

    Returns
    -------
    value (Float): Original value or value replaced by nan
    """
    if value == default or abs(value - default) < treshhold:
        return np.nan
    return value


def set_time_of_day(time_of_day, observation_window):
    """
    Function that adds day- and nighttime to the new column time_of_day depending on the choosen observation window

    Parameters
    ----------
    time_of_day (int): Hour of the Accident
    observation_window (Tupel): Contains the the starting and end point of the daytime definition

    Returns
    -------

    """

    if observation_window[0] <= time_of_day <= observation_window[1]:
        return "daytime"
    else:
        return "nighttime"


if __name__ == "__main__":
    # Creating the visualizations depending on the differentiating option
    visualize_noise_pollution_development(
        "../data/noise_measurements.csv", ";", differentiating=True
    )
