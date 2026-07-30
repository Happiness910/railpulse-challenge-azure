import azure.functions as func
import logging
import requests
import json
import time
import os
import pyodbc
from datetime import datetime   # Conversion timestamp Unix -> date SQL

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="railpulse_ingestion")
def railpulse_ingestion(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("RailPulse ingestion started.")

    # Récupération sécurisée de la chaîne de connexion
    # La valeur est stockée dans Azure Function App Settings
    sql_connection = os.environ["SQL_CONNECTION_STRING"]


    # Endpoint iRail
    url = "https://api.irail.be/liveboard/"


    # Station interrogée
    params = {
        "station": "Gembloux",
        "format": "json"
    }


    headers = {
        "User-Agent": "RailPulseChallenge/1.0"
    }


    max_attempts = 3


    for attempt in range(max_attempts):

        try:
            logging.info(f"Attempt {attempt + 1}/{max_attempts}")


            # Appel API iRail
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=10
            )


            if response.status_code == 200:

                # Transformation de la réponse JSON
                data = response.json()


                # Affichage temporaire pour vérifier la structure du JSON
                logging.info(json.dumps(data, indent=2)[:5000])


                try:

                    # Connexion Azure SQL
                    conn = pyodbc.connect(sql_connection)
                    cursor = conn.cursor()


                    # =====================================================
                    # 1) INSERTION DE LA STATION
                    # =====================================================

                    station_name = data["stationinfo"]["name"]


                    cursor.execute(
                        """
                        INSERT INTO stations (name)
                        VALUES (?)
                        """,
                        station_name
                    )


                    # Récupération de l'id de la station créée
                    cursor.execute(
                        """
                        SELECT station_id
                        FROM stations
                        WHERE name = ?
                        """,
                        station_name
                    )


                    station_id = cursor.fetchone()[0]


                    # =====================================================
                    # 2) INSERTION DES VEHICULES + LIVEBOARD RECORDS
                    # =====================================================


                    departures = data["departures"]["departure"]


                    for departure in departures:


                        # -----------------------------
                        # Table vehicles
                        # -----------------------------

                        vehicle_name = departure["vehicleinfo"]["shortname"]


                        cursor.execute(
                            """
                            INSERT INTO vehicles (name)
                            VALUES (?)
                            """,
                            vehicle_name
                        )


                        # Récupération de l'id du véhicule
                        cursor.execute(
                            """
                            SELECT vehicle_id
                            FROM vehicles
                            WHERE name = ?
                            """,
                            vehicle_name
                        )


                        vehicle_id = cursor.fetchone()[0]


                        # -----------------------------
                        # Table liveboard_records
                        # -----------------------------

                        destination = departure["station"]


                        # iRail donne un timestamp Unix
                        # SQL attend un DATETIME
                        departure_time = datetime.fromtimestamp(
                            int(departure["time"])
                        )


                        # iRail donne un retard en secondes
                        # Notre DB stocke les minutes
                        delay_minutes = int(
                            departure.get("delay", 0)
                        ) // 60


                        platform = departure.get("platform")


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


                    # Validation des insertions
                    conn.commit()

                    # Fermeture connexion
                    conn.close()


                    logging.info(
                        "Station, vehicles and liveboard records inserted successfully."
                    )


                except Exception as e:

                    logging.error(
                        f"SQL insertion failed: {e}",
                        exc_info=True
                    )

                    return func.HttpResponse(
                        f"SQL insertion failed: {e}",
                        status_code=500
                    )


                # Retour du JSON dans le navigateur
                return func.HttpResponse(
                    json.dumps(data),
                    mimetype="application/json",
                    status_code=200
                )


            else:

                logging.warning(
                    f"API returned status {response.status_code}: {response.text}"
                )


        except requests.exceptions.RequestException as e:

            logging.error(
                f"Request failed: {e}"
            )


        # Pause avant nouvel essai
        if attempt < max_attempts - 1:
            time.sleep(2)



    return func.HttpResponse(
        "Unable to fetch SNCB data after 3 attempts.",
        status_code=503
    )

