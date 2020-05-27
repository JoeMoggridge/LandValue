import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import numpy as np



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
    df['middle'] = df['geometry'].copy().apply(lambda x: x.representative_point().coords[:])
    df['middle'] = [middle[0] for middle in df['middle']]
    for idx, row in df.iterrows():
        text = idx.replace(' ', '\n')
        annotations.append(
            plt.annotate(s=text, xy=row['middle'], horizontalalignment='center', fontsize=font_scale, visible=False)
        )
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


if __name__ == '__main__':

    LA = gpd.read_file('Local_Authority_Districts__December_2017__Boundaries_in_Great_Britain-shp'
                       '\\Local_Authority_Districts__December_2017__Boundaries_in_Great_Britain.shp')

    # tweak the names so we get more matches
    for i in range(len(LA)):
        LA.lad17nm[i] = LA.lad17nm[i].split(',')[0].strip()  # drop anything after a comma
        LA.lad17nm[i] = LA.lad17nm[i].replace('South Bucks', 'South Buckinghamshire')
        LA.lad17nm[i] = LA.lad17nm[i].replace('Newcastle upon Tyne', 'Newcastle-upon-Tyne')


    LA.set_index('lad17nm', inplace=True)

    # Ideally I would only parse column D when reading this file.
    # However, I can't figure out the correct syntax for that, so I'll just disgard the unneccassary columns.
    prices = pd.read_excel('Land_value_estimates.xlsx', 'Residential land', header=2, skiprows=1, index_col=2,
                           names=['Unamed', 'Region', 'Local authority', '£/ha'])
    prices = prices.drop(columns={'Unamed', 'Region'})
    prices = prices.loc[prices.index.dropna()]  # drop 'Nan' indexed rows.

    # tweak the names so that we get more matches
    prices.reset_index(inplace=True)
    for i in range(len(prices)):
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].split('(')[0].strip()
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].replace('&', 'and')
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].replace('Bromley London', 'Bromley')
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].replace('Kings Lynn', "King's Lynn")
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].replace('Broxstowe', "Broxtowe")
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].replace('Durham', "County Durham")
        prices.loc[i, 'Local authority'] = prices.loc[i, 'Local authority'].replace('St. Helens', "St Helens")

    prices.set_index('Local authority', inplace=True)

    joined = LA.join(prices)

    # scale by factor of 1 million
    joined['£/ha'] = joined['£/ha']/1e6

    plot_df(joined)
