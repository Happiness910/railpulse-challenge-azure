import azure.functions as func
import logging
import requests
import json
import time
import os
import pyodbc
from datetime import datetime


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)



# ==========================================================
# FONCTION CENTRALE D'INGESTION
# Elle récupère une station iRail et écrit dans Azure SQL
# Elle sera utilisée par :
# - HTTP Trigger
# - Timer Trigger
# ==========================================================

def fetch_and_store_station(station_name):

    logging.info(f"Starting ingestion for {station_name}")


    # Récupération sécurisée de la chaîne SQL
    # Stockée dans Azure Function App Settings
    sql_connection = os.environ["SQL_CONNECTION_STRING"]


    url = "https://api.irail.be/liveboard/"


    params = {
        "station": station_name,
        "format": "json"
    }


    headers = {
        "User-Agent": "RailPulseChallenge/1.0"
    }



    # ======================================================
    # 1) APPEL API iRail
    # ======================================================

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )


    if response.status_code != 200:
        raise Exception(
            f"iRail API error {response.status_code}"
        )


    data = response.json()


    # Log temporaire pour vérifier les données
    logging.info(
        json.dumps(data, indent=2)[:2000]
    )



    # ======================================================
    # 2) CONNEXION AZURE SQL
    # ======================================================

    conn = pyodbc.connect(sql_connection)
    cursor = conn.cursor()



    try:


        # ==================================================
        # INSERTION STATION
        # ==================================================

        real_station_name = data["stationinfo"]["name"]


        # Evite les doublons de stations
        cursor.execute(
            """
            IF NOT EXISTS (
                SELECT 1 FROM stations WHERE name = ?
            )
            INSERT INTO stations(name)
            VALUES (?)
            """,
            real_station_name,
            real_station_name
        )


        cursor.execute(
            """
            SELECT station_id
            FROM stations
            WHERE name = ?
            """,
            real_station_name
        )


        station_id = cursor.fetchone()[0]



        # ==================================================
        # INSERTION VEHICLES + LIVEBOARD RECORDS
        # ==================================================

        departures = data.get(
            "departures",
            {}
        ).get(
            "departure",
            []
        )


        for departure in departures:


            # -------------------------------
            # VEHICLES TABLE
            # -------------------------------

            vehicle_name = departure["vehicleinfo"]["shortname"]


            cursor.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM vehicles WHERE name = ?
                )
                INSERT INTO vehicles(name)
                VALUES (?)
                """,
                vehicle_name,
                vehicle_name
            )


            cursor.execute(
                """
                SELECT vehicle_id
                FROM vehicles
                WHERE name = ?
                """,
                vehicle_name
            )


            vehicle_id = cursor.fetchone()[0]



            # -------------------------------
            # LIVEBOARD_RECORDS TABLE
            # -------------------------------


            destination = departure["station"]


            # Conversion timestamp Unix -> DATETIME SQL
            departure_time = datetime.fromtimestamp(
                int(departure["time"])
            )


            # iRail donne un retard en secondes
            # Notre DB stocke des minutes
            delay_minutes = (
                int(departure.get("delay", 0))
                // 60
            )


            platform = departure.get(
                "platform"
            )



            cursor.execute(
                """
                INSERT INTO liveboard_records
                (
                    station_id,
                    vehicle_id,
                    destination,
                    departure_time,
                    delay_minutes,
                    platform
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    station_id,
                    vehicle_id,
                    destination,
                    departure_time,
                    delay_minutes,
                    platform
                )
            )



        # Validation SQL
        conn.commit()


        logging.info(
            f"{station_name} successfully stored"
        )


    except Exception as e:

        conn.rollback()

        logging.error(
            f"Database error: {e}",
            exc_info=True
        )

        raise e


    finally:

        conn.close()



# ==========================================================
# HTTP TRIGGER
# Endpoint manuel :
# https://...azurewebsites.net/api/railpulse_ingestion
# ==========================================================


@app.route(
    route="railpulse_ingestion"
)
def railpulse_ingestion(req: func.HttpRequest):


    logging.info(
        "Manual ingestion started"
    )


    try:

        fetch_and_store_station(
            "Gembloux"
        )


        return func.HttpResponse(
            "Manual ingestion successful",
            status_code=200
        )


    except Exception as e:

        logging.error(
            str(e),
            exc_info=True
        )

        return func.HttpResponse(
            f"Ingestion failed: {e}",
            status_code=500
        )



# ==========================================================
# TIMER TRIGGER
#
# Exécution automatique toutes les 15 minutes
#
# CRON:
# 0 */15 * * * *
#
# Exemple:
# 12:00
# 12:15
# 12:30
# 12:45
# ==========================================================


@app.timer_trigger(
    schedule="0 */15 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def railpulse_timer_ingestion(
    timer: func.TimerRequest
):


    logging.info(
        "Scheduled ingestion started"
    )


    if timer.past_due:

        logging.warning(
            "Timer execution was late"
        )


    # Stations surveillées automatiquement

    stations = [
        "Gembloux",
        "Antwerpen-Centraal",
        "Gent-Sint-Pieters",
        "Liège-Guillemins"
    ]


    for station in stations:

        try:

            fetch_and_store_station(
                station
            )


        except Exception as e:

            logging.error(
                f"{station} failed: {e}"
            )