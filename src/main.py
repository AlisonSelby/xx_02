import pandas as pd
import requests
import os


def main():
    disease_data = pd.read_csv("../input/individual_level_data.csv", parse_dates=[0], infer_datetime_format=True)
    location_data = pd.read_excel("../data_structural/norway_locations_b2020.xlsx", usecols="A:D")
    if os.path.isfile("../data_structural/pop_data.csv"):
        pop_data_filename = "../data_structural/pop_data.csv"
    else:
        pop_data_filename = "https://data.ssb.no/api/v0/dataset/26975.csv?lang=en"
    pop_data = pd.read_csv(pop_data_filename, quotechar='"', usecols=[0, 1, 3], converters={"year": int})

    pop_data = pd.concat([pop_data, pop_data["region"].str.split(" ", 1, True)], axis=1)
    pop_data.rename(inplace=True, columns={0: "municip_no", 1: "municip_name"})

    def municipality_number(val):
        try:
            return int(val[2:])
        except ValueError:
            return 0

    pop_data["municip_no"].apply(municipality_number)

    #num_per_municip_per_day = disease_data

    aggregate_per_day(disease_data, location_data, pop_data)


def aggregate_per_day(disease_data, location_data, pop_data):
    pass

main()
