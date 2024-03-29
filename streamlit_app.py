import time

import folium
import geopandas as gpd
import pandas as pd
import requests
import streamlit as st
from google.protobuf.json_format import MessageToDict
from google.transit import gtfs_realtime_pb2
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Bus GTFS-RT Locator",
    page_icon="🚌",
)

st.title("Bus GTFS-RT Locator")

HEADERS = {"api_key": st.secrets["wmata_api_key"]}


def get_gtfsrt_vehicle_positions(
    bus_numbers: list[int], headers: dict[str]
) -> gpd.GeoDataFrame | None:
    """Queries GTFS-RT Realtime API and returns a geodataframe for a set of bus numbers.

    Args:
        bus_numbers (list[int]): A list of bus numbers from user input.
        headers (dict): A dict with the API key for the GTFS-RT feed and any other
            required info.

    Returns:
        gpd.GeoDataFrame | None: If selected buses are in service, returns a
            geodataframe with one row per bus and GTFS-RT fields.
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(
        "https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb", headers=headers
    )

    feed.ParseFromString(response.content)
    feed_list = [
        MessageToDict(entity) for entity in feed.entity if int(entity.id) in bus_numbers
    ]
    if len(feed_list) == 0:
        return None
    df_vehicle_positions = pd.json_normalize(feed_list)
    df_vehicle_positions.columns = [
        "bus_id",
        "trip_id",
        "start_date",
        "route_id",
        "latitude",
        "longitude",
        "bearing",
        "speed",
        "stop_sequence",
        "stop_status",
        "timestamp",
        "stop_id",
        "vehicle_id",
    ]
    gdf_vehicle_positions = gpd.GeoDataFrame(
        df_vehicle_positions,
        geometry=gpd.points_from_xy(
            df_vehicle_positions.longitude, df_vehicle_positions.latitude
        ),
    )

    gdf_vehicle_positions["t"] = pd.to_datetime(
        gdf_vehicle_positions.timestamp.astype(int) * 1000000000, utc=True
    ).dt.tz_convert("America/New_York")

    return gdf_vehicle_positions


def main() -> None:
    bus_number_str = st.text_input(
        "Enter up to 10 bus number(s), seperated by a comma:",
        "4766, 4744, 4754, 4778, 1061, 1060, 4772, 4775, 4780",
    )

    try:
        bus_numbers = bus_number_str.replace(" ", "").split(",")
        bus_numbers = [int(x) for x in bus_numbers]
    except ValueError as e:
        st.error(e)

    if len(bus_numbers) > 10:
        st.error("Too many buses...")

    # center on L'Enfant Plaza HQ
    start_location = [38.884863, -77.021447]
    start_zoom = 10
    m = folium.Map(location=start_location, zoom_start=start_zoom)

    while True:
        # Get a geodataframe of vehicle positions if they're logged on and on a revenue trip
        gdf_vehicle_positions = get_gtfsrt_vehicle_positions(bus_numbers, HEADERS)
        if gdf_vehicle_positions is None:
            st.write("No buses in service")
        else:
            center_point = gdf_vehicle_positions.dissolve().centroid
            center = [center_point[0].y, center_point[0].x]

            fg = folium.FeatureGroup(name="Vehicle Positions")
            for vehicle_position in gdf_vehicle_positions.itertuples():
                fg.add_child(
                    folium.Marker(
                        location=[
                            vehicle_position.latitude,
                            vehicle_position.longitude,
                        ],
                        icon=folium.Icon(color="blue", prefix="fa", icon="bus"),
                        popup=f"bus: {vehicle_position.bus_id}<br>route: {vehicle_position.route_id}<br>last update: {vehicle_position.t}",
                        tooltip=f"bus: {vehicle_position.bus_id}<br>route: {vehicle_position.route_id}<br>last update: {vehicle_position.t}",
                    )
                )

            # call to render Folium map in Streamlit
            st.dataframe(
                pd.DataFrame(
                    gdf_vehicle_positions[
                        ["bus_id", "t", "trip_id", "route_id", "latitude", "longitude"]
                    ]
                )
            )
            # m = gdf_vehicle_positions.explore(m=m, name="Vehicle Positions")
            st_folium(m, feature_group_to_add=fg, use_container_width=True)

            time.sleep(30)


if __name__ == "__main__":
    main()
