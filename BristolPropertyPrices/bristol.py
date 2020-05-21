
import matplotlib.pyplot as plt
import geopandas as gpd
import requests as requests
import json
import xml.etree.cElementTree as ET
import pandas as pd
import numpy as np
import mapclassify as mc

def parse_data(response, idx):
    """

    :param response: xml response from Zoopla Api
    :return:
    """

    xml = ET.fromstring(response.content.decode("utf-8"))

    if (xml.find('error_code') is not None):
        print("Error is: " + xml.find('error_string'))

    else:
        sales = pd.DataFrame(index=idx, data={'price': [0], 'count': [0]})

        for areas in xml.iter('areas'):

            postcode = areas.find('prices_url').text.split('/')[-1]
            sector = postcode[:-2].replace('-', ' ').upper() # sector is first 4 digits of postcode, by which dataframe is indexed.

            sales.loc[sector, 'price'] += float(areas.find('average_sold_price_7year').text)
            sales.loc[sector, 'count'] += int(areas.find('number_of_sales_7year').text)

            print('write to: ' + str(sector))

        averageprice = sales['price']/sales['count']
        averagepricemasked = averageprice[sales['count'] != 0].copy()
        newseries= pd.DataFrame(index=idx, data=averagepricemasked, columns={'avg_price'})

        return newseries

        df['avg_price'] = sales['price']/sales['count']
        df_non_zero = df[sales['count'] != 0].copy()  # only use values where count was not zero (thus we discard any divide by zero errors)

        return df_non_zero




def CallZooplaAPI (district, output_type='outcode',  area_type='postcodes'):
    """
    limited to 100 calls per hour. If I want to query ~3000 areas, that will take 30 hours. Hmm, bit shit.
    limited to 100 calls per second.

    :param str district: first 3 digits of postcode
    :param str output_type:
    :param str area_type: if this is 'postcodes' then each <area> tag will correspond to a postcode
    :return:
    """
    print(district)

    parameters = {  'postcode'  : district,
                    'output_type': output_type,
                    'area_type' : area_type,
                    'api_key'   : '545xeuuxq8gn9db7hpqbn5h6' }
    response = requests.get("http://api.zoopla.co.uk/api/v1/average_sold_prices.xml", params=parameters)

    if response.status_code != 200:
        print("bad status code: " + str(response.status_code))
        if response.status_code == 403:
            return response
        return False

    return response

    #response = requests.get( "http://api.zoopla.co.uk/api/v1/average_sold_prices.xml?postcode=bs6+5rg&output_type=county&area_type=streets&api_key=545xeuuxq8gn9db7hpqbn5h6")


def plot_df(df):

    # i would like to figure out how to change the text of this legend, but it seems to be v. tricky.
    df.plot(column=df['avg_price'], legend=True, scheme="User_Defined", cmap='viridis',
            legend_kwds={'title': '£'},
            classification_kwds=dict(bins=[1e5, 2e5, 3e5, 4e5]),
            missing_kwds={'color': 'lightgrey',  "label": "Missing values"})

    # add labels
    df['middle'] = df['geometry'].copy().apply(lambda x: x.representative_point().coords[:])
    df['middle'] = [middle[0] for middle in df['middle']]
    for idx, row in df.iterrows():
        plt.annotate(s=idx, xy=row['middle'], horizontalalignment='center', fontsize=6)

    plt.show()

    df.drop(columns='middle')


if __name__ == '__main__':

    # 1 Get shapefiles for areas
    # areas = first 2 digits of postcode
    # districts = first 3 digits
    # sectors = first 4 digits
    load_from_file = False

    if load_from_file:
        bristol = gpd.read_file('bristol.shp')
        bristol.set_index('sector', inplace=True)  # restore the index so its nice to work with
        bristol.index.astype(str, copy=True)

    else:
        lsoas = gpd.read_file('UK-postcode-boundaries-Jan-2015\\Distribution\\Sectors.shp')

        # only look at bristol postcodes
        bristol = lsoas[lsoas.name.apply((lambda s: str(s).find('BS') == 0))].copy()
        bristol.reset_index(drop=True, inplace=True)
        bristol.set_index('name', inplace=True)
        bristol.index.name = 'sector'

        # take only the first 3 digits
        half_codes = bristol.index.str[0:4].str.strip().unique()
        # take only the first ~20
        half_codes = half_codes[0:20]

        proceed = input('about to make ' + str(len(half_codes)) + ' calls. Proceed? y/n \n')
        if proceed != 'y':
            exit()

        bristol['avg_price'] = np.nan

        for halfcode in half_codes:
            # zoopla API expects either full postcode, or half ( ie first 3 digits)
            prices = CallZooplaAPI(halfcode)

            if prices != False:
                if prices.status_code == 403:
                    break
                else:
                    newdata = parse_data(prices, bristol.index.copy())
                    bristol.update(newdata)
                    # I pass a copy of the index here just to make sure that parse_data()
                    # doesn't accidentally mess the bristol index up.

    if not load_from_file:
        # annoyingly, it seems that geopandas can't write a non-numeric index corectly, so I have to reset the index
        # before I save.
        saveable = bristol.reset_index()
        saveable.to_file('bristol.shp', index=True)
        print('dataframe written to bristol.shp')

    plot_df(bristol.copy())





