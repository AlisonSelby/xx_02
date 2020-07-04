import pandas as pd
import os
import numpy as np
import datetime
import matplotlib.pyplot as plt


def main():
    if not os.path.isdir("../output"):
        os.mkdir("../output")

    disease_data = pd.read_csv("../input/individual_level_data.csv", parse_dates=[0],
                               usecols=[0, 2], infer_datetime_format=True)
    location_data = pd.read_excel("../data_structural/norway_locations_b2020.xlsx", usecols="A:D")
    if os.path.isfile("../data_structural/pop_data.csv"):
        pop_data_filename = "../data_structural/pop_data.csv"
    else:
        pop_data_filename = "https://data.ssb.no/api/v0/dataset/26975.csv?lang=en"
    pop_data = pd.read_csv(pop_data_filename, quotechar='"', usecols=[0, 1, 3], converters={"year": lambda x: datetime.datetime(int(x),1,1)})

    pop_data = pop_data[pop_data.year >= datetime.datetime(2015,1,1)]
    pop_data = pd.concat([pop_data, pop_data["region"].str.split(" ", 1, True)], axis=1)
    pop_data.rename(inplace=True, columns={0: "location_code", 1: "location_name",
                                           "07459: Population, by region, year and contents": "num_population"})

    pop_data["location_code"] = pop_data["location_code"].apply(lambda label: "municip" + label[2:])
    pop_data.columns.str.strip()
    pop_data.sort_values(by=["year", "location_code"], inplace=True)

    create_folder_structure(location_data)
    combined_data = aggregate_per_day(disease_data, location_data, pop_data)
    combined_weekly_data = aggregate_per_week(combined_data)
    dataset_per_location(combined_data, combined_weekly_data, location_data)




def aggregate_per_day(disease_data, location_data, pop_data):
    disease_location_merge = pd.merge(disease_data, location_data, left_on="location_code", right_on="municip_code",
                                      left_index=True)
    disease_location_merge.sort_values(by=["date", "location_code"], inplace=True)
    disease_location_merge = pd.merge_asof(disease_location_merge, pop_data, by="location_code", left_on="date", right_on="year")

    kommune_disease_data = disease_location_merge.copy()[["date", "location_code", "municip_name", "num_population", "county_code", "county_name"]]
    kommune_disease_data = kommune_disease_data.groupby(
        ["date", "location_code", "municip_name", "county_code", "county_name", "num_population"]).size().to_frame().reset_index()
    kommune_disease_data.rename(inplace=True, columns={"municip_name": "location_name", 0: "num_sick"})

    fylke_disease_data = kommune_disease_data.copy()[["date", "county_code", "county_name", "num_population", "num_sick"]]
    fylke_disease_data = kommune_disease_data.groupby(["date", "location_code"]).first().groupby(["date", "county_code", "county_name"]).sum().reset_index()
    fylke_disease_data.rename(inplace=True, columns={"county_code": "location_code", "county_name": "location_name"})

    kommune_disease_data.drop(labels=["county_code", "county_name"], axis=1, inplace=True)

    country_disease_data = fylke_disease_data.copy()
    country_disease_data["location_code"] = "norge"
    country_disease_data["location_name"] = "Norge"
    country_disease_data = country_disease_data.groupby(["date", "location_code", "location_name"]).sum().reset_index()

    combined_data = pd.concat([kommune_disease_data, fylke_disease_data, country_disease_data], axis=0)
#    combined_data.to_excel("../output/full_day.xlsx", index=False)
    return combined_data

def aggregate_per_week(combined_data):
    combined_weekly_data = combined_data.copy()
    combined_weekly_data['date'] = pd.to_datetime(combined_weekly_data['date']) - pd.to_timedelta(7, unit='d')
    combined_weekly_data = combined_weekly_data.groupby([pd.Grouper(key='date', freq='W-MON'), "location_code", "location_name", ]).agg(
        num_population=pd.NamedAgg("num_population", "first"),
        num_sick=pd.NamedAgg("num_sick", "sum")
    ).reset_index()
    combined_weekly_data["date"].dt.strftime("%Y-%W")
#    combined_weekly_data.to_excel("../output/full_week.xlsx", index=False)
    return combined_weekly_data


def create_folder_structure(location_data):
    os.makedirs("../output/Norge", exist_ok=True)
    for idx, row in location_data.iterrows():
        os.makedirs(f"../output/{row['county_name']}/{row['municip_name']}", exist_ok=True)
        os.makedirs(f"../output/{row['county_name']}/_county", exist_ok=True)


def dataset_per_location(combined_data, combined_weekly_data, location_data):
    day_data = combined_data.loc[combined_data["location_code"] == "norge"]
    day_data.to_excel("../output/Norge/full_day.xlsx", index=False)
    combined_weekly_data.loc[combined_weekly_data["location_code"] == "norge"].to_excel("../output/Norge/full_week.xlsx", index=False)

    plt.plot(day_data["date"], day_data["num_sick"])
    plt.xlabel(f"Disease X in Norge (pop. {day_data['num_population'].mean():,})".replace(',', ' '))
    plt.ylabel("Number of sick people")
    plt.savefig(f"../output/Norge/graph.png")
    plt.clf()

    county_codes = location_data["county_code"].unique()
    county_names = location_data["county_name"].unique()
    for fylke_code, fylke_name in zip(county_codes, county_names):
        day_data = combined_data.loc[combined_data["location_code"] == fylke_code]
        day_data.to_excel(f"../output/{fylke_name}/_county/full_day.xlsx", index=False)
        combined_weekly_data.loc[combined_weekly_data["location_code"] == fylke_code].to_excel(f"../output/{fylke_name}/_county/full_week.xlsx", index=False)

        plt.plot(day_data["date"], day_data["num_sick"])
        plt.xlabel(f"Disease X in {fylke_name} (pop. {day_data['num_population'].mean():,})".replace(',', ' '))
        plt.ylabel("Number of sick people")
        plt.savefig(f"../output/{fylke_name}/_county/graph.png")
        plt.clf()

        municip_code = location_data.loc[location_data["county_code"] == fylke_code]["municip_code"]
        municip_name = location_data.loc[location_data["county_code"] == fylke_code]["municip_name"]

        for kommune_code, kommune_name in zip(municip_code, municip_name):
            day_data = combined_data.loc[combined_data["location_code"] == kommune_code]
            day_data.to_excel(f"../output/{fylke_name}/{kommune_name}/full_day.xlsx", index=False)
            combined_weekly_data.loc[combined_weekly_data["location_code"] == kommune_code].to_excel(
                f"../output/{fylke_name}/{kommune_name}/full_week.xlsx", index=False)

            plt.plot(day_data["date"], day_data["num_sick"])
            plt.xlabel(f"Disease X in {kommune_name} (pop. {day_data['num_population'].mean():,})".replace(',', ' '))
            plt.ylabel("Number of sick people")
            plt.savefig(f"../output/{fylke_name}/{kommune_name}/graph.png")
            plt.clf()


main()

