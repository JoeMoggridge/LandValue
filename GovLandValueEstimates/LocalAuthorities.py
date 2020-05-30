import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def plot_df(df):
    fig = plt.figure(figsize=(7, 8))
    ax = fig.add_subplot(111)
    ax.set_axis_off()

    df.plot(ax=ax, column=df['£/ha'], legend=True, scheme="User_Defined", cmap='viridis',
            edgecolor="white", linewidth=0.1,
            legend_kwds={'title':'£ million/ha', 'loc':'lower left', 'bbox_to_anchor': (1, 0)},
            classification_kwds=dict(bins=[1, 2, 3, 4, 6, 8, 10]),
            missing_kwds={'color': 'lightgrey',  "label": "Missing values"} )

    # add labels (which will be too small to see unless we zoom in)
    font_scale = 0  # we set the font size to zero here. It will be set to a non-zero value if we zoom in.
    annotations = []
    df['middle'] = df['geometry'].copy().apply(lambda x:  x.representative_point().coords[:])
    df['middle'] = [middle[0] for middle in df['middle']]
    for idx, row in df.iterrows():
        text = idx.replace(' ', '\n')
        annotations.append(
            plt.annotate(s=text, xy=row['middle'], horizontalalignment='center', fontsize=font_scale, visible=False))

    ax.callbacks.connect('xlim_changed', on_xlims_change)
    df.drop(columns='middle', inplace=True)

    plt.show()

def on_xlims_change(ax):

    font_scale = np.round((7e5 - (ax.get_xlim()[1] - ax.get_xlim()[0])) / 1e5)
    show_annotations = font_scale > 3

    # redraw annotations at this new scale
    for child in ax.get_children():
        if isinstance(child, plt.Annotation):
            plt.annotate(
                s=child.get_text(), xy=child.xy,
                horizontalalignment='center', fontsize=font_scale, visible=show_annotations)
            child.remove()

def fuzzy_merge(df_1, df_2, key1, key2, threshold=90, limit=1):
    """
    :param df_1: the left table to join
    :param df_2: the right table to join
    :param key1: key column of the left table
    :param key2: key column of the right table
    :param threshold: how close the matches should be to return a match, based on Levenshtein distance
    :param limit: the amount of matches that will get returned, these are sorted high to low
    :return: dataframe with boths keys and matches
    """
    s = df_2[key2].tolist()

    m = df_1[key1].apply(lambda x: process.extract(x, s, limit=limit))
    df_1['matches'] = m

    m2 = df_1['matches'].apply(lambda x: ', '.join([i[0] for i in x if i[1] >= threshold]))
    confidence = df_1['matches'].apply(lambda x: x[0][1])
    df_1['matches'] = m2
    df_1['confidence'] = confidence


    return df_1.merge(df_2, left_on='matches', right_on=key2, how='left')

if __name__ == '__main__':

    LA = gpd.read_file('Local_Authority_Districts__December_2017__Boundaries_in_Great_Britain-shp'
                       '\\Local_Authority_Districts__December_2017__Boundaries_in_Great_Britain.shp')
    LA = LA[['lad17nm', 'long', 'lat', 'geometry']]  # we only care about some columns

    # Ideally I would only parse column D when reading this file.
    # However, I can't figure out the correct syntax for that, so I'll just disgard the unneccassary columns.
    prices = pd.read_excel('Land_value_estimates.xlsx', 'Residential land', header=2, skiprows=1, index_col=2,
                           names=['Unamed', 'Region', 'Local authority', '£/ha'])
    prices = prices.drop(columns={'Unamed', 'Region'})
    prices = prices.loc[prices.index.dropna()]  # drop 'Nan' indexed rows.
    prices.reset_index(inplace=True)

    #cut out a  whole load of annoying brackets that mess things up
    for i in range(len(prices)):
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].split('(')[0].strip()

    joined = fuzzy_merge(LA, prices, 'lad17nm', 'Local authority')

    # for debugging purposes, save the data frame.
    joined.to_csv('joined.csv', '|')

    # scale by factor of 1 million
    joined['£/ha'] = joined['£/ha']/1e6

    # plot_df expects dataframe indexed by county.
    joined.set_index('lad17nm', inplace=True)
    plot_df(joined)
