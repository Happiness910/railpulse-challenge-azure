CREATE TABLE stations (
    station_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE vehicles (
    vehicle_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE liveboard_records (
    record_id INT IDENTITY(1,1) PRIMARY KEY,

    station_id INT NOT NULL,
    vehicle_id INT NOT NULL,

    destination VARCHAR(100),
    departure_time DATETIME NOT NULL,
    delay_minutes INT DEFAULT 0,
    platform VARCHAR(20),

    created_at DATETIME DEFAULT GETDATE(),


    CONSTRAINT FK_liveboard_station
        FOREIGN KEY (station_id)
        REFERENCES stations(station_id),


    CONSTRAINT FK_liveboard_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id),


    -- Protection contre les doublons lors des Timer Trigger
    CONSTRAINT UQ_liveboard_record
        UNIQUE (
            station_id,
            vehicle_id,
            departure_time
        )
);