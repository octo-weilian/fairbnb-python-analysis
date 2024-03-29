#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point
import numpy as np

def listing2gdf(url):
    
    #create dataframe from url
    cols= ['id','room_type','beds','latitude','longitude',
           'availability_365','host_is_superhost','price','number_of_reviews']
    df = pd.read_csv(url,usecols=cols)
    df['price'] = df['price'].str.replace('$','')
    df['price'] = pd.to_numeric(df['price'],errors='coerce')
    
    #create geopandas geodataframe
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    df = df.drop(['latitude', 'longitude'], axis=1)
    gdf = GeoDataFrame(df, crs={'init': 'epsg:4326'}, geometry=geometry)
    gdf['date'] = url.split('/')[-3]
    return gdf

def census2gdf(geojson_path):
    
    #load census data from geojson and calculate area
    nbh_geojson = gpd.read_file(geojson_path, driver='GeoJSON')
    nbh_gdf = GeoDataFrame(nbh_geojson, crs={'init': 'epsg:4326'}, geometry=nbh_geojson['geometry'])
    nbh_gdf['area_km2'] = nbh_gdf.to_crs({'init': 'epsg:28992'})['geometry'].area/10**6
    
    return nbh_gdf


def aggregate(airbnb_gdf,nbh_gdf,room_gdf,entire_home_gdf,superhost_gdf,illegal_gdf):
    #perform spatial join
    join_all = gpd.sjoin(nbh_gdf,airbnb_gdf,how='inner',op='contains').groupby('Buurt').size().reset_index(name='Airbnb_ListingCount')
    nbh_gdf = nbh_gdf.merge(join_all,on='Buurt',how='outer')
    
    join_room = gpd.sjoin(nbh_gdf,room_gdf,how='inner',op='contains').groupby('Buurt').size().reset_index(name='Airbnb_RoomRentalCount')
    nbh_gdf = nbh_gdf.merge(join_room,on='Buurt',how = 'outer')
    
    join_entire = gpd.sjoin(nbh_gdf,entire_home_gdf,how='inner',op='contains').groupby('Buurt').size().reset_index(name='Airbnb_EntireLodgeCount')
    nbh_gdf = nbh_gdf.merge(join_entire,on='Buurt',how = 'outer')
    
    join_superhost = gpd.sjoin(nbh_gdf,superhost_gdf,how='inner',op='contains').groupby('Buurt').size().reset_index(name='Airbnb_SuperhostCount')
    nbh_gdf = nbh_gdf.merge(join_superhost,on='Buurt',how = 'outer')
    
    join_beds = gpd.sjoin(nbh_gdf,airbnb_gdf,how='inner',op='contains').groupby(['Buurt'])['beds'].sum().reset_index(name='Airbnb_BedsCount')
    nbh_gdf = nbh_gdf.merge(join_beds,on='Buurt',how = 'outer')
    
    join_price_room = gpd.sjoin(nbh_gdf,room_gdf,how='inner',op='contains').groupby(['Buurt'])['price'].mean().reset_index(name='Airbnb_AvgPriceRoom')
    nbh_gdf = nbh_gdf.merge(join_price_room,on='Buurt',how = 'outer')
    
    join_price_entire = gpd.sjoin(nbh_gdf,entire_home_gdf,how='inner',op='contains').groupby(['Buurt'])['price'].mean().reset_index(name='Airbnb_AvgPriceEntireLodge')
    nbh_gdf = nbh_gdf.merge(join_price_entire,on='Buurt',how = 'outer')
    
    join_illegal = gpd.sjoin(nbh_gdf,illegal_gdf,how='inner',op='contains').groupby('Buurt').size().reset_index(name='Airbnb_Over30Days')
    nbh_gdf = nbh_gdf.merge(join_illegal,on='Buurt',how='outer')
    
    
    nbh_gdf.update(nbh_gdf[['Airbnb_ListingCount','Airbnb_RoomRentalCount',
                            'Airbnb_EntireLodgeCount','Airbnb_SuperhostCount',
                            'Airbnb_BedsCount','Airbnb_AvgPriceRoom','Airbnb_AvgPriceEntireLodge']].fillna(value=0))
    return nbh_gdf

def CalculateTouristIntensity(nbh_gdf,year):
    
    #calculate tourist intensity (bed per 1000 inhabitants)
    #calculate population density (inhabitant per km2)
    #calculate listingcount
    if year in list(nbh_gdf.columns[3:7]):
        nbh_gdf['PopDensity_km2'] = nbh_gdf['2018']/nbh_gdf['area_km2']
        nbh_gdf['Airbnb_TouristIntensity'] = (nbh_gdf['Airbnb_BedsCount']/nbh_gdf[year])
        nbh_gdf['Airbnb_TouristIntensity'] = nbh_gdf['Airbnb_TouristIntensity'].replace([np.inf, -np.inf], 0)
        nbh_gdf['Airbnb_TouristIntensity_scaled'] = (nbh_gdf['Airbnb_TouristIntensity']-nbh_gdf['Airbnb_TouristIntensity'].min())/(nbh_gdf['Airbnb_TouristIntensity'].max()-nbh_gdf['Airbnb_TouristIntensity'].min())
        return nbh_gdf
    
    elif int(year)>2018:
        nbh_gdf['Airbnb_ListingCount']= nbh_gdf['Airbnb_RoomRentalCount'] + nbh_gdf['Airbnb_EntireLodgeCount']
        nbh_gdf['PopDensity_km2'] = nbh_gdf['2018']/nbh_gdf['area_km2']
        nbh_gdf['Airbnb_TouristIntensity'] = (nbh_gdf['Airbnb_BedsCount']/nbh_gdf['2018'])
        nbh_gdf['Airbnb_TouristIntensity'] = nbh_gdf['Airbnb_TouristIntensity'].replace([np.inf, -np.inf], 0)
        nbh_gdf['Airbnb_TouristIntensity_scaled'] = (nbh_gdf['Airbnb_TouristIntensity']-nbh_gdf['Airbnb_TouristIntensity'].min())/(nbh_gdf['Airbnb_TouristIntensity'].max()-nbh_gdf['Airbnb_TouristIntensity'].min())
        return nbh_gdf
    else:
        pass
    
    
    
    
    
    
    
    


